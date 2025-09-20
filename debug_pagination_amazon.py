#!/usr/bin/env python3
"""
DEBUG PAGINATION AMAZON - ANALYSER LES SÉLECTEURS RÉELS
======================================================
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_pagination_amazon():
    """Examine la structure de pagination réelle d'Amazon"""

    url = "https://www.amazon.fr/b/?_encoding=UTF8&node=202412631031&bbn=301061&ref_=Oct_d_odnav_301061&pd_rd_w=g9qg4&content-id=amzn1.sym.a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_p=a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_r=RZDAX1S372CDWBRKD9QK&pd_rd_wg=McLb6&pd_rd_r=757bd697-e1e1-4d4c-9051-89f7b618f570"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

    try:
        print("🔍 Récupération de la page Amazon Crime et polar...")
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        print(f"\n🔍 ANALYSE DE LA PAGINATION:")
        print(f"=" * 50)

        # Tester les sélecteurs actuels
        selecteurs_pagination = [
            'a[aria-label="Aller à la page suivante"]',
            'a[aria-label="Go to next page"]',
            '.s-pagination-next:not(.s-pagination-disabled)',
            '.a-pagination .a-last:not(.a-disabled)',
            'a[aria-label*="next" i]',
            'a[aria-label*="suivant" i]',
            '.a-pagination-button.a-enabled[aria-label*="suivant"]'
        ]

        for selecteur in selecteurs_pagination:
            elements = soup.select(selecteur)
            if elements:
                print(f"  ✅ {selecteur}: {len(elements)} éléments trouvés")
                for i, elem in enumerate(elements[:3]):
                    print(f"     Element {i}: {str(elem)[:200]}...")
            else:
                print(f"  ❌ {selecteur}: Non trouvé")

        # Chercher TOUS les liens avec "page" dans href
        print(f"\n🔍 LIENS AVEC 'page' DANS HREF:")
        links_page = soup.find_all('a', href=True)
        found_page_links = []
        for link in links_page:
            href = link.get('href', '')
            if 'page=' in href.lower():
                found_page_links.append(link)

        if found_page_links:
            print(f"  ✅ Trouvé {len(found_page_links)} liens avec 'page='")
            for i, link in enumerate(found_page_links[:5]):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                aria = link.get('aria-label', '')
                print(f"     Link {i}: href='{href[:100]}...' text='{text}' aria='{aria}'")
        else:
            print(f"  ❌ Aucun lien avec 'page=' trouvé")

        # Chercher TOUS les éléments avec pagination dans classe ou id
        print(f"\n🔍 ÉLÉMENTS AVEC 'pagination' DANS CLASSE/ID:")
        pagination_elements = soup.find_all(attrs={'class': re.compile(r'pagination', re.I)}) + \
                            soup.find_all(attrs={'id': re.compile(r'pagination', re.I)})

        if pagination_elements:
            print(f"  ✅ Trouvé {len(pagination_elements)} éléments pagination")
            for i, elem in enumerate(pagination_elements[:3]):
                classes = elem.get('class', [])
                elem_id = elem.get('id', '')
                print(f"     Element {i}: tag='{elem.name}' classes='{classes}' id='{elem_id}'")
                print(f"                  {str(elem)[:300]}...")
        else:
            print(f"  ❌ Aucun élément pagination trouvé")

        # Chercher des liens avec "Suivant", "Next", etc.
        print(f"\n🔍 LIENS AVEC TEXTE 'SUIVANT/NEXT':")
        text_keywords = ['suivant', 'next', 'page suivante', 'next page', '›', '→']
        found_text_links = []

        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True).lower()
            aria = link.get('aria-label', '').lower()
            title = link.get('title', '').lower()

            if any(keyword in text + aria + title for keyword in text_keywords):
                found_text_links.append(link)

        if found_text_links:
            print(f"  ✅ Trouvé {len(found_text_links)} liens avec texte navigation")
            for i, link in enumerate(found_text_links[:5]):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                aria = link.get('aria-label', '')
                title = link.get('title', '')
                classes = link.get('class', [])
                print(f"     Link {i}: text='{text}' aria='{aria}' title='{title}' classes='{classes}'")
                print(f"               href='{href[:100]}...'")
        else:
            print(f"  ❌ Aucun lien navigation trouvé")

        # Analyser le HTML brut pour patterns de pagination
        print(f"\n🔍 RECHERCHE PATTERNS DE PAGINATION DANS HTML BRUT:")
        html_content = str(soup)

        patterns = [
            r'page[=\s](\d+)',
            r'next.*page',
            r'suivant',
            r'pagination',
            r'page\s*(\d+)',
            r'&page=\d+',
            r'\?page=\d+'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                print(f"  ✅ Pattern '{pattern}': {len(matches)} matches - {matches[:10]}")
            else:
                print(f"  ❌ Pattern '{pattern}': Aucun match")

        # Chercher navigation par numéros de page
        print(f"\n🔍 NAVIGATION PAR NUMÉROS:")
        number_links = soup.find_all('a', string=re.compile(r'^\d+$'))
        if number_links:
            print(f"  ✅ Trouvé {len(number_links)} liens numériques")
            for i, link in enumerate(number_links[:5]):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                classes = link.get('class', [])
                print(f"     Link {i}: text='{text}' classes='{classes}' href='{href[:80]}...'")
        else:
            print(f"  ❌ Aucun lien numérique trouvé")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pagination_amazon()