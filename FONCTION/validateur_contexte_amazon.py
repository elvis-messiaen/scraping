#!/usr/bin/env python3
"""
VALIDATEUR CONTEXTUEL AMAZON - APPROCHE 2025
============================================
Validateur intelligent basé sur l'arborescence et le contexte,
pas sur des mots-clés simples qui peuvent être ambigus.

Principe : Le contexte détermine la validité, pas le mot lui-même
Exemple : "informatique" peut être livre technique OU produit électronique
"""

import re
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


class ValidateurContexteAmazon:
    """
    Validateur contextuel intelligent pour catégories Amazon
    Utilise l'arborescence et le contexte plutôt que des mots-clés simples
    """

    def __init__(self):
        """
        Initialisation du validateur avec les browse nodes et patterns contextuels
        """
        # Browse node principal des livres
        self.BROWSE_NODE_LIVRES = 301061

        # Indicateurs URL positifs (contexte livre)
        self.indicateurs_url_livres = [
            'stripbooks',              # Section livres Amazon
            'node=301',               # Browse node livres
            '/b/?ie=UTF8&node=301',   # URL browse livres direct
            'rh=n%3A301',             # Refinement livres
            'i=stripbooks'            # Index stripbooks
        ]

        # Indicateurs URL négatifs (contexte non-livre)
        self.indicateurs_url_non_livres = [
            'electronics',     # Section électronique
            'computers',       # Section informatique produits
            'software',        # Section logiciels
            'videogames',      # Section jeux vidéo
            'automotive',      # Section auto
            'tools',           # Section outils
            'appliances'       # Section électroménager
        ]

        # Patterns de filtres Amazon à exclure
        self.patterns_filtres_amazon = [
            # Navigation générale
            r'voir\s+plus', r'tout\s+afficher', r'recherche',
            r'aide', r'compte', r'panier', r'commander', r'livraison',
            r'prime', r'service', r'support', r'client',

            # Filtres temporels
            r'depuis\s+\d+\s+(jour|mois|année)s?',
            r'dernière?\s+(semaine|mois|année)',
            r'récent', r'nouveau.*parution',

            # Prix et promotions
            r'jusqu\'à\s+\d+\s*eur', r'de\s+\d+\s+à\s+\d+\s*eur',
            r'promotion', r'solde', r'rabais', r'réduction', r'offre',

            # Notes et évaluations
            r'\d+\s+étoiles?', r'\d+\s+stars?',

            # Formats physiques spécifiques
            r'broché', r'relié', r'poche', r'kindle', r'audible'
        ]

        # Catégories principales valides (contexte confirmé)
        self.categories_principales_valides = {
            'livres', 'romans et polars', 'science-fiction et fantasy',
            'bd et mangas', 'enfants et ados', 'scolaire et études',
            'sciences, techniques et médecine', 'arts et photographie',
            'politique', 'religions et spiritualités', 'musique',
            'nouveautés', 'le livre autrement', 'actualité, politique et société',
            'calendriers et agendas', 'référence', 'études supérieures',
            'humour', 'informatique et internet', 'loisirs créatifs, décoration et maison',
            'santé, forme et diététique', 'sports et loisirs', 'tourisme et voyages'
        }

    def extraire_browse_node(self, url: str) -> Optional[int]:
        """
        Extraire le browse node depuis l'URL

        Args:
            url (str): URL Amazon

        Returns:
            Optional[int]: Browse node ID ou None si non trouvé
        """
        try:
            # Pattern node= direct
            match = re.search(r'node=(\d+)', url)
            if match:
                return int(match.group(1))

            # Pattern rh=n%3A (URL encoded)
            match = re.search(r'rh=n%3A(\d+)', url)
            if match:
                return int(match.group(1))

            return None

        except Exception:
            return None

    def valider_url_structure(self, url: str) -> Tuple[bool, str]:
        """
        Valider la structure URL pour confirmer le contexte livre

        Args:
            url (str): URL à valider

        Returns:
            Tuple[bool, str]: (est_valide, raison)
        """
        if not url:
            return False, "URL vide"

        url_lower = url.lower()

        # Vérifier indicateurs positifs
        est_livre = any(indicateur in url_lower for indicateur in self.indicateurs_url_livres)

        # Vérifier indicateurs négatifs
        est_non_livre = any(indicateur in url_lower for indicateur in self.indicateurs_url_non_livres)

        if est_non_livre:
            return False, "URL contexte non-livre détecté"

        if est_livre:
            return True, "URL contexte livre confirmé"

        # Cas ambigus - analyser browse node
        browse_node = self.extraire_browse_node(url)
        if browse_node:
            if str(browse_node).startswith('301'):  # Branche livres
                return True, f"Browse node livre détecté: {browse_node}"
            else:
                return False, f"Browse node non-livre: {browse_node}"

        return False, "Contexte URL indéterminé"

    def extraire_breadcrumb(self, soup: BeautifulSoup) -> List[str]:
        """
        Extraire le fil d'Ariane (breadcrumb) de la page

        Args:
            soup (BeautifulSoup): Soup de la page

        Returns:
            List[str]: Liste des éléments du breadcrumb
        """
        try:
            # Sélecteurs pour breadcrumb Amazon
            selectors_breadcrumb = [
                '.a-breadcrumb a',
                '#wayfinding-breadcrumbs_feature_div a',
                '.a-unordered-list.a-horizontal.a-size-base a'
            ]

            for selector in selectors_breadcrumb:
                links = soup.select(selector)
                if links:
                    return [link.get_text(strip=True) for link in links]

            return []

        except Exception:
            return []

    def valider_chemin_hierarchique(self, breadcrumb: List[str]) -> Tuple[bool, str]:
        """
        Valider le chemin hiérarchique via breadcrumb

        Args:
            breadcrumb (List[str]): Éléments du breadcrumb

        Returns:
            Tuple[bool, str]: (est_valide, raison)
        """
        if not breadcrumb:
            return False, "Breadcrumb vide"

        breadcrumb_lower = [item.lower() for item in breadcrumb]

        # Vérifier présence de "Livres" ou équivalents
        indicateurs_livres = ['livres', 'books', 'livre']

        if any(indicateur in breadcrumb_lower for indicateur in indicateurs_livres):
            return True, f"Chemin livre confirmé: {' > '.join(breadcrumb)}"

        # Vérifier catégories principales connues
        for item in breadcrumb_lower:
            if item in self.categories_principales_valides:
                return True, f"Catégorie principale valide: {item}"

        return False, f"Chemin hiérarchique non-livre: {' > '.join(breadcrumb)}"

    def analyser_contexte_page(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Analyser le contexte général de la page

        Args:
            soup (BeautifulSoup): Soup de la page

        Returns:
            Dict[str, Any]: Analyse contextuelle
        """
        contexte = {
            'title': '',
            'breadcrumb': [],
            'navigation_elements': [],
            'page_type': 'unknown'
        }

        try:
            # Title de la page
            title_tag = soup.find('title')
            if title_tag:
                contexte['title'] = title_tag.get_text(strip=True).lower()

            # Breadcrumb
            contexte['breadcrumb'] = self.extraire_breadcrumb(soup)

            # Navigation elements
            nav_elements = soup.select('.s-refinements a, .a-section a')
            contexte['navigation_elements'] = [
                elem.get_text(strip=True) for elem in nav_elements[:10]
            ]

            # Type de page
            if 'livre' in contexte['title'] or 'book' in contexte['title']:
                contexte['page_type'] = 'livre'
            elif any('livre' in item.lower() for item in contexte['breadcrumb']):
                contexte['page_type'] = 'livre'
            else:
                contexte['page_type'] = 'autre'

        except Exception:
            pass

        return contexte

    def est_filtre_amazon_generique(self, text: str) -> bool:
        """
        Vérifier si c'est un filtre générique Amazon à exclure

        Args:
            text (str): Texte à vérifier

        Returns:
            bool: True si c'est un filtre à exclure
        """
        text_lower = text.lower().strip()

        # Vérifier patterns
        for pattern in self.patterns_filtres_amazon:
            if re.search(pattern, text_lower):
                return True

        return False

    def est_categorie_livre_valide(self, text: str, url: str, soup: BeautifulSoup = None) -> Tuple[bool, str]:
        """
        Validation contextuelle complète d'une catégorie

        Args:
            text (str): Nom de la catégorie
            url (str): URL de la catégorie
            soup (BeautifulSoup, optional): Soup de la page pour analyse contextuelle

        Returns:
            Tuple[bool, str]: (est_valide, raison_détaillée)
        """
        if not text or not text.strip():
            return False, "Texte vide"

        text_lower = text.lower().strip()

        # 1. Validation basique du nom
        if len(text_lower) < 2 or len(text_lower) > 200:
            return False, f"Longueur incorrecte: {len(text_lower)}"

        if text.isdigit() or text.startswith('http'):
            return False, "Format invalide"

        # 2. Exclure les filtres Amazon génériques
        if self.est_filtre_amazon_generique(text):
            return False, "Filtre Amazon générique détecté"

        # 3. Validation URL structure
        url_valide, raison_url = self.valider_url_structure(url)
        if not url_valide:
            return False, f"URL invalide: {raison_url}"

        # 4. Validation contextuelle avec soup si disponible
        if soup:
            contexte = self.analyser_contexte_page(soup)

            # Vérifier breadcrumb
            if contexte['breadcrumb']:
                breadcrumb_valide, raison_breadcrumb = self.valider_chemin_hierarchique(
                    contexte['breadcrumb']
                )
                if not breadcrumb_valide:
                    return False, f"Breadcrumb invalide: {raison_breadcrumb}"

            # Vérifier type de page
            if contexte['page_type'] != 'livre' and contexte['page_type'] != 'unknown':
                return False, f"Type de page non-livre: {contexte['page_type']}"

        # 5. Validation positive - catégories explicitement valides
        if text_lower in self.categories_principales_valides:
            return True, f"Catégorie principale valide: {text}"

        # 6. Validation par browse node
        browse_node = self.extraire_browse_node(url)
        if browse_node and str(browse_node).startswith('301'):
            return True, f"Browse node livre confirmé: {browse_node}"

        # 7. Validation par patterns thématiques (moins restrictifs)
        patterns_thematiques = [
            # Genres littéraires
            r'roman', r'fiction', r'littérature', r'poésie', r'théâtre',
            r'polar', r'thriller', r'mystère', r'suspense', r'fantasy',
            r'science-fiction', r'fantastique', r'historique', r'biographie',

            # Domaines de connaissance (SANS exclusion)
            r'science', r'histoire', r'politique', r'économie', r'philosophie',
            r'religion', r'spiritualité', r'psychologie', r'sociologie',
            r'médecine', r'santé', r'technique', r'informatique',  # ✅ Gardé !

            # Publics cibles
            r'enfant', r'ado', r'jeunesse', r'adulte', r'scolaire',
            r'étude', r'formation', r'référence',

            # Arts et loisirs
            r'art', r'photographie', r'musique', r'cuisine', r'voyage',
            r'sport', r'loisir', r'culture', r'humour',  # ✅ Gardé !

            # Formats éditoriaux
            r'bd', r'bande.*dessinée', r'manga', r'comic', r'album'
        ]

        est_thematique = any(re.search(pattern, text_lower) for pattern in patterns_thematiques)

        if est_thematique:
            return True, f"Catégorie thématique valide: {text}"

        # 8. Validation finale - si arrive ici, probablement valide dans contexte livre
        return True, f"Catégorie contextuelle valide: {text}"

    def filtrer_categories_batch(self, categories_data: List[Dict]) -> Dict[str, Any]:
        """
        Filtrer un batch de catégories avec validation contextuelle

        Args:
            categories_data (List[Dict]): Liste de dictionnaires avec keys: nom, url, soup (optionnel)

        Returns:
            Dict[str, Any]: Résultats du filtrage avec statistiques
        """
        resultats = {
            'categories_valides': [],
            'categories_rejetees': [],
            'total_traitees': len(categories_data),
            'statistiques': {}
        }

        for item in categories_data:
            nom = item.get('nom', '')
            url = item.get('url', '')
            soup = item.get('soup', None)

            est_valide, raison = self.est_categorie_livre_valide(nom, url, soup)

            if est_valide:
                resultats['categories_valides'].append({
                    'nom': nom,
                    'url': url,
                    'raison_validation': raison
                })
            else:
                resultats['categories_rejetees'].append({
                    'nom': nom,
                    'url': url,
                    'raison_rejet': raison
                })

        # Statistiques
        resultats['statistiques'] = {
            'total': len(categories_data),
            'valides': len(resultats['categories_valides']),
            'rejetees': len(resultats['categories_rejetees']),
            'taux_validation': len(resultats['categories_valides']) / len(categories_data) * 100 if categories_data else 0
        }

        return resultats


def tester_validateur():
    """
    Tests du validateur contextuel
    """
    validateur = ValidateurContexteAmazon()

    # Tests cas d'usage
    tests = [
        {
            'nom': 'Informatique',
            'url': 'https://www.amazon.fr/s?i=stripbooks&k=informatique&node=301061',
            'attendu': True,
            'description': 'Livre informatique - doit être VALIDE'
        },
        {
            'nom': 'Informatique',
            'url': 'https://www.amazon.fr/s?i=computers&k=informatique',
            'attendu': False,
            'description': 'Produit informatique - doit être INVALIDE'
        },
        {
            'nom': 'Sports',
            'url': 'https://www.amazon.fr/s?i=stripbooks&rh=n%3A301061&k=sports',
            'attendu': True,
            'description': 'Livre sports - doit être VALIDE'
        },
        {
            'nom': 'voir plus',
            'url': 'https://www.amazon.fr/s?i=stripbooks',
            'attendu': False,
            'description': 'Filtre navigation - doit être INVALIDE'
        }
    ]

    print("🧪 TESTS VALIDATEUR CONTEXTUEL")
    print("=" * 50)

    for i, test in enumerate(tests, 1):
        resultat, raison = validateur.est_categorie_livre_valide(
            test['nom'], test['url']
        )

        status = "✅ PASS" if resultat == test['attendu'] else "❌ FAIL"
        print(f"{status} Test {i}: {test['description']}")
        print(f"   Catégorie: {test['nom']}")
        print(f"   Résultat: {resultat} - {raison}")
        print()


if __name__ == "__main__":
    tester_validateur()