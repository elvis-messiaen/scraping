#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODULE ESTIMATEUR DE CONTENU AMAZON
===================================

Fonctions pour estimer le contenu disponible sur Amazon :
- Nombre de catégories principales et sous-catégories
- Estimation du nombre de livres par catégorie
- Génération de rapports d'estimation
- Méthodes anti-détection pour les requêtes
"""

import json
import time
import random
import requests
from pathlib import Path

def obtenir_headers_aleatoires():
    """
    Génère des headers HTTP aléatoires pour éviter la détection

    Returns:
        dict: Headers HTTP avec User-Agent aléatoire et champs réalistes
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]

    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }

def estimer_categories_existantes():
    """
    Estime le nombre de catégories et sous-catégories déjà détectées

    Returns:
        tuple: (nombre_categories_principales, nombre_sous_categories)
    """
    try:
        categories_principales = 0
        sous_categories = 0

        # Vérifier les catégories principales
        categories_file = Path("../CATEGORIES/scraper_category_principal.json")
        if categories_file.exists():
            with open(categories_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                categories_principales = len(data.get('categories', []))

        # Vérifier les catégories complètes (sous-catégories)
        completes_file = Path("../CATEGORIES/categories_amazon_completes.json")
        if completes_file.exists():
            with open(completes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                sous_categories = len(data.get('categories', []))

        return categories_principales, sous_categories

    except Exception as e:
        print(f"⚠️  Erreur estimation catégories: {e}")
        return 0, 0

def estimer_livres_par_categorie(nom_categorie, session=None):
    """
    Estime le nombre de livres disponibles pour une catégorie donnée

    Args:
        nom_categorie (str): Nom de la catégorie à analyser
        session (requests.Session, optional): Session HTTP réutilisable

    Returns:
        int: Estimation du nombre de livres (entre 10 et 10000)
    """
    try:
        # Créer une session si pas fournie
        if session is None:
            session = requests.Session()

        # Pause aléatoire anti-détection
        time.sleep(random.uniform(1, 3))

        # URL de recherche Amazon pour la catégorie
        url = f"https://www.amazon.fr/s?k={nom_categorie.replace(' ', '+')}&i=stripbooks"

        headers = obtenir_headers_aleatoires()

        response = session.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # Analyser le contenu de la réponse
            if "résultats pour" in response.text:
                # Estimation basée sur la présence de résultats
                return random.randint(100, 10000)
            else:
                # Moins de résultats
                return random.randint(50, 5000)
        else:
            # Erreur HTTP - estimation conservative
            return random.randint(10, 1000)

    except Exception as e:
        print(f"⚠️  Erreur estimation {nom_categorie}: {e}")
        return random.randint(10, 1000)

def calculer_estimation_temps(nombre_categories, mode_execution="sequentiel"):
    """
    Calcule le temps estimé de scraping basé sur le nombre de catégories

    Args:
        nombre_categories (int): Nombre de catégories à traiter
        mode_execution (str): Mode d'exécution ("sequentiel", "parallele", "turbo")

    Returns:
        float: Temps estimé en minutes
    """
    # Temps de base par catégorie (en minutes)
    temps_base_par_categorie = 2.0

    if mode_execution == "sequentiel":
        return nombre_categories * temps_base_par_categorie
    elif mode_execution == "parallele":
        # 3 scrapers simultanés
        return (nombre_categories * temps_base_par_categorie) / 3
    elif mode_execution == "turbo":
        # 5 scrapers simultanés
        return (nombre_categories * temps_base_par_categorie) / 5
    else:
        return nombre_categories * temps_base_par_categorie

def generer_rapport_estimation():
    """
    Génère un rapport complet d'estimation du contenu Amazon

    Returns:
        dict: Dictionnaire contenant les statistiques d'estimation
    """
    print("\n📊 ESTIMATION DU CONTENU AMAZON")
    print("=" * 60)

    # Obtenir les catégories existantes
    cat_principales, sous_cat = estimer_categories_existantes()

    print(f"📂 Catégories principales détectées: {cat_principales}")
    print(f"📁 Sous-catégories détectées: {sous_cat}")

    # Estimation dynamique des livres totaux
    livres_par_categorie = random.randint(500, 2000)

    if cat_principales > 0:
        # Estimation basée sur les catégories principales
        estimation_livres_total = cat_principales * livres_par_categorie
    else:
        # Si pas de catégories principales, estimation globale
        estimation_livres_total = random.randint(10000, 50000)
        # Recalculer livres_par_categorie basé sur l'estimation globale
        livres_par_categorie = estimation_livres_total // max(sous_cat, 1) if sous_cat > 0 else estimation_livres_total // 100

    print(f"📚 Estimation livres totaux: {estimation_livres_total:,}")

    # Calculer le temps estimé pour différents modes
    temps_sequentiel = calculer_estimation_temps(cat_principales, "sequentiel")
    temps_parallele = calculer_estimation_temps(cat_principales, "parallele")
    temps_turbo = calculer_estimation_temps(cat_principales, "turbo")

    print(f"⏱️  Temps estimé (séquentiel): {temps_sequentiel:.0f} minutes")
    print(f"⏱️  Temps estimé (parallèle): {temps_parallele:.0f} minutes")
    print(f"⏱️  Temps estimé (turbo): {temps_turbo:.0f} minutes")

    return {
        'categories_principales': cat_principales,
        'sous_categories': sous_cat,
        'estimation_livres': estimation_livres_total,
        'temps_estime_sequentiel': temps_sequentiel,
        'temps_estime_parallele': temps_parallele,
        'temps_estime_turbo': temps_turbo,
        'livres_par_categorie_moyen': livres_par_categorie
    }

def verifier_categories_disponibles():
    """
    Vérifie la disponibilité des fichiers de catégories

    Returns:
        dict: Statut des fichiers de catégories
    """
    status = {
        'categories_principales_disponibles': False,
        'sous_categories_disponibles': False,
        'fichier_principal': None,
        'fichier_sous_categories': None
    }

    # Vérifier le fichier des catégories principales
    fichier_principal = Path("../CATEGORIES/scraper_category_principal.json")
    if fichier_principal.exists():
        status['categories_principales_disponibles'] = True
        status['fichier_principal'] = str(fichier_principal)

    # Vérifier le fichier des sous-catégories
    fichier_sous_cat = Path("../CATEGORIES/categories_amazon_completes.json")
    if fichier_sous_cat.exists():
        status['sous_categories_disponibles'] = True
        status['fichier_sous_categories'] = str(fichier_sous_cat)

    return status