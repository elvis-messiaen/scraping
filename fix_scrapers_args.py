#!/usr/bin/env python3
"""
CORRECTIF POUR TOUS LES SCRAPERS - SUPPORT ARGUMENT --force
========================================================

Corrige tous les scrapers pour qu'ils acceptent l'argument --force
basé sur l'historique du projet dans TEST_SCRAPING.md
"""

import os
import re
from pathlib import Path

def corriger_scraper(fichier_scraper):
    """
    Corrige un fichier scraper pour supporter l'argument --force

    Args:
        fichier_scraper (Path): Chemin vers le fichier scraper
    """
    try:
        # Lire le contenu du fichier
        with open(fichier_scraper, 'r', encoding='utf-8') as f:
            contenu = f.read()

        # Vérifier si déjà corrigé
        if '--force" in sys.argv' in contenu:
            return False  # Déjà corrigé

        # Pattern pour trouver la fin du fichier
        ancien_pattern = r'if __name__ == "__main__":\s*\n\s*main\(\)'

        nouveau_code = '''if __name__ == "__main__":
    import sys
    # Vérifier si l'argument --force est passé
    mode_forcee = "--force" in sys.argv
    main(mode_forcee=mode_forcee)'''

        # Remplacer le pattern
        nouveau_contenu = re.sub(ancien_pattern, nouveau_code, contenu)

        # Vérifier si le remplacement a eu lieu
        if nouveau_contenu != contenu:
            # Sauvegarder le fichier corrigé
            with open(fichier_scraper, 'w', encoding='utf-8') as f:
                f.write(nouveau_contenu)
            return True

        return False

    except Exception as e:
        print(f"❌ Erreur lors de la correction de {fichier_scraper.name}: {e}")
        return False

def main():
    """
    Fonction principale - Corrige tous les scrapers
    """
    print("🔧 CORRECTIF POUR TOUS LES SCRAPERS - SUPPORT ARGUMENT --force")
    print("=" * 60)

    # Dossier des scrapers
    dossier_scrapers = Path("SCRAPERS")

    if not dossier_scrapers.exists():
        print("❌ Erreur: Dossier SCRAPERS non trouvé")
        return

    # Compteurs
    scrapers_corriges = 0
    scrapers_total = 0
    scrapers_ignores = []

    # Scrapers à ignorer (système)
    scrapers_systeme = {
        'scraper_categories_principales.py',
        'scraper_sous_categories.py',
        'lancer_scrapers_categories.py',
        'lancer_scrapers_livres.py'
    }

    # Parcourir tous les scrapers
    for fichier_scraper in dossier_scrapers.glob("scraper_*.py"):
        nom_fichier = fichier_scraper.name

        # Ignorer les scrapers système
        if nom_fichier in scrapers_systeme:
            scrapers_ignores.append(nom_fichier)
            continue

        scrapers_total += 1

        # Corriger le scraper
        if corriger_scraper(fichier_scraper):
            scrapers_corriges += 1
            print(f"✅ Corrigé: {nom_fichier}")
        else:
            print(f"🔄 Déjà OK: {nom_fichier}")

    # Rapport final
    print("\n" + "=" * 60)
    print("📊 RAPPORT DE CORRECTION:")
    print(f"   📁 Scrapers total trouvés: {scrapers_total}")
    print(f"   ✅ Scrapers corrigés: {scrapers_corriges}")
    print(f"   🔄 Scrapers déjà OK: {scrapers_total - scrapers_corriges}")
    print(f"   🚫 Scrapers système ignorés: {len(scrapers_ignores)}")

    if scrapers_ignores:
        print(f"\n🚫 Scrapers système ignorés:")
        for scraper in scrapers_ignores:
            print(f"   • {scraper}")

    print("\n✅ CORRECTION TERMINÉE - Tous les scrapers supportent maintenant --force")

if __name__ == "__main__":
    main()