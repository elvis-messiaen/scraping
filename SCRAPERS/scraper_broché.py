#!/usr/bin/env python3
"""
SCRAPER AMAZON AMÉLIORÉ V3.0 - BROCHÉ
==============================================
Catégorie: Broché
URL: https://www.amazon.fr/s?k=Broché&i=stripbooks

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

class ScraperAmazonBroché(ScraperAmazonAmeliore):
    """
    Scraper spécialisé pour: Broché

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
        Initialise le scraper v3.0 pour Broché

        Args:
            mode_forcee (bool): Force la mise à jour de TOUS les livres existants (défaut: False)
        """
        super().__init__(
            nom_categorie="Broché",
            url_categorie="https://www.amazon.fr/s?k=Broché&i=stripbooks",
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
    scraper = ScraperAmazonBroché(mode_forcee=mode_forcee)

    print(f"🚀 Démarrage du scraper v3.0 pour: Broché")
    print("🔧 Fonctionnalités actives:")
    print("   ✅ Anti-doublon intelligent")
    print("   ✅ Mise à jour automatique JSON")
    print("   ✅ Extraction complète (50+ champs)")
    print("   ✅ Backup automatique")
    print("   ✅ Métriques détaillées")

    # Lancement avec toutes les fonctionnalités v3.0
    total_nouveaux = scraper.run_complet()

    if total_nouveaux > 0:
        print(f"\n✅ SUCCÈS: {total_nouveaux} nouveaux livres ajoutés pour Broché")
    else:
        print(f"\n✅ TERMINÉ: Base de données à jour pour Broché")

if __name__ == "__main__":
    main()
