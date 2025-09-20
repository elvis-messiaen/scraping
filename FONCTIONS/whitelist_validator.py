#!/usr/bin/env python3
"""
SYSTÈME WHITELIST-BASED VALIDATION 2025
=======================================
Validation moderne basée sur l'approche whitelist recommandée par les
experts en sécurité : "WL is a best practice against BL"

Principe : Au lieu d'essayer d'énumérer tout ce qui n'est PAS permis
(impossible), on définit clairement ce qui EST autorisé.
"""

import re
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

class ValidationLevel(Enum):
    """Niveaux de validation"""
    CERTAIN = "certain"           # 100% sûr
    TRUSTED = "trusted"           # Très fiable
    PROBABLE = "probable"         # Probablement correct
    UNCERTAIN = "uncertain"       # Incertain

@dataclass
class WhitelistEntry:
    """Entrée dans la whitelist"""
    pattern: str
    category: str
    confidence: float
    description: str
    examples: List[str] = None

class WhitelistValidator:
    """
    Validateur basé sur une approche whitelist pure

    Avantages selon les recherches 2025 :
    - Plus sûr que blacklist
    - Plus prévisible
    - Évite les faux positifs
    - Plus maintenable
    """

    def __init__(self):
        """Initialiser le validateur whitelist"""
        self.url_whitelist = self._build_url_whitelist()
        self.content_whitelist = self._build_content_whitelist()

    def _build_url_whitelist(self) -> List[WhitelistEntry]:
        """
        Construire la whitelist des patterns d'URL autorisés
        Basé sur la structure officielle d'Amazon
        """
        return [
            # PATTERNS URL CERTAINS - Confiance 100%
            WhitelistEntry(
                pattern=r'node=301\d+',
                category='book_certain',
                confidence=1.0,
                description='Nodes 301xxx - Catégories livres principales Amazon',
                examples=['node=301061', 'node=301132', 'node=301146']
            ),

            WhitelistEntry(
                pattern=r'stripbooks',
                category='book_certain',
                confidence=1.0,
                description='Section stripbooks - Livres Amazon',
                examples=['i=stripbooks', '/stripbooks/', 'stripbooks&rh=']
            ),

            WhitelistEntry(
                pattern=r'node=283155',
                category='book_certain',
                confidence=1.0,
                description='Node Books principal international',
                examples=['node=283155']
            ),

            # PATTERNS TRÈS FIABLES - Confiance 95%
            WhitelistEntry(
                pattern=r'node=(17|4|18|53|13996|290060)',
                category='book_trusted',
                confidence=0.95,
                description='Genres littéraires principaux documentés',
                examples=['node=17', 'node=4', 'node=18']
            ),

            WhitelistEntry(
                pattern=r'/livre[s]?[-/]',
                category='book_trusted',
                confidence=0.95,
                description='URLs françaises avec "livre"',
                examples=['/livres/', '/livre-achat/', '/livre-numerique/']
            ),

            WhitelistEntry(
                pattern=r'/book[s]?[-/]',
                category='book_trusted',
                confidence=0.95,
                description='URLs anglaises avec "book"',
                examples=['/books/', '/book-store/', '/books-literature/']
            ),

            # PATTERNS PROBABLES - Confiance 80%
            WhitelistEntry(
                pattern=r'rh=n%3A301',
                category='book_probable',
                confidence=0.80,
                description='Recherche encodée dans catégories livres',
                examples=['rh=n%3A301061', 'rh=n%3A301132']
            ),

            WhitelistEntry(
                pattern=r'node=(404|406|451|465|466|489|531|542|596|969|1064|1087)',
                category='book_probable',
                confidence=0.80,
                description='Nodes spécialisés souvent livres',
                examples=['node=404', 'node=466', 'node=969']
            ),
        ]

    def _build_content_whitelist(self) -> List[WhitelistEntry]:
        """
        Construire la whitelist des contenus autorisés
        """
        return [
            # INDICATEURS CERTAINS DE LIVRES
            WhitelistEntry(
                pattern=r'(paperback|hardcover|broché|relié|poche)',
                category='format_certain',
                confidence=1.0,
                description='Formats de livres physiques',
                examples=['Paperback', 'Hardcover', 'Broché']
            ),

            WhitelistEntry(
                pattern=r'(kindle|ebook|livre numérique|audiobook)',
                category='format_certain',
                confidence=1.0,
                description='Formats de livres numériques',
                examples=['Kindle', 'eBook', 'Audiobook']
            ),

            WhitelistEntry(
                pattern=r'(isbn|éditeur|publisher|auteur|author)',
                category='metadata_certain',
                confidence=1.0,
                description='Métadonnées spécifiques aux livres',
                examples=['ISBN', 'Éditeur', 'Author']
            ),

            # GENRES LITTÉRAIRES FIABLES
            WhitelistEntry(
                pattern=r'(roman|novel|littérature|literature|fiction)',
                category='genre_trusted',
                confidence=0.95,
                description='Genres littéraires principaux',
                examples=['Roman', 'Literature', 'Fiction']
            ),

            WhitelistEntry(
                pattern=r'(biographie|autobiography|essai|essay|poésie|poetry)',
                category='genre_trusted',
                confidence=0.95,
                description='Genres non-fiction spécialisés',
                examples=['Biographie', 'Essay', 'Poetry']
            ),

            # LANGUES (dans contexte livre)
            WhitelistEntry(
                pattern=r'(french|english|spanish|german|italian|portuguese|russian|chinese|japanese)',
                category='language_probable',
                confidence=0.85,
                description='Langues de publication (si contexte livre)',
                examples=['French', 'English', 'Spanish']
            ),
        ]

    def validate_url(self, url: str) -> Tuple[bool, ValidationLevel, float, List[str]]:
        """
        Valider une URL contre la whitelist

        Args:
            url (str): URL à valider

        Returns:
            Tuple[bool, ValidationLevel, float, List[str]]:
                (is_valid, level, confidence, matched_patterns)
        """
        url_lower = url.lower()
        matches = []
        max_confidence = 0.0
        validation_level = ValidationLevel.UNCERTAIN

        # Tester tous les patterns de la whitelist
        for entry in self.url_whitelist:
            if re.search(entry.pattern, url_lower):
                matches.append(f"URL: {entry.description}")

                # Déterminer le niveau de validation
                if entry.confidence >= 1.0:
                    validation_level = ValidationLevel.CERTAIN
                elif entry.confidence >= 0.95:
                    validation_level = max(validation_level, ValidationLevel.TRUSTED, key=lambda x: x.value)
                elif entry.confidence >= 0.80:
                    validation_level = max(validation_level, ValidationLevel.PROBABLE, key=lambda x: x.value)

                max_confidence = max(max_confidence, entry.confidence)

        is_valid = len(matches) > 0 and max_confidence >= 0.80
        return is_valid, validation_level, max_confidence, matches

    def validate_content(self, content: str, context_url: str = "") -> Tuple[bool, ValidationLevel, float, List[str]]:
        """
        Valider un contenu contre la whitelist

        Args:
            content (str): Contenu à valider
            context_url (str): URL de contexte pour améliorer la validation

        Returns:
            Tuple[bool, ValidationLevel, float, List[str]]:
                (is_valid, level, confidence, matched_patterns)
        """
        content_lower = content.lower()
        context_lower = context_url.lower()
        matches = []
        confidence_scores = []

        # Vérifier le contexte URL d'abord
        url_is_book_context = any(
            re.search(pattern, context_lower)
            for pattern in [r'node=301', r'stripbooks', r'/livre', r'/book']
        )

        # Tester tous les patterns de contenu
        for entry in self.content_whitelist:
            if re.search(entry.pattern, content_lower):
                matches.append(f"Contenu: {entry.description}")

                # Ajuster la confiance selon le contexte
                adjusted_confidence = entry.confidence
                if entry.category == 'language_probable' and url_is_book_context:
                    adjusted_confidence = min(0.95, entry.confidence + 0.1)  # Bonus contexte

                confidence_scores.append(adjusted_confidence)

        # Calculer confiance globale
        if confidence_scores:
            max_confidence = max(confidence_scores)
            # Bonus si plusieurs indicateurs
            if len(confidence_scores) >= 2:
                max_confidence = min(1.0, max_confidence + 0.05)
        else:
            max_confidence = 0.0

        # Déterminer niveau de validation
        if max_confidence >= 1.0:
            validation_level = ValidationLevel.CERTAIN
        elif max_confidence >= 0.95:
            validation_level = ValidationLevel.TRUSTED
        elif max_confidence >= 0.80:
            validation_level = ValidationLevel.PROBABLE
        else:
            validation_level = ValidationLevel.UNCERTAIN

        is_valid = len(matches) > 0 and max_confidence >= 0.80
        return is_valid, validation_level, max_confidence, matches

    def validate_category(self, url: str, name: str, context: str = "") -> Dict:
        """
        Validation complète d'une catégorie (URL + contenu)

        Args:
            url (str): URL de la catégorie
            name (str): Nom de la catégorie
            context (str): Contexte additionnel

        Returns:
            Dict: Résultat complet de validation
        """
        # Validation URL
        url_valid, url_level, url_confidence, url_matches = self.validate_url(url)

        # Validation contenu
        full_content = f"{name} {context}"
        content_valid, content_level, content_confidence, content_matches = self.validate_content(full_content, url)

        # Décision finale
        final_valid = url_valid or content_valid  # OR logique : un seul suffit
        final_confidence = max(url_confidence, content_confidence)

        # Niveau final (le plus élevé)
        level_order = [ValidationLevel.UNCERTAIN, ValidationLevel.PROBABLE, ValidationLevel.TRUSTED, ValidationLevel.CERTAIN]
        final_level = max(url_level, content_level, key=lambda x: level_order.index(x))

        # Bonus si les deux validations concordent
        if url_valid and content_valid:
            final_confidence = min(1.0, final_confidence + 0.1)
            final_level = ValidationLevel.CERTAIN if final_confidence >= 0.99 else final_level

        return {
            'is_valid': final_valid,
            'validation_level': final_level.value,
            'confidence_score': final_confidence,
            'url_validation': {
                'valid': url_valid,
                'level': url_level.value,
                'confidence': url_confidence,
                'matches': url_matches
            },
            'content_validation': {
                'valid': content_valid,
                'level': content_level.value,
                'confidence': content_confidence,
                'matches': content_matches
            },
            'all_matches': url_matches + content_matches
        }

    def get_whitelist_stats(self) -> Dict:
        """Obtenir les statistiques de la whitelist"""
        return {
            'url_patterns': len(self.url_whitelist),
            'content_patterns': len(self.content_whitelist),
            'certain_patterns': len([e for e in self.url_whitelist + self.content_whitelist if e.confidence >= 1.0]),
            'trusted_patterns': len([e for e in self.url_whitelist + self.content_whitelist if 0.95 <= e.confidence < 1.0]),
            'probable_patterns': len([e for e in self.url_whitelist + self.content_whitelist if 0.80 <= e.confidence < 0.95])
        }

