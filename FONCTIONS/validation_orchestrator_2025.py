#!/usr/bin/env python3
"""
ORCHESTRATEUR DE VALIDATION 2025
=================================
Système d'orchestration intelligent qui combine tous les modules
de validation selon les meilleures pratiques 2025.

Architecture modulaire :
1. LLM-Based Dual-Expert Classification
2. Browse Node ID Manager
3. Whitelist-Based Validation
4. AI-Powered Detection System

Approche : Validation en cascade avec arbitrage intelligent
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import time

# Imports des modules 2025
try:
    from llm_category_classifier import creer_classificateur_llm, ClassificationResult
    from browse_node_manager import creer_gestionnaire_browse_nodes
    from whitelist_validator import creer_validateur_whitelist
    from ai_detection_system import creer_detecteur_ia
except ImportError as e:
    logging.error(f"Erreur import modules 2025: {e}")
    raise

class ValidationMethod(Enum):
    """Méthodes de validation disponibles"""
    LLM_DUAL_EXPERT = "llm_dual_expert"
    BROWSE_NODE = "browse_node"
    WHITELIST = "whitelist"
    AI_DETECTION = "ai_detection"

@dataclass
class OrchestratorResult:
    """Résultat complet de l'orchestrateur"""
    final_verdict: bool
    final_confidence: float
    primary_method: ValidationMethod
    method_results: Dict[str, Any]
    consensus_level: str
    processing_time: float
    reasoning: str

