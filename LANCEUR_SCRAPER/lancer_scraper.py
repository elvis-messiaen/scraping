#!/usr/bin/env python3
"""
LANCEUR DE SCRAPERS - Lance tous les scrapers de catégories avec reprise automatique
"""

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime
from typing import List, Dict, Any

# Import de la fonction de mise à jour
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'FONCTIONS'))
from mise_a_jour_complet import mettre_a_jour_complet_json

class LanceurScrapers:
    def __init__(self):
        # Détecter le chemin absolu vers SCRAPERS
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)  # Dossier Scraping
        self.dossier_scrapers = os.path.join(parent_dir, 'SCRAPERS')
        
        self.fichier_progres = 'progres_lanceur.json'
        self.fichier_log = 'logs_lanceur.txt'
        
        # Vérifier que le dossier existe
        if not os.path.exists(self.dossier_scrapers):
            print(f"❌ Dossier SCRAPERS introuvable: {self.dossier_scrapers}")
            print("   Vérifiez que le lanceur est dans LANCEUR_SCRAPER/")
            sys.exit(1)
        self.scrapers_liste = []
        self.progres = {
            'scraper_actuel': 0,
            'scrapers_termines': [],
            'scrapers_echecs': [],
            'debut_session': None,
            'derniere_sauvegarde': None
        }
        
    def regenerer_scrapers_si_necessaire(self):
        """Relance la génération des scrapers si nécessaire"""
        chemin_categories = os.path.join(os.path.dirname(self.dossier_scrapers), 'CATEGORIES', 'categories_amazon_completes.json')
        chemin_liste = os.path.join(self.dossier_scrapers, 'liste_scrapers.json')
        
        # Vérifier si les catégories existent et sont récentes
        if not os.path.exists(chemin_categories):
            self.log("❌ Fichier de catégories manquant, impossible de générer les scrapers")
            return
        
        # Vérifier la taille de la liste vs le nombre de scrapers
        if os.path.exists(chemin_liste):
            try:
                with open(chemin_liste, 'r', encoding='utf-8') as f:
                    liste_actuelle = json.load(f)
                
                # Si moins de 50 scrapers, c'est probablement incomplet (changé de 500 à 50)
                if len(liste_actuelle) < 50:
                    self.log(f"⚠️  Seulement {len(liste_actuelle)} scrapers trouvés, régénération nécessaire...")
                    self.regenerer_scrapers_seulement()
                    return
                
            except Exception as e:
                self.log(f"❌ Erreur lecture liste: {e}")
                self.regenerer_scrapers_seulement()
                return
    
    def regenerer_scrapers_seulement(self):
        """Relance SEULEMENT la génération des scrapers (pas le scraping Amazon)"""
        self.log("🔄 Génération des scrapers depuis JSON existant...")
        
        try:
            # Import direct du module scraper_categorie
            sys.path.append(self.dossier_scrapers)
            
            # Créer une instance et lancer seulement les étapes 2 et 3
            from scraper_categorie import ScraperCategorie
            
            scraper_cat = ScraperCategorie()
            
            # ÉTAPE 2: Génération des scrapers (sans scraping Amazon)
            self.log("🔨 ÉTAPE 2/2: Génération des scrapers...")
            scraper_cat.run_generer_scrapers()
            
            # ÉTAPE 3: Création des dossiers LIVRES
            self.log("📁 ÉTAPE 3/2: Création des dossiers LIVRES...")
            scraper_cat.creer_dossiers_livres()
            
            self.log("✅ Génération des scrapers terminée avec succès")
            return True
                
        except Exception as e:
            self.log(f"❌ Erreur génération scrapers: {e}")
            return False

    def charger_liste_scrapers(self):
        """Charge la liste des scrapers depuis le JSON"""
        # D'abord vérifier/régénérer les scrapers si nécessaire
        self.regenerer_scrapers_si_necessaire()
        
        try:
            # Charger depuis le fichier liste_scrapers.json
            chemin_liste = os.path.join(self.dossier_scrapers, 'liste_scrapers.json')
            if os.path.exists(chemin_liste):
                with open(chemin_liste, 'r', encoding='utf-8') as f:
                    self.scrapers_liste = json.load(f)
                print(f"✅ {len(self.scrapers_liste)} scrapers chargés depuis liste_scrapers.json")
                return
            
            # Fallback: scanner le dossier SCRAPERS
            self.scanner_dossier_scrapers()
            
        except Exception as e:
            print(f"❌ Erreur chargement liste: {e}")
            self.scanner_dossier_scrapers()
    
    def scanner_dossier_scrapers(self):
        """Scanne le dossier SCRAPERS pour trouver tous les scrapers"""
        print("🔍 Scan du dossier SCRAPERS...")
        
        scrapers_trouves = []
        
        for fichier in os.listdir(self.dossier_scrapers):
            if fichier.startswith('scraper_') and fichier.endswith('.py') and fichier != 'scraper_categorie.py':
                nom_categorie = fichier.replace('scraper_', '').replace('.py', '').replace('_', ' ').title()
                scrapers_trouves.append({
                    'nom_categorie': nom_categorie,
                    'nom_fichier': fichier,
                    'url_base': 'auto_detecte'
                })
        
        self.scrapers_liste = scrapers_trouves
        print(f"✅ {len(self.scrapers_liste)} scrapers trouvés par scan")
    
    def charger_progres(self):
        """Charge le progrès depuis le fichier de sauvegarde"""
        if os.path.exists(self.fichier_progres):
            try:
                with open(self.fichier_progres, 'r', encoding='utf-8') as f:
                    self.progres = json.load(f)
                print(f"📂 Progrès chargé: {self.progres['scraper_actuel']}/{len(self.scrapers_liste)}")
                print(f"   Terminés: {len(self.progres['scrapers_termines'])}")
                print(f"   Échecs: {len(self.progres['scrapers_echecs'])}")
            except Exception as e:
                print(f"❌ Erreur chargement progrès: {e}")
    
    def sauvegarder_progres(self):
        """Sauvegarde le progrès actuel"""
        self.progres['derniere_sauvegarde'] = datetime.now().isoformat()
        
        try:
            with open(self.fichier_progres, 'w', encoding='utf-8') as f:
                json.dump(self.progres, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ Erreur sauvegarde progrès: {e}")
    
    def log(self, message: str):
        """Écrit dans le fichier de log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ligne_log = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.fichier_log, 'a', encoding='utf-8') as f:
                f.write(ligne_log)
        except Exception as e:
            print(f"❌ Erreur écriture log: {e}")
        
        print(message)  # Afficher aussi à l'écran
    
    def executer_scraper(self, scraper: Dict[str, Any]) -> bool:
        """Exécute un scraper et retourne True si succès"""
        nom_fichier = scraper['nom_fichier']
        nom_categorie = scraper['nom_categorie']
        
        # MISE À JOUR: Toujours relancer pour mettre à jour les livres
        # (Suppression de la vérification "déjà terminé" pour forcer la mise à jour)
        
        # Vérifier si en échec récurrent
        if nom_fichier in self.progres['scrapers_echecs']:
            compteur_echecs = self.progres['scrapers_echecs'].count(nom_fichier)
            if compteur_echecs >= 3:
                self.log(f"❌ {nom_categorie} - Trop d'échecs ({compteur_echecs}), ignoré")
                return False
        
        self.log(f"🚀 Lancement: {nom_categorie} ({nom_fichier})")
        
        try:
            # Chemin complet vers le scraper
            chemin_scraper = os.path.join(self.dossier_scrapers, nom_fichier)
            
            if not os.path.exists(chemin_scraper):
                self.log(f"❌ {nom_categorie} - Fichier introuvable: {chemin_scraper}")
                self.progres['scrapers_echecs'].append(nom_fichier)
                return False
            
            # Exécuter le scraper
            debut_scraper = time.time()
            
            # Utiliser subprocess avec timeout
            result = subprocess.run(
                [sys.executable, chemin_scraper],
                cwd=self.dossier_scrapers,
                capture_output=True,
                text=True,
                timeout=7200  # Timeout de 2 heures par scraper
            )
            
            duree = time.time() - debut_scraper
            
            if result.returncode == 0:
                self.log(f"✅ {nom_categorie} - Terminé avec succès ({duree/60:.1f}min)")
                self.progres['scrapers_termines'].append(nom_fichier)
                return True
            else:
                self.log(f"❌ {nom_categorie} - Échec (code {result.returncode})")
                self.log(f"   Erreur: {result.stderr[:200]}...")
                self.progres['scrapers_echecs'].append(nom_fichier)
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"⏰ {nom_categorie} - Timeout (2h dépassées)")
            self.progres['scrapers_echecs'].append(nom_fichier)
            return False
            
        except Exception as e:
            self.log(f"❌ {nom_categorie} - Erreur: {e}")
            self.progres['scrapers_echecs'].append(nom_fichier)
            return False
    
    def generer_rapport(self):
        """Génère un rapport final"""
        total_scrapers = len(self.scrapers_liste)
        termines = len(self.progres['scrapers_termines'])
        echecs = len(set(self.progres['scrapers_echecs']))  # Unique
        
        rapport = f"""
📊 RAPPORT FINAL DU LANCEUR DE SCRAPERS
{'=' * 50}
Début session: {self.progres.get('debut_session', 'N/A')}
Fin session: {datetime.now().isoformat()}

📈 STATISTIQUES:
   Total scrapers: {total_scrapers}
   ✅ Terminés avec succès: {termines}
   ❌ En échec: {echecs}
   📊 Taux de succès: {(termines/total_scrapers*100):.1f}%

✅ SCRAPERS TERMINÉS:
"""
        
        for scraper_file in self.progres['scrapers_termines']:
            scraper_info = next((s for s in self.scrapers_liste if s['nom_fichier'] == scraper_file), None)
            if scraper_info:
                rapport += f"   - {scraper_info['nom_categorie']}\n"
        
        rapport += "\n❌ SCRAPERS EN ÉCHEC:\n"
        scrapers_echec_uniques = list(set(self.progres['scrapers_echecs']))
        for scraper_file in scrapers_echec_uniques:
            scraper_info = next((s for s in self.scrapers_liste if s['nom_fichier'] == scraper_file), None)
            if scraper_info:
                nb_echecs = self.progres['scrapers_echecs'].count(scraper_file)
                rapport += f"   - {scraper_info['nom_categorie']} ({nb_echecs} échecs)\n"
        
        # Sauvegarder le rapport
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nom_rapport = f"rapport_lanceur_{timestamp}.txt"
        
        with open(nom_rapport, 'w', encoding='utf-8') as f:
            f.write(rapport)
        
        print(rapport)
        self.log(f"📄 Rapport sauvegardé: {nom_rapport}")
    
    def run(self):
        """Fonction principale"""
        print("🚀 LANCEUR DE SCRAPERS")
        print("=" * 50)
        
        # ÉTAPE 1: MISE À JOUR DU FICHIER COMPLET.JSON
        print("📚 ÉTAPE 1: Mise à jour du fichier complet.json...")
        try:
            dossier_livres = os.path.join(os.path.dirname(self.dossier_scrapers), 'LIVRES')
            succes_maj = mettre_a_jour_complet_json(dossier_livres)
            if succes_maj:
                print("✅ Fichier complet.json mis à jour avec succès")
            else:
                print("⚠️ Erreur mise à jour complet.json, continuation...")
        except Exception as e:
            print(f"⚠️ Erreur mise à jour: {e}, continuation...")
        
        print("=" * 50)
        
        # Initialisation
        if not self.progres.get('debut_session'):
            self.progres['debut_session'] = datetime.now().isoformat()
        
        # Charger la liste des scrapers
        self.charger_liste_scrapers()
        
        if not self.scrapers_liste:
            print("❌ Aucun scraper trouvé!")
            return
        
        # Charger le progrès
        self.charger_progres()
        
        self.log(f"🎯 {len(self.scrapers_liste)} scrapers à traiter")
        
        try:
            # Boucle principale
            for i, scraper in enumerate(self.scrapers_liste):
                # Reprendre là où on s'était arrêté
                if i < self.progres['scraper_actuel']:
                    continue
                
                self.progres['scraper_actuel'] = i
                self.sauvegarder_progres()
                
                # Affichage progression
                progression = f"[{i+1}/{len(self.scrapers_liste)}] {(i+1)/len(self.scrapers_liste)*100:.1f}%"
                self.log(f"📊 {progression}")
                
                # Exécuter le scraper
                succes = self.executer_scraper(scraper)
                
                # Sauvegarder après chaque scraper
                self.sauvegarder_progres()
                
                # Délai entre scrapers
                if i < len(self.scrapers_liste) - 1:  # Pas de délai pour le dernier
                    self.log("⏳ Délai de 30s avant le scraper suivant...")
                    time.sleep(30)
            
            # Marquer comme terminé
            self.progres['scraper_actuel'] = len(self.scrapers_liste)
            self.sauvegarder_progres()
            
            self.log("🎉 TOUS LES SCRAPERS TERMINÉS!")
            
        except KeyboardInterrupt:
            self.log("⏸️  Arrêt demandé par l'utilisateur")
            self.log(f"📍 Arrêt à la position: {self.progres['scraper_actuel']}")
            self.log("💡 Relancez le script pour reprendre")
        
        except Exception as e:
            self.log(f"❌ Erreur fatale: {e}")
        
        finally:
            # Générer le rapport final
            self.generer_rapport()
            print("\n💾 Progrès sauvegardé - vous pouvez reprendre plus tard")

if __name__ == "__main__":
    lanceur = LanceurScrapers()
    lanceur.run()