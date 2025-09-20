#!/usr/bin/env python3
"""
Fonctions utilitaires pour nettoyer les fausses catégories
"""

import json
import os
import re
from datetime import datetime
from typing import List, Set, Dict, Any

def est_vraie_categorie_livre(nom_categorie: str) -> bool:
    """
    Détermine si c'est une vraie catégorie de livres physiques français

    Args:
        nom_categorie (str): Nom de la catégorie à vérifier

    Returns:
        bool: True si c'est une vraie catégorie, False sinon

    Description:
    Cette fonction applique des filtres stricts pour éliminer :
    - Les langues étrangères (sauf français)
    - Les prix et promotions
    - Les formats physiques (broché, relié, etc.)
    - Les auteurs individuels
    - Les filtres de recherche Amazon
    - Les cartes cadeaux et services
    """
    if not isinstance(nom_categorie, str) or not nom_categorie.strip():
        return False

    nom_lower = nom_categorie.lower().strip()

    # EXCLUSION 1: Langues étrangères (garder seulement français)
    langues_etrangeres = {
        'anglais', 'allemand', 'espagnol', 'italien', 'portugais', 'russe',
        'chinois', 'japonais', 'arabe', 'hindi', 'néerlandais', 'polonais',
        'suédois', 'danois', 'norvégien', 'finnois', 'grec', 'turc',
        'catalan', 'basque', 'breton', 'gallois', 'gaélique', 'irlandais',
        'latin', 'grec ancien', 'hébreu', 'yiddish', 'sanskrit',
        'ourdou', 'persan', 'tagalog', 'tamil', 'télougou', 'malayalam',
        'marathi', 'gujarati', 'punjabi', 'kannada', 'coréen', 'thaï',
        'vietnamien', 'indonésien', 'malais', 'roumain', 'bulgare',
        'hongrois', 'tchèque', 'slovaque', 'slovène', 'croate', 'serbe',
        'albanais', 'estonien', 'letton', 'lituanien', 'maltais',
        'luxembourgeois', 'frison occidental', 'scots', 'corse',
        'arménien', 'islandais', 'afrikaans'
    }

    if nom_lower in langues_etrangeres:
        return False

    # EXCLUSION 2: Prix et promotions
    patterns_prix = [
        r'jusqu\'à\s+\d+\s*eur', r'de\s+\d+\s+à\s+\d+\s*eur', r'\d+\s*eur\s+et\s+plus',
        r'tous\s+les\s+rabais', r'ventes?\s+flash', r'promotion', r'solde',
        r'rabais', r'réduction', r'offre', r'deal'
    ]

    for pattern in patterns_prix:
        if re.search(pattern, nom_lower):
            return False

    # EXCLUSION 3: Formats physiques et techniques
    formats_techniques = {
        'broché', 'relié', 'poche', 'ebook kindle', 'livre audio',
        'neuf', 'd\'occasion', 'kindle', 'audible', 'pdf', 'epub'
    }

    if nom_lower in formats_techniques:
        return False

    # EXCLUSION 4: Filtres temporels
    patterns_temps = [
        r'depuis\s+\d+\s+mois?', r'dans\s+les\s+\d+\s+mois', r'depuis\s+\d+\s+jours?',
        r'dernière?\s+(semaine|mois|année)', r'récent', r'nouveau.*parution'
    ]

    for pattern in patterns_temps:
        if re.search(pattern, nom_lower):
            return False

    # EXCLUSION 5: Étoiles et notes
    if re.search(r'\d+\s+stars?', nom_lower) or 'étoiles' in nom_lower:
        return False

    # EXCLUSION 6: Auteurs individuels (patterns typiques)
    patterns_auteurs = [
        r'^[a-z]+\s+[a-z]+$',  # Prénom Nom
        r'^[a-z]\.\s*[a-z]+\s+[a-z]+$',  # J. Prénom Nom
        r'collectif$', r'collectif\s+',  # Collectifs d'auteurs
    ]

    for pattern in patterns_auteurs:
        if re.search(pattern, nom_lower) and len(nom_lower.split()) <= 3:
            # Vérifier si ce n'est pas une vraie catégorie qui ressemble à un nom
            vrais_categories_comme_noms = {
                'victor hugo', 'jean-jacques rousseau'  # Exceptions célèbres
            }
            if nom_lower not in vrais_categories_comme_noms:
                return False

    # EXCLUSION 7: Services et non-livres
    services_exclus = {
        'cartes cadeaux', 'carte cadeau', 'amazon global store',
        'climate pledge friendly', 'prime reading', 'kindle unlimited',
        'word wise activé', 'cuisine et maison', 'high-tech',
        'électronique', 'informatique', 'jeux vidéo', 'jouets',
        'vêtements', 'chaussures', 'beauté', 'santé produits',
        'auto moto', 'jardin bricolage'
    }

    if nom_lower in services_exclus:
        return False

    # EXCLUSION 8: Séries et collections
    patterns_series = [
        r'inclus\s+dans\s+une\s+série', r'non\s+inclus\s+dans\s+une\s+série',
        r'premier\s+de\s+la\s+série', r'série\s+\d+', r'tome\s+\d+',
        r'volume\s+\d+', r'collection\s+'
    ]

    for pattern in patterns_series:
        if re.search(pattern, nom_lower):
            return False

    # EXCLUSION 9: Âges spécifiques trop précis
    patterns_ages = [
        r'bébé\s+à\s+\d+\s+ans', r'de\s+\d+\s+à\s+\d+\s+ans',
        r'\d+\s+ans\s+et\s+plus', r'\d+-\d+\s+ans'
    ]

    for pattern in patterns_ages:
        if re.search(pattern, nom_lower):
            return False

    # EXCLUSION 10: Types de livres physiques trop spécifiques
    types_physiques_exclus = {
        'livres d\'images', 'tout-carton', 'livres de coloriage',
        'livres à toucher', 'livres d\'autocollants', 'livres de puzzle',
        'livres pour le bain', 'livres rabats et pop-up',
        'livres sonores', 'livres tissu'
    }

    if nom_lower in types_physiques_exclus:
        return False

    # VALIDATION POSITIVE: Doit être une vraie catégorie thématique
    categories_valides_patterns = [
        # Genres littéraires
        r'roman', r'fiction', r'littérature', r'poésie', r'théâtre',
        r'polar', r'thriller', r'mystère', r'suspense', r'fantasy',
        r'science-fiction', r'fantastique', r'historique', r'biographie',

        # Domaines de connaissance
        r'science', r'histoire', r'politique', r'économie', r'philosophie',
        r'religion', r'spiritualité', r'psychologie', r'sociologie',
        r'médecine', r'santé', r'technique', r'informatique',

        # Publics cibles généraux
        r'enfant', r'ado', r'jeunesse', r'adulte', r'scolaire',
        r'étude', r'formation', r'référence',

        # Arts et loisirs
        r'art', r'photographie', r'musique', r'cuisine', r'voyage',
        r'sport', r'loisir', r'culture', r'humour',

        # Formats éditoriaux
        r'bd', r'bande.*dessinée', r'manga', r'comic', r'album'
    ]

    # Vérifier si correspond à un pattern valide
    est_valide = any(re.search(pattern, nom_lower) for pattern in categories_valides_patterns)

    # Ou si c'est une catégorie reconnue explicitement
    categories_explicitement_valides = {
        'livres', 'nouveautés', 'meilleures ventes', 'beaux livres',
        'livres pour enfants', 'livres pour adultes', 'calendriers et agendas',
        'le livre autrement', 'français'  # Garder seulement français
    }

    if nom_lower in categories_explicitement_valides:
        est_valide = True

    return est_valide

