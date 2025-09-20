#!/usr/bin/env python3
"""
VALIDATION IA GRATUITE - NODE ID DETECTION
==========================================
Système d'IA gratuit pour améliorer la détection des Node IDs livres
basé sur l'analyse des patterns d'URLs sans utiliser les noms.

Utilise des techniques d'apprentissage simple pour découvrir
automatiquement de nouveaux Node IDs livres.
"""

import re
import json
import requests
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter
import logging
from pathlib import Path
from datetime import datetime

class AnalyseurNodeIA:
    """
    Analyseur IA gratuit pour découvrir automatiquement
    les patterns de Node IDs livres basé sur les URLs.
    """

    def __init__(self, cache_file: str = None):
        """
        Initialiser l'analyseur IA

        Args:
            cache_file (str): Fichier de cache pour les découvertes
        """
        self.cache_file = cache_file or "/Users/Simplon/Cours/workspacePython/Scraping/CATEGORIES/ia_nodes_cache.json"

        # Base de connaissances des nodes confirmés
        self.nodes_livres_confirmes = {
            # Nodes 301xxx français
            '301061', '301132', '301133', '301137', '301146', '301147',
            '301131', '301135', '301138', '301139', '301141', '301142',
            '301144', '301997', '301985', '301989', '301973', '301979',
            '301990', '301993', '302036', '302042', '302045', '302047',
            '302068', '302074', '302079', '302084', '302095', '302098',
            '302107', '302110', '302009', '302050', '302049', '302051',

            # Nodes internationaux confirmés
            '283155', '17', '4', '18', '53', '13996', '290060', '154606011',
            '466218', '695398031', '6680516031', '125273011', '52042011',
            '355635011', '12641896031', '4252330031', '4256914031',
            '451166031', '451167031', '1064926'
        }

        self.nodes_non_livres_confirmes = {
            '172282',      # Electronics
            '502394',      # Automotive
            '7141123011',  # Clothing
            '228013',      # Sports & Outdoors
            '11091801',    # Toys & Games
            '2972638011',  # Baby & Toddler Toys
            '166764011',   # Kitchen & Dining
            '3760901',     # Tools & Home Improvement
        }

        # Patterns découverts par l'IA
        self.patterns_decouverts = []
        self.nodes_inconnus = defaultdict(list)  # Node -> [URLs où trouvé]

        self.logger = logging.getLogger(__name__)
        self.charger_cache()

    def analyser_url_structure(self, url: str) -> Dict[str, any]:
        """
        Analyser la structure d'une URL pour extraire des patterns

        Args:
            url (str): URL à analyser

        Returns:
            Dict: Informations structurelles sur l'URL
        """
        url_lower = url.lower()

        # Extraire le node ID
        node_id = self.extraire_node_id(url)

        # Analyser la structure de l'URL
        structure = {
            'node_id': node_id,
            'has_stripbooks': 'stripbooks' in url_lower,
            'has_livre': '/livre' in url_lower or 'livre' in url_lower,
            'has_book': '/book' in url_lower,
            'has_kindle': 'kindle' in url_lower,
            'has_ref_sv_books': 'ref_=sv_books_' in url_lower,
            'has_ref_oct_odnav': 'ref_=oct_d_odnav_' in url_lower,
            'has_rh_param': 'rh=' in url_lower,
            'has_b_path': '/b/' in url_lower,
            'domain': self.extraire_domaine(url),
            'path_segments': len(url.split('/')),
            'query_params': len(url.split('&')) if '&' in url else 1,
        }

        return structure

    def extraire_node_id(self, url: str) -> Optional[str]:
        """Extraire node ID de l'URL"""
        patterns = [
            r'node[=/](\d+)',
            r'rh=n%3A(\d+)',
            r'&n=(\d+)',
            r'browse/(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def extraire_domaine(self, url: str) -> str:
        """Extraire le domaine de l'URL"""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else ''

    def predire_si_livre(self, url: str) -> Tuple[bool, float, str]:
        """
        Prédire si une URL correspond à une catégorie livre
        basé sur l'analyse IA des patterns d'URL

        Args:
            url (str): URL à analyser

        Returns:
            Tuple[bool, float, str]: (is_livre, confidence, raison)
        """
        structure = self.analyser_url_structure(url)
        node_id = structure['node_id']

        # Vérification dans la base confirmée
        if node_id:
            if node_id in self.nodes_livres_confirmes:
                return True, 1.0, f"Node confirmé livre: {node_id}"

            if node_id in self.nodes_non_livres_confirmes:
                return False, 1.0, f"Node confirmé non-livre: {node_id}"

        # Analyse par patterns IA
        score_livre = 0.0
        facteurs = []

        # Pattern 1: Nodes 301xxx français (très fiable)
        if node_id and node_id.startswith('301'):
            score_livre += 0.8
            facteurs.append("Node français 301xxx")

        # Pattern 2: Structure URL avec indicateurs livres
        if structure['has_stripbooks']:
            score_livre += 0.7
            facteurs.append("URL contient 'stripbooks'")

        if structure['has_livre'] or structure['has_book']:
            score_livre += 0.6
            facteurs.append("URL contient 'livre' ou 'book'")

        if structure['has_kindle']:
            score_livre += 0.6
            facteurs.append("URL contient 'kindle'")

        # Pattern 3: Références spécifiques livres
        if structure['has_ref_sv_books']:
            score_livre += 0.5
            facteurs.append("Référence sv_books")

        if structure['has_ref_oct_odnav']:
            score_livre += 0.4
            facteurs.append("Référence navigation Amazon")

        # Pattern 4: Structure générale Amazon livres
        if structure['has_b_path'] and structure['has_rh_param']:
            score_livre += 0.2
            facteurs.append("Structure Amazon browse avec filtres")

        # Pattern 5: Analyse du domaine
        if 'amazon.' in structure['domain']:
            score_livre += 0.1
            facteurs.append("Domaine Amazon")

        # Normaliser le score
        confidence = min(score_livre, 1.0)
        is_livre = confidence >= 0.6  # Seuil de décision

        raison = f"Score: {confidence:.2f} - " + ", ".join(facteurs)

        # Enregistrer pour apprentissage
        if node_id and node_id not in self.nodes_livres_confirmes and node_id not in self.nodes_non_livres_confirmes:
            self.nodes_inconnus[node_id].append(url)

        return is_livre, confidence, raison

    def apprendre_de_nouvelles_donnees(self, urls_livres: List[str], urls_non_livres: List[str] = None):
        """
        Apprendre de nouvelles données pour améliorer les prédictions

        Args:
            urls_livres (List[str]): URLs confirmées comme livres
            urls_non_livres (List[str]): URLs confirmées comme non-livres
        """
        if urls_non_livres is None:
            urls_non_livres = []

        # Analyser les URLs livres
        for url in urls_livres:
            structure = self.analyser_url_structure(url)
            node_id = structure['node_id']

            if node_id and node_id not in self.nodes_livres_confirmes:
                self.nodes_livres_confirmes.add(node_id)
                self.logger.info(f"IA: Nouveau node livre appris: {node_id}")

        # Analyser les URLs non-livres
        for url in urls_non_livres:
            structure = self.analyser_url_structure(url)
            node_id = structure['node_id']

            if node_id and node_id not in self.nodes_non_livres_confirmes:
                self.nodes_non_livres_confirmes.add(node_id)
                self.logger.info(f"IA: Nouveau node non-livre appris: {node_id}")

        self.sauvegarder_cache()

    def generer_rapport_decouverte(self) -> Dict[str, any]:
        """
        Générer un rapport des découvertes de l'IA

        Returns:
            Dict: Rapport complet des découvertes
        """
        # Analyser les nodes inconnus pour trouver des patterns
        patterns_frequents = Counter()

        for node_id, urls in self.nodes_inconnus.items():
            if len(urls) >= 2:  # Nodes trouvés dans plusieurs URLs
                for url in urls:
                    structure = self.analyser_url_structure(url)
                    # Compter les patterns pour ce node
                    if structure['has_stripbooks']:
                        patterns_frequents[f"{node_id}:stripbooks"] += 1
                    if structure['has_livre']:
                        patterns_frequents[f"{node_id}:livre"] += 1
                    if structure['has_ref_sv_books']:
                        patterns_frequents[f"{node_id}:sv_books"] += 1

        suggestions_nouveaux_nodes = []
        for pattern, count in patterns_frequents.most_common(10):
            node_id, pattern_type = pattern.split(':')
            suggestions_nouveaux_nodes.append({
                'node_id': node_id,
                'pattern': pattern_type,
                'occurrences': count,
                'confiance_ia': count / len(self.nodes_inconnus[node_id])
            })

        return {
            'timestamp': datetime.now().isoformat(),
            'nodes_livres_confirmes': len(self.nodes_livres_confirmes),
            'nodes_non_livres_confirmes': len(self.nodes_non_livres_confirmes),
            'nodes_inconnus_detectes': len(self.nodes_inconnus),
            'suggestions_nouveaux_nodes': suggestions_nouveaux_nodes,
            'patterns_les_plus_fiables': [
                'Nodes 301xxx français',
                'URL avec stripbooks',
                'URL avec /livre ou /book',
                'Références sv_books'
            ]
        }

    def sauvegarder_cache(self):
        """Sauvegarder les découvertes de l'IA"""
        try:
            Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)

            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'nodes_livres_confirmes': list(self.nodes_livres_confirmes),
                'nodes_non_livres_confirmes': list(self.nodes_non_livres_confirmes),
                'nodes_inconnus': dict(self.nodes_inconnus),
                'patterns_decouverts': self.patterns_decouverts
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Erreur sauvegarde cache IA: {e}")

    def charger_cache(self):
        """Charger les découvertes précédentes de l'IA"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                self.nodes_livres_confirmes.update(cache_data.get('nodes_livres_confirmes', []))
                self.nodes_non_livres_confirmes.update(cache_data.get('nodes_non_livres_confirmes', []))

                nodes_inconnus_data = cache_data.get('nodes_inconnus', {})
                for node_id, urls in nodes_inconnus_data.items():
                    self.nodes_inconnus[node_id].extend(urls)

                self.patterns_decouverts = cache_data.get('patterns_decouverts', [])

        except Exception as e:
            self.logger.error(f"Erreur chargement cache IA: {e}")

def creer_analyseur_ia() -> AnalyseurNodeIA:
    """Factory function pour créer l'analyseur IA"""
    return AnalyseurNodeIA()

