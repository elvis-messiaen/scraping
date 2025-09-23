#!/usr/bin/env python3
"""
TEST SCRAPER - 10 LIVRES AVEC DESCRIPTIONS
==========================================
Test pour vérifier que les descriptions sont extraites correctement
"""

import sys
import os
import json
import time
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Import de la fonction de description
sys.path.append(os.path.join(os.path.dirname(__file__), 'FONCTION'))
from description import recuperation_description

def scraper_10_livres_test():
    """
    Scrape 10 livres avec descriptions depuis Amazon Science-Fiction
    """
    print("🚀 TEST SCRAPER - 10 LIVRES AVEC DESCRIPTIONS")
    print("=" * 50)

    url_base = "https://www.amazon.fr/s?k=science+fiction&i=stripbooks"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    print(f"Récupération de la page: {url_base}")
    response = requests.get(url_base, headers=headers, timeout=15)

    if response.status_code != 200:
        print(f"❌ Erreur HTTP: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    items = soup.select('.s-result-item[data-component-type="s-search-result"]')

    if not items:
        items = soup.select('.s-result-item')

    print(f"📚 Trouvé {len(items)} éléments sur la page")

    livres = []

    for i, item in enumerate(items[:10]):  # Limiter à 10
        print(f"\n--- Livre {i+1}/10 ---")

        # Titre
        titre_elem = item.select_one('h3 a') or item.select_one('.a-link-normal')
        titre = titre_elem.get_text(strip=True) if titre_elem else "Titre non trouvé"

        # Auteur
        auteur_text = item.get_text()
        import re
        auteur_match = re.search(r'de\s+([A-Za-zÀ-ÿ\s\-\.]+)', auteur_text)
        auteur = auteur_match.group(1).strip() if auteur_match else "Auteur non trouvé"

        # Prix
        prix_elem = item.select_one('.a-price .a-offscreen') or item.select_one('.a-price-whole')
        prix = prix_elem.get_text(strip=True) if prix_elem else "Prix non trouvé"

        # URL
        url_elem = item.select_one('h3 a') or item.select_one('.a-link-normal')
        if url_elem and url_elem.get('href'):
            href = url_elem.get('href')
            url = f"https://www.amazon.fr{href}" if href.startswith('/') else href
        else:
            url = "URL non trouvée"

        # DESCRIPTION avec la fonction
        print(f"🔍 Extraction description pour: {titre[:40]}...")
        description = recuperation_description(item)

        livre = {
            "numero": i+1,
            "titre": titre,
            "auteur": auteur,
            "prix": prix,
            "url": url,
            "description": description,
            "date_scraping": datetime.now().isoformat()
        }

        livres.append(livre)

        print(f"✅ Titre: {titre[:50]}...")
        print(f"👤 Auteur: {auteur}")
        print(f"💰 Prix: {prix}")
        print(f"📄 Description: {description[:60]}...")

        # Délai
        time.sleep(random.uniform(0.5, 1.0))

    # Sauvegarde
    fichier_test = "LIVRES/science_fiction/TEST_10_LIVRES.json"
    os.makedirs(os.path.dirname(fichier_test), exist_ok=True)

    data = {
        "metadata": {
            "test": "10 livres avec descriptions",
            "date": datetime.now().isoformat(),
            "total": len(livres)
        },
        "livres": livres
    }

    with open(fichier_test, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Sauvegardé dans: {fichier_test}")

    # Vérification des descriptions
    descriptions_trouvees = [l for l in livres if l['description'] != "Description non trouvée"]

    print(f"\n📊 RÉSULTATS:")
    print(f"Total livres: {len(livres)}")
    print(f"Descriptions trouvées: {len(descriptions_trouvees)}")
    print(f"Descriptions manquantes: {len(livres) - len(descriptions_trouvees)}")

    if len(descriptions_trouvees) == len(livres):
        print("✅ SUCCÈS: Toutes les descriptions ont été trouvées!")
        return True
    else:
        print("❌ ÉCHEC: Certaines descriptions manquent")
        return False

if __name__ == "__main__":
    success = scraper_10_livres_test()

    if success:
        # Créer le fichier TEST.md
        with open("TEST.md", "w", encoding="utf-8") as f:
            f.write(f"""# TEST - Extraction de Descriptions

## Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Résultat: ✅ SUCCÈS

**Test réalisé:** Extraction de descriptions sur 10 livres science-fiction Amazon

**Résultats:**
- ✅ Toutes les descriptions ont été extraites avec succès
- ✅ Fonctions du dossier FONCTION/ utilisées correctement
- ✅ Sauvegarde JSON fonctionnelle
- ✅ Système opérationnel à 100%

**Fichiers impliqués:**
- `FONCTION/description.py` - Fonctions d'extraction
- `test_scraper_10_livres.py` - Script de test
- `LIVRES/science_fiction/TEST_10_LIVRES.json` - Résultats

**Conclusion:** Le système de récupération de descriptions est fonctionnel et prêt pour utilisation en production.
""")
        print("\n📝 Fichier TEST.md créé avec succès!")