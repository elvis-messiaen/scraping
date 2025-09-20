#!/usr/bin/env python3
"""
NOUVELLE VALIDATION CATEGORIES 2025
===================================
Interface de remplacement pour validation_categories.py
Utilise l'architecture moderne orchestrée.

UTILISATION: Remplacez votre import par :
from validation_categories_2025 import est_categorie_livre_valide
"""

# Import du système orchestré moderne
from validation_orchestrator_2025 import est_categorie_livre_valide_2025

# INTERFACE COMPATIBLE - Remplace l'ancienne fonction
def est_categorie_livre_valide(url: str, text: str) -> bool:
    """
    🚀 NOUVELLE VERSION 2025 - Interface compatible

    Remplace complètement l'ancienne validation par le système
    orchestré moderne avec architecture LLM + IA.

    Args:
        url (str): URL de la catégorie Amazon
        text (str): Nom de la catégorie

    Returns:
        bool: True si catégorie livre validée par le système 2025
    """
    return est_categorie_livre_valide_2025(url, text)

# Autres fonctions compatibles (inchangées)
def est_sous_categorie_valide(url: str, text: str, url_parent: str) -> bool:
    """Interface compatible pour les sous-catégories"""
    return est_categorie_livre_valide(url, text) and url != url_parent

def extraire_node_id(url: str) -> str:
    """Extraire node ID - fonction inchangée"""
    import re
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

def nettoyer_nom_fichier(nom: str) -> str:
    """Nettoyer nom fichier - fonction inchangée"""
    import re
    nom_clean = re.sub(r'[^\w\s-]', ' ', nom.lower())
    nom_clean = re.sub(r'[-\s]+', '_', nom_clean)
    return nom_clean.strip('_')

# Nouvelles fonctions 2025
def obtenir_statistiques_validation() -> dict:
    """
    Obtenir les statistiques du système de validation 2025

    Returns:
        dict: Statistiques complètes de validation
    """
    from validation_orchestrator_2025 import creer_orchestrateur_validation

    orchestrateur = creer_orchestrateur_validation()
    return orchestrateur.get_statistics()

def validation_detaillee(url: str, text: str, context: str = "") -> dict:
    """
    Validation détaillée avec tous les détails du processus 2025

    Args:
        url (str): URL de la catégorie
        text (str): Nom de la catégorie
        context (str): Contexte additionnel

    Returns:
        dict: Résultat détaillé de validation
    """
    from validation_orchestrator_2025 import creer_orchestrateur_validation

    orchestrateur = creer_orchestrateur_validation(enable_all_methods=True)
    resultat = orchestrateur.validate_category(url, text, context)

    return {
        'verdict': resultat.final_verdict,
        'confiance': resultat.final_confidence,
        'methode_principale': resultat.primary_method.value,
        'consensus': resultat.consensus_level,
        'temps_traitement': resultat.processing_time,
        'raisonnement': resultat.reasoning,
        'details_methodes': resultat.method_results
    }

if __name__ == "__main__":
    # Tests de validation de l'interface
    print("🧪 TESTS INTERFACE COMPATIBLE 2025\n")

    test_cases = [
        ("https://www.amazon.fr/b?node=301132", "Romans et polars"),
        ("https://www.amazon.fr/b?node=172282", "Electronics"),
        ("https://www.amazon.fr/stripbooks/paperback", "Paperback Books"),
    ]

    for url, name in test_cases:
        # Test interface simple
        resultat_simple = est_categorie_livre_valide(url, name)

        # Test interface détaillée
        resultat_detaille = validation_detaillee(url, name)

        print(f"Catégorie: {name}")
        print(f"Simple: {'✅ LIVRE' if resultat_simple else '❌ NON-LIVRE'}")
        print(f"Détaillé: Confiance {resultat_detaille['confiance']:.2f}, {resultat_detaille['consensus']} consensus")
        print(f"Raisonnement: {resultat_detaille['raisonnement']}")
        print("-" * 50)

    # Statistiques
    print("\n📊 STATISTIQUES SYSTÈME 2025:")
    stats = obtenir_statistiques_validation()
    for key, value in stats.items():
        if not isinstance(value, dict):
            print(f"   {key}: {value}")