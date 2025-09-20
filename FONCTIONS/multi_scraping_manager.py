#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODULE GESTIONNAIRE MULTI-SCRAPING
==================================

Fonctions pour gérer l'exécution parallèle des scrapers avec :
- Anti-détection (rotation User-Agent, pauses aléatoires)
- Gestion des timeouts et erreurs
- Surveillance des processus
- Optimisation des performances
"""

import os
import sys
import subprocess
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

def obtenir_variables_antidetection():
    """
    Génère les variables d'environnement pour l'anti-détection

    Returns:
        dict: Variables d'environnement configurées pour éviter la détection
    """
    env = os.environ.copy()

    # Configuration des délais aléatoires
    env['SCRAPER_DELAY_MIN'] = str(random.uniform(1, 3))
    env['SCRAPER_DELAY_MAX'] = str(random.uniform(3, 6))

    # Activation des méthodes anti-détection
    env['SCRAPER_ROTATION_AGENTS'] = '1'
    env['SCRAPER_RANDOM_HEADERS'] = '1'
    env['SCRAPER_STEALTH_MODE'] = '1'

    # Configuration des timeouts
    env['SCRAPER_TIMEOUT'] = str(random.randint(30, 60))

    return env

def executer_scraper_avec_antidetection(nom_fichier, timeout_minutes=10):
    """
    Exécute un scraper avec toutes les méthodes anti-détection activées

    Args:
        nom_fichier (str): Nom du fichier scraper à exécuter
        timeout_minutes (int): Timeout en minutes (défaut: 10)

    Returns:
        bool: True si succès, False si échec ou timeout
    """
    try:
        # Pause aléatoire avant démarrage pour éviter la détection
        pause_initiale = random.uniform(1, 5)
        print(f"⏳ {nom_fichier}: Pause anti-détection {pause_initiale:.1f}s")
        time.sleep(pause_initiale)

        # Configuration de l'environnement anti-détection
        env = obtenir_variables_antidetection()

        # Lancement du processus scraper
        process = subprocess.Popen(
            [sys.executable, nom_fichier],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=os.getcwd()
        )

        # Attendre avec timeout
        timeout_secondes = timeout_minutes * 60
        try:
            stdout, stderr = process.communicate(timeout=timeout_secondes)

            if process.returncode == 0:
                print(f"✅ {nom_fichier}: Terminé avec succès")
                return True
            else:
                print(f"⚠️  {nom_fichier}: Code retour {process.returncode}")
                if stderr and len(stderr.strip()) > 0:
                    # Afficher seulement les premières lignes d'erreur
                    erreur_courte = stderr[:300] + "..." if len(stderr) > 300 else stderr
                    print(f"   Erreur: {erreur_courte}")
                return False

        except subprocess.TimeoutExpired:
            print(f"⏰ {nom_fichier}: Timeout après {timeout_minutes} minutes - arrêt forcé")
            process.kill()
            process.wait()  # Nettoyer le processus
            return False

    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de {nom_fichier}: {e}")
        return False

def executer_scrapers_paralleles(liste_scrapers, max_workers=3, timeout_par_scraper=10):
    """
    Exécute plusieurs scrapers en parallèle avec gestion complète

    Args:
        liste_scrapers (list): Liste des fichiers scrapers à exécuter
        max_workers (int): Nombre maximum de scrapers simultanés
        timeout_par_scraper (int): Timeout en minutes par scraper

    Returns:
        dict: Résultats détaillés de l'exécution
    """
    resultats = {
        'reussis': 0,
        'echecs': 0,
        'timeouts': 0,
        'details': [],
        'duree_totale': 0,
        'scrapers_par_minute': 0
    }

    if not liste_scrapers:
        print("⚠️  Aucun scraper à exécuter")
        return resultats

    print(f"🔄 Lancement de {len(liste_scrapers)} scrapers en parallèle")
    print(f"👥 Utilisation de {max_workers} workers maximum")
    print(f"⏰ Timeout: {timeout_par_scraper} minutes par scraper")

    debut_execution = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Soumettre tous les scrapers avec des pauses échelonnées
        futures = {}

        for i, scraper in enumerate(liste_scrapers):
            # Pause échelonnée pour éviter la surcharge simultanée
            if i > 0:
                pause_echelonnee = random.uniform(0.5, 2)
                time.sleep(pause_echelonnee)

            future = executor.submit(
                executer_scraper_avec_antidetection,
                scraper,
                timeout_par_scraper
            )
            futures[future] = {
                'scraper': scraper,
                'debut': time.time()
            }

        # Collecter les résultats au fur et à mesure
        for future in as_completed(futures):
            info_scraper = futures[future]
            scraper = info_scraper['scraper']
            duree_scraper = time.time() - info_scraper['debut']

            try:
                succes = future.result()

                if succes:
                    resultats['reussis'] += 1
                    print(f"✅ {scraper} terminé avec succès ({duree_scraper:.1f}s)")
                else:
                    resultats['echecs'] += 1
                    print(f"❌ {scraper} a échoué ({duree_scraper:.1f}s)")

                # Enregistrer les détails
                resultats['details'].append({
                    'scraper': scraper,
                    'succes': succes,
                    'duree': duree_scraper,
                    'statut': 'succès' if succes else 'échec'
                })

            except Exception as e:
                resultats['echecs'] += 1
                print(f"❌ Erreur inattendue {scraper}: {e}")

                resultats['details'].append({
                    'scraper': scraper,
                    'succes': False,
                    'duree': duree_scraper,
                    'statut': 'erreur',
                    'erreur': str(e)
                })

    # Calculer les statistiques finales
    resultats['duree_totale'] = time.time() - debut_execution
    total_scrapers = len(liste_scrapers)

    if resultats['duree_totale'] > 0:
        resultats['scrapers_par_minute'] = (total_scrapers / resultats['duree_totale']) * 60

    return resultats

def diviser_scrapers_en_groupes(liste_scrapers, taille_groupe):
    """
    Divise une liste de scrapers en groupes pour traitement par lot

    Args:
        liste_scrapers (list): Liste complète des scrapers
        taille_groupe (int): Taille maximale de chaque groupe

    Returns:
        list: Liste de groupes (sous-listes)
    """
    groupes = []
    for i in range(0, len(liste_scrapers), taille_groupe):
        groupe = liste_scrapers[i:i + taille_groupe]
        groupes.append(groupe)

    return groupes

def executer_groupes_scrapers(liste_scrapers, max_workers=3, taille_groupe=None):
    """
    Exécute les scrapers par groupes avec pauses entre les groupes

    Args:
        liste_scrapers (list): Liste des scrapers à exécuter
        max_workers (int): Nombre de workers par groupe
        taille_groupe (int): Taille de chaque groupe (défaut: max_workers * 2)

    Returns:
        dict: Résultats consolidés de tous les groupes
    """
    if taille_groupe is None:
        taille_groupe = max_workers * 2

    groupes = diviser_scrapers_en_groupes(liste_scrapers, taille_groupe)

    resultats_globaux = {
        'reussis': 0,
        'echecs': 0,
        'timeouts': 0,
        'details': [],
        'duree_totale': 0,
        'nombre_groupes': len(groupes)
    }

    print(f"📦 Division en {len(groupes)} groupes de {taille_groupe} scrapers maximum")

    debut_global = time.time()

    for i, groupe in enumerate(groupes, 1):
        print(f"\n🔄 Groupe {i}/{len(groupes)} - {len(groupe)} scrapers")
        print("-" * 50)

        # Exécuter le groupe
        resultats_groupe = executer_scrapers_paralleles(
            groupe,
            max_workers=max_workers,
            timeout_par_scraper=10
        )

        # Consolider les résultats
        resultats_globaux['reussis'] += resultats_groupe['reussis']
        resultats_globaux['echecs'] += resultats_groupe['echecs']
        resultats_globaux['timeouts'] += resultats_groupe['timeouts']
        resultats_globaux['details'].extend(resultats_groupe['details'])

        print(f"✅ Groupe {i} terminé: {resultats_groupe['reussis']} succès, {resultats_groupe['echecs']} échecs")

        # Pause entre les groupes pour éviter la surcharge
        if i < len(groupes):
            pause_inter_groupe = random.uniform(10, 20)
            print(f"🔄 Pause inter-groupe: {pause_inter_groupe:.1f}s")
            time.sleep(pause_inter_groupe)

    resultats_globaux['duree_totale'] = time.time() - debut_global

    return resultats_globaux

def afficher_rapport_execution(resultats):
    """
    Affiche un rapport détaillé des résultats d'exécution

    Args:
        resultats (dict): Résultats retournés par les fonctions d'exécution
    """
    print(f"\n📊 RAPPORT D'EXÉCUTION DÉTAILLÉ")
    print("=" * 60)

    total = resultats['reussis'] + resultats['echecs']

    print(f"✅ Scrapers réussis: {resultats['reussis']}")
    print(f"❌ Scrapers échoués: {resultats['echecs']}")

    if 'timeouts' in resultats:
        print(f"⏰ Timeouts: {resultats['timeouts']}")

    if total > 0:
        taux_reussite = (resultats['reussis'] / total) * 100
        print(f"📈 Taux de réussite: {taux_reussite:.1f}%")

    print(f"⏱️  Durée totale: {resultats['duree_totale']:.2f} secondes")

    if 'scrapers_par_minute' in resultats and resultats['scrapers_par_minute'] > 0:
        print(f"⚡ Vitesse: {resultats['scrapers_par_minute']:.1f} scrapers/minute")

    # Afficher les détails des échecs s'il y en a
    echecs = [d for d in resultats['details'] if not d['succes']]
    if echecs:
        print(f"\n❌ DÉTAIL DES ÉCHECS ({len(echecs)}):")
        for echec in echecs[:5]:  # Limiter à 5 pour éviter le spam
            print(f"   • {echec['scraper']}: {echec.get('statut', 'échec')}")
        if len(echecs) > 5:
            print(f"   ... et {len(echecs)-5} autres échecs")

    print("=" * 60)