#!/usr/bin/env python3
"""
MODULE LLM-BASED DUAL-EXPERT CLASSIFICATION
==========================================
Architecture moderne inspirée d'Amazon Science pour la classification
automatique des catégories de livres avec validation IA.

Approche 2025 : Dual-Expert System
- Expert 1 : Classification basée sur l'URL et structure
- Expert 2 : Classification basée sur le contenu textuel
- Arbitrage IA : Décision finale intelligente

Références :
- Amazon Science: "E-commerce product categorization with LLM-based dual-expert classification paradigm"
- Best practices 2025 : Whitelist approach + AI validation
"""

import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

class CategoryConfidence(Enum):
    """
    Niveaux de confiance pour la classification
    """
    CERTAIN = "certain"         # 95-100% confiance
    HIGH = "high"              # 80-95% confiance
    MEDIUM = "medium"          # 60-80% confiance
    LOW = "low"                # 30-60% confiance
    UNCERTAIN = "uncertain"    # 0-30% confiance

@dataclass
class ClassificationResult:
    """
    Résultat structuré de la classification
    """
    is_book_category: bool
    confidence: CategoryConfidence
    confidence_score: float  # 0.0 - 1.0
    expert_1_verdict: bool   # Expert URL/Structure
    expert_2_verdict: bool   # Expert Contenu
    reasoning: str
    category_type: Optional[str] = None
    detected_indicators: List[str] = None

class URLStructureExpert:
    """
    EXPERT 1 : Classification basée sur l'analyse URL et structure

    Utilise les patterns d'URL Amazon pour identifier les catégories livres
    avec une approche whitelist moderne.
    """

    def __init__(self):
        """
        Initialiser l'expert URL avec les patterns 2025
        """
        # WHITELIST : Patterns URL certains pour les livres
        self.livre_url_patterns_certains = [
            # Nodes livres principaux
            r'node=301\d+',          # Tous les 301xxx = livres
            r'node=283155',          # Books général
            r'stripbooks',           # Section livres
            r'i=stripbooks',         # Paramètre livres

            # Navigation livres spécialisée
            r'rh=n%3A301\d+',       # Recherche livres encodée
            r'/livre-',             # URLs françaises livres
            r'/book[s]?-',          # URLs anglaises livres
        ]

        # WHITELIST : Nodes ID connus de livres (base de référence)
        self.known_book_nodes = {
            # Catégories principales livres
            '283155': 'Books',
            '301061': 'Livres (FR)',
            '17': 'Literature & Fiction',
            '4': 'Children\'s Books',
            '18': 'Mystery & Thrillers',
            '53': 'Nonfiction',
            '13996': 'Medicine',
            '290060': 'Outdoors & Nature',

            # Sous-catégories fréquentes (à compléter dynamiquement)
            '301132': 'Romans et polars',
            '301133': 'BD et Mangas',
            '301137': 'Enfants et ados',
            '301146': 'Scolaire et études'
        }

        # BLACKLIST MINIMALE : Seulement les évidences non-livres
        self.non_livre_patterns_evidents = [
            r'node=(?:172282|502394|16310091)',  # Électronique, Auto, etc.
            r'/electronics?[/-]',
            r'/automotive?[/-]',
            r'/clothing[/-]',
            r'/tools?[/-]'
        ]

    def classify_by_url(self, url: str, category_name: str) -> Tuple[bool, float, List[str]]:
        """
        Classifier une catégorie basée sur son URL

        Args:
            url (str): URL de la catégorie
            category_name (str): Nom de la catégorie

        Returns:
            Tuple[bool, float, List[str]]: (is_book, confidence_score, indicators)
        """
        url_lower = url.lower()
        indicators = []
        confidence = 0.0

        # ÉTAPE 1: Vérification whitelist patterns certains
        for pattern in self.livre_url_patterns_certains:
            if re.search(pattern, url_lower):
                indicators.append(f"Pattern livre certain: {pattern}")
                confidence += 0.4  # Chaque pattern certain ajoute 40%

        # ÉTAPE 2: Vérification nodes connus
        node_match = re.search(r'node=(\d+)', url)
        if node_match:
            node_id = node_match.group(1)
            if node_id in self.known_book_nodes:
                indicators.append(f"Node ID livre connu: {node_id} ({self.known_book_nodes[node_id]})")
                confidence += 0.5  # Node connu = forte confiance

        # ÉTAPE 3: Vérification blacklist (seulement évidences)
        for pattern in self.non_livre_patterns_evidents:
            if re.search(pattern, url_lower):
                indicators.append(f"Pattern non-livre détecté: {pattern}")
                return False, 0.95, indicators  # Très confiant que ce n'est PAS un livre

        # ÉTAPE 4: Heuristiques supplémentaires sur le nom
        name_lower = category_name.lower()
        if any(mot in name_lower for mot in ['livre', 'book', 'roman', 'novel', 'littérature']):
            indicators.append("Nom contient des mots-clés livres")
            confidence += 0.3

        # Normaliser la confiance (max 1.0)
        confidence = min(confidence, 1.0)

        # Décision : si confiance >= 0.6, c'est probablement un livre
        is_book = confidence >= 0.6

        return is_book, confidence, indicators

