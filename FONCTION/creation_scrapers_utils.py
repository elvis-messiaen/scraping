#!/usr/bin/env python3
"""
UTILITAIRES CRÉATION SCRAPERS ET DOSSIERS
==========================================
Fonctions pour créer automatiquement les dossiers LIVRES et les scrapers individuels
pour chaque sous-catégorie détectée.
"""

import os
import re
import json
from datetime import datetime
from typing import Tuple, Optional


def nettoyer_nom_fichier(nom: str) -> str:
    """
    Nettoyer un nom de catégorie pour créer un nom de fichier/dossier valide

    Args:
        nom (str): Nom de catégorie à nettoyer (ex: "Romans et polars")

    Returns:
        str: Nom nettoyé (ex: "romans_et_polars")

    Description:
    - Supprime les caractères spéciaux
    - Remplace espaces et tirets par des underscores
    - Convertit en minuscules
    - Supprime les underscores en début/fin
    """
    if not nom:
        return "inconnu"

    # Remplacer les caractères spéciaux par rien
    nom_clean = re.sub(r'[^\w\s\-àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]', '', nom.lower())

    # Remplacer espaces et tirets multiples par un seul underscore
    nom_clean = re.sub(r'[-\s]+', '_', nom_clean)

    # Supprimer underscores en début/fin
    nom_clean = nom_clean.strip('_')

    # Si vide, retourner un nom par défaut
    return nom_clean if nom_clean else "categorie_inconnue"


def creer_dossier_livres(nom_categorie: str, dossier_base_livres: str) -> str:
    """
    Créer le dossier LIVRES pour une catégorie

    Args:
        nom_categorie (str): Nom de la catégorie
        dossier_base_livres (str): Chemin vers le dossier LIVRES principal

    Returns:
        str: Chemin du dossier créé

    Description:
    Crée la structure :
    LIVRES/
    └── nom_categorie_clean/
        ├── nom_categorie_clean_livres.json
        ├── nom_categorie_clean_livres.csv
        └── nom_categorie_clean_progres.json
    """
    nom_propre = nettoyer_nom_fichier(nom_categorie)
    dossier_categorie = os.path.join(dossier_base_livres, nom_propre)

    # Créer le dossier principal
    os.makedirs(dossier_categorie, exist_ok=True)

    # Créer les fichiers de base vides s'ils n'existent pas
    fichier_json = os.path.join(dossier_categorie, f"{nom_propre}_livres.json")
    fichier_csv = os.path.join(dossier_categorie, f"{nom_propre}_livres.csv")
    fichier_progres = os.path.join(dossier_categorie, f"{nom_propre}_progres.json")

    # Initialiser le JSON s'il n'existe pas
    if not os.path.exists(fichier_json):
        donnees_init = {
            "metadata": {
                "nom_categorie": nom_categorie,
                "nom_fichier": nom_propre,
                "date_creation": datetime.now().isoformat(),
                "total_livres": 0,
                "description": f"Livres de la catégorie {nom_categorie}"
            },
            "livres": []
        }

        with open(fichier_json, 'w', encoding='utf-8') as f:
            json.dump(donnees_init, f, indent=2, ensure_ascii=False)

    # Initialiser le progrès s'il n'existe pas
    if not os.path.exists(fichier_progres):
        progres_init = {
            "page_actuelle": 1,
            "total_livres_scrapes": 0,
            "total_amazon_estime": 0,
            "derniere_sauvegarde": datetime.now().isoformat(),
            "pages_vides_consecutives": 0,
            "urls_traitees_count": 0,
            "statut": "initialisé"
        }

        with open(fichier_progres, 'w', encoding='utf-8') as f:
            json.dump(progres_init, f, indent=2, ensure_ascii=False)

    return dossier_categorie


