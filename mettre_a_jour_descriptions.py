#!/usr/bin/env python3
"""
MISE À JOUR MANUELLE DES DESCRIPTIONS - TOUS LES LIVRES
======================================================
Script pour mettre à jour toutes les descriptions avec Selenium
"""

import sys
import os
import json
from datetime import datetime

# Import des fonctions
sys.path.append(os.path.join(os.path.dirname(__file__), 'FONCTION'))
from description import recuperer_description_depuis_url

def mettre_a_jour_toutes_descriptions():
    """
    Met à jour toutes les descriptions du JSON avec Selenium
    """
    # Charger le JSON
    fichier_json = 'LIVRES/science_fiction/livres_science_fiction_20250922_095730.json'

    with open(fichier_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    livres = data['livres']
    total_livres = len(livres)

    print(f"🚀 MISE À JOUR DE {total_livres} DESCRIPTIONS")
    print("=" * 60)

    descriptions_trouvees = 0

    for i, livre in enumerate(livres):
        print(f"\n📖 Livre {i+1}/{total_livres}: {livre.get('titre', 'Sans titre')[:50]}...")

        if livre.get('url') and livre['url'] != "URL non trouvée":
            # Forcer l'extraction avec Selenium
            nouvelle_description = recuperer_description_depuis_url(livre['url'])
            livre['description'] = nouvelle_description

            if nouvelle_description != "Description non trouvée":
                descriptions_trouvees += 1
                print(f"✅ Description extraite: {nouvelle_description[:80]}...")
            else:
                print("❌ Aucune description trouvée")
        else:
            livre['description'] = "Description non trouvée"
            print("❌ Pas d'URL valide")

    # Mettre à jour les métadonnées
    data['metadata']['date_maj_descriptions'] = datetime.now().isoformat()
    data['metadata']['descriptions_trouvees'] = descriptions_trouvees

    # Sauvegarder
    with open(fichier_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n🎯 RÉSULTATS FINAUX:")
    print(f"Total livres traités: {total_livres}")
    print(f"Descriptions trouvées: {descriptions_trouvees}")
    print(f"Taux de succès: {round(descriptions_trouvees/total_livres*100, 1)}%")
    print(f"💾 JSON mis à jour: {fichier_json}")

if __name__ == "__main__":
    mettre_a_jour_toutes_descriptions()