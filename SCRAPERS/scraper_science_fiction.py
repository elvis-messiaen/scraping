#!/usr/bin/env python3
"""
SCRAPER AMAZON - SCIENCE-FICTION
============================================
Catégorie: Science-Fiction
URL: https://www.amazon.fr/b/?node=1381962031&ref_=Oct_d_odnav_d_301061_17&pd_rd_w=3p5y2&content-id=amzn1.sym.a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_p=a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_r=TYFHHGC958M2P8FVDWP4&pd_rd_wg=6ZrKU&pd_rd_r=6c6eeffb-bf94-44d5-adde-e7f37855774f
Généré automatiquement par le scraper de catégories principales
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import du moteur anti-détection
sys.path.append('/Users/Simplon/Cours/workspacePython/Scraping/FONCTION/anti_detection_503/sequential_browsing')
from sequential_browsing_engine import scraper_avec_sequential_browsing

# Import des fonctions EXISTANTES dans FONCTION
sys.path.append('/Users/Simplon/Cours/workspacePython/Scraping/FONCTION')
from mise_a_jour_utils import mise_a_jour_automatique_demarrage

class ScraperAmazon_ScienceFiction:
    """
    Scraper spécialisé pour la catégorie: Science-Fiction

    Fonctionnalités:
    - Scraper les livres de la catégorie Science-Fiction
    - Extraire titre, auteur, prix, note, etc.
    - Sauvegarder en JSON dans le dossier LIVRES correspondant
    - Gestion anti-détection et délais
    """

    def __init__(self):
        """Initialisation du scraper pour Science-Fiction ULTRA-RAPIDE"""
        self.nom_categorie = "Science-Fiction"
        # URL de recherche Science-Fiction Amazon France (plus fiable)
        self.url_categorie = "https://www.amazon.fr/s?k=science+fiction&i=stripbooks&rh=n%3A301061%2Cp_n_binding_browse-bin%3A492914031%7C492913031"
        self.url_base = "https://www.amazon.fr"

        # Configuration ULTRA-RAPIDE
        self.delay_min = 0.1  # Délai minimal réduit
        self.delay_max = 0.3  # Délai maximal réduit
        self.timeout = 5      # Timeout réduit
        self.max_pages = float('inf')
        self.livres_par_page = 16

        # OPTIMISATIONS VITESSE
        self.max_workers_descriptions = 10  # Threads pour descriptions parallèles
        self.max_workers_pages = 3          # Threads pour pages parallèles
        self.session_pool_size = 5          # Pool de sessions persistantes

        # Thread safety
        self.lock = threading.Lock()
        self.livres_traites = []

        # Headers optimisés
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        # Pool de sessions persistantes pour vitesse maximale
        self.sessions_pool = self.creer_pool_sessions()

        # Setup chemins
        self.setup_chemins()

    def creer_pool_sessions(self):
        """
        Crée un pool de sessions persistantes pour vitesse maximale
        """
        sessions = []
        for i in range(self.session_pool_size):
            session = requests.Session()

            # Configuration optimisée
            session.headers.update(self.headers)

            # Adaptateur avec retry et connection pooling
            retry_strategy = Retry(
                total=2,
                backoff_factor=0.1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20
            )
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            sessions.append(session)

        return sessions

    def obtenir_session(self):
        """
        Obtient une session depuis le pool de manière thread-safe
        """
        with self.lock:
            if self.sessions_pool:
                return self.sessions_pool.pop()
            else:
                # Créer une nouvelle session si pool vide
                return self.creer_session_optimisee()

    def liberer_session(self, session):
        """
        Libère une session vers le pool
        """
        with self.lock:
            if len(self.sessions_pool) < self.session_pool_size:
                self.sessions_pool.append(session)

    def creer_session_optimisee(self):
        """
        Crée une session optimisée
        """
        session = requests.Session()
        session.headers.update(self.headers)

        retry_strategy = Retry(total=2, backoff_factor=0.1)
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def extraire_livres_page_parallele(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extraction parallèle ULTRA-RAPIDE des livres avec threading
        """
        livres_bruts = []

        # Sélecteurs pour les livres Amazon - PAGES DE RECHERCHE basés sur le debug
        selecteurs_livres = [
            # Sélecteurs pour pages de RECHERCHE Amazon (priorité)
            '.s-result-item[data-component-type="s-search-result"]',  # Principal pour recherches
            '.s-result-item',                                         # Fallback recherches
            'div[data-asin]',                                        # Éléments avec ASIN

            # Sélecteurs détectés dans l'analyse HTML
            'div[data-component-type]',  # Détecté: 17 page1, 1 page2
            '[data-cel-widget]',         # Fallback

            # Sélecteurs spécifiques Amazon 2025
            '[data-component-type="s-search-result"]',
            '.s-widget-container .s-result-item',
            '.s-card-container',
            '.octopus-pc-item',
            '.octopus-pc-card-content',

            # Sélecteurs larges avec filtrage intelligent
            '.a-section',  # Beaucoup d'éléments - filtrer par contenu
            'article',

            # Fallbacks finaux
            '.a-section.a-spacing-base',
            '[data-cy="title-recipe-review"]'
        ]

        # Extraire tous les éléments HTML d'abord
        for selecteur in selecteurs_livres:
            try:
                items = soup.select(selecteur)
                print(f"  📚 Sélecteur '{selecteur}': {len(items)} livres trouvés")

                livres_avec_ce_selecteur = []
                for item in items:
                    # Filtrage intelligent pour les sélecteurs larges
                    if selecteur == '.a-section':
                        # Ne traiter que les sections qui contiennent des liens /dp/ (livres)
                        links = item.find_all('a', href=True)
                        has_book_link = any('/dp/' in link.get('href', '') for link in links)
                        if not has_book_link:
                            continue  # Ignorer les sections sans livre

                    # Extraction rapide des données de base
                    livre_base = self.extraire_infos_livre_rapide(item)
                    if livre_base:
                        livres_avec_ce_selecteur.append(livre_base)

                # Si ce sélecteur a trouvé des livres, les ajouter et arrêter la recherche
                if livres_avec_ce_selecteur:
                    livres_bruts.extend(livres_avec_ce_selecteur)
                    print(f"  ✅ Sélecteur '{selecteur}' sélectionné: {len(livres_avec_ce_selecteur)} livres extraits")
                    break  # Arrêter la recherche avec d'autres sélecteurs

            except Exception as e:
                print(f"❌ Erreur sélecteur '{selecteur}': {e}")

        if not livres_bruts:
            # DEBUG: Analyser la structure HTML pour comprendre le problème
            print("🔍 DEBUG: Analyse de la structure HTML...")
            self.debug_html_structure(soup)
            return []

        print(f"🚀 LANCEMENT ASYNC ULTRA-RAPIDE pour {len(livres_bruts)} livres...")

        # EXTRACTION ASYNC DES DESCRIPTIONS
        # UTILISER THREADING DIRECTEMENT (plus stable que async/await)
        print("🚀 Mode threading ultra-rapide activé...")
        livres_avec_descriptions = self.extraire_descriptions_threading_fallback(livres_bruts)

        # Sauvegarde en lot
        with self.lock:
            self.livres_traites.extend(livres_avec_descriptions)
            self.sauvegarder_livres(self.livres_traites)
            print(f"💾 SAUVEGARDE PARALLÈLE: {len(self.livres_traites)} livres")

        return livres_avec_descriptions

    def extraire_infos_livre_rapide(self, item) -> Optional[Dict]:
        """
        Extraction rapide des infos de base (sans description) pour threading
        """
        try:
            # Extraction rapide des données essentielles
            titre = self.extraire_titre_correct(item)
            if titre == "Titre non trouvé" or len(titre) < 10:
                return None

            url = self.extraire_url_correct(item)
            if not url:
                return None

            # Données rapides à extraire
            prix = self.extraire_prix_correct(item)
            auteur = self.extraire_auteur_correct(item)
            note = self.extraire_note_correct(item)
            image = self.extraire_image_complete(item)

            # Autres infos rapides
            nombre_avis = self.extraire_nombre_avis(item)
            editeur = self.extraire_editeur_complet(item)
            format_livre = self.extraire_format_complet(item)
            date_publication = self.extraire_date_publication(item)
            nombre_pages = self.extraire_nombre_pages(item)
            isbn = self.extraire_isbn_complet(item)
            dimensions = self.extraire_dimensions(item)
            disponibilite = self.extraire_disponibilite(item)

            return {
                'titre': titre,
                'auteur': auteur,
                'prix': prix,
                'note': note,
                'nombre_avis': nombre_avis,
                'image': image,
                'description': "En cours d'extraction...",  # Sera remplacé par threading
                'editeur': editeur,
                'format': format_livre,
                'date_publication': date_publication,
                'nombre_pages': nombre_pages,
                'isbn': isbn,
                'dimensions': dimensions,
                'disponibilite': disponibilite,
                'url': url,
                'categorie': self.nom_categorie,
                'scrape_date': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Erreur extraction rapide: {e}")
            return None

    async def extraire_descriptions_async(self, livres_bruts: List[Dict]) -> List[Dict]:
        """
        Extraction ASYNC ULTRA-RAPIDE des descriptions avec système de queue
        100+ requêtes simultanées au lieu de 10 threads
        """
        try:
            print(f"🚀 LANCEMENT SYSTÈME ASYNC: {len(livres_bruts)} livres en parallèle...")

            # Import du système async/queue
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'FONCTION'))
            from queue_system import process_descriptions_batch

            # Transformation des données pour le système async
            livres_pour_async = []
            for livre in livres_bruts:
                livres_pour_async.append({
                    'url': livre['url'],
                    'titre': livre['titre']
                })

            # TRAITEMENT ASYNC ULTRA-RAPIDE avec queue
            livres_avec_descriptions = await process_descriptions_batch(livres_pour_async)

            # Mise à jour des livres originaux avec les descriptions
            livres_complets = []
            for i, livre_original in enumerate(livres_bruts):
                livre_complet = livre_original.copy()

                if i < len(livres_avec_descriptions):
                    description = livres_avec_descriptions[i].get('description', 'Description non trouvée')
                    livre_complet['description'] = description
                    print(f"✅ Async: {livre_original['titre'][:20]}... -> {description[:30]}...")
                else:
                    livre_complet['description'] = "Description non trouvée"

                livres_complets.append(livre_complet)

            print(f"🎯 ASYNC terminé: {len(livres_complets)} livres avec descriptions")
            return livres_complets

        except Exception as e:
            print(f"❌ Erreur système async: {e}")
            # Fallback vers threading si async échoue
            print("🔄 Fallback vers threading...")
            return self.extraire_descriptions_threading_fallback(livres_bruts)

    def extraire_descriptions_threading_fallback(self, livres_bruts: List[Dict]) -> List[Dict]:
        """
        Fallback threading si async échoue
        """
        def extraire_description_thread(livre):
            """Thread worker pour extraction de description"""
            try:
                url = livre['url']
                titre = livre['titre']

                print(f"🔍 Thread fallback: {titre[:30]}...")

                # Import optimisé dans le thread
                sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'FONCTION'))
                from description import recuperer_description_depuis_url

                # Extraction description
                description = recuperer_description_depuis_url(url, titre=titre)
                livre['description'] = description

                print(f"✅ Thread terminé: {titre[:20]}... -> {description[:30]}...")
                return livre

            except Exception as e:
                print(f"❌ Erreur thread {livre.get('titre', 'Unknown')}: {e}")
                livre['description'] = "Description non trouvée"
                return livre

        # THREADING PARALLÈLE DE FALLBACK
        livres_complets = []

        with ThreadPoolExecutor(max_workers=self.max_workers_descriptions) as executor:
            # Soumettre tous les livres en parallèle
            futures = {executor.submit(extraire_description_thread, livre): livre for livre in livres_bruts}

            # Récupérer les résultats
            for future in as_completed(futures):
                try:
                    livre_complet = future.result(timeout=30)  # Timeout par livre
                    livres_complets.append(livre_complet)

                    # Sauvegarde incrémentale ultra-rapide
                    if len(livres_complets) % 5 == 0:  # Sauver tous les 5 livres
                        with self.lock:
                            print(f"💾 Sauvegarde incrémentale: {len(livres_complets)} livres traités")

                except Exception as e:
                    print(f"❌ Erreur future: {e}")
                    # Récupérer le livre original même en cas d'erreur
                    livre_original = futures[future]
                    livre_original['description'] = "Description non trouvée"
                    livres_complets.append(livre_original)

        print(f"🎯 Threading fallback terminé: {len(livres_complets)} livres avec descriptions")
        return livres_complets

    def setup_chemins(self):
        """Configuration des chemins de sauvegarde"""
        base_dir = "/Users/Simplon/Cours/workspacePython/Scraping"
        self.dossier_livres = os.path.join(base_dir, "LIVRES", "science_fiction")
        os.makedirs(self.dossier_livres, exist_ok=True)

        # Chercher le fichier JSON existant ou créer un nom fixe
        nom_fichier = self.nettoyer_nom_fichier(self.nom_categorie)
        fichier_fixe = os.path.join(self.dossier_livres, f"livres_{nom_fichier}.json")

        # Vérifier s'il existe déjà un fichier récent (moins de 24h)
        fichiers_existants = []
        if os.path.exists(self.dossier_livres):
            for fichier in os.listdir(self.dossier_livres):
                if fichier.startswith("livres_science_fiction") and fichier.endswith(".json"):
                    chemin_complet = os.path.join(self.dossier_livres, fichier)
                    fichiers_existants.append((chemin_complet, os.path.getmtime(chemin_complet)))

        # Si un fichier récent existe, l'utiliser pour mise à jour
        if fichiers_existants:
            fichier_plus_recent = max(fichiers_existants, key=lambda x: x[1])
            self.fichier_livres = fichier_plus_recent[0]
            print(f"📝 MISE À JOUR du fichier existant: {os.path.basename(self.fichier_livres)}")
        else:
            # Sinon créer un nouveau fichier avec timestamp
            self.fichier_livres = os.path.join(
                self.dossier_livres,
                f"livres_{nom_fichier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            print(f"🆕 NOUVEAU fichier: {os.path.basename(self.fichier_livres)}")

    def nettoyer_nom_fichier(self, nom: str) -> str:
        """Nettoie un nom pour l'utiliser comme nom de fichier"""
        nom_nettoye = re.sub(r'[^\w\s-]', '', nom)
        nom_nettoye = re.sub(r'[-\s]+', '_', nom_nettoye)
        return nom_nettoye.lower().strip('_')

    def faire_requete(self, url: str) -> Optional[BeautifulSoup]:
        """Effectuer une requête HTTP avec moteur anti-détection Sequential Browsing"""
        try:
            print(f"🔄 Utilisation du moteur Sequential Browsing pour: {url[:80]}...")

            # Utiliser le moteur anti-détection
            soup = scraper_avec_sequential_browsing(url)

            if soup:
                print(f"✅ Page récupérée avec succès via Sequential Browsing")
                return soup
            else:
                print(f"❌ Échec Sequential Browsing, tentative fallback...")

                # Fallback classique en cas d'échec
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                response = requests.get(url, headers=self.headers, timeout=self.timeout)

                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')
                else:
                    print(f"❌ Erreur HTTP {response.status_code}: {url}")
                    return None

        except Exception as e:
            print(f"❌ Erreur requête: {e}")
            return None

    def extraire_livres_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extraire les informations des livres depuis une page"""
        livres = []

        # Sélecteurs pour les livres Amazon - PAGES DE RECHERCHE
        selecteurs_livres = [
            # Pages de recherche Amazon 2024/2025 (CORRECTS)
            '.s-result-item[data-component-type="s-search-result"]',
            '.s-result-item',
            '[data-component-type="s-search-result"]',

            # Fallback pour anciennes versions
            '.a-section.a-spacing-base',
            '[data-cy="title-recipe-review"]'
        ]

        for selecteur in selecteurs_livres:
            try:
                items = soup.select(selecteur)
                print(f"  📚 Sélecteur '{selecteur}': {len(items)} livres trouvés")

                for item in items:
                    livre_data = self.extraire_infos_livre(item)
                    if livre_data:
                        livres.append(livre_data)
                        # SAUVEGARDE APRÈS CHAQUE LIVRE
                        self.sauvegarder_livres(livres)
                        print(f"💾 SAUVEGARDÉ: {len(livres)} livres")

            except Exception as e:
                print(f"    ❌ Erreur sélecteur '{selecteur}': {e}")

        return livres

    def extraire_infos_livre(self, item) -> Optional[Dict]:
        """Extraire TOUTES les informations complètes d'un livre depuis un élément HTML"""
        try:
            # TITRE - Méthode corrigée pour .octopus-pc-item
            titre = self.extraire_titre_correct(item)
            if titre == "Titre non trouvé" or len(titre) < 10:
                return None

            # URL - Méthode corrigée
            url = self.extraire_url_correct(item)
            if not url:
                return None

            # TOUTES LES DONNÉES COMPLÈTES
            prix = self.extraire_prix_correct(item)
            auteur = self.extraire_auteur_correct(item)
            note = self.extraire_note_correct(item)
            image = self.extraire_image_complete(item)

            # DESCRIPTION OPTIMISÉE - Utiliser notre système avec les 6 techniques
            print(f"🔍 Extraction description OPTIMISÉE pour: {titre[:40]}...")
            if url and url != "URL non trouvée":
                # Import des fonctions depuis FONCTION
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'FONCTION'))
                from description import recuperer_description_depuis_url

                description = recuperer_description_depuis_url(url, titre=titre)
                print(f"📝 Description OPTIMISÉE obtenue: {description[:60]}...")
            else:
                description = "Description non trouvée"
                print("❌ Pas d'URL - description impossible")

            nombre_avis = self.extraire_nombre_avis(item)
            editeur = self.extraire_editeur_complet(item)
            format_livre = self.extraire_format_complet(item)
            date_publication = self.extraire_date_publication(item)
            nombre_pages = self.extraire_nombre_pages(item)
            isbn = self.extraire_isbn_complet(item)
            dimensions = self.extraire_dimensions(item)
            disponibilite = self.extraire_disponibilite(item)

            # VÉRIFICATION FORMAT PRIX pour debugging
            print(f"    📖 {titre[:30]}... | 💰 Prix: '{prix}' | 👤 {auteur}")
            if prix and prix != "Prix non trouvé" and prix.count(',') == 1 and not prix.endswith('€'):
                print(f"    ⚠️  PRIX INCOMPLET DÉTECTÉ: '{prix}'")
            elif prix and '€' in prix:
                print(f"    ✅ Prix correct: '{prix}'")

            # STRUCTURE COMPLÈTE DU LIVRE
            livre = {
                'titre': titre,
                'auteur': auteur,
                'prix': prix,
                'note': note,
                'nombre_avis': nombre_avis,
                'image': image,
                'description': description,
                'editeur': editeur,
                'format': format_livre,
                'date_publication': date_publication,
                'nombre_pages': nombre_pages,
                'isbn': isbn,
                'dimensions': dimensions,
                'disponibilite': disponibilite,
                'url': url,
                'categorie': self.nom_categorie,
                'scrape_date': datetime.now().isoformat()
            }

            return livre

        except Exception as e:
            print(f"    ❌ Erreur extraction livre: {e}")
            return None

    def extraire_titre_correct(self, item) -> str:
        """Extraire le titre avec la méthode qui fonctionne pour pages de recherche"""
        try:
            # Méthode 1: Sélecteur titre spécifique pages de recherche
            titre_selectors = [
                'h2.a-size-mini span',
                'h2 a span',
                '.s-link-style a span',
                '[data-cy="title-recipe-review"] h2 a span',
                'h2.s-size-mini span'
            ]

            for selector in titre_selectors:
                titre_elem = item.select_one(selector)
                if titre_elem:
                    text = titre_elem.get_text(strip=True)
                    if len(text) > 5 and 'Livraison' not in text:
                        return text

            # Méthode 2: Chercher dans les liens avec /dp/
            links = item.find_all('a', href=True)
            for link in links:
                if '/dp/' in link.get('href', ''):
                    spans = link.find_all('span')
                    for span in spans:
                        text = span.get_text(strip=True)
                        if len(text) > 10 and 'Livraison' not in text and '€' not in text:
                            return text

            return "Titre non trouvé"
        except Exception:
            return "Titre non trouvé"

    def extraire_prix_correct(self, item) -> str:
        """Extraire le prix correctement pour pages de recherche"""
        try:
            # Sélecteurs prix spécifiques - Priorité au sélecteur avec prix complet
            prix_selectors = [
                '.a-price .a-offscreen',  # PRIORITÉ - Contient souvent le prix complet
                '.s-price-instructions-style .a-offscreen',
                '.a-price-range .a-offscreen',
                '.a-price-whole'  # En dernier car peut être incomplet
            ]

            for selector in prix_selectors:
                prix_elem = item.select_one(selector)
                if prix_elem:
                    text = prix_elem.get_text(strip=True)
                    if '€' in text:  # Prioriser les prix avec symbole €
                        print(f"    💰 Prix trouvé avec sélecteur '{selector}': '{text}'")
                        return text
                    elif any(c.isdigit() for c in text):
                        # Sauvegarder comme fallback si pas d'autres options
                        fallback_prix = text

            # Si pas de prix avec €, chercher dans tout le texte
            texts = item.find_all(string=True)
            prix_parts = []

            for text in texts:
                text_clean = str(text).strip()

                # Chercher prix complet avec €
                if '€' in text_clean and any(c.isdigit() for c in text_clean):
                    import re
                    # Regex amélioré pour prix complets
                    match = re.search(r'(\d+[,.]\d+\s*€|\d+\s*€)', text_clean)
                    if match:
                        prix_trouve = match.group(1)
                        print(f"    💰 Prix complet trouvé dans texte: '{prix_trouve}'")
                        return prix_trouve

            # Import re pour la section suivante
            import re

            # Collecter les parties du prix pour reconstitution
            for text in texts:
                text_clean = str(text).strip()
                if re.match(r'^\d+$', text_clean) and len(text_clean) <= 3:  # Partie entière
                    prix_parts.append(text_clean)
                elif re.match(r'^\d{2}$', text_clean):  # Partie décimale (centimes)
                    prix_parts.append(text_clean)
                elif text_clean == '€':  # Symbole €
                    prix_parts.append(text_clean)
                elif re.match(r'^\d+,$', text_clean):  # Nombre avec virgule
                    prix_parts.append(text_clean)

            # Reconstituer le prix à partir des parties
            if len(prix_parts) >= 2:
                print(f"    🔧 Parties trouvées: {prix_parts}")

                # Essayer de reconstituer le prix
                prix_reconstitue = ""
                for i, part in enumerate(prix_parts):
                    if re.match(r'^\d+$', part) and i == 0:  # Première partie = euros
                        prix_reconstitue += part
                    elif re.match(r'^\d+,$', part):  # Partie avec virgule
                        prix_reconstitue += part
                    elif re.match(r'^\d{2}$', part) and ',' in prix_reconstitue:  # Centimes
                        prix_reconstitue += part
                    elif part == '€':  # Symbole
                        prix_reconstitue += ' €'

                if prix_reconstitue and any(c.isdigit() for c in prix_reconstitue):
                    print(f"    🔧 Prix reconstitué: '{prix_reconstitue}'")
                    return prix_reconstitue

            return "Prix non trouvé"
        except Exception as e:
            print(f"    ❌ Erreur extraction prix: {e}")
            return "Prix non trouvé"

    def extraire_url_correct(self, item) -> Optional[str]:
        """Extraire l'URL correctement pour pages de recherche"""
        try:
            # Chercher le lien principal du titre
            titre_link = item.select_one('h2 a, .s-link-style a')
            if titre_link and titre_link.get('href'):
                href = titre_link.get('href')
                if '/dp/' in href:
                    if href.startswith('/'):
                        return self.url_base + href
                    elif href.startswith('http'):
                        return href

            # Sinon chercher tout lien avec /dp/
            links = item.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/dp/' in href:
                    if href.startswith('/'):
                        return self.url_base + href
                    elif href.startswith('http'):
                        return href
            return None
        except Exception:
            return None

    def extraire_auteur_correct(self, item) -> str:
        """Extraire l'auteur pour pages de recherche"""
        try:
            # Sélecteurs auteur spécifiques
            auteur_selectors = [
                '.a-color-secondary .a-link-normal',
                '.s-link-style + .a-row .a-link-normal',
                '.a-row.a-size-base .a-link-normal'
            ]

            for selector in auteur_selectors:
                auteur_elem = item.select_one(selector)
                if auteur_elem:
                    text = auteur_elem.get_text(strip=True)
                    if len(text) > 2 and len(text) < 50:
                        return text

            # Fallback: chercher "de XXX"
            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                import re
                match = re.search(r'de\s+([A-Za-zÀ-ÿ\s-]+)', text_clean)
                if match and len(match.group(1)) < 50:
                    return match.group(1).strip()

            return "Auteur non trouvé"
        except Exception:
            return "Auteur non trouvé"

    def extraire_note_correct(self, item) -> str:
        """Extraire la note pour pages de recherche"""
        try:
            # Sélecteurs note spécifiques
            note_selectors = [
                '.a-icon-alt',
                '[aria-label*="étoile"]',
                '[class*="star"] .a-icon-alt'
            ]

            for selector in note_selectors:
                note_elem = item.select_one(selector)
                if note_elem:
                    text = note_elem.get_text(strip=True) or note_elem.get('aria-label', '')
                    if 'étoile' in text or 'star' in text.lower():
                        return text

            # Fallback: chercher pattern note
            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                import re
                match = re.search(r'(\d[,.]\d)\s*sur\s*5', text_clean)
                if match:
                    return f"{match.group(1)} sur 5 étoiles"

            return "Note non trouvée"
        except Exception:
            return "Note non trouvée"

    def extraire_image_complete(self, item) -> str:
        """Extraire l'URL de l'image/couverture du livre"""
        try:
            # Sélecteurs d'images spécifiques pour pages de recherche Amazon
            img_selectors = [
                'img[data-image-index]',  # Images produits Amazon
                '.s-image',  # Images de recherche
                'img[src*="images-amazon"]',  # Images Amazon directes
                'img[src*="ssl-images-amazon"]',  # Images SSL Amazon
                'img.s-image',  # Images de résultats de recherche
                'img[alt*="livre"]',  # Images avec alt contenant "livre"
                'img[alt*="book"]'   # Images avec alt contenant "book"
            ]

            for selector in img_selectors:
                img = item.select_one(selector)
                if img and img.get('src'):
                    src = img.get('src')
                    # Vérifier que c'est une vraie image Amazon
                    if any(domain in src for domain in ['images-amazon', 'ssl-images-amazon', 'm.media-amazon']):
                        print(f"    🖼️  Image trouvée avec sélecteur '{selector}': {src[:50]}...")
                        return src

            # Méthode fallback: toutes les images dans l'item
            imgs = item.find_all('img', src=True)
            for img in imgs:
                src = img.get('src', '')
                # Filtrer les vraies images de livres Amazon
                if any(domain in src for domain in ['images-amazon', 'ssl-images-amazon', 'm.media-amazon']):
                    # Éviter les petites icones/placeholders
                    if not any(exclude in src for exclude in ['1x1', 'pixel', 'transparent', 'icon']):
                        print(f"    🖼️  Image fallback trouvée: {src[:50]}...")
                        return src

            return "Image non trouvée"
        except Exception as e:
            print(f"    ❌ Erreur extraction image: {e}")
            return "Image non trouvée"

    def extraire_description_complete(self, item) -> str:
        """Extraire la description/résumé du livre"""
        try:
            # Chercher les éléments de description
            desc_selectors = [
                '.a-size-base-plus',
                '.a-size-small .a-color-secondary',
                '[data-cy="title-recipe-review"] .a-size-small'
            ]

            for selector in desc_selectors:
                desc_elem = item.select_one(selector)
                if desc_elem:
                    text = desc_elem.get_text(strip=True)
                    if text and len(text) > 20:
                        return text

            return "Description non trouvée"
        except Exception:
            return "Description non trouvée"

    def extraire_nombre_avis(self, item) -> str:
        """Extraire le nombre d'avis/commentaires"""
        try:
            # Chercher les éléments avec le nombre d'avis
            avis_patterns = [
                r'(\d+(?:,\d+)?)\s*avis',
                r'(\d+(?:,\d+)?)\s*commentaire',
                r'(\d+(?:,\d+)?)\s*évaluation'
            ]

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                for pattern in avis_patterns:
                    import re
                    match = re.search(pattern, text_clean, re.IGNORECASE)
                    if match:
                        return match.group(0)

            return "Nombre d'avis non trouvé"
        except Exception:
            return "Nombre d'avis non trouvé"

    def extraire_editeur_complet(self, item) -> str:
        """Extraire l'éditeur du livre"""
        try:
            # Chercher dans les textes pour l'éditeur
            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                # Patterns pour éditeur
                if any(word in text_clean.lower() for word in ['éditions', 'éditeur', 'publisher']):
                    if len(text_clean) < 100:  # Éviter les longs textes
                        return text_clean

            return "Éditeur non trouvé"
        except Exception:
            return "Éditeur non trouvé"

    def extraire_format_complet(self, item) -> str:
        """Extraire le format du livre (broché, Kindle, etc.)"""
        try:
            # Chercher les formats dans le texte
            formats_possibles = ['broché', 'relié', 'kindle', 'poche', 'ebook', 'audio', 'numérique']

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip().lower()
                for format_type in formats_possibles:
                    if format_type in text_clean:
                        return format_type.capitalize()

            return "Format non trouvé"
        except Exception:
            return "Format non trouvé"

    def extraire_date_publication(self, item) -> str:
        """Extraire la date de publication"""
        try:
            import re
            # Pattern pour dates (jour mois année)
            date_pattern = r'(\d{1,2}\s+\w+\s+\d{4})'

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                match = re.search(date_pattern, text_clean)
                if match:
                    return match.group(1)

            return "Date de publication non trouvée"
        except Exception:
            return "Date de publication non trouvée"

    def extraire_nombre_pages(self, item) -> str:
        """Extraire le nombre de pages"""
        try:
            import re
            # Pattern pour nombre de pages
            page_pattern = r'(\d+)\s*pages?'

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                match = re.search(page_pattern, text_clean, re.IGNORECASE)
                if match:
                    return f"{match.group(1)} pages"

            return "Nombre de pages non trouvé"
        except Exception:
            return "Nombre de pages non trouvé"

    def extraire_isbn_complet(self, item) -> str:
        """Extraire l'ISBN du livre"""
        try:
            import re
            # Pattern pour ISBN
            isbn_pattern = r'ISBN[-:\s]*(\d{10}|\d{13}|\d{3}-\d{10})'

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                match = re.search(isbn_pattern, text_clean, re.IGNORECASE)
                if match:
                    return match.group(0)

            return "ISBN non trouvé"
        except Exception:
            return "ISBN non trouvé"

    def extraire_dimensions(self, item) -> str:
        """Extraire les dimensions du livre"""
        try:
            import re
            # Pattern pour dimensions (cm x cm)
            dim_pattern = r'(\d+(?:,\d+)?\s*x\s*\d+(?:,\d+)?\s*(?:x\s*\d+(?:,\d+)?)?\s*cm)'

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                match = re.search(dim_pattern, text_clean, re.IGNORECASE)
                if match:
                    return match.group(1)

            return "Dimensions non trouvées"
        except Exception:
            return "Dimensions non trouvées"

    def extraire_disponibilite(self, item) -> str:
        """Extraire la disponibilité du livre"""
        try:
            # Mots clés de disponibilité
            dispo_keywords = [
                'en stock', 'disponible', 'expédié par', 'livraison',
                'rupture', 'indisponible', 'temporairement', 'bientôt'
            ]

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip().lower()
                for keyword in dispo_keywords:
                    if keyword in text_clean and len(text_clean) < 100:
                        return str(text).strip()

            return "Disponibilité non trouvée"
        except Exception:
            return "Disponibilité non trouvée"

    def sauvegarder_livres(self, livres: List[Dict]):
        """Sauvegarder les livres dans un fichier JSON"""
        try:
            data_finale = {
                'metadata': {
                    'categorie': self.nom_categorie,
                    'url_source': self.url_categorie,
                    'date_scraping': datetime.now().isoformat(),
                    'total_livres': len(livres),
                    'scraper_version': '1.0'
                },
                'livres': livres
            }

            with open(self.fichier_livres, 'w', encoding='utf-8') as f:
                json.dump(data_finale, f, indent=2, ensure_ascii=False)

            print(f"💾 Sauvegardé: {self.fichier_livres}")
            print(f"📊 {len(livres)} livres sauvegardés")

        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")

    def generer_url_page(self, page_num: int) -> str:
        """Générer l'URL pour une page spécifique avec format recherche Amazon"""
        if page_num == 1:
            return self.url_categorie
        else:
            # Format correct pour pagination des RECHERCHES Amazon (utilise &page= au lieu de &pg=)
            if '?' in self.url_categorie:
                return f"{self.url_categorie}&page={page_num}"
            else:
                return f"{self.url_categorie}?page={page_num}"


    def mettre_a_jour_livre_complet(self, livre: Dict) -> Optional[Dict]:
        """Met à jour TOUTES les données d'un livre en re-scrapant sa page Amazon"""
        try:
            url = livre.get('url')
            if not url:
                return livre

            titre_court = livre.get('titre', 'N/A')[:30]
            print(f"    🔄 Mise à jour: {titre_court}...")

            # Faire requête vers la page du livre
            soup = self.faire_requete(url)
            if not soup:
                print(f"    ❌ Impossible de charger: {url}")
                return livre

            # Extraire TOUTES les nouvelles informations
            nouveau_livre = livre.copy()  # Conserver l'original comme base

            # Mise à jour du titre
            titre_elem = soup.find('span', {'id': 'productTitle'})
            if titre_elem:
                nouveau_livre['titre'] = titre_elem.get_text(strip=True)

            # Mise à jour du prix (CORRECTION PRIORITAIRE)
            prix_elem = soup.find('span', {'class': 'a-offscreen'})
            if not prix_elem:
                prix_elem = soup.find('span', class_='a-price-whole')
            if prix_elem:
                nouveau_livre['prix'] = prix_elem.get_text(strip=True)

            # Mise à jour de l'auteur
            auteur_elem = soup.find('span', class_='author') or soup.find('a', {'data-asin-item-name': 'author'})
            if auteur_elem:
                nouveau_livre['auteur'] = auteur_elem.get_text(strip=True)

            # Mise à jour de la note
            note_elem = soup.find('span', class_='a-icon-alt')
            if note_elem and 'étoiles' in note_elem.get_text():
                nouveau_livre['note'] = note_elem.get_text(strip=True)

            # Mise à jour description
            desc_elem = soup.find('div', {'id': 'feature-bullets'})
            if desc_elem:
                nouveau_livre['description'] = desc_elem.get_text(strip=True)[:500]

            # Timestamp de mise à jour
            nouveau_livre['date_mise_a_jour'] = datetime.now().isoformat()
            nouveau_livre['mise_a_jour_complete'] = True

            # Comparaison et affichage des changements
            ancien_prix = livre.get('prix', 'N/A')
            nouveau_prix = nouveau_livre.get('prix', 'N/A')
            if ancien_prix != nouveau_prix:
                print(f"       💰 Prix: {ancien_prix} → {nouveau_prix}")

            return nouveau_livre

        except Exception as e:
            print(f"    ❌ Erreur mise à jour livre: {e}")
            return livre

    def debug_html_structure(self, soup: BeautifulSoup):
        """Analyser la structure HTML pour debugging"""
        try:
            print("🔍 ANALYSE HTML STRUCTURE:")
            print(f"  📄 Taille HTML: {len(str(soup))} caractères")

            # Chercher les éléments possibles
            possible_selectors = [
                'div[data-component-type]',
                '.s-result-item',
                '[data-cel-widget]',
                'div[data-asin]',
                '.a-section',
                '.octopus-pc-item',
                '.s-card-container',
                'article',
                '[data-testid]'
            ]

            for selector in possible_selectors:
                elements = soup.select(selector)
                print(f"  📋 '{selector}': {len(elements)} éléments")
                if elements:
                    first_elem = elements[0]
                    attrs = dict(first_elem.attrs) if hasattr(first_elem, 'attrs') else {}
                    print(f"     🔍 Premier élément: {first_elem.name}, attrs: {list(attrs.keys())[:5]}")

            # Chercher des indices de livres dans le HTML
            html_text = str(soup).lower()
            indices = ['livre', 'book', 'title', 'prix', 'price', 'auteur', 'author']
            for indice in indices:
                count = html_text.count(indice)
                if count > 0:
                    print(f"  🔍 Mot-clé '{indice}': {count} occurrences")

            # Afficher début du HTML pour inspection manuelle
            html_snippet = str(soup)[:2000]
            print(f"  📝 Début HTML:\n{html_snippet}...")

        except Exception as e:
            print(f"❌ Erreur debug HTML: {e}")

    def run(self):
        """Exécution principale du scraper avec PAGINATION COMPLÈTE"""
        print(f"🚀 SCRAPER AMAZON - {self.nom_categorie.upper()}")
        print("=" * 60)
        print(f"🎯 URL: {self.url_categorie}")
        print(f"📄 Mode: SCRAPING DYNAMIQUE - Récupération de TOUS les livres existants")

        tous_les_livres = []
        page_actuelle = 1
        pages_sans_resultats = 0

        try:
            while page_actuelle <= self.max_pages and pages_sans_resultats < 3:
                print(f"\n🔹 SCRAPING PAGE {page_actuelle}")

                # Générer URL de la page
                url_page = self.generer_url_page(page_actuelle)
                soup = self.faire_requete(url_page)

                if not soup:
                    print(f"❌ Impossible de charger la page {page_actuelle}")
                    pages_sans_resultats += 1
                    page_actuelle += 1
                    continue

                # EXTRACTION PARALLÈLE ULTRA-RAPIDE
                print("🚀 MODE PARALLÈLE ACTIVÉ - Extraction ultra-rapide des descriptions...")
                livres_page = self.extraire_livres_page_parallele(soup)

                if not livres_page:
                    print(f"❌ Aucun livre trouvé page {page_actuelle}")
                    pages_sans_resultats += 1
                else:
                    print(f"✅ {len(livres_page)} livres extraits page {page_actuelle}")
                    tous_les_livres.extend(livres_page)
                    pages_sans_resultats = 0  # Reset compteur

                    # Sauvegarde progressive à chaque page
                    print(f"💾 MISE À JOUR PROGRESSIVE: {len(tous_les_livres)} livres (page {page_actuelle})")
                    self.sauvegarder_livres(tous_les_livres)

                page_actuelle += 1

                # Délai entre pages
                time.sleep(random.uniform(self.delay_min, self.delay_max))

            # Sauvegarde finale
            if tous_les_livres:
                print(f"\n💾 SAUVEGARDE FINALE")
                self.sauvegarder_livres(tous_les_livres)
                print(f"\n🎉 SCRAPING TERMINÉ - {len(tous_les_livres)} livres pour {self.nom_categorie}")
                print(f"📊 Pages scrapées: {page_actuelle - 1}")
                return len(tous_les_livres)
            else:
                print(f"\n❌ AUCUN LIVRE TROUVÉ")
                return 0

        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            # Sauvegarder ce qu'on a en cas d'erreur
            if tous_les_livres:
                print(f"💾 Sauvegarde d'urgence: {len(tous_les_livres)} livres")
                self.sauvegarder_livres(tous_les_livres)
            return len(tous_les_livres)

if __name__ == "__main__":
    scraper = ScraperAmazon_ScienceFiction()
    total = scraper.run()

    if total > 0:
        print(f"\n✅ SUCCÈS: {total} livres scrapés pour Science-Fiction")
    else:
        print(f"\n❌ ÉCHEC: Aucun livre trouvé pour Science-Fiction")
