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
            'erreurs': 0,
            'estimation_totale': None,  # DYNAMIQUE - sera calculé pendant le scraping
            'temps_debut': None,
            'temps_ecoule': 0,
            'estimation_temps_restant': 0,
            'vitesse_detection': 0  # catégories/seconde
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
        
        # UN SEUL fichier JSON - pas de timestamp pour éviter la multiplication
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
        """Détecter TOUTES les catégories principales depuis la page racine LIVRES SEULEMENT"""
        print(f"🎯 DÉTECTION CATÉGORIES PRINCIPALES LIVRES: {url_base}")
        
        soup = self.faire_requete_optimisee(url_base)
        if not soup:
            return {}
            
        categories_principales = {}
        
        # SÉLECTEURS RESTREINTS - seulement dans l'arborescence livres
        selectors_categories = [
            # Navigation LIVRES spécifique
            '.s-navigation-indent-1 a',
            '.s-navigation-indent-2 a',
            '.s-refinements a',
            
            # Liens vers catégories livres dans le contenu
            '.a-section a[href*="stripbooks"]',
            '.a-section a[href*="i=stripbooks"]',
            
            # Navigation latérale livres uniquement
            'a[href*="ref_=Oct_d_odnav_301061"]',  # Liens qui référencent la page livres
            'a[href*="bbn=301061"]',  # Liens avec breadcrumb livres
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
                        
                    # Extraire le node d'abord
                    node_id = self.extraire_node_id(full_url)
                    
                    if node_id and node_id not in categories_principales:
                        # Toujours ajouter TOUTES les catégories détectées depuis /b?node=301061
                        cat_data = {
                            'nom': text,
                            'url': full_url,
                            'node': node_id,
                            'sous_categories': {},
                            'detecte_par': selector
                        }
                        categories_principales[node_id] = cat_data
                        
                        # Sauvegarde immédiate sans doublon
                        self.sauvegarder_categorie_immediate(node_id, cat_data)
                        print(f"    ✅ {text} (node={node_id}) - AJOUTÉ ET SAUVÉ")
                            
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
                        
                    # Extraire le node et ajouter la sous-catégorie
                    node_id = self.extraire_node_id(full_url)
                    
                    if node_id and node_id not in sous_categories and full_url != url_cat:
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
                        print(f"      {'  ' * current_depth}✅ {text} (node={node_id}) - AJOUTÉ")
                            
            except Exception as e:
                print(f"    ❌ Erreur sous-catégories '{selector}': {e}")
        
        # Pause entre catégories pour éviter le rate limiting
        time.sleep(self.request_delay)
        
        return sous_categories
    
    def est_categorie_valide(self, url: str, text: str) -> bool:
        """Vérifier si c'est une catégorie de livre valide - STRICTEMENT dans l'arborescence livres"""
        url_lower = url.lower()
        
        # OBLIGATION 1: Doit contenir stripbooks OU référencer l'arborescence livres (301061)
        est_livre = (
            'stripbooks' in url_lower or 
            'i=stripbooks' in url_lower or
            'ref_=oct_d_odnav_301061' in url_lower or  # Référence explicite à la page livres
            'bbn=301061' in url_lower  # Breadcrumb livres
        )
        
        # OBLIGATION 2: Si pas de stripbooks, doit avoir des indicateurs livres dans l'URL ou le texte
        if not est_livre:
            # Vérifier si c'est dans l'arborescence livres par le contexte
            indicateurs_livres = [
                'roman', 'livre', 'bd', 'manga', 'fiction', 'littérature', 
                'histoire', 'science', 'enfant', 'ado', 'scolaire', 'etude',
                'cuisine', 'voyage', 'art', 'photographie', 'religion',
                'politique', 'sociologie', 'philosophie', 'médecine'
            ]
            
            texte_lower = text.lower()
            est_livre = any(ind in texte_lower for ind in indicateurs_livres)
        
        # EXCLUSIONS ABSOLUES - jamais des livres
        exclusions_absolues = [
            '/dp/', '/gp/', 'help', 'account', 'cart', 'sign', 'prime',
            'cuisine-maison', 'high-tech', 'jeux-video', 'jeux-jouets',
            'bebe', 'audible', 'informatique', 'personnalises',
            'sante-produits', 'hygiene', 'sports-activites', 'auto-moto',
            'beaute', 'electronique', 'vetement'
        ]
        
        est_exclu = any(ex in url_lower for ex in exclusions_absolues)
        
        # Texte valide
        texte_ok = (
            len(text.strip()) > 2 and 
            len(text.strip()) < 100 and
            not text.isdigit()
        )
        
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
    
    def mettre_a_jour_stats(self):
        """Mettre à jour les statistiques en temps réel"""
        if not self.debut_scraping:
            self.debut_scraping = datetime.now()
            self.stats['temps_debut'] = self.debut_scraping
        
        # Calculer temps écoulé
        temps_ecoule = datetime.now() - self.debut_scraping
        self.stats['temps_ecoule'] = temps_ecoule.total_seconds()
        
        # Calculer total récursif
        def compter_recursif(categories_dict):
            total = len(categories_dict)
            for cat_data in categories_dict.values():
                if 'sous_categories' in cat_data:
                    total += compter_recursif(cat_data['sous_categories'])
            return total
        
        total_recursif = compter_recursif(self.categories_detectees)
        
        # Calculer vitesse
        if self.stats['temps_ecoule'] > 0:
            self.stats['vitesse_detection'] = total_recursif / self.stats['temps_ecoule']
        
        # Afficher stats en temps réel (SANS estimation car dynamique)
        temps_ecoule_str = str(timedelta(seconds=int(self.stats['temps_ecoule'])))
        
        print(f"📊 STATS: {total_recursif} catégories détectées | "
              f"⏱️ Temps: {temps_ecoule_str} | 🚀 Vitesse: {self.stats['vitesse_detection']:.2f} cat/s")
    
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
                
                # CRÉER automatiquement le dossier LIVRES et le scraper pour cette catégorie
                self.traiter_creation_automatique(cat_data['nom'], cat_data['url'])
                
                # Traiter aussi toutes les sous-catégories récursivement
                self.traiter_sous_categories_recursif(sous_cats)
                
                # Mise à jour des statistiques en temps réel
                self.mettre_a_jour_stats()
                
            return {node_id: self.categories_detectees[node_id]}
            
        except Exception as e:
            print(f"❌ Erreur worker {cat_data['nom']}: {e}")
            return {}
    
    def charger_categories_existantes(self):
        """Charger les catégories existantes depuis le fichier JSON"""
        try:
            if os.path.exists(self.fichier_categories_complet):
                with open(self.fichier_categories_complet, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'categories' in data:
                        self.categories_detectees = data['categories']
                        print(f"📊 Catégories existantes chargées: {len(self.categories_detectees)}")
                        return True
        except Exception as e:
            print(f"⚠️ Erreur chargement existant: {e}")
        return False

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
        
        # Métadonnées DYNAMIQUES
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'total_categories_principales': len(self.categories_detectees),
            'total_recursif': total_recursif,
            'urls_analysees': len(self.processed_urls),
            'stats': self.stats,
            'note': 'Détection dynamique - le nombre total varie selon Amazon'
        }
        
        # Structure finale
        data_finale = {
            'metadata': metadata,
            'categories': self.categories_detectees
        }
        
        # Sauvegarde dans UN SEUL fichier JSON
        with open(self.fichier_categories_complet, 'w', encoding='utf-8') as f:
            json.dump(data_finale, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Sauvé: {self.fichier_categories_complet}")
        print(f"🎯 Total récursif détecté: {total_recursif} catégories")
        
        return total_recursif
        
    def sauvegarder_categorie_immediate(self, node_id: str, cat_data: dict):
        """Sauvegarde immédiate d'une catégorie sans doublon"""
        # Vérifier si catégorie existe déjà
        if node_id in self.categories_detectees:
            return False
            
        # Ajouter la catégorie
        self.categories_detectees[node_id] = cat_data
        
        # Sauvegarde immédiate
        self.sauvegarder_categories()
        return True
    
    def run(self):
        """Exécution principale - Détecter DYNAMIQUEMENT toutes les catégories"""
        print("🚀 SCRAPER AMAZON - DÉTECTION DYNAMIQUE CATÉGORIES")
        print("=" * 60)
        
        self.debut_scraping = datetime.now()
        
        try:
            # ÉTAPE 0: Charger catégories existantes pour éviter doublons
            print("\n📊 ÉTAPE 0: CHARGEMENT CATÉGORIES EXISTANTES")
            self.charger_categories_existantes()
            
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
            print(f"📈 Détection dynamique terminée")
            print(f"⏱️ Durée: {duree}")
            print(f"💾 Fichier: {self.fichier_categories_complet}")
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

    def traiter_creation_automatique(self, nom_categorie: str, url_categorie: str):
        """
        Traiter automatiquement la création du dossier LIVRES et du scraper pour une catégorie
        
        Cette fonction vérifie et crée automatiquement :
        1. Le dossier dans LIVRES si il n'existe pas
        2. Le fichier scraper dans SCRAPERS si il n'existe pas
        
        Args:
            nom_categorie (str): Le nom de la catégorie (ex: "Romans et polars")
            url_categorie (str): L'URL de la catégorie Amazon
            
        Description détaillée:
        - Nettoie le nom de catégorie pour créer un nom de fichier/dossier valide
        - Vérifie si le dossier LIVRES/{nom_propre} existe déjà
        - Si pas, le crée avec os.makedirs()
        - Vérifie si le scraper SCRAPERS/scraper_{nom_propre}.py existe déjà  
        - Si pas, le génère depuis le template modele_scraper.py
        - Affiche des logs pour traçabilité
        """
        try:
            # Étape 1: Vérifier et créer le dossier LIVRES
            if not self.verifier_dossier_livres_existe(nom_categorie):
                dossier_cree = self.creer_dossier_livres(nom_categorie)
                print(f"📁 Créé dossier LIVRES: {dossier_cree}")
            else:
                print(f"📁 Dossier LIVRES existe déjà: {nom_categorie}")
            
            # Étape 2: Vérifier et créer le scraper
            if not self.verifier_scraper_existe(nom_categorie):
                scraper_cree = self.creer_scraper_automatique(nom_categorie, url_categorie)
                if scraper_cree:
                    print(f"🔧 Créé scraper: {scraper_cree}")
                else:
                    print(f"❌ Échec création scraper pour: {nom_categorie}")
            else:
                print(f"🔧 Scraper existe déjà: {nom_categorie}")
                
        except Exception as e:
            print(f"❌ Erreur création automatique pour '{nom_categorie}': {e}")

    def traiter_sous_categories_recursif(self, sous_categories_dict: Dict[str, Any]):
        """
        Traiter récursivement toutes les sous-catégories pour créer leurs dossiers et scrapers
        
        Cette fonction parcourt récursivement l'arbre des sous-catégories et applique
        la création automatique (dossier LIVRES + scraper) à chaque sous-catégorie trouvée.
        
        Args:
            sous_categories_dict (Dict[str, Any]): Dictionnaire des sous-catégories à traiter
                Structure attendue:
                {
                    "node_id": {
                        "nom": "Nom de la sous-catégorie",
                        "url": "URL de la sous-catégorie",
                        "sous_categories": { ... }  # Récursif
                    }
                }
        
        Description détaillée:
        - Parcourt chaque sous-catégorie dans le dictionnaire fourni
        - Pour chaque sous-catégorie, appelle traiter_creation_automatique()
        - Si la sous-catégorie a elle-même des sous-catégories, appel récursif
        - Gère les erreurs pour éviter que l'échec d'une sous-catégorie bloque les autres
        - Ajoute des logs pour traçabilité du processus récursif
        """
        try:
            # Parcourir toutes les sous-catégories
            for node_id, sous_cat_data in sous_categories_dict.items():
                nom_sous_cat = sous_cat_data.get('nom', 'Inconnu')
                url_sous_cat = sous_cat_data.get('url', '')
                
                # Traiter cette sous-catégorie
                print(f"🔄 Traitement sous-catégorie récursive: {nom_sous_cat}")
                self.traiter_creation_automatique(nom_sous_cat, url_sous_cat)
                
                # Traitement récursif des sous-sous-catégories
                if 'sous_categories' in sous_cat_data and sous_cat_data['sous_categories']:
                    print(f"🔄 Récursion dans les sous-sous-catégories de: {nom_sous_cat}")
                    self.traiter_sous_categories_recursif(sous_cat_data['sous_categories'])
                    
        except Exception as e:
            print(f"❌ Erreur traitement récursif des sous-catégories: {e}")

if __name__ == "__main__":
    scraper = ScraperAmazonCategories()
    
    # Vérifier les arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        scraper.test_rapide()
    else:
        total = scraper.run()
        
        if total == 0:
            print(f"\n⚠️ ATTENTION: Aucune catégorie détectée")
            print("Pour améliorer la détection:")
            print("- Vérifier la connexion internet")
            print("- Augmenter max_depth dans detecter_sous_categories")
            print("- Ajouter plus de sélecteurs CSS")
            print("- Analyser d'autres pages de navigation")
        else:
            print(f"\n✅ SUCCÈS: {total} catégories détectées dynamiquement")