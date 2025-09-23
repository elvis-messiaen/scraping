#!/usr/bin/env python3
"""
SCRAPER AMAZON OPTIMISÉ - CATÉGORIE: Science-Fiction
URL de base: https://www.amazon.fr/s?k=romans&i=stripbooks&rh=n%3A301061%2Cn%3A1381962031&dc&qid=1757526158&rnid=301061&ref=sr_nr_n_27&ds=v1%3Ajl182Pl%2BoZRm6jb1dPmTnyY%2FTwIeLnaGYa5oldC237Y
"""

import os
import sys
import json
import time
import random
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# Import des fonctions de description et d'extraction
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'FONCTION'))
from description import recuperation_description, mettre_a_jour_descriptions_existantes, recuperer_description_depuis_url
from scraper_base_ameliore import ScraperBaseAmeliore

class ScraperAmazonSciencefiction:
    def __init__(self):
        self.nom_categorie = "Science-Fiction"
        self.nom_fichier = "science_fiction"
        self.url_base_recherche = "https://www.amazon.fr/s?k=romans&i=stripbooks&rh=n%3A301061%2Cn%3A1381962031&dc&qid=1757526158&rnid=301061&ref=sr_nr_n_27&ds=v1%3Ajl182Pl%2BoZRm6jb1dPmTnyY%2FTwIeLnaGYa5oldC237Y"
        
        # Configuration parallélisme
        self.max_workers = 200
        self.pool_size = 50
        self.request_delay = 0.1
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Collections
        self.livres_scraped = []
        self.livres_existants = {}
        self.urls_scrapees = set()
        self.index_by_url = {}
        self.index_by_isbn = {}
        
        # Pool de drivers
        self.drivers_pool = []
        self.driver = None
        
        # Proxies (optionnel)
        self.proxies = []
        self.current_proxy_index = 0
        
        # Créer dossiers
        self.creer_dossiers()
        
        # Charger données existantes
        self.charger_progres()
    
    def creer_dossiers(self):
        """Crée les dossiers nécessaires"""
        dossier_livres = os.path.join('LIVRES', self.nom_fichier)
        os.makedirs(dossier_livres, exist_ok=True)
    
    def setup_driver(self):
        """Configure le driver principal pour navigation"""
        if self.driver:
            return
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox") 
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")
        options.add_argument("--disable-css")
        options.add_argument("--disable-logging")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(8)
            self.driver.implicitly_wait(1)
        except Exception as e:
            print(f"Erreur setup driver: {e}")
            raise
    
    def charger_progres(self):
        """Charge les livres existants depuis LIVRES/"""
        dossier_livres = os.path.join('LIVRES', self.nom_fichier)
        if os.path.exists(dossier_livres):
            fichiers_json = [f for f in os.listdir(dossier_livres) if f.endswith('.json') and 'progres' not in f]
            if fichiers_json:
                for fichier in fichiers_json:
                    chemin_fichier = os.path.join(dossier_livres, fichier)
                    try:
                        with open(chemin_fichier, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Gérer le format avec metadata
                            if isinstance(data, dict) and 'livres' in data:
                                livres = data['livres']
                            elif isinstance(data, list):
                                livres = data
                            else:
                                continue

                            if livres:
                                for livre in livres:
                                    url = livre.get('url', '')
                                    if url:
                                        self.livres_existants[url] = livre
                                print(f"Chargement LIVRES/{self.nom_fichier}: {len(livres)} livres depuis {fichier}")
                    except Exception as e:
                        print(f"Erreur chargement {chemin_fichier}: {e}")

        # Transférer existants vers livres_scraped
        for url, livre in self.livres_existants.items():
            self.livres_scraped.append(livre)

        print(f"CHARGEMENT TERMINÉ: {len(self.livres_scraped):,} livres en mémoire")

    def detecter_total_amazon_actuel(self) -> int:
        """Détection dynamique du total Amazon actuel."""
        try:
            if not self.driver:
                self.setup_driver()
            
            self.driver.get(self.url_base_recherche)
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            selectors_total = [
                '.s-desktop-width-max .sg-col-14-of-20 h1',
                '[data-component-type="s-result-info-bar"] h1',
                'h1 span'
            ]
            
            for selector in selectors_total:
                elem = soup.select_one(selector)
                if elem:
                    texte = elem.get_text()
                    import re
                    match = re.search(r'sur ([0-9,\s]+)', texte)
                    if match:
                        nombre_str = match.group(1).replace(',', '').replace(' ', '')
                        try:
                            return int(nombre_str)
                        except:
                            continue
            
            print(f"Impossible de détecter le total, utilisation par défaut: 50,000 livres")
            return 50000
            
        except Exception as e:
            print(f"Erreur détection total: {e}, utilisation par défaut")
            return 50000

    def sauvegarder_json_mis_a_jour(self):
        """Met à jour le JSON existant avec les descriptions"""
        try:
            dossier_livres = os.path.join('LIVRES', self.nom_fichier)

            # Trouver le fichier JSON existant
            fichiers_json = [f for f in os.listdir(dossier_livres) if f.endswith('.json') and 'progres' not in f and 'descriptions' not in f]

            if not fichiers_json:
                print("❌ Aucun fichier JSON existant trouvé")
                return

            # Prendre le plus récent
            fichier_existant = max(fichiers_json)
            chemin_fichier = os.path.join(dossier_livres, fichier_existant)

            # Charger le JSON existant
            with open(chemin_fichier, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Mettre à jour avec les descriptions
            if isinstance(data, dict) and 'livres' in data:
                data['livres'] = self.livres_scraped
                data['metadata']['date_maj_descriptions'] = datetime.now().isoformat()
            elif isinstance(data, list):
                data = {
                    "metadata": {
                        "categorie": self.nom_categorie,
                        "total_livres": len(self.livres_scraped),
                        "date_maj_descriptions": datetime.now().isoformat(),
                        "url_source": self.url_base_recherche
                    },
                    "livres": self.livres_scraped
                }

            # Sauvegarder dans le même fichier
            with open(chemin_fichier, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"💾 JSON existant mis à jour: {chemin_fichier}")

        except Exception as e:
            print(f"❌ Erreur mise à jour JSON: {e}")

    def scraper_page(self, page_num: int) -> int:
        """Scrape une page de résultats avec extraction complète"""
        try:
            # Utiliser le scraper de base pour extraction complète
            scraper_base = ScraperBaseAmeliore(self.nom_categorie, self.url_base_recherche)

            # Configuration
            scraper_base.nom_categorie = self.nom_categorie
            scraper_base.url_base_recherche = self.url_base_recherche

            # Construction de l'URL avec pagination
            url_page = f"{self.url_base_recherche}&page={page_num}"

            # Faire la requête avec anti-détection
            soup = scraper_base.faire_requete_amelioree(url_page)
            if not soup:
                return 0

            # Extraire les livres avec toutes les informations complètes
            livres_page = scraper_base.extraire_livres_page_ameliore(soup)

            livres_extraits = 0
            for livre in livres_page:
                # FORCER l'extraction de description depuis l'URL avec système optimisé (6 techniques)
                print(f"🔍 Extraction description OPTIMISÉE pour: {livre.get('titre', 'Sans titre')[:40]}...")
                if livre.get('url') and livre['url'] != "URL non trouvée":
                    # Utiliser le système optimisé avec toutes les informations disponibles
                    nouvelle_description = recuperer_description_depuis_url(
                        livre['url'],
                        asin=livre.get('asin'),
                        isbn=livre.get('isbn'),
                        titre=livre.get('titre')
                    )
                    livre['description'] = nouvelle_description
                    print(f"📝 Description OPTIMISÉE obtenue: {nouvelle_description[:60]}...")
                else:
                    livre['description'] = "Description non trouvée"
                    print("❌ Pas d'URL - description impossible")

                # Ajouter les métadonnées
                livre['categorie'] = self.nom_categorie
                livre['scrape_date'] = datetime.now().isoformat()

                self.livres_scraped.append(livre)
                livres_extraits += 1

                # Affichage
                print(f"✅ {livre.get('titre', 'Sans titre')[:50]}... | {livre.get('prix', 'Sans prix')} | {livre.get('description', 'Sans description')[:40]}...")

                # Pas de limite - scraper TOUS les livres

            return livres_extraits

        except Exception as e:
            print(f"❌ Erreur scraping page {page_num}: {e}")
            return 0

    def run(self):
        """Fonction principale de scraping"""
        print(f"SCRAPER OPTIMISÉ - {self.nom_categorie.upper()}")
        print("=" * 60)
        
        # Détection du total Amazon actuel
        total_amazon_actuel = self.detecter_total_amazon_actuel()
        print(f"Total Amazon détecté: {total_amazon_actuel:,} livres")
        
        # État actuel
        stock_existant = len(self.livres_existants)
        reste_a_scraper = max(0, total_amazon_actuel - stock_existant - len(self.livres_scraped))
        
        print(f"État actuel:")
        print(f"   Existants:         {stock_existant:,} livres")
        print(f"   Déjà en mémoire:  {len(self.livres_scraped):,} livres")
        print(f"   RESTE A SCRAPER: {reste_a_scraper:,} livres")

        # Mise à jour des descriptions des livres existants
        if self.livres_scraped:
            print("\n🔄 MISE À JOUR DES DESCRIPTIONS EXISTANTES:")
            self.livres_scraped = mettre_a_jour_descriptions_existantes(self.livres_scraped)

            # Sauvegarder le JSON mis à jour
            self.sauvegarder_json_mis_a_jour()

        if reste_a_scraper <= 0:
            print("Catégorie complète - rien à scraper.")
            return

        # Scraping réel des livres
        print(f"\n🚀 DÉBUT DU SCRAPING - {reste_a_scraper:,} livres à récupérer")

        # Scraper première page (limitée à 10 livres pour test)
        livres_extraits = self.scraper_page(1)

        if livres_extraits > 0:
            # Sauvegarder les nouveaux livres
            self.sauvegarder_json_mis_a_jour()
            print(f"\n✅ SCRAPING TERMINÉ: {livres_extraits} livres extraits et sauvegardés")
        else:
            print("\n❌ Aucun livre extrait")

if __name__ == "__main__":
    scraper = ScraperAmazonSciencefiction()
    scraper.run()
