#!/usr/bin/env python3
"""
Script pour modifier tous les scrapers afin qu'ils ajoutent leurs livres à complet.json
"""

import os
import re
import json
from typing import List

def modifier_scraper(chemin_fichier: str) -> bool:
    """Modifie un scraper pour qu'il ajoute à complet.json"""
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            contenu = f.read()
        
        # Vérifier si déjà modifié
        if 'ajouter_au_complet_json' in contenu:
            print(f"✅ {os.path.basename(chemin_fichier)} - Déjà modifié")
            return True
        
        # 1. Ajouter l'import json si pas présent
        if 'import json' not in contenu:
            contenu = re.sub(r'(import os\n)', r'\\1import json\n', contenu)
        
        # 2. Ajouter la méthode ajouter_au_complet_json après __init__
        methode_complet = '''
    def ajouter_au_complet_json(self, nouveaux_livres: List[dict]):
        """Ajoute les nouveaux livres à complet.json en évitant les doublons"""
        if not nouveaux_livres:
            return
        
        fichier_complet = os.path.join(os.path.dirname(self.dossier_livres), 'complet.json')
        
        try:
            # Charger le fichier complet existant
            if os.path.exists(fichier_complet):
                with open(fichier_complet, 'r', encoding='utf-8') as f:
                    tous_livres = json.load(f)
            else:
                tous_livres = []
            
            # Créer un set des URLs existantes pour éviter les doublons
            urls_existantes = {livre.get('url', '') for livre in tous_livres if livre.get('url')}
            
            # Ajouter seulement les nouveaux livres
            livres_ajoutes = 0
            for livre in nouveaux_livres:
                url_livre = livre.get('url', '')
                if url_livre and url_livre not in urls_existantes:
                    tous_livres.append(livre)
                    urls_existantes.add(url_livre)
                    livres_ajoutes += 1
            
            # Sauvegarder le fichier complet mis à jour
            with open(fichier_complet, 'w', encoding='utf-8') as f:
                json.dump(tous_livres, f, ensure_ascii=False, indent=2)
            
            if livres_ajoutes > 0:
                print(f"   📚 {livres_ajoutes} livres ajoutés à complet.json")
                
        except Exception as e:
            print(f"   ❌ Erreur ajout complet.json: {e}")
'''
        
        # Trouver la fin de __init__ et insérer la nouvelle méthode
        pattern_init = r'(    def __init__\(self\):.*?)(    def [^_])'
        if re.search(pattern_init, contenu, re.DOTALL):
            contenu = re.sub(pattern_init, r'\\1' + methode_complet + r'\\2', contenu, flags=re.DOTALL)
        else:
            # Fallback: ajouter après la première méthode trouvée
            pattern_first_method = r'(    def .*?)(    def [^_])'
            if re.search(pattern_first_method, contenu, re.DOTALL):
                contenu = re.sub(pattern_first_method, r'\\1' + methode_complet + r'\\2', contenu, flags=re.DOTALL)
        
        # 3. Modifier la méthode sauvegarder_progres_complet pour appeler ajouter_au_complet_json
        pattern_sauvegarde = r'(            # Sauvegarde JSON\n            with open\(self\.fichier_json, \'w\', encoding=\'utf-8\'\) as f:\n                json\.dump\(self\.livres_scraped, f, ensure_ascii=False, indent=2\))'
        remplacement_sauvegarde = r'\\1\n            \n            # Ajouter à complet.json\n            self.ajouter_au_complet_json(self.livres_scraped)'
        
        if re.search(pattern_sauvegarde, contenu):
            contenu = re.sub(pattern_sauvegarde, remplacement_sauvegarde, contenu)
        
        # 4. Ajouter aussi l'appel dans la boucle principale quand on ajoute de nouveaux livres
        pattern_nouveaux_livres = r'(                    with self\.lock:\n                        self\.livres_scraped\.extend\(livres_nouveaux\))'
        remplacement_nouveaux = r'\\1\n                    \n                    # Ajouter immédiatement à complet.json\n                    self.ajouter_au_complet_json(livres_nouveaux)'
        
        if re.search(pattern_nouveaux_livres, contenu):
            contenu = re.sub(pattern_nouveaux_livres, remplacement_nouveaux, contenu)
        
        # Sauvegarder le fichier modifié
        with open(chemin_fichier, 'w', encoding='utf-8') as f:
            f.write(contenu)
        
        print(f"✅ {os.path.basename(chemin_fichier)} - Modifié avec succès")
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
    
    print(f"🔧 MODIFICATION DE {len(scrapers)} SCRAPERS")
    print("=" * 50)
    
    modifies = 0
    for scraper in scrapers:
        chemin_scraper = os.path.join(dossier_scrapers, scraper)
        if modifier_scraper(chemin_scraper):
            modifies += 1
    
    print("=" * 50)
    print(f"📊 RÉSULTAT: {modifies}/{len(scrapers)} scrapers modifiés")
    print("✅ Tous les scrapers vont maintenant ajouter à complet.json")

if __name__ == "__main__":
    main()