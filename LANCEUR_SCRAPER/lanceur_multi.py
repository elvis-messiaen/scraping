#!/usr/bin/env python3
"""
LANCEUR MULTI-APPROCHES - Lance plusieurs scrapers simultanément
Threading + Multiprocessing + Queue Redis
"""

import os
import sys
import json
import time
import subprocess
import threading
import multiprocessing as mp
from datetime import datetime
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from queue import Queue
import psutil
import random

# Redis optionnel (si disponible)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class LanceurMulti:
    def __init__(self, mode_test=False):
        # Chemins
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        self.dossier_scrapers = os.path.join(parent_dir, 'SCRAPERS')
        
        # Configuration
        self.max_scrapers_simultanes = 5  # Limite anti-ban Amazon
        self.mode_auto = True  # Choix automatique de l'approche
        self.mode_test = mode_test  # Mode test avec seulement 3 scrapers
        
        # Files d'attente
        self.queue_threading = Queue()
        self.queue_multiprocessing = mp.Queue()
        self.scrapers_liste = []
        
        # Monitoring
        self.resultats = mp.Manager().dict()
        self.verrou_log = threading.Lock()
        
        # Redis (optionnel)
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                self.redis_client.ping()
                print("✅ Redis connecté")
            except:
                self.redis_client = None
                print("⚠️  Redis non disponible")
        
        # Fichiers
        self.fichier_progres = 'progres_multi.json'
        self.fichier_log = 'logs_multi.txt'
        
    def log_thread_safe(self, message: str):
        """Log thread-safe"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ligne_log = f"[{timestamp}] {message}"
        
        with self.verrou_log:
            print(ligne_log)
            try:
                with open(self.fichier_log, 'a', encoding='utf-8') as f:
                    f.write(ligne_log + '\n')
            except Exception as e:
                print(f"❌ Erreur log: {e}")
    
    def charger_scrapers(self):
        """Charge la liste des scrapers"""
        try:
            chemin_liste = os.path.join(self.dossier_scrapers, 'liste_scrapers.json')
            if os.path.exists(chemin_liste):
                with open(chemin_liste, 'r', encoding='utf-8') as f:
                    self.scrapers_liste = json.load(f)
                self.log_thread_safe(f"✅ {len(self.scrapers_liste)} scrapers chargés")
            else:
                self.log_thread_safe("❌ liste_scrapers.json introuvable")
                return False
        except Exception as e:
            self.log_thread_safe(f"❌ Erreur chargement: {e}")
            return False
        return True
    
    def analyser_systeme(self) -> Dict[str, Any]:
        """Analyse les ressources système pour choisir l'approche"""
        cpu_count = mp.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        analyse = {
            'cpu_cores': cpu_count,
            'cpu_usage': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'scrapers_count': len(self.scrapers_liste)
        }
        
        self.log_thread_safe(f"💻 Système: {cpu_count} cores, CPU:{cpu_percent:.1f}%, RAM:{memory.percent:.1f}%")
        return analyse
    
    def choisir_strategie(self, analyse: Dict[str, Any]) -> str:
        """Choix intelligent de la stratégie basé sur les ressources"""
        if analyse['memory_percent'] > 85:
            return 'redis'  # Système surchargé
        elif analyse['cpu_usage'] > 80:
            return 'threading'  # CPU saturé, éviter multiprocessing
        elif analyse['scrapers_count'] > 500 and analyse['cpu_cores'] >= 8:
            return 'multiprocessing'  # Beaucoup de scrapers + CPU puissant
        elif analyse['scrapers_count'] > 200:
            return 'mixed'  # Approche mixte
        else:
            return 'threading'  # Défaut pour petits volumes
    
    def executer_scraper_subprocess(self, scraper: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un scraper via subprocess"""
        nom_fichier = scraper['nom_fichier']
        nom_categorie = scraper['nom_categorie']
        worker_id = mp.current_process().pid
        
        try:
            self.log_thread_safe(f"🚀 [{worker_id}] Lancement: {nom_categorie}")
            
            chemin_scraper = os.path.join(self.dossier_scrapers, nom_fichier)
            if not os.path.exists(chemin_scraper):
                return {'scraper': nom_fichier, 'statut': 'echec', 'erreur': 'Fichier introuvable'}
            
            debut = time.time()
            
            # Délai anti-ban aléatoire
            time.sleep(random.uniform(1, 5))
            
            # Exécution
            result = subprocess.run(
                [sys.executable, chemin_scraper],
                cwd=self.dossier_scrapers,
                capture_output=True,
                text=True,
                timeout=7200  # 2h timeout
            )
            
            duree = time.time() - debut
            
            if result.returncode == 0:
                self.log_thread_safe(f"✅ [{worker_id}] {nom_categorie} terminé ({duree/60:.1f}min)")
                return {'scraper': nom_fichier, 'statut': 'succes', 'duree': duree}
            else:
                erreur = result.stderr[:200] if result.stderr else 'Erreur inconnue'
                self.log_thread_safe(f"❌ [{worker_id}] {nom_categorie} échoué: {erreur}")
                return {'scraper': nom_fichier, 'statut': 'echec', 'erreur': erreur}
                
        except subprocess.TimeoutExpired:
            self.log_thread_safe(f"⏰ [{worker_id}] {nom_categorie} timeout")
            return {'scraper': nom_fichier, 'statut': 'timeout', 'erreur': 'Timeout 2h'}
        except Exception as e:
            self.log_thread_safe(f"❌ [{worker_id}] {nom_categorie} erreur: {e}")
            return {'scraper': nom_fichier, 'statut': 'erreur', 'erreur': str(e)}
    
    def worker_multiprocessing(self, queue_in: mp.Queue, resultats_shared: dict, worker_id: int):
        """Worker multiprocessing"""
        while True:
            try:
                scraper = queue_in.get(timeout=10)
                if scraper is None:  # Signal d'arrêt
                    break
                
                resultat = self.executer_scraper_subprocess(scraper)
                resultats_shared[scraper['nom_fichier']] = resultat
                
                queue_in.task_done()
                
            except Exception as e:
                self.log_thread_safe(f"❌ Worker {worker_id} erreur: {e}")
                break
    
    def lancer_multiprocessing(self, scrapers_batch: List[Dict[str, Any]], nb_workers: int):
        """Lance scrapers via multiprocessing"""
        self.log_thread_safe(f"🔄 Mode MULTIPROCESSING - {nb_workers} workers")
        
        # Ajouter scrapers à la queue
        for scraper in scrapers_batch:
            self.queue_multiprocessing.put(scraper)
        
        # Lancer workers
        processes = []
        for i in range(nb_workers):
            p = mp.Process(
                target=self.worker_multiprocessing,
                args=(self.queue_multiprocessing, self.resultats, i)
            )
            p.start()
            processes.append(p)
        
        # Attendre completion
        for scraper in scrapers_batch:
            while scraper['nom_fichier'] not in self.resultats:
                time.sleep(1)
        
        # Arrêter workers
        for _ in range(nb_workers):
            self.queue_multiprocessing.put(None)
        
        for p in processes:
            p.join(timeout=10)
            if p.is_alive():
                p.terminate()
    
    def worker_threading(self, queue_in: Queue):
        """Worker threading"""
        worker_id = threading.current_thread().ident
        
        while True:
            try:
                scraper = queue_in.get(timeout=10)
                if scraper is None:
                    break
                
                resultat = self.executer_scraper_subprocess(scraper)
                self.resultats[scraper['nom_fichier']] = resultat
                
                queue_in.task_done()
                
            except Exception as e:
                self.log_thread_safe(f"❌ Thread {worker_id} erreur: {e}")
                break
    
    def lancer_threading(self, scrapers_batch: List[Dict[str, Any]], nb_workers: int):
        """Lance scrapers via threading"""
        self.log_thread_safe(f"🧵 Mode THREADING - {nb_workers} workers")
        
        # Ajouter scrapers à la queue
        for scraper in scrapers_batch:
            self.queue_threading.put(scraper)
        
        # Lancer threads
        threads = []
        for i in range(nb_workers):
            t = threading.Thread(target=self.worker_threading, args=(self.queue_threading,))
            t.start()
            threads.append(t)
        
        # Attendre completion
        self.queue_threading.join()
        
        # Arrêter threads
        for _ in range(nb_workers):
            self.queue_threading.put(None)
        
        for t in threads:
            t.join(timeout=5)
    
    def lancer_redis(self, scrapers_batch: List[Dict[str, Any]]):
        """Lance scrapers via Redis queue"""
        if not self.redis_client:
            self.log_thread_safe("❌ Redis non disponible, fallback threading")
            self.lancer_threading(scrapers_batch, 3)
            return
        
        self.log_thread_safe(f"📡 Mode REDIS - Distribution sur workers distants")
        
        # Ajouter scrapers à Redis
        for scraper in scrapers_batch:
            self.redis_client.lpush('scrapers_queue', json.dumps(scraper))
        
        self.log_thread_safe(f"✅ {len(scrapers_batch)} scrapers ajoutés à Redis queue")
        self.log_thread_safe("💡 Lancez des workers Redis sur d'autres machines:")
        self.log_thread_safe("   python3 redis_worker.py")
    
    def run(self):
        """Fonction principale"""
        self.log_thread_safe("🚀 LANCEUR MULTI-APPROCHES")
        self.log_thread_safe("=" * 50)
        
        # Charger scrapers
        if not self.charger_scrapers():
            return
        
        # Mode test : limiter à 3 scrapers
        if self.mode_test:
            self.scrapers_liste = self.scrapers_liste[:3]
            self.log_thread_safe(f"🧪 MODE TEST: Limité à {len(self.scrapers_liste)} scrapers")
        
        # Analyser système
        analyse = self.analyser_systeme()
        strategie = self.choisir_strategie(analyse)
        
        self.log_thread_safe(f"🎯 Stratégie choisie: {strategie.upper()}")
        
        # Calculer nombre optimal de workers
        nb_workers = min(self.max_scrapers_simultanes, analyse['cpu_cores'])
        self.log_thread_safe(f"👥 {nb_workers} workers simultanés (limite anti-ban: {self.max_scrapers_simultanes})")
        
        # Découper en batches
        batch_size = nb_workers * 10  # 10 scrapers par worker
        total_batches = (len(self.scrapers_liste) + batch_size - 1) // batch_size
        
        try:
            for batch_num in range(total_batches):
                debut_batch = batch_num * batch_size
                fin_batch = min((batch_num + 1) * batch_size, len(self.scrapers_liste))
                scrapers_batch = self.scrapers_liste[debut_batch:fin_batch]
                
                self.log_thread_safe(f"📦 Batch {batch_num+1}/{total_batches} - {len(scrapers_batch)} scrapers")
                
                # Lancer selon la stratégie
                debut_batch_time = time.time()
                
                if strategie == 'threading':
                    self.lancer_threading(scrapers_batch, nb_workers)
                elif strategie == 'multiprocessing':
                    self.lancer_multiprocessing(scrapers_batch, nb_workers)
                elif strategie == 'redis':
                    self.lancer_redis(scrapers_batch)
                elif strategie == 'mixed':
                    # Moitié threading, moitié multiprocessing
                    mid = len(scrapers_batch) // 2
                    self.lancer_threading(scrapers_batch[:mid], nb_workers//2)
                    self.lancer_multiprocessing(scrapers_batch[mid:], nb_workers//2)
                
                duree_batch = time.time() - debut_batch_time
                self.log_thread_safe(f"✅ Batch terminé en {duree_batch/60:.1f}min")
                
                # Pause entre batches
                if batch_num < total_batches - 1:
                    self.log_thread_safe("⏳ Pause 60s entre batches...")
                    time.sleep(60)
        
        except KeyboardInterrupt:
            self.log_thread_safe("⏸️  Arrêt demandé")
        
        finally:
            self.generer_rapport_final()
    
    def generer_rapport_final(self):
        """Rapport final des résultats"""
        succes = sum(1 for r in self.resultats.values() if r.get('statut') == 'succes')
        echecs = sum(1 for r in self.resultats.values() if r.get('statut') in ['echec', 'timeout', 'erreur'])
        total = len(self.resultats)
        
        rapport = f"""
📊 RAPPORT MULTI-LANCEUR
{'=' * 40}
Total traités: {total}
✅ Succès: {succes}
❌ Échecs: {echecs}
📊 Taux succès: {(succes/total*100):.1f}%
"""
        
        self.log_thread_safe(rapport)

if __name__ == "__main__":
    # Configuration multiprocessing
    mp.set_start_method('spawn', force=True)
    
    lanceur = LanceurMulti()
    lanceur.run()