class ValidationOrchestrator2025:
    """
    Orchestrateur principal de validation 2025

    Combine intelligemment tous les systèmes de validation pour
    obtenir le résultat le plus fiable possible.
    """

    def __init__(self, enable_all_methods: bool = True):
        """
        Initialiser l'orchestrateur

        Args:
            enable_all_methods (bool): Activer tous les systèmes (sinon seulement essentiels)
        """
        self.enable_all_methods = enable_all_methods

        # Initialiser les systèmes
        self.logger = logging.getLogger(__name__)
        self._initialize_systems()

        # Configuration de validation
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }

        # Statistiques
        self.stats = {
            'total_validations': 0,
            'method_usage': {method.value: 0 for method in ValidationMethod},
            'consensus_achieved': 0,
            'high_confidence_results': 0
        }

    def _initialize_systems(self):
        """Initialiser tous les systèmes de validation"""
        try:
            # Systèmes essentiels (toujours activés)
            self.llm_classifier = creer_classificateur_llm()
            self.browse_node_manager = creer_gestionnaire_browse_nodes()

            if self.enable_all_methods:
                # Systèmes complémentaires
                self.whitelist_validator = creer_validateur_whitelist()
                self.ai_detector = creer_detecteur_ia()
                self.logger.info("Tous les systèmes de validation initialisés")
            else:
                self.whitelist_validator = None
                self.ai_detector = None
                self.logger.info("Systèmes essentiels initialisés uniquement")

        except Exception as e:
            self.logger.error(f"Erreur initialisation systèmes: {e}")
            raise

    def validate_category(self, url: str, name: str, context: str = "") -> OrchestratorResult:
        """
        Validation orchestrée d'une catégorie

        Args:
            url (str): URL de la catégorie
            name (str): Nom de la catégorie
            context (str): Contexte additionnel

        Returns:
            OrchestratorResult: Résultat complet avec arbitrage
        """
        start_time = time.time()
        self.stats['total_validations'] += 1

        self.logger.info(f"Validation orchestrée: {name}")

        method_results = {}

        # MÉTHODE 1: LLM Dual-Expert (priorité haute)
        try:
            llm_result = self.llm_classifier.classify_category(url, name, context)
            method_results['llm_dual_expert'] = {
                'verdict': llm_result.is_book_category,
                'confidence': llm_result.confidence_score,
                'level': llm_result.confidence.value,
                'reasoning': llm_result.reasoning
            }
            self.stats['method_usage'][ValidationMethod.LLM_DUAL_EXPERT.value] += 1
        except Exception as e:
            self.logger.warning(f"Erreur LLM classification: {e}")
            method_results['llm_dual_expert'] = None

        # MÉTHODE 2: Browse Node Analysis
        try:
            node_id = self.browse_node_manager.extract_node_from_url(url)
            if node_id:
                is_book_node, node_confidence = self.browse_node_manager.is_book_node(node_id)
                method_results['browse_node'] = {
                    'verdict': is_book_node,
                    'confidence': node_confidence,
                    'node_id': node_id,
                    'method': 'node_analysis'
                }
                self.stats['method_usage'][ValidationMethod.BROWSE_NODE.value] += 1
            else:
                method_results['browse_node'] = None
        except Exception as e:
            self.logger.warning(f"Erreur Browse Node analysis: {e}")
            method_results['browse_node'] = None

        # MÉTHODE 3: Whitelist Validation (si activée)
        if self.enable_all_methods and self.whitelist_validator:
            try:
                whitelist_result = self.whitelist_validator.validate_category(url, name, context)
                method_results['whitelist'] = whitelist_result
                self.stats['method_usage'][ValidationMethod.WHITELIST.value] += 1
            except Exception as e:
                self.logger.warning(f"Erreur Whitelist validation: {e}")
                method_results['whitelist'] = None

        # MÉTHODE 4: AI Detection (si activée)
        if self.enable_all_methods and self.ai_detector:
            try:
                ai_result = self.ai_detector.detect_category_type(url, name, context)
                method_results['ai_detection'] = {
                    'verdict': ai_result.is_book_category,
                    'confidence': ai_result.confidence_score,
                    'method': ai_result.detection_method,
                    'reasoning': ai_result.reasoning
                }
                self.stats['method_usage'][ValidationMethod.AI_DETECTION.value] += 1
            except Exception as e:
                self.logger.warning(f"Erreur AI detection: {e}")
                method_results['ai_detection'] = None

        # ARBITRAGE INTELLIGENT
        final_result = self._arbitrate_results(method_results, name)
        final_result.processing_time = time.time() - start_time
        final_result.method_results = method_results

        # Mise à jour des statistiques
        if final_result.consensus_level == 'high':
            self.stats['consensus_achieved'] += 1
        if final_result.final_confidence >= 0.8:
            self.stats['high_confidence_results'] += 1

        return final_result

    def _arbitrate_results(self, method_results: Dict[str, Any], category_name: str) -> OrchestratorResult:
        """
        Arbitrage intelligent entre tous les résultats

        Args:
            method_results (Dict): Résultats de toutes les méthodes
            category_name (str): Nom de la catégorie (pour logs)

        Returns:
            OrchestratorResult: Décision finale arbitrée
        """
        valid_results = {k: v for k, v in method_results.items() if v is not None}

        if not valid_results:
            return OrchestratorResult(
                final_verdict=False,
                final_confidence=0.1,
                primary_method=ValidationMethod.LLM_DUAL_EXPERT,
                method_results=method_results,
                consensus_level='none',
                processing_time=0.0,
                reasoning="Aucune méthode n'a pu analyser cette catégorie"
            )

        # Extraire les verdicts et confidences
        verdicts = []
        confidences = []
        method_weights = {
            'llm_dual_expert': 0.4,  # Poids le plus élevé
            'browse_node': 0.3,
            'whitelist': 0.2,
            'ai_detection': 0.1
        }

        for method, result in valid_results.items():
            if isinstance(result, dict):
                verdict = result.get('verdict', False)
                confidence = result.get('confidence', 0.0)
            else:
                verdict = getattr(result, 'is_valid', False)
                confidence = getattr(result, 'confidence_score', 0.0)

            verdicts.append((verdict, confidence, method))
            confidences.append(confidence * method_weights.get(method, 0.1))

        # Calcul du vote pondéré
        positive_weight = sum(conf for verdict, conf, _ in zip(*verdicts) if verdict)
        negative_weight = sum(conf for verdict, conf, _ in zip(*verdicts) if not verdict)
        total_weight = positive_weight + negative_weight

        # Décision finale
        if total_weight == 0:
            final_verdict = False
            final_confidence = 0.1
        else:
            final_verdict = positive_weight > negative_weight
            final_confidence = max(positive_weight, negative_weight) / total_weight

        # Déterminer la méthode principale
        if 'llm_dual_expert' in valid_results:
            primary_method = ValidationMethod.LLM_DUAL_EXPERT
        elif 'browse_node' in valid_results:
            primary_method = ValidationMethod.BROWSE_NODE
        elif 'whitelist' in valid_results:
            primary_method = ValidationMethod.WHITELIST
        else:
            primary_method = ValidationMethod.AI_DETECTION

        # Niveau de consensus
        agreement_count = sum(1 for verdict, _, _ in verdicts if verdict == final_verdict)
        consensus_level = (
            'high' if agreement_count >= len(verdicts) * 0.8 else
            'medium' if agreement_count >= len(verdicts) * 0.6 else
            'low'
        )

        # Génération du raisonnement
        reasoning = self._generate_arbitrage_reasoning(verdicts, final_verdict, consensus_level)

        return OrchestratorResult(
            final_verdict=final_verdict,
            final_confidence=final_confidence,
            primary_method=primary_method,
            method_results=method_results,
            consensus_level=consensus_level,
            processing_time=0.0,  # Sera mis à jour par l'appelant
            reasoning=reasoning
        )

    def _generate_arbitrage_reasoning(self, verdicts: List[Tuple], final_verdict: bool, consensus: str) -> str:
        """Générer une explication de l'arbitrage"""
        positive_methods = [method for verdict, _, method in verdicts if verdict]
        negative_methods = [method for verdict, _, method in verdicts if not verdict]

        reasoning_parts = []

        if final_verdict:
            reasoning_parts.append(f"ACCEPTÉ par {len(positive_methods)} méthode(s): {', '.join(positive_methods)}")
            if negative_methods:
                reasoning_parts.append(f"Désaccord avec: {', '.join(negative_methods)}")
        else:
            reasoning_parts.append(f"REJETÉ par {len(negative_methods)} méthode(s): {', '.join(negative_methods)}")
            if positive_methods:
                reasoning_parts.append(f"Désaccord avec: {', '.join(positive_methods)}")

        reasoning_parts.append(f"Consensus: {consensus}")

        return " | ".join(reasoning_parts)

    def get_statistics(self) -> Dict[str, Any]:
        """Obtenir les statistiques de l'orchestrateur"""
        return {
            **self.stats,
            'consensus_rate': self.stats['consensus_achieved'] / max(1, self.stats['total_validations']),
            'high_confidence_rate': self.stats['high_confidence_results'] / max(1, self.stats['total_validations'])
        }

