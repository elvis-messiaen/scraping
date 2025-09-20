#!/usr/bin/env python3
"""
MIGRATION SYSTÈME CATÉGORIES 2025
=================================
Script de migration pour transformer l'ancien fichier JSON vers
le nouveau système de validation orchestré.

FONCTIONNALITÉS :
- Sauvegarde automatique de l'ancien fichier
- Validation des catégories existantes avec le nouveau système
- Enrichissement des métadonnées
- Conservation des données valides
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging

# Import du nouveau système
from validation_categories_2025 import validation_detaillee, obtenir_statistiques_validation

class MigrateurCategories2025:
    """
    Migrateur pour transformer l'ancien système vers le nouveau
    """

    def __init__(self, fichier_categories: str):
        """
        Initialiser le migrateur

        Args:
            fichier_categories (str): Chemin vers le fichier JSON existant
        """
        self.fichier_categories = Path(fichier_categories)
        self.fichier_sauvegarde = self.fichier_categories.with_suffix('.backup.json')

        # Configuration logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Statistiques de migration
        self.stats_migration = {
            'categories_total': 0,
            'categories_validees': 0,
            'categories_rejetees': 0,
            'categories_incertaines': 0,
            'nodes_enrichis': 0,
            'erreurs': 0
        }

    def creer_sauvegarde(self) -> bool:
        """
        Créer une sauvegarde du fichier existant

        Returns:
            bool: True si sauvegarde réussie
        """
        try:
            if self.fichier_categories.exists():
                shutil.copy2(self.fichier_categories, self.fichier_sauvegarde)
                self.logger.info(f"✅ Sauvegarde créée: {self.fichier_sauvegarde}")
                return True
            else:
                self.logger.warning("❌ Fichier source inexistant")
                return False
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde: {e}")
            return False

    def charger_categories_existantes(self) -> Dict[str, Any]:
        """
        Charger les catégories du fichier existant

        Returns:
            Dict: Données du fichier JSON
        """
        try:
            with open(self.fichier_categories, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Erreur chargement: {e}")
            return {'metadata': {}, 'categories': {}}

    def valider_categorie_avec_nouveau_systeme(self, node_id: str, nom: str, url: str) -> Dict[str, Any]:
        """
        Valider une catégorie avec le nouveau système 2025

        Args:
            node_id (str): ID du node Amazon
            nom (str): Nom de la catégorie
            url (str): URL de la catégorie

        Returns:
            Dict: Résultat de validation détaillée
        """
        try:
            # Utiliser le système de validation 2025
            resultat = validation_detaillee(url, nom, context=f"node_{node_id}")

            return {
                'valide': resultat['verdict'],
                'confiance': resultat['confiance'],
                'methode_principale': resultat['methode_principale'],
                'consensus': resultat['consensus'],
                'raisonnement': resultat['raisonnement'],
                'timestamp_validation': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Erreur validation {node_id}: {e}")
            return {
                'valide': False,
                'confiance': 0.0,
                'methode_principale': 'error',
                'consensus': 'none',
                'raisonnement': f'Erreur validation: {str(e)}',
                'timestamp_validation': datetime.now().isoformat()
            }

    def migrer_categories(self) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """
        Migrer toutes les catégories vers le nouveau système

        Returns:
            Tuple[Dict, Dict]: (nouveau_fichier_json, statistiques)
        """
        self.logger.info("🚀 DÉBUT MIGRATION CATÉGORIES 2025")

        # 1. Créer sauvegarde
        if not self.creer_sauvegarde():
            raise Exception("Impossible de créer la sauvegarde")

        # 2. Charger données existantes
        donnees_anciennes = self.charger_categories_existantes()
        categories_anciennes = donnees_anciennes.get('categories', {})

        self.stats_migration['categories_total'] = len(categories_anciennes)
        self.logger.info(f"📊 {self.stats_migration['categories_total']} catégories à migrer")

        # 3. Structure du nouveau fichier
        nouveau_fichier = {
            'metadata': {
                'version': '2025',
                'timestamp_migration': datetime.now().isoformat(),
                'fichier_source': str(self.fichier_categories),
                'fichier_sauvegarde': str(self.fichier_sauvegarde),
                'systeme_validation': 'orchestrateur_2025',
                'migration_stats': {}
            },
            'categories': {}
        }

        # 4. Migrer chaque catégorie
        for node_id, ancienne_categorie in categories_anciennes.items():
            try:
                nom = ancienne_categorie.get('nom', '')
                url = ancienne_categorie.get('url', '')

                self.logger.info(f"🔄 Migration {node_id}: {nom}")

                # Validation avec nouveau système
                validation_resultat = self.valider_categorie_avec_nouveau_systeme(node_id, nom, url)

                # Construire la nouvelle structure enrichie
                nouvelle_categorie = {
                    # Données originales conservées
                    'nom': nom,
                    'url': url,
                    'node': node_id,
                    'sous_categories': ancienne_categorie.get('sous_categories', {}),
                    'detecte_par': ancienne_categorie.get('detecte_par', 'migration'),

                    # NOUVELLES MÉTADONNÉES 2025
                    'validation_2025': validation_resultat,
                    'est_valide': validation_resultat['valide'],
                    'niveau_confiance': validation_resultat['confiance'],
                    'statut_migration': 'migre_avec_succes'
                }

                nouveau_fichier['categories'][node_id] = nouvelle_categorie

                # Mise à jour des statistiques
                if validation_resultat['valide']:
                    if validation_resultat['confiance'] >= 0.8:
                        self.stats_migration['categories_validees'] += 1
                    else:
                        self.stats_migration['categories_incertaines'] += 1
                else:
                    self.stats_migration['categories_rejetees'] += 1

                self.stats_migration['nodes_enrichis'] += 1

                self.logger.info(f"✅ {node_id}: {'VALIDÉ' if validation_resultat['valide'] else 'REJETÉ'} "
                               f"(conf: {validation_resultat['confiance']:.2f})")

            except Exception as e:
                self.logger.error(f"❌ Erreur migration {node_id}: {e}")
                self.stats_migration['erreurs'] += 1

        # 5. Finaliser les métadonnées
        nouveau_fichier['metadata']['migration_stats'] = self.stats_migration
        nouveau_fichier['metadata']['total_categories_migrees'] = len(nouveau_fichier['categories'])

        # 6. Statistiques du système 2025
        try:
            stats_systeme = obtenir_statistiques_validation()
            nouveau_fichier['metadata']['stats_systeme_2025'] = stats_systeme
        except Exception as e:
            self.logger.warning(f"Impossible d'obtenir les stats du système: {e}")

        self.logger.info("✅ MIGRATION TERMINÉE")
        return nouveau_fichier, self.stats_migration

    def sauvegarder_fichier_migre(self, nouveau_fichier: Dict[str, Any]) -> bool:
        """
        Sauvegarder le fichier migré

        Args:
            nouveau_fichier (Dict): Données migrées

        Returns:
            bool: True si sauvegarde réussie
        """
        try:
            with open(self.fichier_categories, 'w', encoding='utf-8') as f:
                json.dump(nouveau_fichier, f, indent=2, ensure_ascii=False)

            self.logger.info(f"💾 Fichier migré sauvegardé: {self.fichier_categories}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde fichier migré: {e}")
            return False

    def afficher_rapport_migration(self, stats: Dict[str, int]):
        """
        Afficher le rapport complet de migration

        Args:
            stats (Dict): Statistiques de migration
        """
        print("\n" + "="*60)
        print("📊 RAPPORT MIGRATION CATÉGORIES 2025")
        print("="*60)

        print(f"📈 Total catégories traitées: {stats['categories_total']}")
        print(f"✅ Catégories validées (conf >= 0.8): {stats['categories_validees']}")
        print(f"⚠️  Catégories incertaines (conf < 0.8): {stats['categories_incertaines']}")
        print(f"❌ Catégories rejetées: {stats['categories_rejetees']}")
        print(f"🔧 Nodes enrichis avec métadonnées 2025: {stats['nodes_enrichis']}")
        print(f"💥 Erreurs rencontrées: {stats['erreurs']}")

        taux_succes = (stats['categories_validees'] / max(1, stats['categories_total'])) * 100
        print(f"\n🎯 Taux de validation: {taux_succes:.1f}%")

        print(f"\n📁 Fichier sauvegardé: {self.fichier_sauvegarde}")
        print(f"📁 Fichier migré: {self.fichier_categories}")

def executer_migration_complete(fichier_categories: str) -> bool:
    """
    Exécuter la migration complète des catégories

    Args:
        fichier_categories (str): Chemin vers le fichier à migrer

    Returns:
        bool: True si migration réussie
    """
    try:
        # Créer le migrateur
        migrateur = MigrateurCategories2025(fichier_categories)

        # Exécuter la migration
        nouveau_fichier, stats = migrateur.migrer_categories()

        # Sauvegarder
        if migrateur.sauvegarder_fichier_migre(nouveau_fichier):
            # Afficher le rapport
            migrateur.afficher_rapport_migration(stats)
            return True
        else:
            print("❌ Échec sauvegarde du fichier migré")
            return False

    except Exception as e:
        print(f"💥 ERREUR CRITIQUE MIGRATION: {e}")
        return False

if __name__ == "__main__":
    # EXÉCUTION DE LA MIGRATION
    fichier_path = "/Users/Simplon/Cours/workspacePython/Scraping/CATEGORIES/categories_amazon_completes.json"

    print("🚀 LANCEMENT MIGRATION CATÉGORIES VERS SYSTÈME 2025")
    print(f"📁 Fichier source: {fichier_path}")

    confirmation = input("\n⚠️  Confirmer la migration ? (y/n): ").lower().strip()

    if confirmation == 'y':
        succes = executer_migration_complete(fichier_path)
        if succes:
            print("\n🎉 MIGRATION RÉUSSIE ! Votre fichier a été migré vers le système 2025.")
            print("📋 Toutes vos catégories existantes ont été préservées et enrichies.")
        else:
            print("\n💥 ÉCHEC DE LA MIGRATION. Vérifiez les logs pour plus de détails.")
    else:
        print("🔄 Migration annulée par l'utilisateur.")