def nettoyer_fausses_categories(fichier_json: str) -> Dict[str, Any]:
    """
    Nettoie un fichier JSON en supprimant toutes les fausses catégories

    Args:
        fichier_json (str): Chemin vers le fichier JSON à nettoyer

    Returns:
        Dict[str, Any]: Statistiques du nettoyage

    Description:
    Cette fonction charge un fichier JSON de catégories, applique les filtres
    stricts pour identifier les vraies catégories de livres français,
    et supprime tout le reste.
    """
    print(f"🧹 NETTOYAGE FAUSSES CATÉGORIES: {fichier_json}")

    try:
        if not os.path.exists(fichier_json):
            print(f"❌ Fichier {fichier_json} introuvable")
            return {'erreur': 'Fichier inexistant'}

        # Charger le fichier
        with open(fichier_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'categories' not in data:
            print(f"❌ Pas de clé 'categories' dans le fichier")
            return {'erreur': 'Structure JSON invalide'}

        categories_avant = data['categories'].copy()
        total_avant = len(categories_avant)

        print(f"📊 Analyse de {total_avant} catégories...")

        # Analyser chaque catégorie
        categories_valides = []
        categories_supprimees = []

        for i, categorie in enumerate(categories_avant, 1):
            if not isinstance(categorie, str):
                categories_supprimees.append({
                    'nom': str(categorie),
                    'raison': 'Type invalide'
                })
                continue

            if est_vraie_categorie_livre(categorie):
                categories_valides.append(categorie)
                print(f"✅ [{i:3d}] Gardé: {categorie}")
            else:
                categories_supprimees.append({
                    'nom': categorie,
                    'raison': 'Pas une vraie catégorie de livre'
                })
                print(f"❌ [{i:3d}] Supprimé: {categorie}")

        # Mettre à jour les données
        data['categories'] = categories_valides
        data['metadata']['total_categories'] = len(categories_valides)
        data['metadata']['timestamp'] = datetime.now().isoformat()
        data['metadata']['derniere_purge'] = datetime.now().isoformat()

        # Sauvegarder
        with open(fichier_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Statistiques
        stats = {
            'categories_avant': total_avant,
            'categories_apres': len(categories_valides),
            'categories_supprimees': len(categories_supprimees),
            'categories_gardees': len(categories_valides),
            'taux_suppression': (len(categories_supprimees) / total_avant * 100) if total_avant > 0 else 0,
            'details_supprimees': categories_supprimees
        }

        print(f"\n✅ NETTOYAGE TERMINÉ:")
        print(f"   Catégories avant: {stats['categories_avant']}")
        print(f"   Catégories après: {stats['categories_apres']}")
        print(f"   Supprimées: {stats['categories_supprimees']} ({stats['taux_suppression']:.1f}%)")
        print(f"   Gardées: {stats['categories_gardees']}")

        # Afficher exemples supprimées
        if categories_supprimees:
            print(f"\n🗑️ EXEMPLES SUPPRIMÉS:")
            for i, item in enumerate(categories_supprimees[:10]):
                print(f"   {i+1}. {item['nom']} - {item['raison']}")
            if len(categories_supprimees) > 10:
                print(f"   ... et {len(categories_supprimees)-10} autres")

        return stats

    except Exception as e:
        print(f"❌ Erreur nettoyage: {e}")
        return {'erreur': str(e)}

def sauvegarder_categories_supprimees(categories_supprimees: List[Dict], fichier_sauvegarde: str):
    """
    Sauvegarder la liste des catégories supprimées pour audit

    Args:
        categories_supprimees (List[Dict]): Liste des catégories supprimées
        fichier_sauvegarde (str): Fichier où sauvegarder

    Description:
    Cette fonction sauvegarde la liste complète des catégories supprimées
    avec leurs raisons pour permettre un audit et éventuellement récupérer
    des catégories supprimées par erreur.
    """
    try:
        data_audit = {
            'metadata': {
                'timestamp_suppression': datetime.now().isoformat(),
                'total_supprimees': len(categories_supprimees),
                'description': 'Liste des catégories supprimées lors du nettoyage'
            },
            'categories_supprimees': categories_supprimees
        }

        with open(fichier_sauvegarde, 'w', encoding='utf-8') as f:
            json.dump(data_audit, f, indent=2, ensure_ascii=False)

        print(f"💾 Audit sauvegardé: {fichier_sauvegarde}")

    except Exception as e:
        print(f"❌ Erreur sauvegarde audit: {e}")

if __name__ == "__main__":
    # Test de la fonction
    fichier_test = "/Users/Simplon/Cours/workspacePython/Scraping/CATEGORIES/categories_amazon_completes.json"
    stats = nettoyer_fausses_categories(fichier_test)
    print(f"\nRésultats: {stats}")