def verifier_dossier_livres_existe(nom_categorie: str, dossier_base_livres: str) -> bool:
    """
    Vérifier si le dossier LIVRES existe déjà pour une catégorie

    Args:
        nom_categorie (str): Nom de la catégorie
        dossier_base_livres (str): Chemin vers le dossier LIVRES principal

    Returns:
        bool: True si le dossier existe, False sinon
    """
    nom_propre = nettoyer_nom_fichier(nom_categorie)
    dossier_categorie = os.path.join(dossier_base_livres, nom_propre)
    return os.path.exists(dossier_categorie)


def generer_template_scraper(nom_categorie: str, url_categorie: str = "") -> str:
    """
    Générer le contenu du template scraper v3.0 pour une catégorie

    Args:
        nom_categorie (str): Nom de la catégorie
        url_categorie (str): URL de la catégorie (optionnel)

    Returns:
        str: Contenu du fichier scraper v3.0 uniforme
    """
    nom_propre = nettoyer_nom_fichier(nom_categorie)
    nom_classe = nom_categorie.replace(' ', '').replace('-', '').replace(',', '')
    nom_classe = re.sub(r'[^\w]', '', nom_classe)

    template = f'''#!/usr/bin/env python3
"""
SCRAPER AMAZON AMÉLIORÉ V3.0 - {nom_categorie.upper()}
{'=' * (40 + len(nom_categorie))}
Catégorie: {nom_categorie}
URL: {url_categorie}

FONCTIONNALITÉS COMPLÈTES V3.0:
✅ Anti-doublon intelligent (ASIN/ISBN/Hash)
✅ Mise à jour automatique du fichier JSON
✅ Extraction complète de TOUS les champs Amazon
✅ Sauvegarde avec backup automatique
✅ Métriques de performance détaillées
✅ Gestion d'erreurs robuste
✅ Fusion intelligente des données
✅ Structure de fichiers organisée
✅ Historique des mises à jour

Généré automatiquement par le système v3.0
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent pour importer le modèle
sys.path.insert(0, str(Path(__file__).parent.parent))

from FONCTION.modele_scraper_ameliore import ScraperAmazonAmeliore

class ScraperAmazon{nom_classe}(ScraperAmazonAmeliore):
    """
    Scraper spécialisé pour: {nom_categorie}

    Hérite de toutes les fonctionnalités avancées du modèle v3.0:
    - Anti-doublon basé sur ASIN/ISBN/Hash
    - Mise à jour automatique sans créer de doublons
    - Extraction de 50+ champs par livre
    - Backups automatiques avant chaque mise à jour
    - Métriques détaillées de performance
    - Gestion d'erreurs robuste avec retry
    - Structure de dossiers organisée
    """

    def __init__(self, mode_forcee: bool = False):
        """
        Initialise le scraper v3.0 pour {nom_categorie}

        Args:
            mode_forcee (bool): Force la mise à jour de TOUS les livres existants (défaut: False)
        """
        super().__init__(
            nom_categorie="{nom_categorie}",
            url_categorie="{url_categorie}",
            mode_mise_a_jour_forcee=mode_forcee
        )

        # Configuration spécifique si nécessaire
        # self.delay_min = 2.0  # Délai minimum entre requêtes
        # self.delay_max = 4.0  # Délai maximum entre requêtes

def main(mode_forcee: bool = False):
    """
    Fonction principale - Lance le scraping complet avec toutes les fonctionnalités v3.0

    Args:
        mode_forcee (bool): Active le mode de mise à jour forcée de TOUS les livres
    """
    scraper = ScraperAmazon{nom_classe}(mode_forcee=mode_forcee)

    print(f"🚀 Démarrage du scraper v3.0 pour: {nom_categorie}")
    print("🔧 Fonctionnalités actives:")
    print("   ✅ Anti-doublon intelligent")
    print("   ✅ Mise à jour automatique JSON")
    print("   ✅ Extraction complète (50+ champs)")
    print("   ✅ Backup automatique")
    print("   ✅ Métriques détaillées")

    # Lancement avec toutes les fonctionnalités v3.0
    total_nouveaux = scraper.run_complet()

    if total_nouveaux > 0:
        print(f"\\n✅ SUCCÈS: {{total_nouveaux}} nouveaux livres ajoutés pour {nom_categorie}")
    else:
        print(f"\\n✅ TERMINÉ: Base de données à jour pour {nom_categorie}")

if __name__ == "__main__":
    main()
'''

    return template


