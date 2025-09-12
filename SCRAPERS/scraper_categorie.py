#!/usr/bin/env python3
"""
SCRAPER AMAZON CATÉGORIES - DÉTECTION RÉCURSIVE COMPLÈTE
=========================================================
Objectif: Détecter TOUTES les 1462 catégories et sous-catégories Amazon
Méthode: Analyse récursive multi-thread avec optimisations
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Tuple, Any
from urllib.parse import urljoin, urlparse, unquote
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import shutil
import string

class ScraperAmazonCategories:
    def __init__(self):
        self.setup_chemins()
        self.categories_detectees = {}
        self.sous_categories_detectees = {}
        self.processed_urls = set()
        self.categories_queue = Queue()
        self.stats = {
            'categories_principales': 0,
            'sous_categories': 0,
            'total_detectees': 0,
            'pages_analysees': 0,
            'erreurs': 0
        }
        
        # Configuration optimisée pour récursion complète
        self.url_base_amazon = "https://www.amazon.fr"
        self.max_workers = 8  # Plus de threads pour aller plus vite
        self.request_delay = 0.5  # Délai réduit
        self.timeout_request = 15
        self.retry_limit = 3
        
        # Headers rotatifs pour éviter les blocages
        self.headers_pool = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'},
        ]
        
        self.lock = threading.Lock()
        self.categories_lock = threading.Lock()
        self.total_categories = 0
        self.total_sous_categories = 0
        self.debut_scraping = None
        self.optimiseur = None
        
    def setup_chemins(self):
        """Configuration des chemins de fichiers"""
        base_dir = "/Users/Simplon/Cours/workspacePython/Scraping"
        self.dossier_categories = os.path.join(base_dir, "CATEGORIES")
        self.dossier_livres = os.path.join(base_dir, "LIVRES")  
        self.dossier_scrapers = os.path.join(base_dir, "SCRAPERS")
        
        os.makedirs(self.dossier_categories, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.fichier_categories_json = os.path.join(self.dossier_categories, f"categories_completes_1462_{timestamp}.json")
        self.fichier_categories_csv = os.path.join(self.dossier_categories, f"categories_completes_1462_{timestamp}.csv")
        self.fichier_categories_complet = os.path.join(self.dossier_categories, "categories_amazon_completes.json")
        
        print(f"📁 Dossier catégories: {self.dossier_categories}")
        print(f"📁 Dossier livres: {self.dossier_livres}")
        print(f"📁 Dossier scrapers: {self.dossier_scrapers}")
        
    def faire_requete_optimisee(self, url: str, retries: int = 0) -> Optional[BeautifulSoup]:
        """Requête optimisée avec gestion d'erreurs et rotation headers"""
        if retries >= self.retry_limit:
            return None
            
        try:
            headers = random.choice(self.headers_pool)
            print(f"🔍 [{retries+1}] {url}")
            
            response = requests.get(url, headers=headers, timeout=self.timeout_request)
            
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            elif response.status_code == 503:  # Service indisponible - retry
                print(f"⚠️ 503 Service Unavailable - retry {retries+1}")
                time.sleep(random.uniform(2, 5))
                return self.faire_requete_optimisee(url, retries + 1)
            else:
                print(f"❌ HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur requête: {e}")
            if retries < self.retry_limit:
                time.sleep(random.uniform(1, 3))
                return self.faire_requete_optimisee(url, retries + 1)
            return None
    
    def detecter_categories_principales(self, url_base: str = "https://www.amazon.fr/b?node=301061") -> Dict[str, Any]:
        """Détecter TOUTES les catégories principales depuis la page racine"""
        print(f"🎯 DÉTECTION CATÉGORIES PRINCIPALES: {url_base}")
        
        soup = self.faire_requete_optimisee(url_base)
        if not soup:
            return {}
            
        categories_principales = {}
        
        # SÉLECTEURS ÉTENDUS pour capturer TOUTES les catégories
        selectors_categories = [
            # Navigation principale
            '#nav-subnav a[href*="/b/"]',
            '.nav-category-button',
            '.nav-a[href*="node="]',
            
            # Sections de catégories
            '.s-navigation-indent-1 a[href*="/b/"]',
            '.s-navigation-indent-2 a[href*="/b/"]',
            '.a-section a[href*="node="]',
            
            # Liens browse nodes
            'a[href*="/b/?ie=UTF8&node="]',
            'a[href*="/b/?node="]',
            
            # Catégories dans le contenu principal
            '.s-result-item a[href*="/b/"]',
            '.a-cardui a[href*="node="]',
            
            # Navigation latérale
            '.a-unordered-list a[href*="/b/"]',
            '.a-link-normal[href*="node="]',
            
            # Toutes les autres possibilités
            'a[href*="stripbooks"]',
            'a[data-category]',
        ]
        
        for selector in selectors_categories:
            try:
                links = soup.select(selector)
                print(f"  Sélecteur '{selector}': {len(links)} liens")
                
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if not href or not text or len(text) < 3:
                        continue
                        
                    # Construire URL complète
                    if href.startswith('/'):
                        full_url = self.url_base_amazon + href
                    else:
                        full_url = href
                        
                    # Filtrer les URLs non-catégories
                    if self.est_categorie_valide(full_url, text):
                        node_id = self.extraire_node_id(full_url)
                        
                        if node_id and node_id not in categories_principales:
                            categories_principales[node_id] = {
                                'nom': text,
                                'url': full_url,
                                'node': node_id,
                                'sous_categories': {},
                                'detecte_par': selector
                            }
                            print(f"    ✅ {text} (node={node_id})")
                            
            except Exception as e:
                print(f"    ❌ Erreur sélecteur '{selector}': {e}")
        
        print(f"🎯 TOTAL CATÉGORIES PRINCIPALES: {len(categories_principales)}")
        return categories_principales
    
    def detecter_sous_categories(self, categorie_principale: Dict[str, Any], max_depth: int = 3, current_depth: int = 0) -> Dict[str, Any]:
        """Détecter RÉCURSIVEMENT toutes les sous-catégories d'une catégorie"""
        if current_depth >= max_depth:
            return {}
            
        nom_cat = categorie_principale['nom']
        url_cat = categorie_principale['url']
        
        print(f"🔍 Sous-catégories [{current_depth}]: {nom_cat}")
        
        soup = self.faire_requete_optimisee(url_cat)
        if not soup:
            return {}
            
        sous_categories = {}
        
        # SÉLECTEURS SPÉCIALISÉS pour les sous-catégories
        selectors_sous_cat = [
            # Navigation indentée (sous-catégories)
            '.s-navigation-indent-1 a',
            '.s-navigation-indent-2 a', 
            '.s-navigation-indent-3 a',
            
            # Filtres de catégories
            '.a-section.a-spacing-none a[href*="rh="]',
            '.s-refinements a[href*="node="]',
            
            # Liens vers nodes enfants
            'a[href*="ref_=sr_nr_n_"]',
            'a[href*="&rh=n%3A"]',
            
            # Sections de navigation
            '.a-unordered-list.a-nostyle a',
            '.nav-category-button',
            
            # Browse nodes spécifiques
            'a[href*="/b/?ie=UTF8&node="]',
            'a[href*="stripbooks&rh=n%3A"]',
            
            # Toutes les autres sous-catégories possibles
            '.a-link-normal[href*="node="]',
        ]
        
        for selector in selectors_sous_cat:
            try:
                links = soup.select(selector)
                
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if not href or not text or len(text) < 2:
                        continue
                        
                    # URL complète
                    if href.startswith('/'):
                        full_url = self.url_base_amazon + href
                    else:
                        full_url = href
                        
                    # Valider la sous-catégorie
                    if self.est_sous_categorie_valide(full_url, text, url_cat):
                        node_id = self.extraire_node_id(full_url)
                        
                        if node_id and node_id not in sous_categories:
                            sous_cat_data = {
                                'nom': text,
                                'url': full_url,
                                'node': node_id,
                                'parent': nom_cat,
                                'profondeur': current_depth,
                                'detecte_par': selector,
                                'sous_categories': {}
                            }
                            
                            # RÉCURSION: Chercher les sous-sous-catégories
                            if current_depth < max_depth - 1:
                                time.sleep(self.request_delay)
                                sous_cat_data['sous_categories'] = self.detecter_sous_categories(
                                    sous_cat_data, max_depth, current_depth + 1
                                )
                            
                            sous_categories[node_id] = sous_cat_data
                            print(f"      {'  ' * current_depth}✅ {text} (node={node_id})")
                            
            except Exception as e:
                print(f"    ❌ Erreur sous-catégories '{selector}': {e}")
        
        # Pause entre catégories pour éviter le rate limiting
        time.sleep(self.request_delay)
        
        return sous_categories
    
    def est_categorie_valide(self, url: str, text: str) -> bool:
        """Vérifier si c'est une catégorie de livre valide - SEULEMENT dans l'arborescence 301061"""
        url_lower = url.lower()
        
        # RÈGLE SIMPLE: Doit contenir stripbooks OU être un lien /b/ avec node= dans l'arborescence livres
        est_livre = (
            'stripbooks' in url_lower or 
            ('i=stripbooks' in url_lower) or
            ('/b/' in url_lower and 'node=' in url_lower)
        )
        
        # Exclure les liens non-livres évidents
        exclusions_evidentes = ['/dp/', '/gp/', 'help', 'account', 'cart', 'sign']
        est_exclu = any(ex in url_lower for ex in exclusions_evidentes)
        
        # Texte valide
        texte_ok = len(text.strip()) > 2 and len(text.strip()) < 100
        
        return est_livre and not est_exclu and texte_ok
    
    def est_sous_categorie_valide(self, url: str, text: str, url_parent: str) -> bool:
        """Vérifier si c'est une sous-catégorie valide"""
        # Même validation que catégorie + pas identique au parent
        return self.est_categorie_valide(url, text) and url != url_parent
    
    def extraire_node_id(self, url: str) -> Optional[str]:
        """Extraire l'ID de node depuis une URL Amazon"""
        patterns = [
            r'node[=/](\d+)',
            r'rh=n%3A(\d+)',
            r'&n=(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def traiter_categorie_worker(self, categorie_data: Tuple[str, Dict]) -> Dict[str, Any]:
        """Worker pour traitement parallèle des catégories"""
        node_id, cat_data = categorie_data
        
        try:
            print(f"🔧 Worker traite: {cat_data['nom']}")
            
            # Détecter les sous-catégories de cette catégorie
            sous_cats = self.detecter_sous_categories(cat_data, max_depth=4)
            
            with self.categories_lock:
                self.categories_detectees[node_id] = cat_data
                self.categories_detectees[node_id]['sous_categories'] = sous_cats
                self.stats['sous_categories'] += len(sous_cats)
                self.stats['total_detectees'] = len(self.categories_detectees)
                
            return {node_id: self.categories_detectees[node_id]}
            
        except Exception as e:
            print(f"❌ Erreur worker {cat_data['nom']}: {e}")
            return {}
    
    def sauvegarder_categories(self):
        """Sauvegarder toutes les catégories détectées"""
        print(f"💾 SAUVEGARDE: {len(self.categories_detectees)} catégories")
        
        # Compter le total récursif
        def compter_recursif(categories_dict):
            total = len(categories_dict)
            for cat_data in categories_dict.values():
                if 'sous_categories' in cat_data:
                    total += compter_recursif(cat_data['sous_categories'])
            return total
        
        total_recursif = compter_recursif(self.categories_detectees)
        
        # Métadonnées
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'total_categories_principales': len(self.categories_detectees),
            'total_recursif': total_recursif,
            'objectif_copilot': 1462,
            'pourcentage_atteint': f"{total_recursif/1462*100:.1f}%",
            'urls_analysees': len(self.processed_urls),
            'stats': self.stats
        }
        
        # Structure finale
        data_finale = {
            'metadata': metadata,
            'categories': self.categories_detectees
        }
        
        # Sauvegarde JSON
        with open(self.fichier_categories_json, 'w', encoding='utf-8') as f:
            json.dump(data_finale, f, indent=2, ensure_ascii=False)
        
        # Remplacer le fichier de référence
        with open(self.fichier_categories_complet, 'w', encoding='utf-8') as f:
            json.dump(data_finale, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sauvé: {self.fichier_categories_json}")
        print(f"🎯 Total récursif: {total_recursif}/1462 ({total_recursif/1462*100:.1f}%)")
        
        return total_recursif
    
    def run(self):
        """Exécution principale - Détecter les 1462 catégories"""
        print("🚀 SCRAPER AMAZON - DÉTECTION 1462 CATÉGORIES")
        print("=" * 60)
        
        self.debut_scraping = datetime.now()
        
        try:
            # ÉTAPE 1: Détecter toutes les catégories principales
            print("\n🎯 ÉTAPE 1: CATÉGORIES PRINCIPALES")
            categories_principales = self.detecter_categories_principales()
            
            if not categories_principales:
                print("❌ Aucune catégorie principale détectée")
                return 0
            
            print(f"✅ {len(categories_principales)} catégories principales détectées")
            
            # ÉTAPE 2: Traitement parallèle des sous-catégories
            print(f"\n🔧 ÉTAPE 2: SOUS-CATÉGORIES (Parallèle avec {self.max_workers} workers)")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.traiter_categorie_worker, (node_id, cat_data)): node_id
                    for node_id, cat_data in categories_principales.items()
                }
                
                for future in as_completed(futures):
                    node_id = futures[future]
                    try:
                        result = future.result()
                        if result:
                            print(f"✅ Terminé: {list(result.keys())[0]}")
                    except Exception as e:
                        print(f"❌ Erreur future {node_id}: {e}")
            
            # ÉTAPE 3: Sauvegarde finale
            print(f"\n💾 ÉTAPE 3: SAUVEGARDE FINALE")
            total_final = self.sauvegarder_categories()
            
            # STATISTIQUES FINALES
            duree = datetime.now() - self.debut_scraping
            print(f"\n{'=' * 60}")
            print(f"🎉 SCRAPING TERMINÉ")
            print(f"📊 Total détecté: {total_final} catégories")
            print(f"🎯 Objectif Copilot: 1462 catégories")
            print(f"📈 Réussite: {total_final/1462*100:.1f}%")
            print(f"⏱️ Durée: {duree}")
            print(f"💾 Fichier: {self.fichier_categories_json}")
            print(f"{'=' * 60}")
            
            return total_final
            
        except KeyboardInterrupt:
            print("\n⚠️ Arrêt demandé - Sauvegarde en cours...")
            self.sauvegarder_categories()
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            import traceback
            traceback.print_exc()
        
        return len(self.categories_detectees)
    
    def test_rapide(self):
        """Test rapide sur quelques catégories"""
        print("🧪 TEST RAPIDE - QUELQUES CATÉGORIES")
        
        # Test sur une seule catégorie principale
        categories_test = self.detecter_categories_principales()
        if categories_test:
            # Prendre les 2 premières catégories
            categories_limitees = dict(list(categories_test.items())[:2])
            
            for node_id, cat_data in categories_limitees.items():
                print(f"🔍 Test: {cat_data['nom']}")
                sous_cats = self.detecter_sous_categories(cat_data, max_depth=2)
                print(f"  → {len(sous_cats)} sous-catégories")
                
                # Compter récursivement
                def compter_recursif(cats):
                    total = len(cats)
                    for cat in cats.values():
                        if 'sous_categories' in cat:
                            total += compter_recursif(cat['sous_categories'])
                    return total
                
                total_test = compter_recursif(sous_cats)
                print(f"  → {total_test} total récursif")
        
        print("✅ Test rapide terminé")

    def nettoyer_nom_fichier(self, nom: str) -> str:
        """Nettoyer un nom pour créer un nom de fichier valide"""
        # Remplacer les caractères spéciaux
        nom_clean = re.sub(r'[^\w\s-]', '', nom.lower())
        nom_clean = re.sub(r'[-\s]+', '_', nom_clean)
        return nom_clean.strip('_')

    def creer_dossier_livres(self, nom_categorie: str):
        """Créer le dossier pour les livres d'une catégorie"""
        nom_propre = self.nettoyer_nom_fichier(nom_categorie)
        dossier_cat = os.path.join(self.dossier_livres, nom_propre)
        os.makedirs(dossier_cat, exist_ok=True)
        return dossier_cat

    def verifier_dossier_livres_existe(self, nom_categorie: str) -> bool:
        """Vérifier si le dossier livres existe déjà"""
        nom_propre = self.nettoyer_nom_fichier(nom_categorie)
        dossier_cat = os.path.join(self.dossier_livres, nom_propre)
        return os.path.exists(dossier_cat)

    def verifier_scraper_existe(self, nom_categorie: str) -> bool:
        """Vérifier si le scraper existe déjà"""
        nom_propre = self.nettoyer_nom_fichier(nom_categorie)
        fichier_scraper = os.path.join(self.dossier_scrapers, f"scraper_{nom_propre}.py")
        return os.path.exists(fichier_scraper)

    def creer_scraper_automatique(self, nom_categorie: str, url_categorie: str):
        """Créer automatiquement un scraper pour une catégorie"""
        nom_propre = self.nettoyer_nom_fichier(nom_categorie)
        fichier_scraper = os.path.join(self.dossier_scrapers, f"scraper_{nom_propre}.py")
        
        if os.path.exists(fichier_scraper):
            return fichier_scraper
            
        # Charger le template
        template_path = os.path.join(self.dossier_scrapers, "modele_scraper.py")
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Remplacer les placeholders
            contenu = template.replace('{{NOM_CATEGORIE}}', nom_categorie)
            contenu = contenu.replace('{{URL_BASE}}', url_categorie)
            
            # Sauvegarder
            with open(fichier_scraper, 'w', encoding='utf-8') as f:
                f.write(contenu)
            
            return fichier_scraper
        
        return None

if __name__ == "__main__":
    scraper = ScraperAmazonCategories()
    
    # Vérifier les arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        scraper.test_rapide()
    else:
        total = scraper.run()
        
        if total < 1462:
            print(f"\n⚠️ ATTENTION: {total}/1462 catégories détectées")
            print("Pour améliorer la détection:")
            print("- Augmenter max_depth dans detecter_sous_categories")
            print("- Ajouter plus de sélecteurs CSS")
            print("- Analyser d'autres pages de navigation")