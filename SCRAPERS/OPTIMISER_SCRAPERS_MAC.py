#!/usr/bin/env python3
"""
OPTIMISATION DES SCRAPERS POUR MAC
Réduit le parallélisme pour éviter les crashes Chrome et surcharge Mac
"""

import os
import re

def optimiser_scrapers_pour_mac():
    """Réduit les paramètres de parallélisme dans tous les scrapers"""
    print("🔧 OPTIMISATION DES SCRAPERS POUR PERFORMANCE MAC")
    print("=" * 60)
    
    # Nouveaux paramètres optimisés pour Mac
    nouveaux_parametres = {
        'max_workers': 50,      # 50 au lieu de 200
        'pool_size': 15,        # 15 au lieu de 50  
        'batch_size': 30,       # 30 au lieu de 100
        'request_delay': 0.2,   # 200ms au lieu de 100ms
        'timeout_livre': 20,    # 20s au lieu de 30s
        'timeout_page': 10,     # 10s au lieu de 8s
        'wait_implicit': 2      # 2s au lieu de 1s
    }
    
    scrapers_modifies = 0
    
    # Trouver tous les scrapers
    scrapers = [f for f in os.listdir('.') if f.startswith('scraper_') and f.endswith('.py')]
    
    for scraper_file in scrapers:
        try:
            with open(scraper_file, 'r', encoding='utf-8') as f:
                contenu = f.read()
            
            contenu_original = contenu
            
            # 1. Réduire max_workers
            contenu = re.sub(
                r'self\.max_workers = \d+',
                f'self.max_workers = {nouveaux_parametres["max_workers"]}',
                contenu
            )
            
            # 2. Réduire pool_size 
            contenu = re.sub(
                r'self\.pool_size = \d+',
                f'self.pool_size = {nouveaux_parametres["pool_size"]}',
                contenu
            )
            
            # 3. Augmenter request_delay
            contenu = re.sub(
                r'self\.request_delay = [0-9.]+',
                f'self.request_delay = {nouveaux_parametres["request_delay"]}',
                contenu
            )
            
            # 4. Réduire batch_size
            contenu = re.sub(
                r'batch_size = min\(\d+, len\(self\.drivers_pool\) \* 2\)',
                f'batch_size = min({nouveaux_parametres["batch_size"]}, len(self.drivers_pool) * 2)',
                contenu
            )
            
            # 5. Augmenter timeout par livre
            contenu = re.sub(
                r'resultat = future\.result\(timeout=\d+\)',
                f'resultat = future.result(timeout={nouveaux_parametres["timeout_livre"]})',
                contenu
            )
            
            # 6. Ajuster timeouts Chrome
            contenu = re.sub(
                r'driver\.set_page_load_timeout\(\d+\)',
                f'driver.set_page_load_timeout({nouveaux_parametres["timeout_page"]})',
                contenu
            )
            
            contenu = re.sub(
                r'driver\.implicitly_wait\(\d+\)',
                f'driver.implicitly_wait({nouveaux_parametres["wait_implicit"]})',
                contenu
            )
            
            # 7. Ajouter commentaire d'optimisation
            if '# Configuration parallélisme extrême' in contenu:
                contenu = contenu.replace(
                    '# Configuration parallélisme extrême',
                    '# Configuration optimisée pour Mac (performance stable)'
                )
            
            # 8. Mettre à jour le commentaire du pool
            if 'POOL EXTRÊME CRÉÉ' in contenu:
                contenu = contenu.replace(
                    'POOL EXTRÊME CRÉÉ',
                    'POOL MAC OPTIMISÉ CRÉÉ'
                )
            
            # Sauvegarder si modifié
            if contenu != contenu_original:
                with open(scraper_file, 'w', encoding='utf-8') as f:
                    f.write(contenu)
                
                scrapers_modifies += 1
                print(f"✅ {scraper_file}")
            
        except Exception as e:
            print(f"❌ Erreur {scraper_file}: {e}")
    
    print(f"\n🎉 OPTIMISATION TERMINÉE: {scrapers_modifies} scrapers optimisés")
    print("\n📊 NOUVEAUX PARAMÈTRES MAC:")
    print(f"   Workers parallèles:    {nouveaux_parametres['max_workers']} (vs 200)")
    print(f"   Drivers physiques:     {nouveaux_parametres['pool_size']} (vs 50)")  
    print(f"   Batch size:           {nouveaux_parametres['batch_size']} (vs 100)")
    print(f"   Délai entre requêtes: {nouveaux_parametres['request_delay']}s (vs 0.1s)")
    print(f"   Timeout page:         {nouveaux_parametres['timeout_page']}s (vs 8s)")
    print(f"   Timeout livre:        {nouveaux_parametres['timeout_livre']}s (vs 30s)")
    
    print("\n🚀 PERFORMANCE ATTENDUE:")
    print("   ✅ Moins de crashes Chrome")
    print("   ✅ Moins de surcharge Mac")  
    print("   ✅ Plus de stabilité")
    print("   📉 Vitesse réduite mais plus fiable")
    
    return scrapers_modifies

if __name__ == "__main__":
    optimiser_scrapers_pour_mac()