def creer_scraper_automatique(nom_categorie: str, url_categorie: str, dossier_scrapers: str) -> Optional[str]:
    """
    Créer automatiquement un fichier scraper pour une catégorie

    Args:
        nom_categorie (str): Nom de la catégorie
        url_categorie (str): URL de la catégorie
        dossier_scrapers (str): Chemin vers le dossier SCRAPERS

    Returns:
        Optional[str]: Chemin du fichier scraper créé, None si erreur

    Description:
    Crée un fichier scraper_nom_categorie.py dans le dossier SCRAPERS
    avec un template fonctionnel prêt à utiliser.
    """
    nom_propre = nettoyer_nom_fichier(nom_categorie)
    fichier_scraper = os.path.join(dossier_scrapers, f"scraper_{nom_propre}.py")

    # Si le fichier existe déjà, ne pas l'écraser
    if os.path.exists(fichier_scraper):
        print(f"📄 Scraper existe déjà: {os.path.basename(fichier_scraper)}")
        return fichier_scraper

    try:
        # Générer le contenu du scraper
        contenu_scraper = generer_template_scraper(nom_categorie, url_categorie)

        # Écrire le fichier
        with open(fichier_scraper, 'w', encoding='utf-8') as f:
            f.write(contenu_scraper)

        # Rendre le fichier exécutable (Linux/Mac)
        try:
            os.chmod(fichier_scraper, 0o755)
        except:
            pass  # Ignore les erreurs de chmod sur Windows

        print(f"📄 Scraper créé: {os.path.basename(fichier_scraper)}")
        return fichier_scraper

    except Exception as e:
        print(f"❌ Erreur création scraper {nom_categorie}: {e}")
        return None