# INTERFACE POUR REMPLACEMENT
def est_categorie_livre_valide_ia(url: str, text: str) -> bool:
    """
    Interface IA gratuite pour validation des catégories
    Basée uniquement sur l'analyse d'URL, pas sur le nom.

    Args:
        url (str): URL de la catégorie
        text (str): Nom (utilisé seulement pour les filtres évidents)

    Returns:
        bool: True si catégorie livre selon l'IA
    """
    analyseur = creer_analyseur_ia()

    # Filtres évidents dans le texte (prix, conditions, etc.)
    text_lower = text.lower()
    filtres_evidents = ['eur', '$', '€', 'prime eligible', 'stars', 'rating']

    for filtre in filtres_evidents:
        if filtre in text_lower:
            return False

    # Prédiction IA basée sur URL
    is_livre, confidence, raison = analyseur.predire_si_livre(url)

    # Log de la décision IA pour debugging
    logging.info(f"IA: {url} -> {is_livre} (conf: {confidence:.2f}) - {raison}")

    return is_livre

if __name__ == "__main__":
    # Tests de l'IA
    analyseur = creer_analyseur_ia()

    test_urls = [
        "https://www.amazon.fr/b/?node=301132",  # Romans et polars
        "https://www.amazon.fr/stripbooks/literature",  # Literature
        "https://www.amazon.fr/b?node=172282",  # Electronics
        "https://www.amazon.fr/b?node=999999",  # Node inconnu
    ]

    print("🤖 TESTS IA GRATUITE - ANALYSE NODE IDs")
    print("="*50)

    for url in test_urls:
        is_livre, conf, raison = analyseur.predire_si_livre(url)
        print(f"{'✅ LIVRE' if is_livre else '❌ NON-LIVRE'} (conf: {conf:.2f})")
        print(f"   URL: {url}")
        print(f"   Raison: {raison}")
        print()

    # Générer rapport
    rapport = analyseur.generer_rapport_decouverte()
    print("📊 RAPPORT DÉCOUVERTES IA:")
    print(f"   Nodes livres connus: {rapport['nodes_livres_confirmes']}")
    print(f"   Nodes inconnus détectés: {rapport['nodes_inconnus_detectes']}")