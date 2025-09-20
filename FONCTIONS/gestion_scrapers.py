#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MODULE GESTION DES SCRAPERS
===========================

Fonctions utilitaires pour la gestion des scrapers :
- Détection automatique des scrapers disponibles
- Exécution séquentielle avec logs temps réel
- Validation des fichiers scrapers
- Gestion des rapports et statistiques
"""

import os
import sys
import subprocess
import glob
import time
from pathlib import Path

def obtenir_liste_scrapers_disponibles():
    """
    Détecte automatiquement tous les scrapers disponibles dans le répertoire

    Returns:
        dict: Dictionnaire avec les listes de scrapers organisées par type
    """
    scrapers = {
        'principaux': [],
        'individuels': [],
        'total': 0
    }

    # Scrapers principaux (ordre spécifique)
    scrapers_principaux_ordre = [
        'scraper_categories_principales.py',
        'scraper_sous_categories.py'
    ]

    for scraper_principal in scrapers_principaux_ordre:
        if os.path.exists(scraper_principal):
            scrapers['principaux'].append(scraper_principal)

    # Scrapers individuels (tous les autres scraper_*.py)
    for fichier in sorted(glob.glob("scraper_*.py")):
        # Exclure les scrapers principaux et les fichiers de test
        if (fichier not in scrapers_principaux_ordre and
            not fichier.startswith('scraper_test') and
            not fichier.endswith('_test.py')):
            scrapers['individuels'].append(fichier)

    scrapers['total'] = len(scrapers['principaux']) + len(scrapers['individuels'])

    return scrapers

def valider_scraper(chemin_scraper):
    """
    Valide qu'un fichier scraper est fonctionnel et bien formé

    Args:
        chemin_scraper (str): Chemin vers le fichier scraper à valider

    Returns:
        dict: Résultat de la validation avec détails
    """
    resultat = {
        'valide': False,
        'erreurs': [],
        'avertissements': [],
        'taille_fichier': 0
    }

    try:
        # Vérifier l'existence du fichier
        if not os.path.exists(chemin_scraper):
            resultat['erreurs'].append(f"Fichier inexistant: {chemin_scraper}")
            return resultat

        # Vérifier la taille du fichier
        taille = os.path.getsize(chemin_scraper)
        resultat['taille_fichier'] = taille

        if taille == 0:
            resultat['erreurs'].append("Fichier vide")
            return resultat

        if taille < 100:
            resultat['avertissements'].append("Fichier très petit (< 100 bytes)")

        # Vérifier le contenu du fichier
        with open(chemin_scraper, 'r', encoding='utf-8') as f:
            contenu = f.read()

            # Vérifications de base
            if not contenu.strip():
                resultat['erreurs'].append("Contenu vide")
                return resultat

            # Vérifier la présence d'imports essentiels
            if 'import' not in contenu:
                resultat['avertissements'].append("Aucun import détecté")

            # Vérifier la présence de fonctions
            if 'def ' not in contenu:
                resultat['avertissements'].append("Aucune fonction détectée")

            # Vérifier la syntaxe Python basique
            if not contenu.startswith('#'):
                resultat['avertissements'].append("Pas de shebang ou commentaire initial")

        # Si aucune erreur critique, marquer comme valide
        if not resultat['erreurs']:
            resultat['valide'] = True

    except Exception as e:
        resultat['erreurs'].append(f"Erreur de validation: {e}")

    return resultat

def executer_scraper_sequentiel(nom_fichier, afficher_logs=True):
    """
    Exécute un scraper en mode séquentiel avec affichage des logs en temps réel

    Args:
        nom_fichier (str): Nom du fichier scraper à exécuter
        afficher_logs (bool): Afficher les logs en temps réel (défaut: True)

    Returns:
        dict: Résultats de l'exécution avec détails
    """
    resultat = {
        'succes': False,
        'code_retour': None,
        'duree': 0,
        'logs_stdout': '',
        'logs_stderr': '',
        'lignes_output': 0
    }

    try:
        if afficher_logs:
            print(f"\n🚀 Lancement de {nom_fichier}...")
            print("=" * 60)

        debut = time.time()

        # Validation préalable du scraper
        validation = valider_scraper(nom_fichier)
        if not validation['valide']:
            print(f"❌ Validation échouée pour {nom_fichier}:")
            for erreur in validation['erreurs']:
                print(f"   • {erreur}")
            return resultat

        # Exécution du scraper
        process = subprocess.Popen(
            [sys.executable, nom_fichier],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Lecture des logs en temps réel si demandé
        if afficher_logs:
            logs_stdout = []
            logs_stderr = []

            # Lire stdout en temps réel
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    ligne_nettoyee = output.strip()
                    print(ligne_nettoyee)
                    logs_stdout.append(ligne_nettoyee)
                    resultat['lignes_output'] += 1

            # Lire stderr s'il y en a
            stderr_output = process.stderr.read()
            if stderr_output:
                logs_stderr.append(stderr_output.strip())

            resultat['logs_stdout'] = '\n'.join(logs_stdout)
            resultat['logs_stderr'] = '\n'.join(logs_stderr)

        else:
            # Exécution silencieuse
            stdout, stderr = process.communicate()
            resultat['logs_stdout'] = stdout
            resultat['logs_stderr'] = stderr
            resultat['lignes_output'] = len(stdout.splitlines()) if stdout else 0

        # Calculer la durée et le code de retour
        resultat['duree'] = time.time() - debut
        resultat['code_retour'] = process.returncode

        # Déterminer le succès
        if process.returncode == 0:
            resultat['succes'] = True
            if afficher_logs:
                print(f"✅ {nom_fichier} terminé avec succès ({resultat['duree']:.2f}s)")
        else:
            if afficher_logs:
                print(f"❌ {nom_fichier} terminé avec erreur (code: {process.returncode})")
                if resultat['logs_stderr']:
                    print(f"   Erreur: {resultat['logs_stderr'][:200]}...")

    except Exception as e:
        resultat['duree'] = time.time() - debut if 'debut' in locals() else 0
        if afficher_logs:
            print(f"❌ Erreur lors de l'exécution de {nom_fichier}: {e}")

    return resultat

def executer_sequence_scrapers(liste_scrapers, pause_entre_scrapers=2):
    """
    Exécute une séquence de scrapers avec pauses et gestion d'erreurs

    Args:
        liste_scrapers (list): Liste des scrapers à exécuter dans l'ordre
        pause_entre_scrapers (int): Pause en secondes entre chaque scraper

    Returns:
        dict: Résultats consolidés de toute la séquence
    """
    resultats = {
        'scrapers_reussis': 0,
        'scrapers_echecs': 0,
        'duree_totale': 0,
        'details': [],
        'premiere_erreur': None
    }

    if not liste_scrapers:
        return resultats

    print(f"🔄 Exécution séquentielle de {len(liste_scrapers)} scrapers")
    print(f"⏳ Pause entre scrapers: {pause_entre_scrapers}s")

    debut_sequence = time.time()

    for i, scraper in enumerate(liste_scrapers, 1):
        print(f"\n[{i}/{len(liste_scrapers)}] 📖 Traitement de {scraper}")

        # Exécuter le scraper
        resultat_scraper = executer_scraper_sequentiel(scraper)

        # Enregistrer les résultats
        if resultat_scraper['succes']:
            resultats['scrapers_reussis'] += 1
        else:
            resultats['scrapers_echecs'] += 1
            if resultats['premiere_erreur'] is None:
                resultats['premiere_erreur'] = {
                    'scraper': scraper,
                    'erreur': resultat_scraper['logs_stderr']
                }

        resultats['details'].append({
            'scraper': scraper,
            'position': i,
            'succes': resultat_scraper['succes'],
            'duree': resultat_scraper['duree'],
            'code_retour': resultat_scraper['code_retour'],
            'lignes_output': resultat_scraper['lignes_output']
        })

        # Pause entre les scrapers (sauf pour le dernier)
        if i < len(liste_scrapers) and pause_entre_scrapers > 0:
            print(f"⏳ Pause de {pause_entre_scrapers} secondes...")
            time.sleep(pause_entre_scrapers)

    resultats['duree_totale'] = time.time() - debut_sequence

    return resultats

def generer_rapport_scrapers(resultats):
    """
    Génère un rapport détaillé des résultats d'exécution

    Args:
        resultats (dict): Résultats retournés par executer_sequence_scrapers
    """
    print(f"\n📊 RAPPORT D'EXÉCUTION SÉQUENTIELLE")
    print("=" * 70)

    total = resultats['scrapers_reussis'] + resultats['scrapers_echecs']

    print(f"✅ Scrapers réussis: {resultats['scrapers_reussis']}")
    print(f"❌ Scrapers échoués: {resultats['scrapers_echecs']}")

    if total > 0:
        taux_reussite = (resultats['scrapers_reussis'] / total) * 100
        print(f"📈 Taux de réussite: {taux_reussite:.1f}%")

        vitesse = total / (resultats['duree_totale'] / 60) if resultats['duree_totale'] > 0 else 0
        print(f"⚡ Vitesse moyenne: {vitesse:.1f} scrapers/minute")

    print(f"⏱️  Durée totale: {resultats['duree_totale']:.2f} secondes ({resultats['duree_totale']/60:.1f} minutes)")

    # Détails des performances
    if resultats['details']:
        print(f"\n📋 DÉTAIL DES PERFORMANCES:")
        print("-" * 50)

        for detail in resultats['details']:
            statut = "✅" if detail['succes'] else "❌"
            print(f"{statut} {detail['scraper']:<40} {detail['duree']:>6.1f}s {detail['lignes_output']:>4d} lignes")

    # Première erreur rencontrée
    if resultats['premiere_erreur']:
        print(f"\n❌ PREMIÈRE ERREUR RENCONTRÉE:")
        print(f"   Scraper: {resultats['premiere_erreur']['scraper']}")
        erreur = resultats['premiere_erreur']['erreur']
        if erreur:
            erreur_courte = erreur[:200] + "..." if len(erreur) > 200 else erreur
            print(f"   Erreur: {erreur_courte}")

    print("=" * 70)

def verifier_environnement_scrapers():
    """
    Vérifie que l'environnement est prêt pour l'exécution des scrapers

    Returns:
        dict: État de l'environnement avec recommandations
    """
    etat = {
        'pret': True,
        'problemes': [],
        'avertissements': [],
        'recommandations': []
    }

    # Vérifier le répertoire de travail
    if not os.getcwd().endswith('SCRAPERS'):
        etat['problemes'].append("Pas dans le répertoire SCRAPERS")
        etat['pret'] = False

    # Vérifier les dossiers nécessaires
    dossiers_requis = ['../CATEGORIES', '../LIVRES']
    for dossier in dossiers_requis:
        if not os.path.exists(dossier):
            etat['avertissements'].append(f"Dossier manquant: {dossier}")
            etat['recommandations'].append(f"Créer le dossier {dossier}")

    # Vérifier les scrapers principaux
    scrapers_principaux = ['scraper_categories_principales.py', 'scraper_sous_categories.py']
    for scraper in scrapers_principaux:
        if not os.path.exists(scraper):
            etat['problemes'].append(f"Scraper principal manquant: {scraper}")
            etat['pret'] = False

    # Vérifier Python et modules
    try:
        import requests
        import json
    except ImportError as e:
        etat['problemes'].append(f"Module Python manquant: {e}")
        etat['pret'] = False

    return etat