#!/usr/bin/env python3
"""
DEBUG HTML AMAZON - EXAMINER STRUCTURE RÉELLE
============================================
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_amazon_html():
    """Examine la structure HTML réelle d'Amazon"""

    url = "https://www.amazon.fr/b/?node=407116&ref_=Oct_d_odnav_301061&pd_rd_w=g9qg4&content-id=amzn1.sym.a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_p=a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_r=RZDAX1S372CDWBRKD9QK&pd_rd_wg=McLb6&pd_rd_r=757bd697-e1e1-4d4c-9051-89f7b618f570"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    try:
        print("🔍 Récupération de la page Amazon...")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        # Trouver les éléments de livres
        elements = soup.select('.octopus-pc-item')
        print(f"📚 Trouvé {len(elements)} éléments .octopus-pc-item")

        if not elements:
            print("❌ Aucun élément trouvé avec .octopus-pc-item")
            return

        # Examiner le premier élément en détail
        premier_element = elements[0]
        print(f"\n🔍 ANALYSE DU PREMIER ÉLÉMENT:")
        print(f"=" * 50)

        # Extraire le titre
        titre_elem = premier_element.select_one('a[href*="/dp/"]')
        if titre_elem:
            titre = titre_elem.get('title', '') or titre_elem.get_text(strip=True)
            print(f"📖 Titre: {titre}")

        # Examiner TOUS les spans pour chercher l'auteur
        print(f"\n🔍 TOUS LES SPANS dans l'élément:")
        spans = premier_element.find_all('span')
        for i, span in enumerate(spans[:20]):  # Limiter à 20 pour lisibilité
            text = span.get_text(strip=True)
            classes = span.get('class', [])
            if text and len(text) < 200:  # Éviter les très longs textes
                print(f"  Span {i}: '{text}' (classes: {classes})")

        # Examiner TOUS les liens
        print(f"\n🔍 TOUS LES LIENS dans l'élément:")
        links = premier_element.find_all('a', href=True)
        for i, link in enumerate(links[:10]):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            title = link.get('title', '')
            if text and len(text) < 200:
                print(f"  Link {i}: '{text}' href='{href[:50]}...' title='{title[:50]}...'")

        # Examiner les classes CSS spécifiques qu'on recherche
        print(f"\n🔍 SÉLECTEURS SPÉCIFIQUES:")
        selecteurs_test = [
            '.a-row .a-size-base:not(.a-color-secondary)',
            '.a-color-secondary .a-size-base',
            '.octopus-pc-author-info',
            '.octopus-pc-item .a-color-secondary',
            '[data-cy="title-recipe-review"] .a-size-base',
            '[data-a-target="byline-link"]',
            '[data-cy="byline-link"]',
        ]

        for selecteur in selecteurs_test:
            elem = premier_element.select_one(selecteur)
            if elem:
                text = elem.get_text(strip=True)
                print(f"  ✅ {selecteur}: '{text}'")
            else:
                print(f"  ❌ {selecteur}: Non trouvé")

        # Examiner le HTML brut de l'élément (première partie)
        print(f"\n🔍 HTML BRUT (premiers 1000 caractères):")
        html_brut = str(premier_element)[:1000]
        print(html_brut)

        # Chercher des patterns d'auteur dans le texte brut
        print(f"\n🔍 PATTERNS D'AUTEUR dans le texte:")
        texte_complet = premier_element.get_text(' ', strip=True)
        patterns = [
            r'de\s+([A-Za-zÀ-ÿ\s\-\.\']+?)(?:\s*\(|$|\s*,)',
            r'par\s+([A-Za-zÀ-ÿ\s\-\.\']+?)(?:\s*\(|$|\s*,)',
            r'by\s+([A-Za-zÀ-ÿ\s\-\.\']+?)(?:\s*\(|$|\s*,)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, texte_complet, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern '{pattern}': {matches}")
            else:
                print(f"  ❌ Pattern '{pattern}': Aucun match")

        print(f"\n🔍 TEXTE COMPLET DE L'ÉLÉMENT:")
        print(f"'{texte_complet[:500]}...'")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_amazon_html()