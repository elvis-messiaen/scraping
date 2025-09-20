#!/usr/bin/env python3
"""
SIMPLIFICATEUR JSON CATÉGORIES
==============================
Extrait uniquement les noms des catégories/sous-catégories
depuis le JSON complet vers un format simple
"""

import json
from pathlib import Path
from typing import Set, List

def extraire_noms_recursif(categories_dict: dict, noms_extraits: Set[str]) -> None:
    """
    Extraire récursivement tous les noms de catégories

    Args:
        categories_dict (dict): Dictionnaire des catégories
        noms_extraits (Set[str]): Set pour stocker les noms uniques
    """
    for cat_id, cat_data in categories_dict.items():
        # Extraire le nom de la catégorie
        nom = cat_data.get('nom', '').strip()
        if nom:
            noms_extraits.add(nom)

        # Traiter récursivement les sous-catégories
        sous_categories = cat_data.get('sous_categories', {})
        if sous_categories:
            extraire_noms_recursif(sous_categories, noms_extraits)

def filtrer_categories_livres(noms: Set[str]) -> List[str]:
    """
    Filtrer pour ne garder que les catégories qui semblent être des livres

    Args:
        noms (Set[str]): Ensemble des noms de catégories

    Returns:
        List[str]: Liste filtrée des catégories livres
    """
    # Mots-clés indiquant des catégories NON-livres
    mots_cles_exclus = {
        'baby', 'stroller', 'pram', 'gift card', 'electronics', 'computer',
        'phone', 'clothing', 'fashion', 'beauty', 'automotive', 'car',
        'motorbike', 'toy', 'game', 'sport', 'kitchen', 'home', 'garden',
        'tool', 'health', 'personal care', 'prime video', 'audible',
        'music', 'movie', 'dvd', 'cd', 'vinyl', 'sell on amazon',
        'custom product', 'outlet', 'deal', 'free delivery', 'mobile app',
        'resale', 'top up', 'career', 'recycling', 'shopper toolkit'
    }

    categories_livres = []

    for nom in noms:
        nom_lower = nom.lower()

        # Exclure si contient des mots-clés non-livres
        if any(mot in nom_lower for mot in mots_cles_exclus):
            continue

        # Inclure si c'est clairement livre-related
        if any(mot in nom_lower for mot in ['book', 'livre', 'literature', 'fiction', 'novel', 'poetry', 'essay']):
            categories_livres.append(nom)
            continue

        # Inclure les catégories générales qui peuvent contenir des livres
        if any(mot in nom_lower for mot in [
            'education', 'science', 'history', 'philosophy', 'religion',
            'art', 'culture', 'language', 'reference', 'academic',
            'student', 'study', 'learn', 'textbook', 'manual'
        ]):
            categories_livres.append(nom)

    return sorted(categories_livres)

def simplifier_json_categories():
    """
    Fonction principale pour simplifier le JSON
    """
    # Chemins des fichiers
    fichier_complet = "/Users/Simplon/Cours/workspacePython/Scraping/CATEGORIES/categories_amazon_completes.json"
    fichier_simple = "/Users/Simplon/Cours/workspacePython/Scraping/CATEGORIES/categories_noms_seulement.json"
    fichier_livres = "/Users/Simplon/Cours/workspacePython/Scraping/CATEGORIES/categories_livres_filtrees.json"

    print("📋 SIMPLIFICATION JSON CATÉGORIES")
    print("=" * 50)

    try:
        # Charger le JSON complet
        print("📂 Chargement JSON complet...")
        with open(fichier_complet, 'r', encoding='utf-8') as f:
            data = json.load(f)

        categories = data.get('categories', {})
        print(f"   Trouvé {len(categories)} catégories principales")

        # Extraire tous les noms
        print("🔍 Extraction des noms...")
        noms_extraits = set()
        extraire_noms_recursif(categories, noms_extraits)

        print(f"   Extrait {len(noms_extraits)} noms uniques")

        # Créer le JSON simple (tous les noms)
        json_simple = {
            "metadata": {
                "total_categories": len(noms_extraits),
                "source": "categories_amazon_completes.json",
                "description": "Tous les noms de catégories extraits"
            },
            "categories": sorted(list(noms_extraits))
        }

        # Sauvegarder JSON simple
        with open(fichier_simple, 'w', encoding='utf-8') as f:
            json.dump(json_simple, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON simple sauvé: {fichier_simple}")

        # Filtrer pour les livres seulement
        print("📚 Filtrage catégories livres...")
        categories_livres = filtrer_categories_livres(noms_extraits)

        print(f"   Trouvé {len(categories_livres)} catégories livres")

        # Créer le JSON livres
        json_livres = {
            "metadata": {
                "total_categories_livres": len(categories_livres),
                "source": "categories_amazon_completes.json",
                "description": "Catégories filtrées pour les livres uniquement"
            },
            "categories_livres": categories_livres
        }

        # Sauvegarder JSON livres
        with open(fichier_livres, 'w', encoding='utf-8') as f:
            json.dump(json_livres, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON livres sauvé: {fichier_livres}")

        # Afficher quelques exemples
        print(f"\n📋 EXEMPLES CATÉGORIES LIVRES:")
        for i, nom in enumerate(categories_livres[:10]):
            print(f"   {i+1}. {nom}")

        if len(categories_livres) > 10:
            print(f"   ... et {len(categories_livres) - 10} autres")

        print(f"\n🎯 RÉSULTATS:")
        print(f"   Total catégories: {len(noms_extraits)}")
        print(f"   Catégories livres: {len(categories_livres)}")
        print(f"   Fichier simple: {Path(fichier_simple).name}")
        print(f"   Fichier livres: {Path(fichier_livres).name}")

    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    simplifier_json_categories()