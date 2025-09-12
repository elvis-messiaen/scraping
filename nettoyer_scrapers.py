#!/usr/bin/env python3
"""
Script pour retirer la méthode ajouter_au_complet_json de tous les scrapers
"""

import os
import re
from typing import List

def nettoyer_scraper(chemin_fichier: str) -> bool:
    """Retire la méthode ajouter_au_complet_json d'un scraper"""
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            contenu = f.read()
        
        # Vérifier si la méthode existe
        if 'ajouter_au_complet_json' not in contenu:
            print(f"✅ {os.path.basename(chemin_fichier)} - Déjà nettoyé")
            return True
        
        # 1. Supprimer la méthode ajouter_au_complet_json complète
        pattern_methode = r'\n    def ajouter_au_complet_json\(self, nouveaux_livres: List\[dict\]\):.*?(?=\n    def |\nclass |\nif __name__|$)'
        contenu = re.sub(pattern_methode, '', contenu, flags=re.DOTALL)
        
        # 2. Supprimer l'appel dans sauvegarder_progres_complet
        pattern_appel_sauvegarde = r'\n            \n            # Ajouter à complet\.json\n            self\.ajouter_au_complet_json\(self\.livres_scraped\)'
        contenu = re.sub(pattern_appel_sauvegarde, '', contenu)
        
        # 3. Supprimer l'appel dans la boucle principale
        pattern_appel_boucle = r'\n                    \n                    # Ajouter immédiatement à complet\.json\n                    self\.ajouter_au_complet_json\(livres_nouveaux\)'
        contenu = re.sub(pattern_appel_boucle, '', contenu)
        
        # 4. Nettoyer les imports inutiles si pas d'autres utilisations de json
        # (on garde json car il peut être utilisé ailleurs)
        
        # Sauvegarder le fichier nettoyé
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(contenu)
        
        print(f"✅ {os.path.basename(chemin_fichier)} - Nettoyé avec succès")
        return True
        
    except Exception as e:
        print(f"❌ {os.path.basename(chemin_fichier)} - Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    dossier_scrapers = '/Users/Simplon/Cours/workspacePython/Scraping/SCRAPERS'
    
    if not os.path.exists(dossier_scrapers):
        print(f"❌ Dossier introuvable: {dossier_scrapers}")
        return
    
    # Lister tous les scrapers
    scrapers = [f for f in os.listdir(dossier_scrapers) 
                if f.startswith('scraper_') and f.endswith('.py') and f != 'scraper_categorie.py']
    
    print(f"🧹 NETTOYAGE DE {len(scrapers)} SCRAPERS")
    print("=" * 50)
    
    nettoyes = 0
    for scraper in scrapers:
        chemin_scraper = os.path.join(dossier_scrapers, scraper)
        if nettoyer_scraper(chemin_scraper):
            nettoyes += 1
    
    print("=" * 50)
    print(f"📊 RÉSULTAT: {nettoyes}/{len(scrapers)} scrapers nettoyés")
    print("✅ Toutes les méthodes ajouter_au_complet_json supprimées")

if __name__ == "__main__":
    main()