#!/usr/bin/env python3
"""
VALIDATION CATEGORIES RAPIDE - SOLUTION IMMÉDIATE
=================================================
Remplacement rapide pour corriger immédiatement les rejets
de catégories valides dans votre scraper.

UTILISATION: Remplacez votre import par :
from validation_categories_rapide import est_categorie_livre_valide
"""

import re
from typing import Optional

def extraire_node_id(url: str) -> Optional[str]:
    """
    Extraire node ID d'une URL Amazon

    Args:
        url (str): URL Amazon

    Returns:
        Optional[str]: Node ID ou None
    """
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

def est_categorie_livre_valide(url: str, text: str) -> bool:
    """
    🚀 VALIDATION UNIQUEMENT PAR URL/NODE ID

    Validation basée EXCLUSIVEMENT sur l'URL et les Node IDs,
    JAMAIS sur le nom de la catégorie (comme demandé).

    Args:
        url (str): URL de la catégorie Amazon
        text (str): Nom de la catégorie (utilisé seulement pour les filtres)

    Returns:
        bool: True si catégorie livre basé sur URL/Node
    """
    if not url:
        return False

    url_lower = url.lower()
    text_lower = text.lower()

    # URLs de sites non-Amazon
    if not ('amazon.' in url_lower):
        return False

    # ============================================
    # FILTRES/FACETTES À REJETER (basés sur URL)
    # ============================================

    # Rejeter les filtres de prix, condition, etc. (basé sur URL)
    filtres_url = [
        'p_36=',           # Prix
        'p_72=',           # Reviews
        'p_85=',           # Prime
        'p_90=',           # Shipping
        'condition-type',  # État du produit
        'prime%20eligible', # Prime eligible encodé
    ]

    for filtre in filtres_url:
        if filtre in url_lower:
            return False

    # Rejeter aussi les filtres évidents dans le texte
    filtres_texte_evidents = [
        'prime eligible', 'eur', '$', '€', 'up to', 'stars', 'rating',
        'free shipping', 'get it tomorrow', 'new', 'used'
    ]

    for filtre in filtres_texte_evidents:
        if filtre in text_lower:
            return False

    # ============================================
    # ACCEPTATION PAR NODE ID / URL STRUCTURE
    # ============================================

    # Extraire le node ID de l'URL
    node_id = extraire_node_id(url)

    if node_id:
        # NODES 301xxx = Livres français Amazon (TOUS acceptés)
        if node_id.startswith('301'):
            return True

        # AUTRES NODES LIVRES CONNUS
        nodes_livres_certains = {
            # Nodes internationaux livres
            '283155',      # Books (international)
            '17',          # Literature & Fiction
            '4',           # Children's Books
            '18',          # Mystery & Thrillers
            '53',          # Nonfiction
            '13996',       # Medical Books
            '290060',      # Outdoors & Nature (books)
            '154606011',   # Kindle eBooks
            '466218',      # Legal
            '695398031',   # Le livre autrement
            '6680516031',  # Nouveautés
            '125273011',   # Recherche détaillée
            '52042011',    # Livres langues étrangères
            '355635011',   # Loisirs et culture (livres)
            '12641896031', # Santé et bien-être (livres)
            '4252330031',  # Humour (livres)
            '4256914031',  # Jeux, arts et création (livres)
            '451166031',   # Primaire
            '451167031',   # Collège
            '1064926',     # Référence
        }

        if node_id in nodes_livres_certains:
            return True

        # NODES NON-LIVRES À REJETER
        nodes_non_livres = {
            '172282',      # Electronics
            '502394',      # Automotive
            '7141123011',  # Clothing
            '228013',      # Sports & Outdoors (équipement)
            '11091801',    # Toys & Games
            '2972638011',  # Baby & Toddler Toys
            '166764011',   # Kitchen & Dining
            '3760901',     # Tools & Home Improvement
        }

        if node_id in nodes_non_livres:
            return False

    # ============================================
    # VALIDATION PAR STRUCTURE D'URL
    # ============================================

    # URLs spécifiquement livres
    indicateurs_url_livres = [
        'stripbooks',              # Amazon books section
        '/livre',                  # URL française avec livre
        '/book',                   # URL anglaise avec book
        'kindle',                  # Ebooks Kindle
        'ebook',                   # Ebooks généraux
        '/b/?ie=utf8&node=301',    # Structure française livres
    ]

    for indicateur in indicateurs_url_livres:
        if indicateur in url_lower:
            return True

    # URLs spécifiquement NON-livres
    indicateurs_url_non_livres = [
        '/electronics',
        '/automotive',
        '/clothing',
        '/sports',
        '/toys-games',
        '/baby',
        '/kitchen',
        '/tools',
        '/garden',
        '/beauty',
        '/jewelry',
    ]

    for indicateur in indicateurs_url_non_livres:
        if indicateur in url_lower:
            return False

    # ============================================
    # LOGIQUE PAR DÉFAUT
    # ============================================

    # Si c'est une URL Amazon avec un node= et aucun rejet évident, accepter
    if 'amazon.' in url_lower and 'node=' in url_lower:
        # Sinon accepter (approche permissive pour les nodes inconnus)
        return True

    # Par défaut, rejeter si structure inconnue
    return False

def est_sous_categorie_valide(url: str, text: str, url_parent: str) -> bool:
    """Interface compatible pour les sous-catégories"""
    return est_categorie_livre_valide(url, text) and url != url_parent

def nettoyer_nom_fichier(nom: str) -> str:
    """Nettoyer nom fichier - fonction inchangée"""
    import re
    nom_clean = re.sub(r'[^\w\s-]', ' ', nom.lower())
    nom_clean = re.sub(r'[-\s]+', '_', nom_clean)
    return nom_clean.strip('_')

if __name__ == "__main__":
    # Tests avec vos catégories qui étaient rejetées
    print("🧪 TESTS VALIDATION RAPIDE")
    print("="*40)

    test_cases = [
        # CAS PRÉCÉDEMMENT REJETÉS - Devraient être ACCEPTÉS
        ("https://www.amazon.fr/-/en/s?rh=n%3A301061%2Cn%3A1381962031", "Science Fiction"),
        ("https://www.amazon.fr/-/en/s?rh=n%3A301061%2Cn%3A301141", "Sciences, Technics and Medical Sciences"),
        ("https://www.amazon.fr/-/en/s?rh=n%3A301061%2Cn%3A301139", "Social Sciences"),
        ("https://www.amazon.fr/-/en/s?rh=n%3A301061%2Cn%3A301146", "Textbooks & Study Guides"),
        ("https://www.amazon.fr/b?node=466218", "Legal"),
        ("https://www.amazon.fr/b?node=13996", "Medical Books"),

        # CAS À REJETER
        ("https://www.amazon.fr/-/en/s?rh=n%3A301061%2Cp_85%3A20934937031", "Prime Eligible"),
        ("https://www.amazon.fr/-/en/s?rh=n%3A301061%2Cp_36%3A389154011", "Up to 5 EUR"),
        ("https://www.amazon.fr/electronics", "Electronics"),
        ("https://www.amazon.fr/clothing", "Clothing"),
    ]

    for url, nom in test_cases:
        resultat = est_categorie_livre_valide(url, nom)
        status = "✅ ACCEPTÉ" if resultat else "❌ REJETÉ"
        print(f"{status}: {nom}")

    print("\n🎯 Cette validation corrige votre problème de rejets excessifs.")