def creer_validateur_whitelist() -> WhitelistValidator:
    """
    Factory function pour créer un validateur whitelist

    Returns:
        WhitelistValidator: Instance configurée
    """
    return WhitelistValidator()

# INTERFACE COMPATIBLE
def est_categorie_livre_valide_whitelist(url: str, text: str) -> bool:
    """
    Interface simple compatible avec l'ancien système

    Args:
        url (str): URL de la catégorie
        text (str): Nom de la catégorie

    Returns:
        bool: True si validé par whitelist
    """
    validator = creer_validateur_whitelist()
    result = validator.validate_category(url, text)

    # Accepter seulement si niveau >= PROBABLE
    return result['is_valid'] and result['confidence_score'] >= 0.80

if __name__ == "__main__":
    # TESTS DE VALIDATION
    validator = creer_validateur_whitelist()

    test_cases = [
        ("https://www.amazon.fr/b?node=301132", "Romans et polars"),
        ("https://www.amazon.fr/stripbooks/literature", "Literature & Fiction"),
        ("https://www.amazon.fr/b?node=172282", "Electronics"),
        ("https://www.amazon.fr/b?node=466218", "Legal"),
        ("https://www.amazon.fr/livre-poche/paperback", "Paperback Books"),
    ]

    print("🔍 TESTS VALIDATION WHITELIST\n")

    for url, name in test_cases:
        result = validator.validate_category(url, name)

        print(f"Catégorie: {name}")
        print(f"URL: {url}")
        print(f"✅ Valide: {result['is_valid']}")
        print(f"📊 Niveau: {result['validation_level']}")
        print(f"🎯 Confiance: {result['confidence_score']:.2f}")
        print(f"🔍 Matches: {result['all_matches']}")
        print("-" * 60)

    # Statistiques whitelist
    stats = validator.get_whitelist_stats()
    print(f"\n📊 STATISTIQUES WHITELIST:")
    for key, value in stats.items():
        print(f"   {key}: {value}")