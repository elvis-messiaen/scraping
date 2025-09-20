#!/usr/bin/env python3
"""
Fonctions utilitaires pour la gestion des catégories dans les fichiers JSON
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

def verifier_categorie_existante(fichier_json: str, nom_categorie: str, lien_amazon: str = "") -> bool:
    """
    Vérifie si une catégorie existe déjà dans le fichier JSON

    Args:
        fichier_json (str): Chemin vers le fichier JSON des catégories
        nom_categorie (str): Nom de la catégorie à vérifier
        lien_amazon (str): Lien Amazon associé (optionnel)

    Returns:
        bool: True si la catégorie existe, False sinon

    Description:
    Cette fonction charge le fichier JSON et vérifie si le nom de catégorie
    donné existe déjà dans la liste des catégories. La vérification est
    insensible à la casse et aux espaces pour éviter les doublons subtils.
    """
    try:
        if not os.path.exists(fichier_json):
            print(f"📄 Fichier {fichier_json} n'existe pas - catégorie non existante")
            return False

        with open(fichier_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Récupérer la liste des catégories
        categories_existantes = []
        if isinstance(data, dict) and 'categories' in data:
            categories_existantes = data['categories']
        elif isinstance(data, list):
            categories_existantes = data

        # Formatage du lien pour affichage
        lien_affiche = ""
        if lien_amazon:
            if len(lien_amazon) > 50:
                lien_affiche = f" 🔗 {lien_amazon[:25]}...{lien_amazon[-20:]}"
            else:
                lien_affiche = f" 🔗 {lien_amazon}"

        # Vérification insensible à la casse et aux espaces
        nom_normalise = nom_categorie.strip().lower()

        for cat_existante in categories_existantes:
            if isinstance(cat_existante, str):
                cat_normalise = cat_existante.strip().lower()
                if nom_normalise == cat_normalise:
                    print(f"✅ Catégorie '{nom_categorie}' existe déjà comme '{cat_existante}'{lien_affiche}")
                    return True

        print(f"❌ Catégorie '{nom_categorie}' n'existe pas{lien_affiche}")
        return False

    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la catégorie '{nom_categorie}': {e}")
        return False

def ajouter_categorie_si_absente(fichier_json: str, nom_categorie: str,
                                metadata_update: Optional[Dict] = None, lien_amazon: str = "") -> bool:
    """
    Ajoute une catégorie au fichier JSON seulement si elle n'existe pas déjà

    Args:
        fichier_json (str): Chemin vers le fichier JSON des catégories
        nom_categorie (str): Nom de la catégorie à ajouter
        metadata_update (Optional[Dict]): Métadonnées à mettre à jour
        lien_amazon (str): Lien Amazon associé (optionnel)

    Returns:
        bool: True si la catégorie a été ajoutée, False si elle existait déjà ou en cas d'erreur

    Description:
    Cette fonction vérifie d'abord si la catégorie existe avec verifier_categorie_existante(),
    puis l'ajoute seulement si elle n'existe pas. Elle met aussi à jour les métadonnées
    comme le compteur total et le timestamp.
    """
    try:
        # Vérifier si la catégorie existe déjà
        if verifier_categorie_existante(fichier_json, nom_categorie, lien_amazon):
            print(f"🔄 Catégorie '{nom_categorie}' existe déjà - pas d'ajout")
            return False

        # Charger ou créer la structure JSON
        if os.path.exists(fichier_json):
            with open(fichier_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            print(f"📄 Création du fichier {fichier_json}")
            data = {
                "metadata": {
                    "timestamp": "",
                    "date_debut": "",
                    "date_fin": "",
                    "duree_seconde": 0,
                    "duree_humaine": "",
                    "total_categories": 0,
                    "url_source": "https://www.amazon.fr/b?node=301061",
                    "description": "Catégories principales de livres Amazon.fr"
                },
                "categories": []
            }

        # S'assurer que la structure est correcte
        if 'categories' not in data:
            data['categories'] = []
        if 'metadata' not in data:
            data['metadata'] = {}

        # Ajouter la nouvelle catégorie
        data['categories'].append(nom_categorie)

        # Mettre à jour les métadonnées
        data['metadata']['total_categories'] = len(data['categories'])
        data['metadata']['timestamp'] = datetime.now().isoformat()

        # Mettre à jour les métadonnées personnalisées si fournies
        if metadata_update:
            for key, value in metadata_update.items():
                data['metadata'][key] = value

        # Sauvegarder
        with open(fichier_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Formatage du lien pour affichage
        lien_affiche = ""
        if lien_amazon:
            if len(lien_amazon) > 50:
                lien_affiche = f" 🔗 {lien_amazon[:25]}...{lien_amazon[-20:]}"
            else:
                lien_affiche = f" 🔗 {lien_amazon}"

        print(f"✅ Catégorie '{nom_categorie}' ajoutée avec succès{lien_affiche}")
        print(f"📊 Total catégories: {len(data['categories'])}")

        return True

    except Exception as e:
        print(f"❌ Erreur lors de l'ajout de la catégorie '{nom_categorie}': {e}")
        return False

def ajouter_categories_batch(fichier_json: str, liste_categories: List[str],
                           metadata_update: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Ajoute une liste de catégories en batch, seulement celles qui n'existent pas

    Args:
        fichier_json (str): Chemin vers le fichier JSON des catégories
        liste_categories (List[str]): Liste des catégories à ajouter
        metadata_update (Optional[Dict]): Métadonnées à mettre à jour

    Returns:
        Dict[str, Any]: Statistiques de l'opération

    Description:
    Cette fonction traite une liste complète de catégories et n'ajoute que celles
    qui n'existent pas déjà. Elle retourne des statistiques détaillées sur l'opération.
    """
    try:
        print(f"🔄 AJOUT BATCH: {len(liste_categories)} catégories à traiter")

        # Charger ou créer la structure JSON
        if os.path.exists(fichier_json):
            with open(fichier_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            print(f"📄 Création du fichier {fichier_json}")
            data = {
                "metadata": {
                    "timestamp": "",
                    "date_debut": "",
                    "date_fin": "",
                    "duree_seconde": 0,
                    "duree_humaine": "",
                    "total_categories": 0,
                    "url_source": "https://www.amazon.fr/b?node=301061",
                    "description": "Catégories principales de livres Amazon.fr"
                },
                "categories": []
            }

        # S'assurer que la structure est correcte
        if 'categories' not in data:
            data['categories'] = []
        if 'metadata' not in data:
            data['metadata'] = {}

        # Statistiques
        categories_avant = len(data['categories'])
        categories_ajoutees = 0
        categories_existantes = 0
        categories_echouees = 0

        # Normaliser les catégories existantes pour comparaison
        categories_existantes_normalisees = {
            cat.strip().lower(): cat
            for cat in data['categories']
            if isinstance(cat, str)
        }

        # Traiter chaque catégorie
        for nom_categorie in liste_categories:
            if not isinstance(nom_categorie, str) or not nom_categorie.strip():
                categories_echouees += 1
                continue

            nom_normalise = nom_categorie.strip().lower()

            # Vérifier si existe déjà
            if nom_normalise in categories_existantes_normalisees:
                categories_existantes += 1
                print(f"🔄 '{nom_categorie}' existe déjà comme '{categories_existantes_normalisees[nom_normalise]}'")
                continue

            # Ajouter la nouvelle catégorie
            data['categories'].append(nom_categorie.strip())
            categories_existantes_normalisees[nom_normalise] = nom_categorie.strip()
            categories_ajoutees += 1
            print(f"✅ '{nom_categorie}' ajoutée")

        # Mettre à jour les métadonnées
        data['metadata']['total_categories'] = len(data['categories'])
        data['metadata']['timestamp'] = datetime.now().isoformat()

        # Mettre à jour les métadonnées personnalisées si fournies
        if metadata_update:
            for key, value in metadata_update.items():
                data['metadata'][key] = value

        # Sauvegarder
        with open(fichier_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Statistiques finales
        stats = {
            'categories_avant': categories_avant,
            'categories_apres': len(data['categories']),
            'categories_ajoutees': categories_ajoutees,
            'categories_existantes': categories_existantes,
            'categories_echouees': categories_echouees,
            'categories_traitees': len(liste_categories),
            'fichier_json': fichier_json
        }

        print(f"\n📊 RÉSUMÉ AJOUT BATCH:")
        print(f"   Catégories avant: {stats['categories_avant']}")
        print(f"   Catégories après: {stats['categories_apres']}")
        print(f"   Nouvelles ajoutées: {stats['categories_ajoutees']}")
        print(f"   Déjà existantes: {stats['categories_existantes']}")
        print(f"   Échecs: {stats['categories_echouees']}")
        print(f"   Total traitées: {stats['categories_traitees']}")

        return stats

    except Exception as e:
        print(f"❌ Erreur lors de l'ajout batch: {e}")
        return {
            'categories_avant': 0,
            'categories_apres': 0,
            'categories_ajoutees': 0,
            'categories_existantes': 0,
            'categories_echouees': len(liste_categories) if liste_categories else 0,
            'categories_traitees': len(liste_categories) if liste_categories else 0,
            'erreur': str(e)
        }

def nettoyer_doublons_categories(fichier_json: str,
                                conserver_premier: bool = True) -> Dict[str, Any]:
    """
    Nettoie les doublons dans un fichier JSON de catégories

    Args:
        fichier_json (str): Chemin vers le fichier JSON des catégories
        conserver_premier (bool): Si True, conserve la première occurrence, sinon la dernière

    Returns:
        Dict[str, Any]: Statistiques du nettoyage

    Description:
    Cette fonction identifie et supprime les doublons dans la liste des catégories.
    La comparaison est insensible à la casse et aux espaces.
    """
    try:
        print(f"🧹 NETTOYAGE DOUBLONS: {fichier_json}")

        if not os.path.exists(fichier_json):
            print(f"❌ Fichier {fichier_json} n'existe pas")
            return {'erreur': 'Fichier inexistant'}

        # Charger le fichier
        with open(fichier_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'categories' not in data:
            print(f"❌ Pas de clé 'categories' dans le fichier")
            return {'erreur': 'Structure JSON invalide'}

        categories_avant = len(data['categories'])
        categories_originales = data['categories'].copy()

        # Nettoyer les doublons
        categories_nettoyees = []
        categories_vues = set()
        doublons_supprimes = []

        for i, categorie in enumerate(categories_originales):
            if not isinstance(categorie, str):
                continue

            cat_normalise = categorie.strip().lower()

            if cat_normalise not in categories_vues:
                categories_nettoyees.append(categorie.strip())
                categories_vues.add(cat_normalise)
            else:
                # Trouver l'original
                original = next((c for c in categories_nettoyees
                               if c.strip().lower() == cat_normalise), None)
                doublons_supprimes.append({
                    'doublon': categorie,
                    'original': original,
                    'position': i
                })

        # Mettre à jour les données
        data['categories'] = categories_nettoyees
        data['metadata']['total_categories'] = len(categories_nettoyees)
        data['metadata']['timestamp'] = datetime.now().isoformat()

        # Sauvegarder
        with open(fichier_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Statistiques
        stats = {
            'categories_avant': categories_avant,
            'categories_apres': len(categories_nettoyees),
            'doublons_supprimes': len(doublons_supprimes),
            'doublons_details': doublons_supprimes
        }

        print(f"✅ Nettoyage terminé:")
        print(f"   Catégories avant: {stats['categories_avant']}")
        print(f"   Catégories après: {stats['categories_apres']}")
        print(f"   Doublons supprimés: {stats['doublons_supprimes']}")

        if doublons_supprimes:
            print(f"   Doublons supprimés:")
            for doublon in doublons_supprimes[:5]:
                print(f"     - '{doublon['doublon']}' (gardé: '{doublon['original']}')")
            if len(doublons_supprimes) > 5:
                print(f"     ... et {len(doublons_supprimes)-5} autres")

        return stats

    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return {'erreur': str(e)}