def traiter_creation_automatique_complete(fichier_categories_json: str, dossier_scrapers: str, dossier_base_livres: str) -> dict:
    """
    Lit le JSON des catégories principales et crée les scrapers + dossiers LIVRES pour chaque catégorie

    Args:
        fichier_categories_json (str): Chemin vers le fichier JSON des catégories principales
        dossier_scrapers (str): Chemin vers le dossier SCRAPERS
        dossier_base_livres (str): Chemin vers le dossier LIVRES principal

    Returns:
        dict: Statistiques de création {'scrapers_crees': X, 'livres_crees': Y, 'erreurs': Z}

    Description:
    Fonction complète qui :
    1. Lit le fichier JSON des catégories principales
    2. Pour chaque catégorie: vérifie/crée le dossier LIVRES + scraper
    3. Retourne les statistiques de création
    """
    print(f"🔧 CRÉATION AUTOMATIQUE À PARTIR DU JSON")
    print(f"📄 Lecture: {fichier_categories_json}")

    stats = {
        'scrapers_crees': 0,
        'livres_crees': 0,
        'erreurs': 0,
        'categories_traitees': 0
    }

    try:
        # Étape 1: Charger le JSON des catégories principales
        if not os.path.exists(fichier_categories_json):
            print(f"❌ Fichier {fichier_categories_json} introuvable")
            return stats

        with open(fichier_categories_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extraire les catégories
        if isinstance(data, dict) and 'categories' in data:
            categories = data['categories']
        elif isinstance(data, list):
            categories = data
        else:
            print(f"❌ Structure JSON invalide")
            return stats

        print(f"📋 {len(categories)} catégories principales trouvées")

        # Étape 2: Traiter chaque catégorie
        for i, nom_categorie in enumerate(categories, 1):
            print(f"\n🔧 [{i}/{len(categories)}] Traitement: {nom_categorie}")
            stats['categories_traitees'] += 1

            try:
                # URL par défaut (sera mise à jour plus tard avec les vraies URLs)
                url_categorie = f"https://www.amazon.fr/s?k={nom_categorie.replace(' ', '+')}&i=stripbooks"

                # Créer/vérifier dossier LIVRES
                if not verifier_dossier_livres_existe(nom_categorie, dossier_base_livres):
                    dossier_cree = creer_dossier_livres(nom_categorie, dossier_base_livres)
                    print(f"📁 Dossier LIVRES créé: {os.path.basename(dossier_cree)}")
                    stats['livres_crees'] += 1
                else:
                    nom_propre = nettoyer_nom_fichier(nom_categorie)
                    dossier_cree = os.path.join(dossier_base_livres, nom_propre)
                    print(f"📁 Dossier LIVRES existant: {os.path.basename(dossier_cree)}")

                # Créer scraper automatique
                scraper_cree = creer_scraper_automatique(nom_categorie, url_categorie, dossier_scrapers)

                if scraper_cree:
                    print(f"✅ Scraper créé: {os.path.basename(scraper_cree)}")
                    stats['scrapers_crees'] += 1
                else:
                    print(f"⚠️ Scraper non créé pour: {nom_categorie}")
                    stats['erreurs'] += 1

            except Exception as e:
                print(f"❌ Erreur traitement {nom_categorie}: {e}")
                stats['erreurs'] += 1

        # Étape 3: Rapport final
        print(f"\n📊 RAPPORT FINAL:")
        print(f"   📁 Dossiers LIVRES créés: {stats['livres_crees']}")
        print(f"   📄 Scrapers créés: {stats['scrapers_crees']}")
        print(f"   ❌ Erreurs: {stats['erreurs']}")
        print(f"   ✅ Catégories traitées: {stats['categories_traitees']}")

        return stats

    except Exception as e:
        print(f"❌ Erreur générale création automatique: {e}")
        stats['erreurs'] += 1
        return stats


def lister_creations_existantes(dossier_livres: str, dossier_scrapers: str) -> dict:
    """
    Lister toutes les créations existantes (dossiers + scrapers)

    Args:
        dossier_livres (str): Chemin vers LIVRES/
        dossier_scrapers (str): Chemin vers SCRAPERS/

    Returns:
        dict: Statistiques des créations existantes
    """
    stats = {
        'dossiers_livres': 0,
        'scrapers': 0,
        'paires_completes': 0,
        'dossiers_orphelins': [],
        'scrapers_orphelins': []
    }

    # Lister dossiers LIVRES
    dossiers_livres = []
    if os.path.exists(dossier_livres):
        dossiers_livres = [d for d in os.listdir(dossier_livres)
                          if os.path.isdir(os.path.join(dossier_livres, d))]
        stats['dossiers_livres'] = len(dossiers_livres)

    # Lister scrapers
    scrapers = []
    if os.path.exists(dossier_scrapers):
        scrapers = [f.replace('scraper_', '').replace('.py', '')
                   for f in os.listdir(dossier_scrapers)
                   if f.startswith('scraper_') and f.endswith('.py')]
        stats['scrapers'] = len(scrapers)

    # Analyser paires complètes
    for dossier in dossiers_livres:
        if dossier in scrapers:
            stats['paires_completes'] += 1
        else:
            stats['dossiers_orphelins'].append(dossier)

    for scraper in scrapers:
        if scraper not in dossiers_livres:
            stats['scrapers_orphelins'].append(scraper)

    return stats


if __name__ == "__main__":
    # Tests des fonctions
    print("🧪 TEST CRÉATION SCRAPERS UTILS")

    # Test nettoyage nom
    test_noms = ["Romans et polars", "Science-Fiction & Fantasy", "Livres pour enfants (0-3 ans)"]
    print(f"\\n📝 Test nettoyage noms:")
    for nom in test_noms:
        propre = nettoyer_nom_fichier(nom)
        print(f"   '{nom}' -> '{propre}'")

    print(f"\\n✅ Tests terminés")