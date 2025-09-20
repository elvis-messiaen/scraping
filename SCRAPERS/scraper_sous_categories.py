#!/usr/bin/env python3
"""
SCRAPER SOUS-CATÉGORIES AMAZON
==============================
Objectif: Détecter les sous-catégories des catégories principales existantes
Méthode: Lecture des catégories principales depuis le JSON et détection des sous-catégories
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
from typing import Dict, List, Set, Optional, Any
from urllib.parse import urljoin

# Ajouter le dossier FONCTION au path pour importer les utilitaires
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'FONCTION'))

from gestion_categories_utils import (
    verifier_categorie_existante,
    ajouter_categorie_si_absente,
    ajouter_categories_batch
)
from validateur_contexte_amazon import ValidateurContexteAmazon
from creation_scrapers_utils import (
    traiter_creation_automatique_complete,
    lister_creations_existantes
)
from metriques_temps_reel import MetriquesTempsReel, AffichageTerminal

class ScraperSousCategories:
    def __init__(self):
        """
        Scraper spécialisé pour détecter les sous-catégories
        à partir des catégories principales existantes
        """
        self.setup_chemins()
        self.categories_principales = []
        self.sous_categories_detectees = {}
        self.processed_urls = set()
        self.debut_scraping = None

        # ANTI-DOUBLONS : Set global pour éviter les doublons
        self.sous_categories_globales = set()
        self.categories_deja_trouvees = set()

        # Configuration
        self.url_base_amazon = "https://www.amazon.fr"
        self.request_delay = 1.0
        self.timeout_request = 15
        self.retry_limit = 3
        self.max_depth = 3  # Profondeur maximale de récursion

        # Headers rotatifs
        self.headers_pool = [
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
        ]

        # Validateur contextuel intelligent
        self.validateur = ValidateurContexteAmazon()

        # Métriques temps réel
        self.metriques = MetriquesTempsReel()

        # Chemins pour création automatique
        base_dir = "/Users/Simplon/Cours/workspacePython/Scraping"
        self.dossier_livres = os.path.join(base_dir, "LIVRES")
        self.dossier_scrapers = os.path.join(base_dir, "SCRAPERS")

        # S'assurer que les dossiers existent
        os.makedirs(self.dossier_livres, exist_ok=True)
        os.makedirs(self.dossier_scrapers, exist_ok=True)

        print("🎯 SCRAPER SOUS-CATÉGORIES AMAZON")
        print("📖 Lecture des catégories principales depuis JSON")
        print("🔧 Création automatique: LIVRES + SCRAPERS activée")
        print("📊 Métriques temps réel: ACTIVÉES")

    def setup_chemins(self):
        """Configuration des chemins de fichiers"""
        base_dir = "/Users/Simplon/Cours/workspacePython/Scraping"
        self.dossier_categories = os.path.join(base_dir, "CATEGORIES")

        # Fichiers de catégories
        self.fichier_categories_principales = os.path.join(
            self.dossier_categories, "scraper_category_principal.json"
        )
        self.fichier_categories_completes = os.path.join(
            self.dossier_categories, "categories_amazon_completes.json"
        )

        print(f"📁 Dossier: {self.dossier_categories}")
        print(f"📄 Catégories principales: {self.fichier_categories_principales}")
        print(f"📄 Catégories complètes: {self.fichier_categories_completes}")

    def charger_categories_principales(self) -> List[str]:
        """
        Charger les catégories principales depuis le fichier JSON

        Returns:
            List[str]: Liste des noms de catégories principales
        """
        print("📖 CHARGEMENT DES CATÉGORIES PRINCIPALES")

        try:
            if not os.path.exists(self.fichier_categories_principales):
                print(f"❌ Fichier {self.fichier_categories_principales} introuvable")
                return []

            with open(self.fichier_categories_principales, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extraire les catégories
            if isinstance(data, dict) and 'categories' in data:
                categories = data['categories']
            elif isinstance(data, list):
                categories = data
            else:
                print(f"❌ Structure JSON invalide")
                return []

            print(f"✅ {len(categories)} catégories principales chargées")

            # Afficher les premières catégories
            print(f"📋 Catégories chargées:")
            for i, cat in enumerate(categories[:10], 1):
                print(f"   {i}. {cat}")
            if len(categories) > 10:
                print(f"   ... et {len(categories)-10} autres")

            self.categories_principales = categories
            return categories

        except Exception as e:
            print(f"❌ Erreur chargement catégories principales: {e}")
            return []

    def faire_requete(self, url: str, retries: int = 0) -> Optional[BeautifulSoup]:
        """Faire une requête avec gestion d'erreurs"""
        if retries >= self.retry_limit:
            return None

        try:
            headers = random.choice(self.headers_pool)
            # Ne plus afficher l'URL ici, c'est géré par les métriques

            response = requests.get(url, headers=headers, timeout=self.timeout_request)

            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            elif response.status_code == 503:
                print(f"⚠️ 503 Service Unavailable - retry {retries+1}")
                time.sleep(random.uniform(2, 5))
                return self.faire_requete(url, retries + 1)
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Erreur requête: {e}")
            if retries < self.retry_limit:
                time.sleep(random.uniform(1, 3))
                return self.faire_requete(url, retries + 1)
            return None

    def construire_url_categorie(self, nom_categorie: str) -> Optional[str]:
        """
        Construire l'URL de recherche pour une catégorie en utilisant le JSON principal

        Args:
            nom_categorie (str): Nom de la catégorie

        Returns:
            Optional[str]: URL de recherche ou None si impossible à construire
        """
        # Charger l'URL depuis le JSON des catégories principales
        try:
            with open(self.fichier_categories_principales, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Chercher l'URL associée à cette catégorie
            if isinstance(data, dict) and 'categories' in data:
                categories_data = data['categories']

                # Si c'est un dictionnaire avec URLs
                if isinstance(categories_data, dict):
                    for cat_name, cat_url in categories_data.items():
                        if cat_name == nom_categorie:
                            print(f"🔗 URL trouvée dans JSON: {cat_url}")
                            return cat_url

                # Si c'est une liste, chercher dans les métadonnées
                elif isinstance(categories_data, list):
                    # Vérifier s'il y a des métadonnées avec URLs
                    if 'metadata' in data and 'urls' in data['metadata']:
                        urls_data = data['metadata']['urls']
                        if nom_categorie in urls_data:
                            print(f"🔗 URL trouvée dans métadonnées: {urls_data[nom_categorie]}")
                            return urls_data[nom_categorie]

        except Exception as e:
            print(f"⚠️ Erreur lecture JSON pour URL: {e}")

        # Fallback: construire URL de recherche spécialisée
        print(f"🔍 Construction URL de recherche pour: {nom_categorie}")
        return f"https://www.amazon.fr/s?k={nom_categorie.replace(' ', '+')}&i=stripbooks&rh=n%3A301061"

    def detecter_sous_categories(self, nom_categorie: str, url_categorie: str = None,
                               profondeur: int = 0) -> List[str]:
        """
        Détecter les sous-catégories d'une catégorie donnée

        Args:
            nom_categorie (str): Nom de la catégorie parent
            url_categorie (str): URL de la catégorie (optionnel)
            profondeur (int): Profondeur actuelle de récursion

        Returns:
            List[str]: Liste des noms des sous-catégories détectées
        """
        if profondeur >= self.max_depth:
            print(f"⚠️ Profondeur maximale atteinte pour {nom_categorie}")
            return []

        print(f"🔍 Détection sous-catégories [{profondeur}]: {nom_categorie}")

        # Construire URL si pas fournie
        if not url_categorie:
            url_categorie = self.construire_url_categorie(nom_categorie)

        if not url_categorie:
            print(f"❌ Impossible de construire URL pour {nom_categorie}")
            return []

        # Faire la requête
        soup = self.faire_requete(url_categorie)
        if not soup:
            print(f"❌ Impossible de charger la page pour {nom_categorie}")
            return []

        sous_categories = []

        # Sélecteurs pour les sous-catégories
        selectors_sous_cat = [
            # Navigation latérale (refinements)
            '.s-refinements a[href*="node="]',
            '.s-refinements a[href*="rh="]',

            # Navigation indentée
            '.s-navigation-indent-2 a',
            '.s-navigation-indent-3 a',

            # Filtres de catégories
            '.a-section.a-spacing-none a[href*="node="]',
            '.a-section.a-spacing-none a[href*="rh="]',

            # Liens vers browse nodes
            'a[href*="/b/?ie=UTF8&node="]',
            'a[href*="stripbooks&rh=n%3A"]',

            # Sections de navigation générale
            '.a-unordered-list a[href*="node="]',
        ]

        for selector in selectors_sous_cat:
            try:
                links = soup.select(selector)

                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    if not text or len(text) < 2:
                        continue

                    # URL complète
                    if href.startswith('/'):
                        full_url = self.url_base_amazon + href
                    else:
                        full_url = href

                    # Validation de la sous-catégorie avec le validateur contextuel
                    est_valide, raison = self.validateur.est_categorie_livre_valide(text, full_url, soup)
                    if est_valide:
                        # ANTI-DOUBLONS : Vérifier si pas déjà trouvée globalement
                        if text not in self.sous_categories_globales and text not in sous_categories:
                            sous_categories.append(text)
                            self.sous_categories_globales.add(text)  # Ajouter au set global
                            print(f"✅ NOUVELLE: {text} 🔗 {full_url}")
                            # Mettre à jour les métriques pour chaque sous-catégorie trouvée
                            self.metriques.update_item(f"{nom_categorie} -> {text}", full_url, True)
                        elif text in self.sous_categories_globales:
                            print(f"🔄 DOUBLON IGNORÉ: {text}")
                    else:
                        print(f"❌ REJETÉ: {text} (Raison: {raison}) 🔗 {full_url}")

            except Exception as e:
                # Mettre à jour les métriques pour les erreurs
                self.metriques.update_item(f"Erreur {selector}", url_categorie or "", False)
                self.metriques.afficher_erreur(f"Sélecteur '{selector}': {e}", url_categorie or "")

        # Pause pour éviter le rate limiting
        time.sleep(self.request_delay)

        print(f"📊 {nom_categorie}: {len(sous_categories)} sous-catégories détectées")
        return sous_categories


    def verifier_categorie_existe_deja(self, nom_categorie: str, lien_amazon: str = "") -> bool:
        """
        Vérifier si une catégorie existe déjà dans les fichiers JSON

        Args:
            nom_categorie (str): Nom de la catégorie à vérifier
            lien_amazon (str): Lien Amazon associé (optionnel)

        Returns:
            bool: True si existe déjà, False sinon
        """
        # Vérifier dans catégories principales
        if verifier_categorie_existante(self.fichier_categories_principales, nom_categorie, lien_amazon):
            print(f"🔄 '{nom_categorie}' existe dans catégories principales")
            return True

        # Vérifier dans catégories complètes
        if verifier_categorie_existante(self.fichier_categories_completes, nom_categorie, lien_amazon):
            print(f"🔄 '{nom_categorie}' existe dans catégories complètes")
            return True

        return False

    def ajouter_sous_categories(self, sous_categories: List[str]) -> Dict[str, Any]:
        """
        Ajouter les sous-catégories au fichier de catégories complètes
        seulement si elles n'existent pas déjà

        Args:
            sous_categories (List[str]): Liste des noms des sous-catégories

        Returns:
            Dict[str, Any]: Statistiques de l'ajout
        """
        print(f"➕ AJOUT SOUS-CATÉGORIES: {len(sous_categories)} à traiter")

        # Filtrer pour ne garder que les nouvelles
        nouvelles_sous_categories = []

        for nom_sous_cat in sous_categories:
            if not self.verifier_categorie_existe_deja(nom_sous_cat):
                nouvelles_sous_categories.append(nom_sous_cat)
                print(f"✅ Nouvelle: {nom_sous_cat}")
            else:
                print(f"🔄 Existe déjà: {nom_sous_cat}")

        # Ajouter en batch les nouvelles sous-catégories
        if nouvelles_sous_categories:
            stats = ajouter_categories_batch(
                self.fichier_categories_completes,
                nouvelles_sous_categories,
                {
                    'derniere_mise_a_jour_sous_categories': datetime.now().isoformat(),
                    'description': 'Catégories et sous-catégories Amazon complètes'
                }
            )
            print(f"✅ {stats['categories_ajoutees']} nouvelles sous-catégories ajoutées")
            return stats
        else:
            print("🔄 Aucune nouvelle sous-catégorie à ajouter")
            return {
                'categories_ajoutees': 0,
                'categories_existantes': len(sous_categories),
                'categories_traitees': len(sous_categories)
            }

    def traiter_categorie_principale(self, nom_categorie: str) -> Dict[str, Any]:
        """
        Traiter une catégorie principale pour détecter ses sous-catégories

        Args:
            nom_categorie (str): Nom de la catégorie principale

        Returns:
            Dict[str, Any]: Résultats du traitement
        """
        # Mettre à jour les métriques pour la nouvelle catégorie
        self.metriques.update_categorie(nom_categorie)

        try:
            # Construire l'URL pour les métriques
            url_categorie = self.construire_url_categorie(nom_categorie)

            # Détecter les sous-catégories
            sous_categories = self.detecter_sous_categories(nom_categorie)

            if not sous_categories:
                self.metriques.update_item(f"{nom_categorie} (aucune sous-cat)", url_categorie or "", True)
                return {
                    'categorie_principale': nom_categorie,
                    'sous_categories_detectees': 0,
                    'nouvelles_ajoutees': 0
                }

            # Ajouter les sous-catégories nouvelles
            stats_ajout = self.ajouter_sous_categories(sous_categories)

            # Stocker pour statistiques
            self.sous_categories_detectees[nom_categorie] = sous_categories

            return {
                'categorie_principale': nom_categorie,
                'sous_categories_detectees': len(sous_categories),
                'nouvelles_ajoutees': stats_ajout['categories_ajoutees'],
                'existantes_ignorees': stats_ajout['categories_existantes']
            }

        except Exception as e:
            url_categorie = self.construire_url_categorie(nom_categorie)
            self.metriques.afficher_erreur(f"Traitement {nom_categorie}: {e}", url_categorie or "")
            return {
                'categorie_principale': nom_categorie,
                'sous_categories_detectees': 0,
                'nouvelles_ajoutees': 0,
                'erreur': str(e)
            }

    def run(self):
        """Exécution principale du scraper de sous-catégories"""
        AffichageTerminal.ligne_separatrice()
        print("🚀 DÉMARRAGE SCRAPER SOUS-CATÉGORIES AVEC MÉTRIQUES TEMPS RÉEL")
        AffichageTerminal.ligne_separatrice()

        self.debut_scraping = datetime.now()

        try:
            # Étape 1: Charger les catégories principales
            AffichageTerminal.titre_section("ÉTAPE 1: CHARGEMENT CATÉGORIES PRINCIPALES")
            categories_principales = self.charger_categories_principales()

            if not categories_principales:
                print("❌ Aucune catégorie principale trouvée")
                return {}

            # Charger le nombre EXACT de catégories existantes pour métriques précises
            try:
                with open(self.fichier_categories_completes, 'r', encoding='utf-8') as f:
                    data_existantes = json.load(f)
                    nb_categories_exactes = len(data_existantes.get('categories', []))
                    print(f"📊 Catégories existantes dans JSON: {nb_categories_exactes}")
            except:
                nb_categories_exactes = 0
                print(f"📊 Aucune catégorie existante trouvée")

            # Utiliser le nombre EXACT comme base pour les métriques
            self.metriques.demarrer(total_estime=nb_categories_exactes)

            # Étape 2: Traiter chaque catégorie principale
            AffichageTerminal.titre_section(f"ÉTAPE 2: DÉTECTION SOUS-CATÉGORIES ({len(categories_principales)} catégories)")

            resultats = {}
            total_sous_categories = 0
            total_nouvelles = 0

            for i, nom_categorie in enumerate(categories_principales, 1):
                resultat = self.traiter_categorie_principale(nom_categorie)
                resultats[nom_categorie] = resultat

                total_sous_categories += resultat.get('sous_categories_detectees', 0)
                total_nouvelles += resultat.get('nouvelles_ajoutees', 0)

                # Mettre à jour l'estimation si nécessaire
                if total_sous_categories > self.metriques.total_estime:
                    nouvelle_estimation = int(total_sous_categories * len(categories_principales) / i)
                    self.metriques.mettre_a_jour_total_estime(nouvelle_estimation)

                # Pause entre catégories
                time.sleep(self.request_delay)

            # Étape 3: Affichage du bilan final avec métriques
            self.metriques.afficher_bilan_final()

            print(f"\n📋 RÉSULTATS DÉTAILLÉS:")
            print(f"📁 Catégories principales traitées: {len(categories_principales)}")
            print(f"🔍 Sous-catégories détectées: {total_sous_categories}")
            print(f"✅ Nouvelles sous-catégories ajoutées: {total_nouvelles}")
            print(f"💾 Fichier mis à jour: {self.fichier_categories_completes}")

            # Étape 4: Création automatique des scrapers et fichiers LIVRES
            if total_nouvelles > 0:
                print(f"\n🔧 CRÉATION AUTOMATIQUE SCRAPERS + LIVRES")
                print("=" * 50)
                try:
                    stats_creation = traiter_creation_automatique_complete(
                        self.fichier_categories_principales,
                        self.dossier_scrapers,
                        self.dossier_livres
                    )
                    print(f"✅ Scrapers créés: {stats_creation.get('scrapers_crees', 0)}")
                    print(f"✅ Fichiers LIVRES créés: {stats_creation.get('livres_crees', 0)}")
                    print(f"❌ Erreurs rencontrées: {stats_creation.get('erreurs', 0)}")
                    print(f"📊 Catégories traitées: {stats_creation.get('categories_traitees', 0)}")
                except Exception as e:
                    print(f"❌ Erreur création automatique: {e}")

            return resultats

        except KeyboardInterrupt:
            print("\n⚠️ Arrêt demandé par l'utilisateur")
            self.metriques.afficher_bilan_final()
        except Exception as e:
            self.metriques.afficher_erreur(f"Erreur générale: {e}")
            import traceback
            traceback.print_exc()

        return {}

if __name__ == "__main__":
    scraper = ScraperSousCategories()
    resultats = scraper.run()

    if resultats:
        print(f"\n✅ SUCCÈS: Sous-catégories traitées pour {len(resultats)} catégories principales")
    else:
        print(f"\n❌ ÉCHEC: Problème lors du traitement des sous-catégories")