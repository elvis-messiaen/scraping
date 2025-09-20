#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LANCEUR DE SCRAPERS AMAZON - CATÉGORIES ET SOUS-CATÉGORIES UNIQUEMENT
====================================================================

Lance uniquement les scrapers de catégories et sous-catégories :
1. Estimation du contenu Amazon
2. Scraping des catégories principales
3. Scraping des sous-catégories

ARCHITECTURE:
- Toutes les fonctions sont dans le module FONCTIONS/
- Ce fichier ne fait qu'appeler les fonctions appropriées
- Pour scraper les livres, utiliser : lancer_scrapers_livres.py
"""

import os
import sys
import time
from pathlib import Path

# Ajouter le répertoire parent au path pour importer le module FONCTIONS
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import des modules de fonctions
from FONCTIONS import estimateur_contenu
from FONCTIONS import multi_scraping_manager
from FONCTIONS import gestion_scrapers

def executer_scraper(nom_fichier):
    """
    Wrapper pour l'exécution d'un scraper SANS timeout forcé
    Utilise gestion_scrapers pour laisser le scraper se terminer naturellement
    """
    print(f"🚀 Lancement de {nom_fichier}...")
    resultat = gestion_scrapers.executer_scraper_sequentiel(nom_fichier, afficher_logs=True)
    if resultat['succes']:
        print(f"✅ {nom_fichier} terminé avec succès")
        return True
    else:
        print(f"❌ {nom_fichier} terminé avec erreur")
        return False

def executer_scraper_avec_timeout(nom_fichier, timeout_seconds):
    """
    Wrapper pour l'exécution d'un scraper AVEC timeout
    """
    import subprocess
    import signal

    print(f"🚀 Lancement de {nom_fichier} (timeout: {timeout_seconds}s)...")

    try:
        # Lancer le scraper avec timeout
        result = subprocess.run(
            [sys.executable, nom_fichier],
            timeout=timeout_seconds,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✅ {nom_fichier} terminé avec succès")
            return True
        else:
            print(f"❌ {nom_fichier} terminé avec erreur (code: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏰ {nom_fichier} timeout après {timeout_seconds}s - ARRÊT FORCÉ")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de {nom_fichier}: {e}")
        return False

def main():
    """Fonction principale - lance tous les scrapers dans l'ordre avec estimations et multi-scraping"""

    print("🚀 LANCEUR AUTOMATIQUE DE SCRAPERS AMAZON")
    print("=" * 60)
    print("✨ Fonctionnalités avancées :")
    print("  • Estimation du contenu Amazon")
    print("  • Multi-scraping avec anti-détection")
    print("  • Pauses intelligentes et rotation des agents")
    print("  • Surveillance en temps réel")
    print("=" * 60)

    # PHASE 1: Estimation du contenu
    print("\n🔍 PHASE 1: ESTIMATION DU CONTENU")
    estimation = estimateur_contenu.generer_rapport_estimation()

    # Configuration automatique du mode turbo maximum
    import multiprocessing

    # Déterminer le nombre maximum de workers possible
    cpu_count = multiprocessing.cpu_count()
    max_workers = min(cpu_count * 2, 10)  # Max 10 workers pour éviter la surcharge Amazon
    mode_nom = "Turbo Maximum"

    print(f"\n⚡ MODE TURBO MAXIMUM ACTIVÉ AUTOMATIQUEMENT")
    print(f"🔧 {max_workers} scrapers simultanés (détecté: {cpu_count} CPU)")

    # Lancement automatique
    print(f"\n🚀 LANCEMENT AUTOMATIQUE EN MODE TURBO:")
    print(f"   📂 {estimation['categories_principales']} catégories principales")
    print(f"   📁 {estimation['sous_categories']} sous-catégories")
    print(f"   📚 ~{estimation['estimation_livres']:,} livres estimés")
    print(f"   ⏱️  ~{estimation['temps_estime_turbo']:.0f} minutes estimées (turbo)")
    print(f"   🔧 Mode: {mode_nom} ({max_workers} workers)")
    print(f"\n⚡ DÉMARRAGE IMMÉDIAT...")

    # PHASE 2: Exécution des scrapers
    debut_total = time.time()
    scrapers_reussis = 0
    scrapers_echecs = 0

    # Vérifier l'environnement avant de commencer
    etat_env = gestion_scrapers.verifier_environnement_scrapers()
    if not etat_env['pret']:
        print("❌ Environnement non prêt:")
        for probleme in etat_env['problemes']:
            print(f"   • {probleme}")
        return

    try:
        print(f"\n🚀 PHASE 2: EXÉCUTION EN MODE {mode_nom.upper()}")
        print("=" * 60)

        # ÉTAPE 1: Catégories principales (OBLIGATOIRE - SANS TIMEOUT)
        print("\n📂 ÉTAPE 1/2: CATÉGORIES PRINCIPALES")
        print("-" * 40)

        if os.path.exists("scraper_categories_principales.py"):
            print("🔍 Détection des catégories principales Amazon...")
            print("⚠️  ATTENTION: Attente obligatoire de la fin de cette étape")
            if executer_scraper("scraper_categories_principales.py"):
                scrapers_reussis += 1
                print("✅ Catégories principales détectées avec succès")
            else:
                scrapers_echecs += 1
                print("❌ ÉCHEC catégories principales - ARRÊT")
                return
        else:
            print("⚠️  scraper_categories_principales.py non trouvé")

        # ÉTAPE 2: Sous-catégories (OBLIGATOIRE - SANS TIMEOUT)
        print("\n📁 ÉTAPE 2/2: SOUS-CATÉGORIES")
        print("-" * 40)

        if os.path.exists("scraper_sous_categories.py"):
            print("🔍 Détection des sous-catégories Amazon...")
            print("⚠️  ATTENTION: Attente obligatoire de la fin de cette étape")
            if executer_scraper("scraper_sous_categories.py"):
                scrapers_reussis += 1
                print("✅ Sous-catégories détectées avec succès")
            else:
                scrapers_echecs += 1
                print("❌ ÉCHEC sous-catégories - ARRÊT")
                return
        else:
            print("⚠️  scraper_sous_categories.py non trouvé")

        print("\n✅ CATÉGORIES ET SOUS-CATÉGORIES TERMINÉES")
        print("-" * 50)
        print("📋 Pour scraper les livres, utilisez : python3 lancer_scrapers_livres.py")

    except KeyboardInterrupt:
        print("\n\n🛑 INTERRUPTION DÉTECTÉE")
        print("Arrêt de la séquence en cours...")

    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")

    finally:
        # PHASE 3: Rapport final détaillé
        duree_totale = time.time() - debut_total

        print("\n" + "=" * 80)
        print("📊 RAPPORT FINAL DÉTAILLÉ")
        print("=" * 80)

        # Statistiques de performance
        print(f"⏱️  Durée totale: {duree_totale:.2f} secondes ({duree_totale/60:.1f} minutes)")
        print(f"✅ Scrapers réussis: {scrapers_reussis}")
        print(f"❌ Scrapers échoués: {scrapers_echecs}")

        total_scrapers = scrapers_reussis + scrapers_echecs
        if total_scrapers > 0:
            taux_reussite = (scrapers_reussis / total_scrapers) * 100
            print(f"📈 Taux de réussite: {taux_reussite:.1f}%")

            vitesse = total_scrapers / (duree_totale / 60) if duree_totale > 0 else 0
            print(f"⚡ Vitesse moyenne: {vitesse:.1f} scrapers/minute")

        # Vérification des résultats
        print(f"\n📁 VÉRIFICATION DES FICHIERS GÉNÉRÉS:")

        # Vérifier les dossiers LIVRES
        dossier_livres = Path("../LIVRES")
        if dossier_livres.exists():
            nb_dossiers = len([d for d in dossier_livres.iterdir() if d.is_dir()])
            print(f"   📂 {nb_dossiers} dossiers de catégories créés")

            # Compter les fichiers JSON
            nb_json = len(list(dossier_livres.glob("**/*.json")))
            print(f"   📄 {nb_json} fichiers de données générés")
        else:
            print("   ⚠️  Dossier LIVRES non trouvé")

        print("=" * 80)
        print("🏁 SÉQUENCE TERMINÉE")
        print("=" * 80)

if __name__ == "__main__":
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists("scraper_categories_principales.py") and not os.path.exists("scraper_sous_categories.py"):
        print("❌ Erreur: Fichiers scrapers principaux non trouvés")
        print("Assurez-vous d'être dans le répertoire SCRAPERS")
        sys.exit(1)

    main()