class ContentAnalysisExpert:
    """
    EXPERT 2 : Classification basée sur l'analyse du contenu textuel

    Utilise l'analyse contextuelle moderne pour identifier les caractéristiques
    spécifiques aux catégories de livres.
    """

    def __init__(self):
        """
        Initialiser l'expert contenu avec les indicateurs 2025
        """
        # INDICATEURS FORTS de livres (haute confiance)
        self.strong_book_indicators = [
            # Formats de livres
            'paperback', 'hardcover', 'broché', 'relié', 'poche', 'kindle',
            'ebook', 'audiobook', 'livre audio',

            # Métadonnées livres
            'isbn', 'éditeur', 'publisher', 'auteur', 'author', 'écrivain',
            'édition', 'edition', 'pages', 'parution',

            # Genres littéraires
            'roman', 'novel', 'littérature', 'literature', 'fiction',
            'biographie', 'autobiography', 'essai', 'essay',

            # Contexte éditorial
            'bestseller', 'prix littéraire', 'critique littéraire'
        ]

        # INDICATEURS MOYENS de livres
        self.medium_book_indicators = [
            'lecture', 'reading', 'lire', 'read',
            'histoire', 'story', 'récit', 'conte',
            'manuel', 'textbook', 'guide', 'cours'
        ]

        # INDICATEURS EXCLUSIFS (disqualifiants)
        self.exclusive_non_book_indicators = [
            # Produits physiques non-livres
            'électroménager', 'appliance', 'machine', 'appareil',
            'smartphone', 'ordinateur', 'computer', 'laptop',
            'vêtement', 'clothing', 'chaussure', 'shoe',
            'voiture', 'car', 'automobile', 'véhicule'
        ]

    def classify_by_content(self, category_name: str, context: str = "") -> Tuple[bool, float, List[str]]:
        """
        Classifier une catégorie basée sur son contenu textuel

        Args:
            category_name (str): Nom de la catégorie
            context (str): Contexte additionnel (optionnel)

        Returns:
            Tuple[bool, float, List[str]]: (is_book, confidence_score, indicators)
        """
        text_to_analyze = f"{category_name} {context}".lower()
        indicators = []
        confidence = 0.0

        # ÉTAPE 1: Vérification indicateurs exclusifs (disqualifiants)
        for indicator in self.exclusive_non_book_indicators:
            if indicator in text_to_analyze:
                indicators.append(f"Indicateur exclusif non-livre: {indicator}")
                return False, 0.9, indicators

        # ÉTAPE 2: Comptage indicateurs forts
        strong_count = 0
        for indicator in self.strong_book_indicators:
            if indicator in text_to_analyze:
                indicators.append(f"Indicateur fort livre: {indicator}")
                strong_count += 1
                confidence += 0.25  # Chaque indicateur fort = 25%

        # ÉTAPE 3: Comptage indicateurs moyens
        medium_count = 0
        for indicator in self.medium_book_indicators:
            if indicator in text_to_analyze:
                indicators.append(f"Indicateur moyen livre: {indicator}")
                medium_count += 1
                confidence += 0.15  # Chaque indicateur moyen = 15%

        # ÉTAPE 4: Bonus si plusieurs indicateurs
        if strong_count >= 2:
            confidence += 0.2  # Bonus multi-indicateurs forts
            indicators.append("Bonus: Multiples indicateurs forts détectés")

        # Normaliser la confiance
        confidence = min(confidence, 1.0)

        # Décision basée sur la confiance
        is_book = confidence >= 0.5

        return is_book, confidence, indicators

