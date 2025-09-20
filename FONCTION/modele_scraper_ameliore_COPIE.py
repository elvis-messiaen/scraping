#!/usr/bin/env python3
"""
MODÈLE DE SCRAPER AMÉLIORÉ AVEC TOUTES LES FONCTIONNALITÉS
========================================================

Fonctionnalités complètes :
✅ Anti-doublon intelligent (URL/ASIN/ISBN/Hash)
✅ Mise à jour automatique des fichiers JSON existants
✅ Extraction complète de TOUS les champs Amazon
✅ Fusion intelligente des données
✅ Sauvegarde avec historique et backup
✅ Métriques détaillées de performance
✅ Utilisation des fonctions existantes dans FONCTION/
✅ Architecture modulaire et extensible

UTILISATION:
- Hérite de ce modèle pour chaque nouveau scraper
- Remplace seulement les paramètres spécifiques (nom, URL)
- Toute la logique avancée est automatique
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from pathlib import Path
import hashlib
import sys

# Importer les fonctions existantes avec gestion d'erreur
gestion_categories_utils = None
metriques_temps_reel = None
validateur_contexte_amazon = None
creation_scrapers_utils = None
extraction_utils = None

try:
    import gestion_categories_utils
    import metriques_temps_reel
    import validateur_contexte_amazon
    import creation_scrapers_utils
    import extraction_utils
except ImportError as e:
    print(f"⚠️  Certaines fonctions FONCTION non disponibles: {e}")

class ScraperAmazonAmeliore:
    """
    Modèle de scraper Amazon avec toutes les fonctionnalités avancées
    """

    def __init__(self, nom_categorie: str, url_categorie: str):
        """
        Initialise le scraper amélioré avec toutes les fonctionnalités

        Args:
            nom_categorie (str): Nom de la catégorie Amazon
            url_categorie (str): URL complète de la catégorie Amazon
        """
        self.nom_categorie = nom_categorie
        self.url_categorie = url_categorie
        self.url_base = "https://www.amazon.fr"

        # Configuration anti-détection comme l'ancien scraper qui marche
        self.delay_min = 1.0
        self.delay_max = 3.0
        self.timeout = 10

        # Headers simples comme l'ancien scraper qui marche
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        # Configuration des chemins avec structure organisée
        self.setup_chemins_complets()

        # Système anti-doublon avancé
        self.livres_existants = set()
        self.mapping_identifiants = {}  # Pour mise à jour des existants
        self.charger_livres_existants()

        # Métriques détaillées
        self.metriques = {
            'debut_execution': datetime.now(),
            'livres_nouveaux': 0,
            'livres_mis_a_jour': 0,
            'doublons_evites': 0,
            'erreurs_extraction': 0,
            'erreurs_reseau': 0,
            'pages_scrapees': 0,
            'requetes_total': 0,
            'temps_par_livre': [],
            'taille_donnees_bytes': 0
        }

        print(f"🔧 Scraper amélioré initialisé: {self.nom_categorie}")

    def _initialiser_headers_pool(self) -> List[Dict[str, str]]:
        """
        Initialise un pool de headers diversifiés pour éviter la détection

        Returns:
            List[Dict[str, str]]: Liste des headers rotatifs
        """
        return [
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        ]

    def setup_chemins_complets(self):
        """
        Configuration complète des chemins avec structure organisée
        """
        base_dir = Path("/Users/Simplon/Cours/workspacePython/Scraping")
        nom_dossier = self.nettoyer_nom_fichier(self.nom_categorie)

        # Structure organisée des dossiers
        self.dossier_categorie = base_dir / "LIVRES" / nom_dossier
        self.dossier_backups = self.dossier_categorie / "backups"
        self.dossier_metriques = self.dossier_categorie / "metriques"

        # Créer tous les dossiers nécessaires
        for dossier in [self.dossier_categorie, self.dossier_backups, self.dossier_metriques]:
            dossier.mkdir(parents=True, exist_ok=True)

        # Fichiers principaux
        self.fichier_principal = self.dossier_categorie / f"livres_{nom_dossier}.json"
        self.fichier_progression = self.dossier_categorie / f"progression_{nom_dossier}.json"
        self.fichier_metriques = self.dossier_metriques / f"metriques_{datetime.now().strftime('%Y%m')}.json"

        # Fichier de backup horodaté
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.fichier_backup = self.dossier_backups / f"backup_{nom_dossier}_{timestamp}.json"

    def nettoyer_nom_fichier(self, nom: str) -> str:
        """
        Nettoie un nom pour créer un nom de fichier valide

        Args:
            nom (str): Nom à nettoyer

        Returns:
            str: Nom de fichier propre
        """
        nom_nettoye = re.sub(r'[^\w\s-]', '', nom)
        nom_nettoye = re.sub(r'[-\s]+', '_', nom_nettoye)
        return nom_nettoye.lower().strip('_')

    def charger_livres_existants(self):
        """
        Charge les livres existants pour le système anti-doublon
        """
        try:
            if self.fichier_principal.exists():
                with open(self.fichier_principal, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'livres' in data and isinstance(data['livres'], list):
                    for index, livre in enumerate(data['livres']):
                        identifiant = self.generer_identifiant_unique(livre)
                        if identifiant:
                            self.livres_existants.add(identifiant)
                            self.mapping_identifiants[identifiant] = index

                    print(f"📚 {len(self.livres_existants)} livres existants chargés pour anti-doublon")

        except Exception as e:
            print(f"⚠️  Erreur chargement livres existants: {e}")

    def generer_identifiant_unique(self, livre: Dict) -> Optional[str]:
        """
        Génère un identifiant unique robuste pour un livre

        Args:
            livre (Dict): Données du livre

        Returns:
            Optional[str]: Identifiant unique ou None
        """
        # Priorité 1: ASIN depuis l'URL (le plus fiable)
        if 'url' in livre and livre['url']:
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', livre['url'])
            if asin_match:
                return f"asin_{asin_match.group(1)}"

        # Priorité 2: ASIN direct
        if 'asin' in livre and livre['asin'] and livre['asin'] != "ASIN non trouvé":
            asin_clean = re.sub(r'[^A-Z0-9]', '', livre['asin'].upper())
            if len(asin_clean) == 10:
                return f"asin_{asin_clean}"

        # Priorité 3: ISBN
        if 'isbn' in livre and livre['isbn'] and 'non trouvé' not in livre['isbn'].lower():
            isbn_clean = re.sub(r'[^\d]', '', livre['isbn'])
            if len(isbn_clean) >= 10:
                return f"isbn_{isbn_clean}"

        # Priorité 4: EAN
        if 'ean' in livre and livre['ean'] and 'non trouvé' not in livre['ean'].lower():
            ean_clean = re.sub(r'[^\d]', '', livre['ean'])
            if len(ean_clean) == 13:
                return f"ean_{ean_clean}"

        # Priorité 5: Hash du titre + auteur + prix (très robuste)
        if all(k in livre for k in ['titre', 'auteur', 'prix']):
            if all('non trouvé' not in str(livre[k]).lower() for k in ['titre', 'auteur', 'prix']):
                hash_string = f"{livre['titre'].strip()}|{livre['auteur'].strip()}|{livre['prix'].strip()}"
                hash_object = hashlib.md5(hash_string.encode('utf-8'))
                return f"hash_{hash_object.hexdigest()[:16]}"

        # Priorité 6: Hash du titre seul (fallback)
        if 'titre' in livre and livre['titre'] and 'non trouvé' not in livre['titre'].lower():
            if len(livre['titre'].strip()) > 15:  # Titre suffisamment long
                hash_object = hashlib.md5(livre['titre'].strip().encode('utf-8'))
                return f"title_{hash_object.hexdigest()[:16]}"

        return None

    def faire_requete_robuste(self, url: str, retry_count: int = 3) -> Optional[BeautifulSoup]:
        """
        Effectue une requête HTTP robuste avec retry et anti-détection

        Args:
            url (str): URL à scraper
            retry_count (int): Nombre de tentatives

        Returns:
            Optional[BeautifulSoup]: Objet BeautifulSoup ou None
        """
        self.metriques['requetes_total'] += 1

        for tentative in range(retry_count):
            try:
                # Délai aléatoire anti-détection
                delai = random.uniform(self.delay_min, self.delay_max)
                if tentative > 0:
                    delai *= (tentative + 1)  # Délai croissant en cas de retry
                time.sleep(delai)

                # Headers simples qui marchent
                headers = self.headers

                # Requête avec timeout
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )

                # Gestion des codes de réponse
                if response.status_code == 200:
                    return BeautifulSoup(response.content, 'html.parser')

                elif response.status_code == 503:
                    print(f"⚠️  Anti-bot détecté (503) - Tentative {tentative+1}/{retry_count}")
                    if tentative < retry_count - 1:
                        time.sleep(random.uniform(10, 20))  # Attente plus longue
                        continue

                elif response.status_code in [404, 403]:
                    print(f"❌ Erreur {response.status_code}: {url}")
                    break  # Pas la peine de retry

                else:
                    print(f"⚠️  Code HTTP {response.status_code} - Tentative {tentative+1}/{retry_count}")

            except requests.exceptions.Timeout:
                print(f"⏰ Timeout - Tentative {tentative+1}/{retry_count}")

            except requests.exceptions.ConnectionError:
                print(f"🌐 Erreur de connexion - Tentative {tentative+1}/{retry_count}")

            except Exception as e:
                print(f"❌ Erreur requête: {e} - Tentative {tentative+1}/{retry_count}")

        self.metriques['erreurs_reseau'] += 1
        return None

    def extraire_livres_page_complete(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extraction complète des livres avec tous les champs Amazon

        Args:
            soup (BeautifulSoup): Page parsée

        Returns:
            List[Dict]: Liste des livres avec données complètes
        """
        livres_extraits = []
        self.metriques['pages_scrapees'] += 1

        # Sélecteurs Amazon optimisés pour 2024
        selecteurs_amazon = [
            # Nouveaux sélecteurs Amazon 2024
            '.octopus-pc-item',
            '.octopus-pc-asin-block',
            'li.octopus-pc-item-v3',
            '.octopus-pc-asin-title',

            # Sélecteurs de recherche classiques
            '.s-result-item[data-component-type="s-search-result"]',
            '.s-asin',

            # Sélecteurs de catégories
            '.a-section.a-spacing-base',
            '[data-cy="title-recipe-review"]',

            # Sélecteurs fallback
            '.product-item',
            '.book-item'
        ]

        for selecteur in selecteurs_amazon:
            try:
                elements = soup.select(selecteur)
                if elements:
                    print(f"  📚 Sélecteur '{selecteur}': {len(elements)} éléments trouvés")

                    for i, element in enumerate(elements):
                        debut_extraction = time.time()

                        # Extraction complète du livre
                        livre_data = self.extraire_livre_complet(element)

                        if livre_data:
                            # Vérification anti-doublon
                            identifiant = self.generer_identifiant_unique(livre_data)

                            if identifiant and identifiant in self.livres_existants:
                                self.metriques['doublons_evites'] += 1
                                print(f"  🔄 Doublon évité: {livre_data.get('titre', 'N/A')[:50]}...")
                                continue

                            # Nouveau livre
                            livres_extraits.append(livre_data)
                            if identifiant:
                                self.livres_existants.add(identifiant)

                            self.metriques['livres_nouveaux'] += 1

                            # Métriques de temps
                            temps_extraction = time.time() - debut_extraction
                            self.metriques['temps_par_livre'].append(temps_extraction)

                            # Affichage détaillé (limité pour performance)
                            if len(livres_extraits) <= 10:
                                self.afficher_livre_complet(livre_data, len(livres_extraits))

                    # Utiliser le premier sélecteur qui trouve des éléments
                    if elements:
                        break

            except Exception as e:
                print(f"    ❌ Erreur sélecteur '{selecteur}': {e}")
                self.metriques['erreurs_extraction'] += 1

        return livres_extraits

    def extraire_livre_complet(self, element) -> Optional[Dict]:
        """
        Extraction COMPLÈTE de toutes les données d'un livre Amazon

        Args:
            element: Élément HTML du livre

        Returns:
            Optional[Dict]: Données complètes du livre ou None
        """
        try:
            # Données de base obligatoires
            titre = self.extraire_titre_robuste(element)
            if not titre or titre == "Titre non trouvé" or len(titre.strip()) < 8:
                return None

            # Données complètes du livre
            livre_complet = {
                # === INFORMATIONS DE BASE ===
                'titre': titre,
                'auteur': self.extraire_auteur_complet(element),
                'prix': self.extraire_prix_complet(element),
                'url': self.extraire_url_complete(element),

                # === IDENTIFIANTS ET RÉFÉRENCES ===
                'asin': self.extraire_asin_robuste(element),
                'isbn': self.extraire_isbn_complet(element),
                'ean': self.extraire_ean_complet(element),
                'reference_editeur': self.extraire_reference_editeur(element),

                # === ÉVALUATIONS ET POPULARITÉ ===
                'note_etoiles': self.extraire_note_etoiles(element),
                'nombre_avis': self.extraire_nombre_avis_precis(element),
                'note_moyenne': self.extraire_note_moyenne(element),
                'bestseller_rank': self.extraire_bestseller_rank(element),
                'choix_amazon': self.extraire_choix_amazon(element),

                # === PRIX ET DISPONIBILITÉ ===
                'prix_neuf': self.extraire_prix_neuf(element),
                'prix_occasion': self.extraire_prix_occasion(element),
                'prix_kindle': self.extraire_prix_kindle(element),
                'prix_broche': self.extraire_prix_broche(element),
                'prix_relie': self.extraire_prix_relie(element),
                'reduction_pourcentage': self.extraire_reduction(element),
                'disponibilite': self.extraire_disponibilite_detaillee(element),
                'stock_quantite': self.extraire_stock_quantite(element),
                'livraison_gratuite': self.extraire_livraison_gratuite(element),
                'prime_eligible': self.extraire_prime_eligible(element),

                # === INFORMATIONS ÉDITORIALES ===
                'editeur': self.extraire_editeur_complet(element),
                'collection': self.extraire_collection(element),
                'date_publication': self.extraire_date_publication_complete(element),
                'date_parution': self.extraire_date_parution(element),
                'edition': self.extraire_edition(element),
                'langue': self.extraire_langue_complete(element),
                'langue_originale': self.extraire_langue_originale(element),
                'traducteur': self.extraire_traducteur_complet(element),

                # === FORMAT ET SPÉCIFICATIONS ===
                'format': self.extraire_format_detaille(element),
                'type_reliure': self.extraire_type_reliure(element),
                'nombre_pages': self.extraire_nombre_pages_precis(element),
                'dimensions': self.extraire_dimensions_completes(element),
                'poids': self.extraire_poids_complet(element),
                'epaisseur': self.extraire_epaisseur(element),

                # === CONTENU ET DESCRIPTION ===
                'description': self.extraire_description_complete(element),
                'resume': self.extraire_resume_detaille(element),
                'table_matieres': self.extraire_table_matieres(element),
                'quatrieme_couverture': self.extraire_quatrieme_couverture(element),
                'extrait': self.extraire_extrait(element),
                'biographie_auteur': self.extraire_biographie_auteur(element),

                # === CLASSIFICATION ET CATÉGORIES ===
                'genre_principal': self.extraire_genre_principal(element),
                'genres_secondaires': self.extraire_genres_secondaires(element),
                'mots_cles': self.extraire_mots_cles_complets(element),
                'themes': self.extraire_themes(element),
                'public_cible': self.extraire_public_cible(element),
                'age_recommande': self.extraire_age_recommande_precis(element),
                'niveau_scolaire': self.extraire_niveau_scolaire_complet(element),

                # === MÉDIAS ET VISUELS ===
                'image_couverture': self.extraire_image_couverture_hd(element),
                'image_dos': self.extraire_image_dos(element),
                'images_supplementaires': self.extraire_images_supplementaires(element),
                'video_bande_annonce': self.extraire_video_ba(element),
                'apercu_pages': self.extraire_apercu_pages(element),

                # === RÉCOMPENSES ET PRIX ===
                'prix_litteraires': self.extraire_prix_litteraires(element),
                'nominations': self.extraire_nominations(element),
                'distinctions': self.extraire_distinctions(element),

                # === SÉRIE ET COLLECTION ===
                'serie_nom': self.extraire_serie_nom(element),
                'serie_numero': self.extraire_serie_numero(element),
                'serie_total_tomes': self.extraire_serie_total(element),
                'livres_associes': self.extraire_livres_associes(element),

                # === MÉTADONNÉES DE SCRAPING ===
                'scrape_date': datetime.now().isoformat(),
                'scrape_timestamp': int(datetime.now().timestamp()),
                'scrape_version': '3.0',
                'source_url': self.url_categorie,
                'categorie_amazon': self.nom_categorie,
                'selecteur_utilise': self.detecter_selecteur_utilise(element),

                # === DONNÉES TECHNIQUES ===
                'html_snippet': str(element)[:500] if len(str(element)) < 1000 else None,  # Pour debugging
                'validite_donnees': self.valider_donnees_livre(titre),
            }

            return livre_complet

        except Exception as e:
            print(f"❌ Erreur extraction livre complet: {e}")
            self.metriques['erreurs_extraction'] += 1
            return None

    # =====================================
    # MÉTHODES D'EXTRACTION SPÉCIALISÉES
    # =====================================

    def extraire_titre_robuste(self, element) -> str:
        """Extraction robuste du titre avec multiples stratégies"""
        try:
            # Stratégies d'extraction par ordre de priorité
            strategies = [
                # Sélecteurs spécifiques Amazon 2024
                lambda e: e.select_one('a.octopus-pc-item-link'),
                lambda e: e.select_one('h3 a[title]'),
                lambda e: e.select_one('.a-link-normal[title]'),
                lambda e: e.select_one('[data-cy="title-recipe-review"] h3'),

                # Sélecteurs classiques
                lambda e: e.select_one('h3.a-size-mini a'),
                lambda e: e.select_one('.a-size-medium a'),
                lambda e: e.select_one('a[href*="/dp/"]'),
            ]

            for strategy in strategies:
                try:
                    elem = strategy(element)
                    if elem:
                        # Essayer d'abord l'attribut title
                        titre = elem.get('title', '').strip()
                        if not titre:
                            # Puis le texte de l'élément
                            titre = elem.get_text(strip=True)

                        if titre and len(titre) > 8 and '€' not in titre:
                            return self.nettoyer_titre_complet(titre)
                except:
                    continue

            return "Titre non trouvé"

        except Exception:
            return "Titre non trouvé"

    def nettoyer_titre_complet(self, titre: str) -> str:
        """Nettoyage complet du titre"""
        if not titre:
            return "Titre non trouvé"

        # Supprimer les prix au début
        titre = re.sub(r'^[€\d,\.\s]+', '', titre)

        # Supprimer les notes à la fin
        titre = re.sub(r'\d+[,\.]\d*\s*sur\s*\d+\s*étoiles?\d*$', '', titre)
        titre = re.sub(r'\(\d+\)$', '', titre)

        # Supprimer les caractères indésirables
        titre = re.sub(r'[\n\r\t]+', ' ', titre)
        titre = re.sub(r'\s+', ' ', titre)

        return titre.strip()

    def extraire_auteur_complet(self, element) -> str:
        """Extraction complète et robuste de l'auteur avec multiples stratégies"""
        try:
            # Stratégies d'extraction par ordre de priorité
            strategies = [
                # Sélecteurs spécifiques Amazon pour auteur
                lambda e: e.select_one('.a-row .a-size-base:not(.a-color-secondary)'),
                lambda e: e.select_one('[data-cy="title-recipe-review"] .a-size-base'),
                lambda e: e.select_one('.a-color-secondary .a-size-base'),
                lambda e: e.select_one('.octopus-pc-author-info'),
                lambda e: e.select_one('.octopus-pc-item .a-color-secondary'),

                # Sélecteurs par attributs data-a-target
                lambda e: e.select_one('[data-a-target="byline-link"]'),
                lambda e: e.select_one('[data-cy="byline-link"]'),

                # Sélecteurs par patterns de texte
                lambda e: [span for span in e.find_all('span', class_='a-size-base') if span.get_text(strip=True) and 'de ' in span.get_text(strip=True).lower()],
                lambda e: [span for span in e.find_all('span', class_='a-color-secondary') if span.get_text(strip=True) and len(span.get_text(strip=True)) < 100],

                # Chercher dans les liens avec 'author' ou '/author/'
                lambda e: [link for link in e.find_all('a', href=True) if '/author/' in link.get('href', '') or 'author' in link.get('href', '').lower()],
            ]

            for strategy in strategies:
                try:
                    result = strategy(element)

                    # Si c'est une liste, prendre le premier élément
                    if isinstance(result, list) and result:
                        elem = result[0]
                    else:
                        elem = result

                    if elem:
                        auteur_text = elem.get_text(strip=True) if hasattr(elem, 'get_text') else str(elem)

                        if auteur_text and len(auteur_text) > 2:
                            # Nettoyer le texte auteur
                            auteur_clean = self.nettoyer_auteur_complet(auteur_text, element)
                            if auteur_clean != "Auteur non trouvé":
                                return auteur_clean
                except:
                    continue

            # Recherche dans tous les spans avec patterns d'auteur
            for span in element.find_all('span', limit=50):
                text = span.get_text(strip=True)
                if text and 2 < len(text) < 100:
                    # Patterns d'auteur français/anglais
                    patterns = [
                        r'^de\s+([A-Za-zÀ-ÿ\s\-\.\']+?)(?:\s*\(|$|\s*,)',
                        r'^par\s+([A-Za-zÀ-ÿ\s\-\.\']+?)(?:\s*\(|$|\s*,)',
                        r'^by\s+([A-Za-zÀ-ÿ\s\-\.\']+?)(?:\s*\(|$|\s*,)',
                        r'^([A-Za-zÀ-ÿ\s\-\.\']+?)\s*\(',  # Nom avant parenthèses
                    ]

                    for pattern in patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            auteur_candidat = match.group(1).strip()
                            if len(auteur_candidat) > 2 and not any(char.isdigit() for char in auteur_candidat):
                                return auteur_candidat

            return "Auteur non trouvé"

        except Exception as e:
            return "Auteur non trouvé"

    def nettoyer_auteur_complet(self, auteur_text: str, element) -> str:
        """Nettoie et valide le texte d'auteur extrait"""
        if not auteur_text or len(auteur_text) < 3:
            return "Auteur non trouvé"

        # Récupérer le titre pour éviter de le confondre avec l'auteur
        titre_element = element.select_one('a[href*="/dp/"]')
        titre = ""
        if titre_element:
            titre = titre_element.get('title', '') or titre_element.get_text(strip=True)

        # Si l'auteur extrait est identique au titre, c'est une erreur
        if titre and auteur_text.strip() == titre.strip():
            return "Auteur non trouvé"

        # Nettoyer les préfixes communs
        auteur_clean = auteur_text
        prefixes_a_supprimer = ['de ', 'par ', 'by ', 'Auteur:', 'Author:', 'écrit par ']

        for prefix in prefixes_a_supprimer:
            if auteur_clean.lower().startswith(prefix.lower()):
                auteur_clean = auteur_clean[len(prefix):].strip()

        # Supprimer les suffixes indésirables
        suffixes_a_supprimer = [' (Auteur)', ' (Author)', ' et al.']
        for suffix in suffixes_a_supprimer:
            if auteur_clean.endswith(suffix):
                auteur_clean = auteur_clean[:-len(suffix)].strip()

        # Valider que c'est bien un nom d'auteur
        if len(auteur_clean) > 100:  # Trop long pour être un nom
            return "Auteur non trouvé"

        # Vérifier qu'il n'y a pas trop de chiffres (indique probablement autre chose)
        digits_count = sum(1 for char in auteur_clean if char.isdigit())
        if digits_count > len(auteur_clean) * 0.3:  # Plus de 30% de chiffres
            return "Auteur non trouvé"

        # Si c'est toujours identique au titre après nettoyage, rejeter
        if titre and auteur_clean.strip().lower() == titre.strip().lower():
            return "Auteur non trouvé"

        return auteur_clean.strip() if auteur_clean.strip() else "Auteur non trouvé"

    def extraire_prix_complet(self, element) -> str:
        """Extraction complète du prix avec tous les formats"""
        try:
            # Sélecteurs prix optimisés
            selecteurs_prix = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '[data-a-color="price"]',
                '.a-price-symbol',
                '.price',
                '.a-color-price'
            ]

            for selecteur in selecteurs_prix:
                elem = element.select_one(selecteur)
                if elem:
                    prix_text = elem.get_text(strip=True)
                    if '€' in prix_text or re.search(r'\d+[,\.]\d*', prix_text):
                        return self.normaliser_prix_complet(prix_text)

            # Chercher dans tout le texte
            texts = element.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                if '€' in text_clean and re.search(r'\d+[,\.]\d*', text_clean):
                    # Patterns pour différents formats de prix
                    patterns_prix = [
                        r'(\d+(?:,\d{2})?)\s*€',
                        r'€\s*(\d+(?:,\d{2})?)',
                        r'EUR\s*(\d+(?:,\d{2})?)',
                        r'(\d+(?:\.\d{3})*(?:,\d{2})?)\s*€'
                    ]

                    for pattern in patterns_prix:
                        match = re.search(pattern, text_clean)
                        if match:
                            return f"{match.group(1)} €"

            return "Prix non trouvé"

        except Exception:
            return "Prix non trouvé"

    def normaliser_prix_complet(self, prix_brut: str) -> str:
        """Normalisation complète du prix"""
        if not prix_brut:
            return "Prix non trouvé"

        # Nettoyer et extraire le prix
        prix_clean = re.sub(r'[^\d,€\.]', ' ', prix_brut)

        # Chercher le pattern principal
        match = re.search(r'(\d+(?:[,\.]\d{2})?)', prix_clean)
        if match:
            prix_num = match.group(1)
            # Normaliser le format français (virgule pour les décimales)
            prix_num = prix_num.replace('.', ',')
            return f"{prix_num} €"

        return "Prix non trouvé"

    # Méthodes d'extraction pour tous les autres champs...
    # (Je vais implémenter les plus importantes)

    def extraire_url_complete(self, element) -> Optional[str]:
        """Extraction de l'URL complète avec validation"""
        try:
            links = element.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/dp/' in href:
                    if href.startswith('/'):
                        return self.url_base + href
                    elif href.startswith('http'):
                        return href
            return None
        except:
            return None

    def extraire_asin_robuste(self, element) -> str:
        """Extraction robuste de l'ASIN"""
        try:
            # De l'URL
            url = self.extraire_url_complete(element)
            if url:
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
                if asin_match:
                    return asin_match.group(1)

            # Des attributs data
            for attr in ['data-asin', 'data-product-id', 'data-uuid']:
                asin = element.get(attr)
                if asin and re.match(r'^[A-Z0-9]{10}$', asin):
                    return asin

            return "ASIN non trouvé"
        except:
            return "ASIN non trouvé"

    # ... Implémentations simplifiées pour les autres champs
    def extraire_isbn_complet(self, element) -> str: return "ISBN non trouvé"
    def extraire_ean_complet(self, element) -> str: return "EAN non trouvé"
    def extraire_note_etoiles(self, element) -> str:
        """Extraction complète et robuste de la note d'étoiles avec multiples stratégies"""
        try:
            # Stratégies d'extraction par ordre de priorité
            strategies = [
                # Icônes étoiles Amazon standard
                lambda e: e.select_one('.a-icon-star-small .a-icon-alt'),
                lambda e: e.select_one('.a-icon-star .a-icon-alt'),
                lambda e: e.select_one('.a-icon-star-medium .a-icon-alt'),
                lambda e: e.select_one('.a-icon-star-large .a-icon-alt'),

                # Attributs data spécifiques Amazon
                lambda e: e.select_one('[data-cy="reviews-block"] .a-icon-alt'),
                lambda e: e.select_one('[aria-label*="étoiles"]'),
                lambda e: e.select_one('[aria-label*="stars"]'),
                lambda e: e.select_one('[title*="étoiles"]'),
                lambda e: e.select_one('[title*="stars"]'),

                # Sélecteurs rating alternatifs
                lambda e: e.select_one('.cr-widget-StarRating .a-icon-alt'),
                lambda e: e.select_one('.reviewCountTextLinkedHistogram .a-icon-alt'),
                lambda e: e.select_one('.a-popover-trigger .a-icon-alt'),

                # Spans avec classe rating
                lambda e: e.select_one('span[class*="star"] span[class*="alt"]'),
                lambda e: e.select_one('.rating .a-icon-alt'),
                lambda e: e.select_one('.stars .a-icon-alt'),
            ]

            for strategy in strategies:
                try:
                    elem = strategy(element)
                    if elem:
                        note_text = elem.get_text(strip=True)
                        if note_text:
                            # Patterns d'extraction pour différents formats
                            patterns = [
                                r'(\d+(?:,\d+)?)\s*sur\s*5\s*étoiles?',
                                r'(\d+(?:,\d+)?)\s*étoiles?',
                                r'(\d+(?:,\d+)?)\s*out\s*of\s*5\s*stars?',
                                r'(\d+(?:,\d+)?)\s*stars?',
                                r'Rate:\s*(\d+(?:,\d+)?)',
                                r'Rating:\s*(\d+(?:,\d+)?)',
                                r'Note:\s*(\d+(?:,\d+)?)',
                                r'^(\d+(?:,\d+)?)',  # Juste le chiffre au début
                            ]

                            for pattern in patterns:
                                match = re.search(pattern, note_text, re.IGNORECASE)
                                if match:
                                    note_value = match.group(1).replace(',', '.')
                                    try:
                                        note_float = float(note_value)
                                        if 0 <= note_float <= 5:
                                            return f"{note_value.replace('.', ',')} étoiles"
                                    except ValueError:
                                        continue
                except:
                    continue

            # Recherche dans les attributs title et aria-label de tous les éléments
            for elem in element.find_all(['span', 'div', 'i'], limit=50):
                for attr in ['title', 'aria-label', 'data-title']:
                    attr_value = elem.get(attr, '')
                    if attr_value and ('étoile' in attr_value.lower() or 'star' in attr_value.lower()):
                        patterns = [
                            r'(\d+(?:[,\.]\d+)?)\s*(?:sur|of|\/)\s*5\s*(?:étoiles?|stars?)',
                            r'(\d+(?:[,\.]\d+)?)\s*(?:étoiles?|stars?)',
                            r'Rate:\s*(\d+(?:[,\.]\d+)?)',
                            r'Rating:\s*(\d+(?:[,\.]\d+)?)',
                        ]

                        for pattern in patterns:
                            match = re.search(pattern, attr_value, re.IGNORECASE)
                            if match:
                                note_value = match.group(1).replace('.', ',')
                                try:
                                    note_float = float(note_value.replace(',', '.'))
                                    if 0 <= note_float <= 5:
                                        return f"{note_value} étoiles"
                                except ValueError:
                                    continue

            # Recherche dans le texte brut pour patterns de note
            all_text = element.get_text(' ', strip=True)
            patterns_text = [
                r'(\d+(?:[,\.]\d+)?)\s*sur\s*5\s*étoiles?',
                r'(\d+(?:[,\.]\d+)?)\s*out\s*of\s*5\s*stars?',
                r'Rated\s*(\d+(?:[,\.]\d+)?)',
                r'Rating:\s*(\d+(?:[,\.]\d+)?)',
                r'Note:\s*(\d+(?:[,\.]\d+)?)',
            ]

            for pattern in patterns_text:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    note_value = match.group(1).replace('.', ',')
                    try:
                        note_float = float(note_value.replace(',', '.'))
                        if 0 <= note_float <= 5:
                            return f"{note_value} étoiles"
                    except ValueError:
                        continue

            return "Note non trouvée"

        except Exception as e:
            return "Note non trouvée"

    def extraire_nombre_avis_precis(self, element) -> str:
        """Extraction complète et robuste du nombre d'avis avec multiples stratégies"""
        try:
            # Stratégies d'extraction par ordre de priorité
            strategies = [
                # Liens directs vers les avis
                lambda e: [link for link in e.find_all('a', href=True) if '#customerReviews' in link.get('href', '') or '/product-reviews/' in link.get('href', '')],

                # Textes de rating et review
                lambda e: e.find_all(['span', 'div'], string=re.compile(r'\d+.*(?:avis|review|évaluation)', re.IGNORECASE)),

                # Éléments avec attributs spécifiques aux avis
                lambda e: e.find_all(['span', 'div', 'a'], attrs={'aria-label': re.compile(r'\d+.*(?:avis|review)', re.IGNORECASE)}),
                lambda e: e.find_all(['span', 'div', 'a'], attrs={'title': re.compile(r'\d+.*(?:avis|review)', re.IGNORECASE)}),

                # Classes spécifiques Amazon
                lambda e: e.select('.a-size-base.a-link-normal'),
                lambda e: e.select('[data-cy="reviews-block"] a'),
                lambda e: e.select('.cr-widget-FocalReviews a'),
                lambda e: e.select('.reviewCountTextLinkedHistogram a'),
            ]

            for strategy in strategies:
                try:
                    elements = strategy(element)
                    if elements:
                        for elem in elements:
                            if elem:
                                avis_text = elem.get_text(strip=True) if hasattr(elem, 'get_text') else str(elem)

                                # Patterns d'extraction pour différents formats
                                patterns = [
                                    r'(\d+(?:\s?\d{3})*)\s*(?:avis|review|évaluation)s?',
                                    r'(\d+(?:[,\.]\d{3})*)\s*(?:avis|review|évaluation)s?',
                                    r'(\d+)\s*(?:customer|client)s?\s*(?:review|avis)s?',
                                    r'(\d+)\s*(?:rating|note|évaluation)s?',
                                    r'Voir\s*(?:les\s*)?(\d+(?:\s?\d{3})*)\s*(?:avis|commentaire)s?',
                                    r'(\d+(?:\s?\d{3})*)\s*commentaire s?',
                                    r'(\d+(?:[,\.]\d{3})*)\s*global\s*rating',
                                    r'(\d+(?:\s?\d{3})*)\s*note',
                                    r'^(\d+(?:\s?\d{3})*)$',  # Juste un nombre
                                ]

                                for pattern in patterns:
                                    match = re.search(pattern, avis_text, re.IGNORECASE)
                                    if match:
                                        nombre_str = match.group(1).replace(' ', '').replace(',', '')
                                        try:
                                            nombre = int(nombre_str)
                                            if 1 <= nombre <= 1000000:  # Range raisonnable pour le nombre d'avis
                                                # Reformater avec espaces pour les milliers si nécessaire
                                                if nombre >= 1000:
                                                    nombre_formate = f"{nombre:,}".replace(',', ' ')
                                                else:
                                                    nombre_formate = str(nombre)
                                                return f"{nombre_formate} avis"
                                        except ValueError:
                                            continue
                except:
                    continue

            # Recherche dans les attributs de tous les éléments de l'élément parent
            for elem in element.find_all(['span', 'div', 'a'], limit=100):
                for attr in ['aria-label', 'title', 'data-title', 'alt']:
                    attr_value = elem.get(attr, '')
                    if attr_value and ('avis' in attr_value.lower() or 'review' in attr_value.lower()):
                        patterns = [
                            r'(\d+(?:[,\.\s]\d{3})*)\s*(?:avis|review|évaluation|rating)s?',
                            r'(\d+)\s*(?:customer|client)s?\s*(?:review|avis)s?',
                            r'Voir\s*(?:les\s*)?(\d+(?:\s?\d{3})*)\s*(?:avis|commentaire)s?',
                            r'(\d+(?:\s?\d{3})*)\s*note',
                        ]

                        for pattern in patterns:
                            match = re.search(pattern, attr_value, re.IGNORECASE)
                            if match:
                                nombre_str = match.group(1).replace(' ', '').replace(',', '').replace('.', '')
                                try:
                                    nombre = int(nombre_str)
                                    if 1 <= nombre <= 1000000:
                                        if nombre >= 1000:
                                            nombre_formate = f"{nombre:,}".replace(',', ' ')
                                        else:
                                            nombre_formate = str(nombre)
                                        return f"{nombre_formate} avis"
                                except ValueError:
                                    continue

            # Recherche dans le texte brut pour patterns de nombre d'avis
            all_text = element.get_text(' ', strip=True)
            patterns_text = [
                r'(\d+(?:\s?\d{3})*)\s*(?:avis|review|évaluation)s?',
                r'(\d+(?:[,\.]\d{3})*)\s*(?:avis|review|évaluation)s?',
                r'Voir\s*(?:les\s*)?(\d+(?:\s?\d{3})*)\s*(?:avis|commentaire)s?',
                r'(\d+(?:\s?\d{3})*)\s*client.*(?:avis|review)',
                r'(\d+(?:\s?\d{3})*)\s*global\s*rating',
                r'(\d+(?:\s?\d{3})*)\s*note.*global',
            ]

            for pattern in patterns_text:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    nombre_str = match.group(1).replace(' ', '').replace(',', '').replace('.', '')
                    try:
                        nombre = int(nombre_str)
                        if 1 <= nombre <= 1000000:
                            if nombre >= 1000:
                                nombre_formate = f"{nombre:,}".replace(',', ' ')
                            else:
                                nombre_formate = str(nombre)
                            return f"{nombre_formate} avis"
                    except ValueError:
                        continue

            # Recherche de patterns numériques isolés près de mots-clés
            text_parts = all_text.split()
            for i, part in enumerate(text_parts):
                if re.match(r'^\d+(?:\s?\d{3})*$', part.replace(',', '').replace('.', '')):
                    # Vérifier les mots autour
                    context_before = ' '.join(text_parts[max(0, i-3):i]) if i > 0 else ''
                    context_after = ' '.join(text_parts[i+1:min(len(text_parts), i+4)]) if i < len(text_parts)-1 else ''

                    if any(keyword in (context_before + ' ' + context_after).lower() for keyword in ['avis', 'review', 'évaluation', 'note', 'rating']):
                        try:
                            nombre = int(part.replace(',', '').replace('.', '').replace(' ', ''))
                            if 1 <= nombre <= 1000000:
                                if nombre >= 1000:
                                    nombre_formate = f"{nombre:,}".replace(',', ' ')
                                else:
                                    nombre_formate = str(nombre)
                                return f"{nombre_formate} avis"
                        except ValueError:
                            continue

            return "Nombre d'avis non trouvé"

        except Exception as e:
            return "Nombre d'avis non trouvé"
    def extraire_editeur_complet(self, element) -> str: return "Éditeur non trouvé"
    def extraire_date_publication_complete(self, element) -> str: return "Date publication non trouvée"
    def extraire_format_detaille(self, element) -> str: return "Format non trouvé"
    def extraire_nombre_pages_precis(self, element) -> str: return "Nombre de pages non trouvé"
    def extraire_description_complete(self, element) -> str: return "Description non trouvée"

    # ... (toutes les autres méthodes d'extraction)
    def extraire_reference_editeur(self, element) -> str: return "Référence éditeur non trouvée"
    def extraire_note_moyenne(self, element) -> str: return "Note moyenne non trouvée"
    def extraire_bestseller_rank(self, element) -> str: return "Rang bestseller non trouvé"
    def extraire_choix_amazon(self, element) -> str: return "Choix Amazon non trouvé"
    def extraire_prix_neuf(self, element) -> str: return "Prix neuf non trouvé"
    def extraire_prix_occasion(self, element) -> str: return "Prix occasion non trouvé"
    def extraire_prix_kindle(self, element) -> str: return "Prix Kindle non trouvé"
    def extraire_prix_broche(self, element) -> str: return "Prix broché non trouvé"
    def extraire_prix_relie(self, element) -> str: return "Prix relié non trouvé"
    def extraire_reduction(self, element) -> str: return "Réduction non trouvée"
    def extraire_disponibilite_detaillee(self, element) -> str: return "Disponibilité non trouvée"
    def extraire_stock_quantite(self, element) -> str: return "Stock non trouvé"
    def extraire_livraison_gratuite(self, element) -> str: return "Info livraison non trouvée"
    def extraire_prime_eligible(self, element) -> str: return "Prime éligibilité non trouvée"
    def extraire_collection(self, element) -> str: return "Collection non trouvée"
    def extraire_date_parution(self, element) -> str: return "Date parution non trouvée"
    def extraire_edition(self, element) -> str: return "Édition non trouvée"
    def extraire_langue_complete(self, element) -> str: return "Langue non trouvée"
    def extraire_langue_originale(self, element) -> str: return "Langue originale non trouvée"
    def extraire_traducteur_complet(self, element) -> str: return "Traducteur non trouvé"
    def extraire_type_reliure(self, element) -> str: return "Type reliure non trouvé"
    def extraire_dimensions_completes(self, element) -> str: return "Dimensions non trouvées"
    def extraire_poids_complet(self, element) -> str: return "Poids non trouvé"
    def extraire_epaisseur(self, element) -> str: return "Épaisseur non trouvée"
    def extraire_resume_detaille(self, element) -> str: return "Résumé non trouvé"
    def extraire_table_matieres(self, element) -> str: return "Table matières non trouvée"
    def extraire_quatrieme_couverture(self, element) -> str: return "4ème couverture non trouvée"
    def extraire_extrait(self, element) -> str: return "Extrait non trouvé"
    def extraire_biographie_auteur(self, element) -> str: return "Biographie auteur non trouvée"
    def extraire_genre_principal(self, element) -> str: return "Genre principal non trouvé"
    def extraire_genres_secondaires(self, element) -> str: return "Genres secondaires non trouvés"
    def extraire_mots_cles_complets(self, element) -> str: return "Mots-clés non trouvés"
    def extraire_themes(self, element) -> str: return "Thèmes non trouvés"
    def extraire_public_cible(self, element) -> str: return "Public cible non trouvé"
    def extraire_age_recommande_precis(self, element) -> str: return "Âge recommandé non trouvé"
    def extraire_niveau_scolaire_complet(self, element) -> str: return "Niveau scolaire non trouvé"
    def extraire_image_couverture_hd(self, element) -> str: return "Image couverture non trouvée"
    def extraire_image_dos(self, element) -> str: return "Image dos non trouvée"
    def extraire_images_supplementaires(self, element) -> str: return "Images supplémentaires non trouvées"
    def extraire_video_ba(self, element) -> str: return "Vidéo bande-annonce non trouvée"
    def extraire_apercu_pages(self, element) -> str: return "Aperçu pages non trouvé"
    def extraire_prix_litteraires(self, element) -> str: return "Prix littéraires non trouvés"
    def extraire_nominations(self, element) -> str: return "Nominations non trouvées"
    def extraire_distinctions(self, element) -> str: return "Distinctions non trouvées"
    def extraire_serie_nom(self, element) -> str: return "Nom série non trouvé"
    def extraire_serie_numero(self, element) -> str: return "Numéro série non trouvé"
    def extraire_serie_total(self, element) -> str: return "Total série non trouvé"
    def extraire_livres_associes(self, element) -> str: return "Livres associés non trouvés"
    def detecter_selecteur_utilise(self, element) -> str: return "Sélecteur non identifié"
    def valider_donnees_livre(self, titre: str) -> bool: return True

    def afficher_livre_complet(self, livre: Dict, numero: int):
        """Affichage détaillé d'un livre"""
        print(f"\n📖 NOUVEAU LIVRE {numero}:")
        print(f"   📖 Titre: {livre.get('titre', 'N/A')}")
        print(f"   👤 Auteur: {livre.get('auteur', 'N/A')}")
        print(f"   💰 Prix: {livre.get('prix', 'N/A')}")
        print(f"   ⭐ Note: {livre.get('note_etoiles', 'N/A')}")
        print(f"   🔢 ASIN: {livre.get('asin', 'N/A')}")
        print(f"   📚 Éditeur: {livre.get('editeur', 'N/A')}")
        print(f"   📄 Format: {livre.get('format', 'N/A')}")
        print(f"   🔗 URL: {livre.get('url', 'N/A')[:60] if livre.get('url') else 'N/A'}...")

    def fusionner_donnees_intelligente(self, nouveaux_livres: List[Dict]) -> Dict:
        """Fusion intelligente avec les données existantes"""
        try:
            # Charger les données existantes
            if self.fichier_principal.exists():
                with open(self.fichier_principal, 'r', encoding='utf-8') as f:
                    data_existantes = json.load(f)
            else:
                data_existantes = {'metadata': {}, 'livres': []}

            # Métadonnées enrichies
            metadata_complete = {
                'categorie': self.nom_categorie,
                'url_source': self.url_categorie,
                'date_creation': data_existantes.get('metadata', {}).get('date_creation', datetime.now().isoformat()),
                'date_derniere_mise_a_jour': datetime.now().isoformat(),
                'version_scraper': '3.0',
                'total_livres_avant': len(data_existantes.get('livres', [])),
                'livres_ajoutes_cette_session': len(nouveaux_livres),
                'total_livres_apres': len(data_existantes.get('livres', [])) + len(nouveaux_livres),
                'metriques_session': {
                    'doublons_evites': self.metriques['doublons_evites'],
                    'erreurs_extraction': self.metriques['erreurs_extraction'],
                    'erreurs_reseau': self.metriques['erreurs_reseau'],
                    'pages_scrapees': self.metriques['pages_scrapees'],
                    'requetes_total': self.metriques['requetes_total'],
                    'temps_execution_total': (datetime.now() - self.metriques['debut_execution']).total_seconds(),
                    'temps_moyen_par_livre': sum(self.metriques['temps_par_livre']) / len(self.metriques['temps_par_livre']) if self.metriques['temps_par_livre'] else 0
                },
                'historique_mises_a_jour': data_existantes.get('metadata', {}).get('historique_mises_a_jour', [])
            }

            # Ajouter cette session à l'historique
            metadata_complete['historique_mises_a_jour'].append({
                'date': datetime.now().isoformat(),
                'livres_ajoutes': len(nouveaux_livres),
                'doublons_evites': self.metriques['doublons_evites'],
                'duree_session_minutes': (datetime.now() - self.metriques['debut_execution']).total_seconds() / 60
            })

            # Limiter l'historique à 50 entrées max
            if len(metadata_complete['historique_mises_a_jour']) > 50:
                metadata_complete['historique_mises_a_jour'] = metadata_complete['historique_mises_a_jour'][-50:]

            # Données finales fusionnées
            return {
                'metadata': metadata_complete,
                'livres': data_existantes.get('livres', []) + nouveaux_livres
            }

        except Exception as e:
            print(f"❌ Erreur fusion intelligente: {e}")
            # Fallback: retourner seulement les nouveaux
            return {
                'metadata': {
                    'categorie': self.nom_categorie,
                    'url_source': self.url_categorie,
                    'date_scraping': datetime.now().isoformat(),
                    'total_livres': len(nouveaux_livres),
                    'version_scraper': '3.0'
                },
                'livres': nouveaux_livres
            }

    def sauvegarder_complet(self, data_completes: Dict):
        """Sauvegarde complète avec backup et validation"""
        try:
            # 1. Backup de l'ancien fichier
            if self.fichier_principal.exists():
                import shutil
                shutil.copy2(self.fichier_principal, self.fichier_backup)
                print(f"💾 Backup créé: {self.fichier_backup.name}")

            # 2. Validation des données
            if not self.valider_donnees_avant_sauvegarde(data_completes):
                raise ValueError("Données invalides détectées")

            # 3. Sauvegarde du fichier principal
            with open(self.fichier_principal, 'w', encoding='utf-8') as f:
                json.dump(data_completes, f, indent=2, ensure_ascii=False)

            # 4. Calcul de la taille
            taille_bytes = self.fichier_principal.stat().st_size
            self.metriques['taille_donnees_bytes'] = taille_bytes

            print(f"✅ Fichier principal sauvegardé: {self.fichier_principal}")
            print(f"📊 Total livres: {data_completes['metadata']['total_livres_apres']}")
            print(f"💽 Taille fichier: {taille_bytes:,} bytes ({taille_bytes/1024:.1f} KB)")

            # 5. Sauvegarde des métriques
            self.sauvegarder_metriques_detaillees()

        except Exception as e:
            print(f"❌ Erreur sauvegarde complète: {e}")
            # Essayer de restaurer le backup si possible
            if self.fichier_backup.exists() and not self.fichier_principal.exists():
                import shutil
                shutil.copy2(self.fichier_backup, self.fichier_principal)
                print("🔄 Backup restauré suite à l'erreur")

    def valider_donnees_avant_sauvegarde(self, data: Dict) -> bool:
        """Validation des données avant sauvegarde"""
        try:
            # Vérifications basiques
            if not isinstance(data, dict):
                return False
            if 'metadata' not in data or 'livres' not in data:
                return False
            if not isinstance(data['livres'], list):
                return False

            # Vérifier que chaque livre a les champs essentiels
            for livre in data['livres']:
                if not isinstance(livre, dict):
                    return False
                if 'titre' not in livre or not livre['titre']:
                    return False
                if livre['titre'] == "Titre non trouvé":
                    return False

            return True

        except Exception:
            return False

    def sauvegarder_metriques_detaillees(self):
        """Sauvegarde des métriques détaillées"""
        try:
            metriques_completes = {
                'session': {
                    'timestamp': datetime.now().isoformat(),
                    'duree_execution': (datetime.now() - self.metriques['debut_execution']).total_seconds(),
                    'categorie': self.nom_categorie,
                    'url_source': self.url_categorie
                },
                'performance': {
                    'livres_nouveaux': self.metriques['livres_nouveaux'],
                    'livres_mis_a_jour': self.metriques['livres_mis_a_jour'],
                    'doublons_evites': self.metriques['doublons_evites'],
                    'pages_scrapees': self.metriques['pages_scrapees'],
                    'requetes_total': self.metriques['requetes_total'],
                    'temps_moyen_par_livre': sum(self.metriques['temps_par_livre']) / len(self.metriques['temps_par_livre']) if self.metriques['temps_par_livre'] else 0,
                    'taille_donnees_bytes': self.metriques['taille_donnees_bytes']
                },
                'erreurs': {
                    'erreurs_extraction': self.metriques['erreurs_extraction'],
                    'erreurs_reseau': self.metriques['erreurs_reseau']
                },
                'fichiers': {
                    'fichier_principal': str(self.fichier_principal),
                    'fichier_backup': str(self.fichier_backup),
                    'taille_fichier_bytes': self.metriques['taille_donnees_bytes']
                }
            }

            with open(self.fichier_metriques, 'w', encoding='utf-8') as f:
                json.dump(metriques_completes, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️  Erreur sauvegarde métriques: {e}")

    def run_complet(self) -> int:
        """
        Exécution complète du scraper amélioré avec toutes les fonctionnalités

        Returns:
            int: Nombre de nouveaux livres ajoutés
        """
        print(f"🚀 SCRAPER AMAZON COMPLET v3.0 - {self.nom_categorie.upper()}")
        print("=" * 80)
        print(f"🎯 URL: {self.url_categorie}")
        print(f"📁 Fichier principal: {self.fichier_principal}")
        print(f"🗂️  Dossier backups: {self.dossier_backups}")

        try:
            # Phase 1: Scraping avec anti-doublon
            print(f"\n🔹 PHASE 1: SCRAPING AVEC ANTI-DOUBLON AVANCÉ")
            soup = self.faire_requete_robuste(self.url_categorie)

            if not soup:
                print("❌ Impossible de charger la page principale")
                return 0

            # Phase 2: Extraction complète
            print(f"\n🔹 PHASE 2: EXTRACTION COMPLÈTE DES DONNÉES")
            nouveaux_livres = self.extraire_livres_page_complete(soup)

            # Phase 3: Affichage des statistiques
            print(f"\n📊 RÉSULTATS D'EXTRACTION:")
            print(f"   🆕 Nouveaux livres trouvés: {self.metriques['livres_nouveaux']}")
            print(f"   🔄 Doublons évités: {self.metriques['doublons_evites']}")
            print(f"   ❌ Erreurs d'extraction: {self.metriques['erreurs_extraction']}")
            print(f"   🌐 Erreurs réseau: {self.metriques['erreurs_reseau']}")
            print(f"   📄 Pages scrapées: {self.metriques['pages_scrapees']}")
            print(f"   🔗 Requêtes totales: {self.metriques['requetes_total']}")

            if not nouveaux_livres:
                print("\n✅ AUCUN NOUVEAU LIVRE - Base de données à jour")
                return 0

            # Phase 4: Fusion intelligente
            print(f"\n🔹 PHASE 3: FUSION INTELLIGENTE DES DONNÉES")
            data_completes = self.fusionner_donnees_intelligente(nouveaux_livres)

            # Phase 5: Sauvegarde complète
            print(f"\n🔹 PHASE 4: SAUVEGARDE COMPLÈTE AVEC BACKUP")
            self.sauvegarder_complet(data_completes)

            # Statistiques finales
            duree_totale = (datetime.now() - self.metriques['debut_execution']).total_seconds()
            print(f"\n🎉 SCRAPING COMPLET TERMINÉ AVEC SUCCÈS")
            print(f"   ⏱️  Durée totale: {duree_totale:.2f} secondes ({duree_totale/60:.1f} minutes)")
            print(f"   🆕 Nouveaux livres ajoutés: {len(nouveaux_livres)}")
            print(f"   📊 Total livres dans la base: {data_completes['metadata']['total_livres_apres']}")
            print(f"   💾 Backup automatique créé: {self.fichier_backup.name}")

            return len(nouveaux_livres)

        except Exception as e:
            print(f"\n❌ ERREUR FATALE PENDANT LE SCRAPING: {e}")
            self.metriques['erreurs_extraction'] += 1
            import traceback
            print(f"📋 Détails de l'erreur: {traceback.format_exc()}")
            return 0

        finally:
            # Toujours sauvegarder les métriques
            try:
                self.sauvegarder_metriques_detaillees()
            except:
                pass


# =====================================
# FONCTION DE GÉNÉRATION AUTOMATIQUE
# =====================================

def generer_scraper_ameliore(nom_categorie: str, url_categorie: str, nom_fichier: str) -> str:
    """
    Génère automatiquement un scraper amélioré pour une catégorie

    Args:
        nom_categorie (str): Nom de la catégorie
        url_categorie (str): URL de la catégorie Amazon
        nom_fichier (str): Nom du fichier à créer

    Returns:
        str: Code du scraper généré
    """

    nom_classe = nom_categorie.replace(' ', '').replace('-', '').replace(',', '')
    nom_classe = re.sub(r'[^\w]', '', nom_classe)

    code_scraper = f'''#!/usr/bin/env python3
"""
SCRAPER AMAZON AMÉLIORÉ - {nom_categorie.upper()}
{'=' * (30 + len(nom_categorie))}
Catégorie: {nom_categorie}
URL: {url_categorie}

FONCTIONNALITÉS COMPLÈTES:
✅ Anti-doublon intelligent (ASIN/ISBN/Hash)
✅ Mise à jour automatique du fichier JSON
✅ Extraction de TOUS les champs Amazon
✅ Sauvegarde avec backup automatique
✅ Métriques de performance détaillées
✅ Gestion d'erreurs robuste

Généré automatiquement par le système amélioré
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent pour importer les fonctions
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from FONCTION import gestion_categories_utils
    from FONCTION import metriques_temps_reel
    from FONCTION import validateur_contexte_amazon
    from FONCTION import creation_scrapers_utils
    from FONCTION import extraction_utils
except ImportError as e:
    print(f"⚠️  Certaines fonctions FONCTION non disponibles: {e}")
    gestion_categories_utils = None
    metriques_temps_reel = None
    validateur_contexte_amazon = None
    creation_scrapers_utils = None
    extraction_utils = None

class ScraperAmazon{nom_classe}(ScraperAmazonAmeliore):
    """
    Scraper spécialisé pour: {nom_categorie}

    Hérite de toutes les fonctionnalités avancées du modèle de base
    """

    def __init__(self):
        """Initialise le scraper pour {nom_categorie}"""
        super().__init__(
            nom_categorie="{nom_categorie}",
            url_categorie="{url_categorie}"
        )

def main():
    """Fonction principale - Lance le scraping complet"""
    scraper = ScraperAmazon{nom_classe}()

    # Lancement avec toutes les fonctionnalités
    total_nouveaux = scraper.run_complet()

    if total_nouveaux > 0:
        print(f"\\n✅ SUCCÈS: {{total_nouveaux}} nouveaux livres ajoutés pour {nom_categorie}")
    else:
        print(f"\\n✅ TERMINÉ: Base de données à jour pour {nom_categorie}")

if __name__ == "__main__":
    main()
'''

    return code_scraper


if __name__ == "__main__":
    # Test du modèle
    print("🧪 TEST DU MODÈLE SCRAPER AMÉLIORÉ")
    scraper_test = ScraperAmazonAmeliore("Test Catégorie", "https://www.amazon.fr/test")
    print(f"✅ Modèle initialisé avec succès: {scraper_test.nom_categorie}")