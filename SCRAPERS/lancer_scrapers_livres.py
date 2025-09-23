#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LANCEUR MULTI-THREADING DES SCRAPERS DE LIVRES AMAZON
====================================================

Lance uniquement les scrapers de livres (exclut catégories et sous-catégories)
en utilisant le multi-threading pour optimiser les performances.

FONCTIONNALITÉS:
- Multi-threading configurable
- Exclusion automatique des scrapers de catégories
- Gestion d'erreurs avancée
- Métriques en temps réel
- Anti-détection Amazon
- Rotation automatique des User-Agents

ARCHITECTURE:
- Toutes les fonctions utilitaires sont dans FONCTION/
- Ce fichier orchestre uniquement le lancement multi-threading
- Séparation claire entre scraping de catégories et de livres
"""

import os
import sys
import time
import threading
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime

# Ajouter le répertoire parent au path pour importer le module FONCTION
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import des modules de fonctions
try:
    from FONCTION import gestion_categories_utils
    from FONCTION import metriques_temps_reel
    from FONCTION import validateur_contexte_amazon
except ImportError as e:
    print(f"❌ Erreur d'import des modules FONCTION: {e}")
    print("Assurez-vous que les modules sont dans le dossier FONCTION/")
    sys.exit(1)

class GestionnaireScrapersLivres:
    """
    Gestionnaire principal pour le lancement multi-threading des scrapers de livres
    """

    def __init__(self, mode_mise_a_jour_forcee: bool = False):
        """
        Initialise le gestionnaire avec la configuration par défaut

        Args:
            mode_mise_a_jour_forcee (bool): Force la mise à jour de TOUS les livres existants
        """
        self.repertoire_scrapers = Path(__file__).parent
        self.repertoire_livres = Path(__file__).parent.parent / "LIVRES"
        self.repertoire_categories = Path(__file__).parent.parent / "CATEGORIES"
        self.mode_mise_a_jour_forcee = mode_mise_a_jour_forcee

        # Configuration multi-threading
        self.max_workers = self._detecter_workers_optimaux()
        self.delai_entre_scrapers = 2  # secondes

        # Métriques
        self.scrapers_reussis = 0
        self.scrapers_echecs = 0
        self.scrapers_en_cours = []
        self.verrou_metriques = threading.Lock()

        # Compteur global de livres scrapés
        self.total_livres_scrapes = 0
        self.total_nouveaux_livres = 0
        self.total_livres_mis_a_jour = 0
        self.total_doublons_evites = 0
        self.verrou_compteurs = threading.Lock()

        # Scrapers à exclure (catégories et sous-catégories)
        self.scrapers_exclus = {
            'scraper_categories_principales.py',
            'scraper_sous_categories.py',
            'lancer_scrapers_categories.py',
            'lancer_scrapers_livres.py'
        }

        print(f"🔧 Gestionnaire initialisé avec {self.max_workers} workers")

    def _detecter_workers_optimaux(self) -> int:
        """
        Détecte le nombre optimal de workers pour le multi-threading

        Returns:
            int: Nombre de workers recommandé
        """
        import multiprocessing

        cpu_count = multiprocessing.cpu_count()

        # Stratégie ultra-conservative pour éviter la détection Amazon (503)
        if cpu_count <= 2:
            workers = 1
        elif cpu_count <= 4:
            workers = 2
        elif cpu_count <= 8:
            workers = 2
        else:
            workers = 2  # Maximum réduit suite aux erreurs 503

        return workers

    def obtenir_scrapers_livres(self) -> List[str]:
        """
        Obtient la liste des scrapers v3 de livres (priorité aux v3, sinon anciens)

        Returns:
            List[str]: Liste des noms de fichiers scrapers v3
        """
        scrapers_disponibles = []

        # RECHERCHE TOUS LES SCRAPERS DE LIVRES
        print("🔍 Recherche des scrapers de livres...")
        for fichier_scraper in self.repertoire_scrapers.glob("scraper_*.py"):
            nom_fichier = fichier_scraper.name

            # Exclure les scrapers système (catégories, sous-catégories, etc.)
            if nom_fichier not in self.scrapers_exclus:
                scrapers_disponibles.append(nom_fichier)

        # Trier par ordre alphabétique pour cohérence
        scrapers_disponibles.sort()

        print(f"✅ {len(scrapers_disponibles)} scrapers de livres détectés")
        return scrapers_disponibles

    def valider_environnement(self) -> Dict[str, Any]:
        """
        Valide que l'environnement est prêt pour le scraping

        Returns:
            Dict[str, Any]: État de validation de l'environnement
        """
        validation = {
            'pret': True,
            'problemes': [],
            'infos': []
        }

        # Vérifier la structure des dossiers
        if not self.repertoire_livres.exists():
            self.repertoire_livres.mkdir(exist_ok=True)
            validation['infos'].append(f"Dossier LIVRES créé: {self.repertoire_livres}")

        # Vérifier la connectivité Amazon (avec headers anti-détection)
        try:
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get("https://www.amazon.fr", headers=headers, timeout=10)
            # Amazon peut retourner 200, 503 (anti-bot) ou 405 - tous indiquent une connectivité
            if response.status_code in [200, 405, 503]:
                validation['infos'].append(f"Connectivité Amazon.fr : OK (code {response.status_code})")
            else:
                validation['problemes'].append(f"Amazon.fr retourne code {response.status_code}")
                validation['pret'] = False
        except Exception as e:
            validation['problemes'].append(f"Erreur de connectivité: {e}")
            validation['pret'] = False

        # Vérifier les modules Python requis
        modules_requis = ['requests', 'bs4', 'fake_useragent']
        for module in modules_requis:
            try:
                __import__(module)
                validation['infos'].append(f"Module {module} : OK")
            except ImportError:
                validation['problemes'].append(f"Module manquant: {module}")
                validation['pret'] = False

        return validation

    def _extraire_statistiques_livres(self, output_scraper: str) -> Dict[str, int]:
        """
        Extrait les statistiques de livres depuis la sortie d'un scraper

        Args:
            output_scraper (str): Sortie texte du scraper

        Returns:
            Dict[str, int]: Statistiques extraites (nouveaux_livres, doublons_evites, total_livres)
        """
        import re

        stats = {
            'nouveaux_livres': 0,
            'livres_mis_a_jour': 0,
            'doublons_evites': 0,
            'total_livres': 0
        }

        if not output_scraper:
            return stats

        try:
            # Patterns pour extraire les statistiques des scrapers v3 (basés sur l'historique réel)
            patterns = {
                'nouveaux_livres': [
                    r'📚 Nouveaux livres totaux:\s*(\d+)',
                    r'nouveaux livres totaux:\s*(\d+)',
                    r'🆕 Nouveaux livres trouvés:\s*(\d+)',
                    r'Nouveaux livres trouvés:\s*(\d+)',
                    r'(\d+)\s+nouveaux livres ajoutés',
                    r'SUCCÈS:\s*(\d+)\s+nouveaux livres',
                    r'nouveaux_livres.*?:\s*(\d+)',
                    r'livres_nouveaux.*?:\s*(\d+)'
                ],
                'livres_mis_a_jour': [
                    r'🔄 MISE À JOUR FORCÉE:.*?(\d+)',
                    r'📝 Livres mis à jour:\s*(\d+)',
                    r'Livres mis à jour:\s*(\d+)',
                    r'(\d+)\s+livres mis à jour',
                    r'livres_mis_a_jour.*?:\s*(\d+)',
                    r'MISE À JOUR:.*?(\d+)'
                ],
                'doublons_evites': [
                    r'🔄 Doublons évités:\s*(\d+)',
                    r'Doublons évités:\s*(\d+)',
                    r'(\d+)\s+doublons évités',
                    r'doublons_evites.*?:\s*(\d+)',
                    r'doublons.*?:\s*(\d+)'
                ],
                'total_livres': [
                    r'📊 Total livres:\s*(\d+)',
                    r'Total livres dans la base:\s*(\d+)',
                    r'total_livres_apres.*?:\s*(\d+)',
                    r'Total dans la base:\s*(\d+)',
                    r'base de données.*?(\d+)',
                    r'fichier principal.*?(\d+)'
                ]
            }

            for stat_name, patterns_list in patterns.items():
                for pattern in patterns_list:
                    matches = re.findall(pattern, output_scraper, re.IGNORECASE)
                    if matches:
                        # Prendre la dernière occurrence (la plus récente)
                        try:
                            stats[stat_name] = max(stats[stat_name], int(matches[-1]))
                        except (ValueError, IndexError):
                            continue

        except Exception as e:
            print(f"⚠️  Erreur extraction statistiques: {e}")

        return stats

    def executer_scraper_unique(self, nom_scraper: str) -> Dict[str, Any]:
        """
        Exécute un seul scraper avec gestion d'erreurs

        Args:
            nom_scraper (str): Nom du fichier scraper

        Returns:
            Dict[str, Any]: Résultat de l'exécution
        """
        import subprocess
        import time

        debut = time.time()
        chemin_scraper = self.repertoire_scrapers / nom_scraper

        # Mise à jour des métriques
        with self.verrou_metriques:
            self.scrapers_en_cours.append(nom_scraper)

        try:
            print(f"🚀 Démarrage: {nom_scraper}")

            # Construire la commande pour le scraper
            commande = [sys.executable]

            # Toujours utiliser le scraper directement
            commande.append(str(chemin_scraper))

            # Ajouter l'argument mode forcé si activé
            if self.mode_mise_a_jour_forcee:
                commande.append("--force")

            # Exécuter le scraper avec affichage en temps réel
            print(f"🔍 Exécution détaillée: {nom_scraper}")
            process = subprocess.Popen(
                commande,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.repertoire_scrapers,
                bufsize=1,
                universal_newlines=True
            )

            output_lines = []
            while True:
                line = process.stdout.readline()
                if line:
                    line = line.strip()
                    output_lines.append(line)
                    # Afficher chaque ligne en temps réel
                    print(f"    {line}")
                elif process.poll() is not None:
                    break

            return_code = process.wait()
            output_text = '\n'.join(output_lines)

            # Créer un objet resultat similaire à subprocess.run
            class MockResult:
                def __init__(self, returncode, stdout):
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = ""

            resultat = MockResult(return_code, output_text)


            # Extraire les statistiques de livres depuis la sortie
            stats_livres = self._extraire_statistiques_livres(resultat.stdout)

            # Mettre à jour les compteurs globaux
            with self.verrou_compteurs:
                self.total_nouveaux_livres += stats_livres.get('nouveaux_livres', 0)
                self.total_livres_mis_a_jour += stats_livres.get('livres_mis_a_jour', 0)
                self.total_doublons_evites += stats_livres.get('doublons_evites', 0)
                self.total_livres_scrapes += stats_livres.get('total_livres', 0)

            duree = time.time() - debut

            if resultat.returncode == 0:
                with self.verrou_metriques:
                    self.scrapers_reussis += 1
                    if nom_scraper in self.scrapers_en_cours:
                        self.scrapers_en_cours.remove(nom_scraper)

                print(f"✅ Terminé: {nom_scraper} ({duree:.1f}s)")

                return {
                    'scraper': nom_scraper,
                    'succes': True,
                    'duree': duree,
                    'message': 'Succès'
                }
            else:
                with self.verrou_metriques:
                    self.scrapers_echecs += 1
                    if nom_scraper in self.scrapers_en_cours:
                        self.scrapers_en_cours.remove(nom_scraper)

                print(f"❌ Échec: {nom_scraper} (code: {resultat.returncode})")

                return {
                    'scraper': nom_scraper,
                    'succes': False,
                    'duree': duree,
                    'message': f'Erreur code {resultat.returncode}'
                }

        except subprocess.TimeoutExpired:
            with self.verrou_metriques:
                self.scrapers_echecs += 1
                if nom_scraper in self.scrapers_en_cours:
                    self.scrapers_en_cours.remove(nom_scraper)

            duree = time.time() - debut
            print(f"⏰ Timeout: {nom_scraper} (>300s)")

            return {
                'scraper': nom_scraper,
                'succes': False,
                'duree': duree,
                'message': 'Timeout (>300s)'
            }

        except Exception as e:
            with self.verrou_metriques:
                self.scrapers_echecs += 1
                if nom_scraper in self.scrapers_en_cours:
                    self.scrapers_en_cours.remove(nom_scraper)

            duree = time.time() - debut
            print(f"💥 Erreur: {nom_scraper} - {str(e)}")

            return {
                'scraper': nom_scraper,
                'succes': False,
                'duree': duree,
                'message': f'Exception: {str(e)}'
            }

    def lancer_multi_threading(self, scrapers: List[str]) -> Dict[str, Any]:
        """
        Lance les scrapers en multi-threading

        Args:
            scrapers (List[str]): Liste des scrapers à exécuter

        Returns:
            Dict[str, Any]: Résultats de l'exécution multi-threading
        """
        debut_global = time.time()
        resultats = []

        print(f"🚀 Lancement multi-threading: {len(scrapers)} scrapers")
        print(f"⚡ Configuration: {self.max_workers} workers simultanés")
        print("=" * 60)

        # Lancer le monitoring en temps réel dans un thread séparé
        stop_monitoring = threading.Event()
        thread_monitoring = threading.Thread(
            target=self._afficher_progression_temps_reel,
            args=(len(scrapers), stop_monitoring)
        )
        thread_monitoring.daemon = True
        thread_monitoring.start()

        try:
            # Exécution avec ThreadPoolExecutor
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Soumettre tous les scrapers
                futures = []
                for i, scraper in enumerate(scrapers):
                    # Délai échelonné pour éviter la surcharge initiale
                    if i > 0:
                        time.sleep(self.delai_entre_scrapers)

                    future = executor.submit(self.executer_scraper_unique, scraper)
                    futures.append(future)

                # Collecter les résultats au fur et à mesure
                for future in concurrent.futures.as_completed(futures):
                    try:
                        resultat = future.result()
                        resultats.append(resultat)
                    except Exception as e:
                        print(f"❌ Erreur lors de la récupération du résultat: {e}")

        except KeyboardInterrupt:
            print("\n🛑 INTERRUPTION DÉTECTÉE - Arrêt en cours...")

        finally:
            # Arrêter le monitoring
            stop_monitoring.set()
            thread_monitoring.join(timeout=1)

        duree_totale = time.time() - debut_global

        # Calcul des statistiques finales
        scrapers_reussis = sum(1 for r in resultats if r['succes'])
        scrapers_echecs = len(resultats) - scrapers_reussis

        return {
            'resultats': resultats,
            'scrapers_reussis': scrapers_reussis,
            'scrapers_echecs': scrapers_echecs,
            'duree_totale': duree_totale,
            'vitesse_moyenne': len(resultats) / (duree_totale / 60) if duree_totale > 0 else 0
        }

    def _afficher_progression_temps_reel(self, total_scrapers: int, stop_event: threading.Event):
        """
        Affiche la progression en temps réel dans un thread séparé avec compteurs globaux

        Args:
            total_scrapers (int): Nombre total de scrapers à traiter
            stop_event (threading.Event): Événement pour arrêter le monitoring
        """
        while not stop_event.is_set():
            with self.verrou_metriques:
                total_termines = self.scrapers_reussis + self.scrapers_echecs
                en_cours = len(self.scrapers_en_cours)

            with self.verrou_compteurs:
                total_nouveaux = self.total_nouveaux_livres
                total_mis_a_jour = self.total_livres_mis_a_jour
                total_doublons = self.total_doublons_evites
                total_livres = self.total_livres_scrapes

            if total_termines > 0:
                pourcentage = (total_termines / total_scrapers) * 100
                print(f"\r📊 Scrapers: {total_termines}/{total_scrapers} ({pourcentage:.1f}%) "
                      f"| ✅ {self.scrapers_reussis} | ❌ {self.scrapers_echecs} | 🔄 {en_cours} "
                      f"| 🆕 {total_nouveaux:,} nouveaux | 📝 {total_mis_a_jour:,} mis à jour | 🔄 {total_doublons:,} doublons | 📖 {total_livres:,} total", end="")

            # Attendre 3 secondes ou jusqu'à l'arrêt
            if stop_event.wait(3):
                break

        print()  # Nouvelle ligne à la fin

    def generer_rapport_final(self, resultats_execution: Dict[str, Any]):
        """
        Génère un rapport final détaillé de l'exécution

        Args:
            resultats_execution (Dict[str, Any]): Résultats de l'exécution
        """
        print("\n" + "=" * 80)
        print("📊 RAPPORT FINAL - SCRAPING MULTI-THREADING DES LIVRES")
        print("=" * 80)

        # Statistiques globales
        print(f"⏱️  Durée totale: {resultats_execution['duree_totale']:.2f} secondes "
              f"({resultats_execution['duree_totale']/60:.1f} minutes)")
        print(f"✅ Scrapers réussis: {resultats_execution['scrapers_reussis']}")
        print(f"❌ Scrapers échoués: {resultats_execution['scrapers_echecs']}")

        total = resultats_execution['scrapers_reussis'] + resultats_execution['scrapers_echecs']
        if total > 0:
            taux_reussite = (resultats_execution['scrapers_reussis'] / total) * 100
            print(f"📈 Taux de réussite: {taux_reussite:.1f}%")

        print(f"⚡ Vitesse moyenne: {resultats_execution['vitesse_moyenne']:.1f} scrapers/minute")

        # Statistiques de livres
        print(f"\n📚 STATISTIQUES GLOBALES DE LIVRES:")
        print(f"   🆕 Total nouveaux livres ajoutés: {self.total_nouveaux_livres:,}")
        print(f"   📝 Total livres mis à jour: {self.total_livres_mis_a_jour:,}")
        print(f"   🔄 Total doublons évités: {self.total_doublons_evites:,}")
        print(f"   📊 Total livres dans toutes les bases: {self.total_livres_scrapes:,}")

        total_traite = self.total_nouveaux_livres + self.total_livres_mis_a_jour
        if total_traite > 0:
            efficacite = (total_traite / (total_traite + self.total_doublons_evites)) * 100
            print(f"   📈 Efficacité (nouveaux+mis à jour/total): {efficacite:.1f}%")

        if self.total_livres_mis_a_jour > 0:
            print(f"   🔄 Mode MISE À JOUR FORCÉE activé: {self.total_livres_mis_a_jour:,} livres rafraîchis")

        # Détail des échecs
        echecs = [r for r in resultats_execution['resultats'] if not r['succes']]
        if echecs:
            print(f"\n❌ DÉTAIL DES ÉCHECS ({len(echecs)}):")
            for echec in echecs[:10]:  # Limiter à 10 pour la lisibilité
                print(f"   • {echec['scraper']}: {echec['message']}")
            if len(echecs) > 10:
                print(f"   ... et {len(echecs) - 10} autres échecs")

        # Vérification des fichiers générés
        print(f"\n📁 VÉRIFICATION DES FICHIERS GÉNÉRÉS:")
        if self.repertoire_livres.exists():
            nb_dossiers = len([d for d in self.repertoire_livres.iterdir() if d.is_dir()])
            nb_json = len(list(self.repertoire_livres.glob("**/*.json")))
            print(f"   📂 {nb_dossiers} dossiers de catégories")
            print(f"   📄 {nb_json} fichiers JSON de données")
        else:
            print("   ⚠️  Aucun dossier LIVRES trouvé")

        # Sauvegarder le rapport en JSON
        self._sauvegarder_rapport_json(resultats_execution)

        print("=" * 80)
        print("🏁 SCRAPING MULTI-THREADING TERMINÉ")
        print("=" * 80)

    def _sauvegarder_rapport_json(self, resultats_execution: Dict[str, Any]):
        """
        Sauvegarde le rapport d'exécution en JSON

        Args:
            resultats_execution (Dict[str, Any]): Résultats à sauvegarder
        """
        try:
            rapport = {
                'timestamp': datetime.now().isoformat(),
                'type': 'scraping_livres_multi_threading',
                'configuration': {
                    'max_workers': self.max_workers,
                    'delai_entre_scrapers': self.delai_entre_scrapers
                },
                'statistiques': {
                    'scrapers_reussis': resultats_execution['scrapers_reussis'],
                    'scrapers_echecs': resultats_execution['scrapers_echecs'],
                    'duree_totale': resultats_execution['duree_totale'],
                    'vitesse_moyenne': resultats_execution['vitesse_moyenne']
                },
                'resultats_detailles': resultats_execution['resultats']
            }

            fichier_rapport = self.repertoire_scrapers.parent / f"rapport_scraping_livres_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(fichier_rapport, 'w', encoding='utf-8') as f:
                json.dump(rapport, f, indent=2, ensure_ascii=False)

            print(f"💾 Rapport sauvegardé: {fichier_rapport.name}")

        except Exception as e:
            print(f"⚠️  Erreur lors de la sauvegarde du rapport: {e}")


def main(mode_forcee: bool = False):
    """
    Fonction principale - Lance le scraping multi-threading des livres

    Args:
        mode_forcee (bool): Active le mode de mise à jour forcée de TOUS les livres
    """
    print("🚀 LANCEUR MULTI-THREADING DES SCRAPERS V3.0 - TOUTES CATÉGORIES")
    print("=" * 70)
    print("✨ Fonctionnalités v3.0 :")
    print("  🔄 Multi-threading optimisé (priorité aux scrapers v3)")
    print("  🚫 Anti-doublon intelligent sur TOUS les scrapers")
    print("  📝 Mise à jour automatique des JSON (pas de nouveaux fichiers)")
    print("  📊 Extraction complète de TOUS les champs disponibles")
    print("  💾 Backup automatique pour chaque scraper")
    print("  📈 Métriques détaillées en temps réel")
    print("  🔍 Anti-détection Amazon avancé")
    print("  ⚠️  Gestion d'erreurs robuste")

    if mode_forcee:
        print("  🔄 MODE MISE À JOUR FORCÉE ACTIVÉ: TOUS les livres existants seront mis à jour")
        print("  📋 LOGS DÉTAILLÉS ACTIVÉS: Chaque livre traité sera affiché")

    print("=" * 70)

    # Initialiser le gestionnaire avec le mode forcé
    gestionnaire = GestionnaireScrapersLivres(mode_mise_a_jour_forcee=mode_forcee)

    # Validation de l'environnement
    validation = gestionnaire.valider_environnement()
    if not validation['pret']:
        print("❌ Environnement non prêt:")
        for probleme in validation['problemes']:
            print(f"   • {probleme}")
        return

    # Afficher les infos de validation
    for info in validation['infos']:
        print(f"ℹ️  {info}")

    # Obtenir la liste des scrapers de livres
    scrapers_livres = gestionnaire.obtenir_scrapers_livres()

    if not scrapers_livres:
        print("⚠️  Aucun scraper de livres trouvé")
        return

    print(f"\n📋 {len(scrapers_livres)} scrapers de livres détectés")
    print(f"🔧 Configuration: {gestionnaire.max_workers} workers simultanés")

    print(f"\n⚡ LANCEMENT AUTOMATIQUE DE {len(scrapers_livres)} SCRAPERS...")
    time.sleep(1)

    try:
        # Lancer l'exécution multi-threading
        resultats = gestionnaire.lancer_multi_threading(scrapers_livres)

        # Générer le rapport final
        gestionnaire.generer_rapport_final(resultats)

    except KeyboardInterrupt:
        print("\n🛑 INTERRUPTION DÉTECTÉE")
        print("Arrêt en cours...")
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists("scraper_categories_principales.py"):
        print("❌ Erreur: Scrapers principaux non trouvés")
        print("Assurez-vous d'être dans le répertoire SCRAPERS")
        sys.exit(1)

    # MODE FORCÉ OBLIGATOIRE - TOUS les livres sont mis à jour à CHAQUE lancement
    main(mode_forcee=True)