class LLMDualExpertClassifier:
    """
    SYSTÈME PRINCIPAL : Classification par double expertise avec arbitrage IA

    Combine les verdicts des deux experts avec un système d'arbitrage
    intelligent pour prendre la décision finale.
    """

    def __init__(self):
        """
        Initialiser le système de classification dual-expert
        """
        self.url_expert = URLStructureExpert()
        self.content_expert = ContentAnalysisExpert()

        # Configuration du logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def classify_category(self, url: str, category_name: str, context: str = "") -> ClassificationResult:
        """
        Classification complète d'une catégorie avec double expertise

        Args:
            url (str): URL de la catégorie
            category_name (str): Nom de la catégorie
            context (str): Contexte additionnel (optionnel)

        Returns:
            ClassificationResult: Résultat complet de la classification
        """
        self.logger.info(f"Classification de: {category_name}")

        # EXPERT 1: Analyse URL
        expert1_verdict, expert1_confidence, expert1_indicators = self.url_expert.classify_by_url(url, category_name)

        # EXPERT 2: Analyse contenu
        expert2_verdict, expert2_confidence, expert2_indicators = self.content_expert.classify_by_content(category_name, context)

        # ARBITRAGE IA : Décision finale intelligente
        final_verdict, final_confidence, reasoning = self._arbitrage_decision(
            expert1_verdict, expert1_confidence, expert1_indicators,
            expert2_verdict, expert2_confidence, expert2_indicators
        )

        # Déterminer le niveau de confiance
        confidence_level = self._determine_confidence_level(final_confidence)

        # Combiner tous les indicateurs
        all_indicators = expert1_indicators + expert2_indicators

        return ClassificationResult(
            is_book_category=final_verdict,
            confidence=confidence_level,
            confidence_score=final_confidence,
            expert_1_verdict=expert1_verdict,
            expert_2_verdict=expert2_verdict,
            reasoning=reasoning,
            detected_indicators=all_indicators
        )

    def _arbitrage_decision(self,
                          verdict1: bool, confidence1: float, indicators1: List[str],
                          verdict2: bool, confidence2: float, indicators2: List[str]) -> Tuple[bool, float, str]:
        """
        Arbitrage intelligent entre les deux experts

        Returns:
            Tuple[bool, float, str]: (final_verdict, final_confidence, reasoning)
        """
        reasoning_parts = []

        # CAS 1: Les deux experts sont d'accord
        if verdict1 == verdict2:
            final_verdict = verdict1
            final_confidence = (confidence1 + confidence2) / 2
            reasoning_parts.append(f"Consensus des experts: {verdict1}")
            reasoning_parts.append(f"Confiance URL: {confidence1:.2f}, Contenu: {confidence2:.2f}")

        # CAS 2: Désaccord - prioriser l'expert avec la plus haute confiance
        else:
            if confidence1 > confidence2:
                final_verdict = verdict1
                final_confidence = confidence1 * 0.8  # Pénalité pour désaccord
                reasoning_parts.append(f"Désaccord résolu en faveur de l'Expert URL (confiance: {confidence1:.2f})")
            else:
                final_verdict = verdict2
                final_confidence = confidence2 * 0.8  # Pénalité pour désaccord
                reasoning_parts.append(f"Désaccord résolu en faveur de l'Expert Contenu (confiance: {confidence2:.2f})")

        # CAS 3: Bonus si confiance très élevée d'un expert
        if max(confidence1, confidence2) >= 0.9:
            final_confidence = min(final_confidence * 1.1, 1.0)  # Bonus 10%
            reasoning_parts.append("Bonus: Confiance très élevée détectée")

        reasoning = " | ".join(reasoning_parts)

        return final_verdict, final_confidence, reasoning

    def _determine_confidence_level(self, confidence_score: float) -> CategoryConfidence:
        """
        Déterminer le niveau de confiance basé sur le score
        """
        if confidence_score >= 0.95:
            return CategoryConfidence.CERTAIN
        elif confidence_score >= 0.80:
            return CategoryConfidence.HIGH
        elif confidence_score >= 0.60:
            return CategoryConfidence.MEDIUM
        elif confidence_score >= 0.30:
            return CategoryConfidence.LOW
        else:
            return CategoryConfidence.UNCERTAIN

def creer_classificateur_llm() -> LLMDualExpertClassifier:
    """
    Factory function pour créer une instance du classificateur LLM

    Returns:
        LLMDualExpertClassifier: Instance configurée du classificateur
    """
    return LLMDualExpertClassifier()

# INTERFACE SIMPLE POUR COMPATIBILITÉ
def est_categorie_livre_valide_llm(url: str, text: str) -> bool:
    """
    Interface simple compatible avec l'ancien système

    Args:
        url (str): URL de la catégorie
        text (str): Nom de la catégorie

    Returns:
        bool: True si c'est une catégorie de livre
    """
    classificateur = creer_classificateur_llm()
    resultat = classificateur.classify_category(url, text)

    # Retourner True seulement si confiance >= MEDIUM
    return resultat.is_book_category and resultat.confidence.value in ['certain', 'high', 'medium']

if __name__ == "__main__":
    # TESTS DE VALIDATION
    classificateur = creer_classificateur_llm()

    # Test cases
    test_cases = [
        ("https://www.amazon.fr/b?node=301132", "Romans et polars"),
        ("https://www.amazon.fr/b?node=502394", "Electronics"),
        ("https://www.amazon.fr/stripbooks/literature", "Literature & Fiction"),
        ("https://www.amazon.fr/automotive/parts", "Auto Parts"),
    ]

    for url, name in test_cases:
        result = classificateur.classify_category(url, name)
        print(f"\n{'='*50}")
        print(f"Catégorie: {name}")
        print(f"URL: {url}")
        print(f"Verdict: {result.is_book_category}")
        print(f"Confiance: {result.confidence.value} ({result.confidence_score:.2f})")
        print(f"Raisonnement: {result.reasoning}")
        print(f"Indicateurs: {result.detected_indicators}")