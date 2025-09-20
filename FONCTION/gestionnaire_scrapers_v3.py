#!/usr/bin/env python3
"""
GESTIONNAIRE DES SCRAPERS V3.0
==============================

Fonctions utilitaires pour gérer et lancer les scrapers v3.0 avec toutes les fonctionnalités :
- Détection automatique des scrapers v3
- Lancement en multi-threading
- Suivi des métriques globales
- Gestion des erreurs et retry
- Rapport de synthèse

UTILISATION:
from FONCTION.gestionnaire_scrapers_v3 import GestionnaireScrapersV3

gestionnaire = GestionnaireScrapersV3()
resultats = gestionnaire.lancer_tous_scrapers_v3()
"""

import os
import sys
import time
import json
import threading
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class GestionnaireScrapersV3:
    """
    Gestionnaire pour tous les scrapers v3.0 avec fonctionnalités avancées
    """

    def __init__(self, max_workers: int = 6):
        """
        Initialise le gestionnaire des scrapers v3.0

        Args:
            max_workers (int): Nombre maximum de threads parallèles
        """
        self.max_workers = max_workers
        self.repertoire_scrapers = Path(__file__).parent.parent / "SCRAPERS"

        # Statistiques globales
        self.stats_globales = {
            'debut_execution': datetime.now(),
            'scrapers_executes': 0,
            'scrapers_reussis': 0,
            'scrapers_echec': 0,
            'total_livres_nouveaux': 0,
            'total_doublons_evites': 0,
            'total_erreurs': 0,
            'duree_totale': 0
        }

        # Thread safety
        self.lock = threading.Lock()

        print(f"🔧 Gestionnaire v3.0 initialisé avec {max_workers} workers")

    def detecter_scrapers_v3(self) -> List[Path]:
        """
        Détecte tous les scrapers v3 disponibles

        Returns:
            List[Path]: Liste des chemins vers les scrapers v3
        """
        scrapers_v3 = []

        # Fichiers à exclure
        exclusions = {
            'convertir_tous_scrapers_v3.py',
            'scraper_categories_principales.py',
            'scraper_sous_categories.py',
            'lancer_scrapers_categories.py',
            'lancer_scrapers_livres.py'
        }

        for fichier in self.repertoire_scrapers.glob("*_v3.py"):
            if fichier.name not in exclusions:
                scrapers_v3.append(fichier)

        # Trier par nom pour avoir un ordre déterministe
        scrapers_v3.sort(key=lambda x: x.name)

        print(f"📋 {len(scrapers_v3)} scrapers v3.0 détectés")
        return scrapers_v3

    def executer_scraper_v3(self, chemin_scraper: Path) -> Dict:
        """
        Exécute un scraper v3 spécifique

        Args:
            chemin_scraper (Path): Chemin vers le scraper

        Returns:
            Dict: Résultats de l'exécution
        """
        nom_scraper = chemin_scraper.stem
        debut_execution = time.time()

        resultats = {
            'nom_scraper': nom_scraper,
            'chemin': str(chemin_scraper),
            'debut': datetime.now().isoformat(),
            'duree': 0,
            'succes': False,
            'livres_nouveaux': 0,
            'doublons_evites': 0,
            'erreurs': 0,
            'message': '',
            'categorie': 'Inconnue'
        }

        try:
            print(f"\n🚀 Lancement: {nom_scraper}")

            # Importer et exécuter le scraper
            sys.path.insert(0, str(self.repertoire_scrapers))

            # Import dynamique du module
            spec = __import__(nom_scraper)

            # Créer une instance du scraper
            # Trouver la classe principale (celle qui hérite de ScraperAmazonAmeliore)
            for attr_name in dir(spec):
                attr = getattr(spec, attr_name)
                if (hasattr(attr, '__bases__') and
                    any('ScraperAmazonAmeliore' in str(base) for base in attr.__bases__)):

                    scraper_instance = attr()

                    # Extraire infos de base
                    resultats['categorie'] = getattr(scraper_instance, 'nom_categorie', 'Inconnue')

                    # Lancer le scraping
                    livres_nouveaux = scraper_instance.run_complet()

                    # Récupérer les métriques
                    if hasattr(scraper_instance, 'metriques'):
                        metriques = scraper_instance.metriques
                        resultats['livres_nouveaux'] = livres_nouveaux
                        resultats['doublons_evites'] = metriques.get('doublons_evites', 0)
                        resultats['erreurs'] = metriques.get('erreurs_extraction', 0) + metriques.get('erreurs_reseau', 0)
                    else:
                        resultats['livres_nouveaux'] = livres_nouveaux

                    resultats['succes'] = True
                    resultats['message'] = f"✅ {livres_nouveaux} nouveaux livres"
                    break

            else:
                resultats['message'] = "❌ Classe scraper non trouvée"

        except Exception as e:
            resultats['message'] = f"❌ Erreur: {str(e)[:100]}"
            print(f"❌ Erreur {nom_scraper}: {e}")

        finally:
            resultats['duree'] = time.time() - debut_execution

            # Mise à jour thread-safe des stats globales
            with self.lock:
                self.stats_globales['scrapers_executes'] += 1
                if resultats['succes']:
                    self.stats_globales['scrapers_reussis'] += 1
                    self.stats_globales['total_livres_nouveaux'] += resultats['livres_nouveaux']
                    self.stats_globales['total_doublons_evites'] += resultats['doublons_evites']
                else:
                    self.stats_globales['scrapers_echec'] += 1
                self.stats_globales['total_erreurs'] += resultats['erreurs']

            print(f"⏱️  {nom_scraper}: {resultats['duree']:.1f}s - {resultats['message']}")

        return resultats

    def lancer_tous_scrapers_v3(self) -> Dict:
        """
        Lance tous les scrapers v3 en parallèle

        Returns:
            Dict: Résultats complets de l'exécution
        """
        print("🚀 LANCEMENT MASSIF DES SCRAPERS V3.0")
        print("=" * 60)
        print("🎯 Fonctionnalités actives sur TOUS les scrapers:")
        print("   ✅ Anti-doublon intelligent")
        print("   ✅ Mise à jour automatique JSON")
        print("   ✅ Extraction complète (50+ champs)")
        print("   ✅ Backup automatique")
        print("   ✅ Métriques détaillées")
        print("=" * 60)

        # Détecter tous les scrapers v3
        scrapers_v3 = self.detecter_scrapers_v3()

        if not scrapers_v3:
            print("⚠️  Aucun scraper v3 trouvé")
            return self.generer_rapport_final([])

        print(f"🔥 Lancement de {len(scrapers_v3)} scrapers avec {self.max_workers} workers en parallèle\n")

        # Exécution en parallèle
        resultats_execution = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Soumettre tous les scrapers
            futures = {
                executor.submit(self.executer_scraper_v3, scraper): scraper
                for scraper in scrapers_v3
            }

            # Collecter les résultats au fur et à mesure
            for future in as_completed(futures):
                scraper_path = futures[future]
                try:
                    resultat = future.result()
                    resultats_execution.append(resultat)
                except Exception as e:
                    print(f"❌ Erreur fatale {scraper_path.name}: {e}")
                    resultats_execution.append({
                        'nom_scraper': scraper_path.stem,
                        'succes': False,
                        'message': f"Erreur fatale: {e}",
                        'duree': 0,
                        'livres_nouveaux': 0,
                        'doublons_evites': 0,
                        'erreurs': 1
                    })

        return self.generer_rapport_final(resultats_execution)

    def generer_rapport_final(self, resultats: List[Dict]) -> Dict:
        """
        Génère un rapport final complet

        Args:
            resultats (List[Dict]): Résultats de tous les scrapers

        Returns:
            Dict: Rapport final avec toutes les statistiques
        """
        self.stats_globales['duree_totale'] = (datetime.now() - self.stats_globales['debut_execution']).total_seconds()

        # Analyser les résultats
        scrapers_avec_livres = [r for r in resultats if r['livres_nouveaux'] > 0]
        scrapers_sans_livres = [r for r in resultats if r['livres_nouveaux'] == 0 and r['succes']]
        scrapers_erreur = [r for r in resultats if not r['succes']]

        # Top 10 des plus productifs
        top_productifs = sorted(scrapers_avec_livres, key=lambda x: x['livres_nouveaux'], reverse=True)[:10]

        # Rapport complet
        print("\n" + "=" * 80)
        print("📊 RAPPORT FINAL - SCRAPERS V3.0")
        print("=" * 80)
        print(f"⏱️  Durée totale: {self.stats_globales['duree_totale']:.1f} secondes ({self.stats_globales['duree_totale']/60:.1f} minutes)")
        print(f"🔢 Scrapers exécutés: {self.stats_globales['scrapers_executes']}")
        print(f"✅ Succès: {self.stats_globales['scrapers_reussis']}")
        print(f"❌ Échecs: {self.stats_globales['scrapers_echec']}")
        print(f"📚 Total nouveaux livres: {self.stats_globales['total_livres_nouveaux']}")
        print(f"🔄 Total doublons évités: {self.stats_globales['total_doublons_evites']}")
        print(f"⚠️  Total erreurs: {self.stats_globales['total_erreurs']}")

        if self.stats_globales['scrapers_executes'] > 0:
            taux_reussite = (self.stats_globales['scrapers_reussis'] / self.stats_globales['scrapers_executes']) * 100
            print(f"📈 Taux de réussite: {taux_reussite:.1f}%")

        # Détails par catégorie
        print(f"\n📋 DÉTAILS PAR CATÉGORIE:")
        print(f"   📚 Scrapers avec nouveaux livres: {len(scrapers_avec_livres)}")
        print(f"   ✅ Scrapers à jour (0 nouveaux): {len(scrapers_sans_livres)}")
        print(f"   ❌ Scrapers en erreur: {len(scrapers_erreur)}")

        # Top des plus productifs
        if top_productifs:
            print(f"\n🏆 TOP 10 DES PLUS PRODUCTIFS:")
            for i, scraper in enumerate(top_productifs, 1):
                print(f"   {i:2d}. {scraper['nom_scraper']}: {scraper['livres_nouveaux']} livres")

        # Scrapers en erreur
        if scrapers_erreur:
            print(f"\n❌ SCRAPERS EN ERREUR:")
            for scraper in scrapers_erreur[:10]:  # Limiter à 10
                print(f"   ❌ {scraper['nom_scraper']}: {scraper['message']}")

        print("\n🎉 MISSION ACCOMPLIE - TOUS LES SCRAPERS V3.0 LANCÉS !")
        print("📁 Vérifiez les backups et métriques dans chaque dossier LIVRES/")

        # Rapport pour retour
        rapport_final = {
            'stats_globales': self.stats_globales,
            'scrapers_avec_livres': len(scrapers_avec_livres),
            'scrapers_sans_livres': len(scrapers_sans_livres),
            'scrapers_erreur': len(scrapers_erreur),
            'top_productifs': top_productifs,
            'scrapers_erreur_details': scrapers_erreur,
            'tous_resultats': resultats
        }

        return rapport_final

    def sauvegarder_rapport_global(self, rapport: Dict):
        """
        Sauvegarde le rapport global dans un fichier JSON

        Args:
            rapport (Dict): Rapport complet à sauvegarder
        """
        try:
            repertoire_rapports = Path(__file__).parent.parent / "RAPPORTS_GLOBAUX"
            repertoire_rapports.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            fichier_rapport = repertoire_rapports / f"rapport_scrapers_v3_{timestamp}.json"

            with open(fichier_rapport, 'w', encoding='utf-8') as f:
                json.dump(rapport, f, indent=2, ensure_ascii=False, default=str)

            print(f"📄 Rapport global sauvegardé: {fichier_rapport}")

        except Exception as e:
            print(f"⚠️  Erreur sauvegarde rapport: {e}")


def lancer_scrapers_v3_massivement(max_workers: int = 6) -> Dict:
    """
    Fonction utilitaire pour lancer massivement tous les scrapers v3

    Args:
        max_workers (int): Nombre de workers parallèles

    Returns:
        Dict: Rapport complet de l'exécution
    """
    gestionnaire = GestionnaireScrapersV3(max_workers=max_workers)
    rapport = gestionnaire.lancer_tous_scrapers_v3()
    gestionnaire.sauvegarder_rapport_global(rapport)
    return rapport


if __name__ == "__main__":
    # Test du gestionnaire
    print("🧪 TEST DU GESTIONNAIRE SCRAPERS V3.0")
    rapport = lancer_scrapers_v3_massivement(max_workers=6)
    print(f"✅ Test terminé avec {rapport['stats_globales']['scrapers_reussis']} succès")