def creer_orchestrateur_validation(enable_all_methods: bool = True) -> ValidationOrchestrator2025:
    """
    Factory function pour créer l'orchestrateur de validation

    Args:
        enable_all_methods (bool): Activer tous les systèmes ou seulement essentiels

    Returns:
        ValidationOrchestrator2025: Instance configurée
    """
    return ValidationOrchestrator2025(enable_all_methods)

# INTERFACE SIMPLE POUR REMPLACEMENT
def est_categorie_livre_valide_2025(url: str, text: str) -> bool:
    """
    Interface simple compatible - NOUVELLE VERSION 2025

    Remplace complètement l'ancienne fonction de validation
    par le système orchestré moderne.

    Args:
        url (str): URL de la catégorie
        text (str): Nom de la catégorie

    Returns:
        bool: True si validé comme catégorie livre
    """
    orchestrateur = creer_orchestrateur_validation(enable_all_methods=False)  # Mode rapide
    resultat = orchestrateur.validate_category(url, text)

    # Accepter si confiance >= medium et consensus >= medium
    return (resultat.final_verdict and
            resultat.final_confidence >= 0.6 and
            resultat.consensus_level in ['medium', 'high'])

if __name__ == "__main__":
    # TESTS COMPLETS DE L'ORCHESTRATEUR
    logging.basicConfig(level=logging.INFO)

    orchestrateur = creer_orchestrateur_validation(enable_all_methods=True)

    test_cases = [
        ("https://www.amazon.fr/b?node=301132", "Romans et polars", ""),
        ("https://www.amazon.fr/b?node=172282", "Electronics", ""),
        ("https://www.amazon.fr/stripbooks/literature", "Literature & Fiction", "bestselling authors"),
        ("https://www.amazon.fr/b?node=466218", "Legal", "law books and guides"),
        ("https://www.amazon.fr/cooking/french", "French Cooking", "recipe books"),
        ("https://www.amazon.fr/automotive/parts", "Auto Parts", "car accessories"),
    ]

    print("🎭 TESTS ORCHESTRATEUR VALIDATION 2025\n")

    for url, name, context in test_cases:
        print(f"{'='*60}")
        print(f"Catégorie: {name}")
        print(f"URL: {url}")
        if context:
            print(f"Contexte: {context}")

        result = orchestrateur.validate_category(url, name, context)

        print(f"\n🎯 RÉSULTAT FINAL:")
        print(f"   Verdict: {'✅ LIVRE' if result.final_verdict else '❌ NON-LIVRE'}")
        print(f"   Confiance: {result.final_confidence:.2f}")
        print(f"   Méthode principale: {result.primary_method.value}")
        print(f"   Consensus: {result.consensus_level}")
        print(f"   Temps: {result.processing_time:.3f}s")
        print(f"   Raisonnement: {result.reasoning}")

        print(f"\n📊 DÉTAILS PAR MÉTHODE:")
        for method, data in result.method_results.items():
            if data:
                verdict = data.get('verdict', data.get('is_valid', 'N/A'))
                confidence = data.get('confidence', data.get('confidence_score', 'N/A'))
                print(f"   {method}: {'✅' if verdict else '❌'} (conf: {confidence})")
            else:
                print(f"   {method}: ⚠️ Non disponible")

        print()

    # Statistiques finales
    stats = orchestrateur.get_statistics()
    print(f"📊 STATISTIQUES ORCHESTRATEUR:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for subkey, subvalue in value.items():
                print(f"      {subkey}: {subvalue}")
        else:
            print(f"   {key}: {value:.2f}" if isinstance(value, float) else f"   {key}: {value}")