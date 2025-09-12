#!/usr/bin/env python3
"""
RESTAURER L'AFFICHAGE COMPLET DANS TOUS LES SCRAPERS
Applique les mêmes améliorations d'affichage que scraper_cuisine.py à tous les autres scrapers
"""

import os
import re
import glob

def lire_fichier(fichier_path):
    """Lire le contenu d'un fichier"""
    try:
        with open(fichier_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Erreur lecture {fichier_path}: {e}")
        return None

def ecrire_fichier(fichier_path, contenu):
    """Écrire le contenu dans un fichier"""
    try:
        with open(fichier_path, 'w', encoding='utf-8') as f:
            f.write(contenu)
        return True
    except Exception as e:
        print(f"❌ Erreur écriture {fichier_path}: {e}")
        return False

def extraire_methode_run_cuisine():
    """Extraire la méthode run() mise à jour de scraper_cuisine.py"""
    cuisine_path = "scraper_cuisine.py"
    contenu_cuisine = lire_fichier(cuisine_path)
    
    if not contenu_cuisine:
        return None
    
    # Extraire la méthode run() complète
    pattern_run = r'(    def run\(self\):.*?(?=\n    def |\n\nif __name__|$))'
    match = re.search(pattern_run, contenu_cuisine, re.DOTALL)
    
    if match:
        return match.group(1)
    else:
        print("❌ Impossible d'extraire la méthode run() de scraper_cuisine.py")
        return None

def mise_a_jour_scraper(fichier_scraper, nouvelle_methode_run):
    """Mettre à jour un scraper avec la nouvelle méthode run()"""
    contenu = lire_fichier(fichier_scraper)
    if not contenu:
        return False
    
    # Remplacer la méthode run() existante
    pattern_run_existante = r'    def run\(self\):.*?(?=\n    def |\n\nif __name__|$)'
    
    if re.search(pattern_run_existante, contenu, re.DOTALL):
        nouveau_contenu = re.sub(pattern_run_existante, nouvelle_methode_run, contenu, flags=re.DOTALL)
        
        # Vérifier que le remplacement a fonctionné
        if nouveau_contenu != contenu:
            return ecrire_fichier(fichier_scraper, nouveau_contenu)
        else:
            print(f"⚠️ Aucune modification pour {fichier_scraper}")
            return False
    else:
        print(f"❌ Méthode run() non trouvée dans {fichier_scraper}")
        return False

def main():
    print("🚀 RESTAURATION AFFICHAGE COMPLET - TOUS LES SCRAPERS")
    print("=" * 60)
    
    # Extraire la méthode run() mise à jour de scraper_cuisine.py
    print("📖 Extraction de la méthode run() de scraper_cuisine.py...")
    nouvelle_methode_run = extraire_methode_run_cuisine()
    
    if not nouvelle_methode_run:
        print("❌ Impossible de continuer sans la méthode run() de référence")
        return
    
    print("✅ Méthode run() extraite avec succès")
    print(f"📏 Taille: {len(nouvelle_methode_run)} caractères")
    
    # Trouver tous les scrapers (sauf scraper_cuisine.py qui est déjà à jour)
    scrapers = glob.glob("scraper_*.py")
    scrapers = [s for s in scrapers if s != "scraper_cuisine.py"]
    
    print(f"🎯 {len(scrapers)} scrapers à mettre à jour")
    print("-" * 60)
    
    # Mettre à jour chaque scraper
    scrapers_reussis = 0
    scrapers_echoues = 0
    
    for i, scraper in enumerate(scrapers, 1):
        nom_scraper = os.path.basename(scraper)
        print(f"🔄 [{i}/{len(scrapers)}] Mise à jour {nom_scraper}...")
        
        if mise_a_jour_scraper(scraper, nouvelle_methode_run):
            print(f"   ✅ {nom_scraper} mis à jour avec succès")
            scrapers_reussis += 1
        else:
            print(f"   ❌ Échec mise à jour {nom_scraper}")
            scrapers_echoues += 1
    
    # Résultats finaux
    print("\n" + "=" * 60)
    print("🏁 RESTAURATION TERMINÉE")
    print(f"✅ Scrapers mis à jour: {scrapers_reussis}")
    print(f"❌ Scrapers échoués: {scrapers_echoues}")
    print(f"📊 Total: {len(scrapers)}")
    
    if scrapers_reussis > 0:
        print(f"\n🎉 SUCCÈS: {scrapers_reussis} scrapers ont maintenant l'affichage complet !")
        print("📺 Tous les scrapers affichent maintenant:")
        print("   - Messages de démarrage détaillés")
        print("   - Progression de détection Amazon")
        print("   - Chargement des données existantes")
        print("   - Progression page par page")
        print("   - Métriques complètes toutes les 10 pages")
        print("   - Sauvegardes automatiques")
        print("   - Découpage automatique")
    
    if scrapers_echoues > 0:
        print(f"\n⚠️ ATTENTION: {scrapers_echoues} scrapers n'ont pas pu être mis à jour")

if __name__ == "__main__":
    main()