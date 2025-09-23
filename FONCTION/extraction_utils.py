#!/usr/bin/env python3
"""
Fonctions utilitaires pour l'extraction des informations de livres
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import Optional, Dict, Any, List

def extraire_infos_livre(element_livre, nom_categorie: str, urls_traitees: set) -> Optional[Dict[str, Any]]:
    """Extraction optimisée pour les nouveaux formats Amazon"""
    try:
        # Méthode 1: Chercher lien /dp/ dans l'élément
        lien_element = element_livre.find('a', href=True)
        if not lien_element:
            # Méthode alternative: chercher dans les sous-éléments
            lien_element = element_livre.find(['h2', 'h3']).find('a', href=True) if element_livre.find(['h2', 'h3']) else None
        
        if not lien_element:
            return None
            
        url_livre = lien_element.get('href', '')
        if not url_livre or '/dp/' not in url_livre:
            return None
        
        # URL complète
        if url_livre.startswith('/'):
            url_livre = f"https://www.amazon.fr{url_livre}"
        elif not url_livre.startswith('http'):
            url_livre = f"https://www.amazon.fr/{url_livre}"
        
        # Éviter les doublons
        if url_livre in urls_traitees:
            return None
        
        # Titre - plusieurs méthodes
        titre = ""
        # Méthode 1: Dans le lien
        titre_dans_lien = lien_element.get_text(strip=True)
        if titre_dans_lien and len(titre_dans_lien) > 5:
            titre = titre_dans_lien
        
        # Méthode 2: Span ou div avec titre
        if not titre:
            titre_element = element_livre.find(['span', 'div'], class_=re.compile(r'title|name', re.I))
            if titre_element:
                titre = titre_element.get_text(strip=True)
        
        # Méthode 3: H2/H3 avec titre
        if not titre:
            titre_element = element_livre.find(['h2', 'h3'])
            if titre_element:
                titre = titre_element.get_text(strip=True)
        
        if not titre or len(titre) < 3:
            titre = "Titre non disponible"
        
        # Auteur - recherche flexible
        auteur = ""
        auteur_selectors = [
            '[class*="author"]',
            '[class*="by"]',
            'span[class*="a-size-base"]'
        ]
        for selector in auteur_selectors:
            auteur_element = element_livre.select_one(selector)
            if auteur_element:
                auteur_text = auteur_element.get_text(strip=True)
                if auteur_text and 'de ' in auteur_text:
                    auteur = auteur_text
                    break
                elif auteur_text and len(auteur_text) > 2:
                    auteur = auteur_text
                    break
        
        # Prix - recherche flexible
        prix = ""
        prix_selectors = [
            '[class*="price"]',
            '[class*="a-price-whole"]',
            'span[class*="a-offscreen"]'
        ]
        for selector in prix_selectors:
            prix_element = element_livre.select_one(selector)
            if prix_element:
                prix_text = prix_element.get_text(strip=True)
                if '€' in prix_text or ',' in prix_text:
                    prix = prix_text
                    break
        
        # Note/étoiles
        note = ""
        note_element = element_livre.find(['span', 'i'], class_=re.compile(r'rating|star', re.I))
        if note_element:
            note = note_element.get('aria-label', note_element.get_text(strip=True))
        
        livre_info = {
            'titre': titre,
            'auteur': auteur if auteur else "Auteur non disponible", 
            'prix': prix if prix else "Prix non disponible",
            'note': note if note else "Note non disponible",
            'url': url_livre,
            'categorie': nom_categorie,
            'date_scraping': datetime.now().isoformat(),
            'source': 'Amazon FR'
        }
        
        # Ajouter à la liste des URLs traitées
        urls_traitees.add(url_livre)
        
        return livre_info
        
    except Exception as e:
        print(f"⚠️ Erreur extraction livre: {e}")
        return None

def extraire_infos_livre_url(url: str):
    """Extrait les informations d'un livre à partir de son URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraction des informations de base
        livre = {
            'url': url,
            'date_scraping': datetime.now().isoformat(),
            'titre': '',
            'auteur': '',
            'prix': '',
            'note': '',
            'nb_avis': '',
            'description': '',
            'stock': ''
        }
        
        # Titre
        titre_elem = soup.find('span', {'id': 'productTitle'})
        if titre_elem:
            livre['titre'] = titre_elem.get_text(strip=True)
        
        # Auteur
        auteur_elem = soup.find('span', class_='author')
        if not auteur_elem:
            auteur_elem = soup.find('a', {'data-asin-item-name': 'author'})
        if auteur_elem:
            livre['auteur'] = auteur_elem.get_text(strip=True)
        
        # Prix - avec regex amélioré pour capturer prix complets
        prix_elem = soup.find('span', {'class': 'a-offscreen'})  # Priorité à a-offscreen
        if not prix_elem:
            prix_elem = soup.find('span', class_='a-price-whole')

        if prix_elem:
            prix_text = prix_elem.get_text(strip=True)
            livre['prix'] = prix_text
        else:
            # Fallback: chercher avec regex amélioré dans tout le HTML
            texts = soup.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                if '€' in text_clean and any(c.isdigit() for c in text_clean):
                    import re
                    # Chercher patterns comme: 19,90 € ou 19€90 ou 19.90€
                    match = re.search(r'(\d+[,.]\d+\s*€|\d+\s*€\s*\d+|\d+\s*€)', text_clean)
                    if match:
                        livre['prix'] = match.group(1)
                        break
        
        # Note
        note_elem = soup.find('span', class_='a-icon-alt')
        if note_elem and 'étoiles' in note_elem.get_text():
            livre['note'] = note_elem.get_text(strip=True)
        
        # Description
        desc_elem = soup.find('div', {'id': 'feature-bullets'})
        if desc_elem:
            livre['description'] = desc_elem.get_text(strip=True)[:500]
        
        return livre
        
    except Exception as e:
        print(f"Erreur extraction {url}: {e}")
        return None

def scraper_page(url_base_recherche: str, page_num: int, nom_categorie: str, urls_traitees: set,
                verifier_presence_livres_robuste_func, optimiseur=None) -> List[Dict[str, Any]]:
    """Scrape optimisé pour Amazon moderne avec sélecteurs multiples"""
    print(f"\n🔄 SCRAPING PAGE {page_num} - {nom_categorie}")
    url_page = f"{url_base_recherche}&page={page_num}"
    print(f"🌐 URL: {url_page}")
    livres_page = []
    
    try:
        print(f"⏳ Connexion à Amazon page {page_num}...")
        # Utiliser l'optimiseur si disponible
        if optimiseur:
            print(f"🚀 Utilisation optimiseur pour page {page_num}")
            response = optimiseur.faire_requete_optimisee(url_page)
        else:
            print(f"📡 Requête standard pour page {page_num}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(url_page, headers=headers, timeout=10)
        print(f"✅ Réponse reçue: {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"🔍 Analyse de la page {page_num} pour détecter des livres...")
        # Vérifier présence de livres AVANT d'essayer d'extraire
        if not verifier_presence_livres_robuste_func(soup, page_num):
            print(f"❌ PAGE {page_num} VIDE - Aucun livre détecté")
            return []
        
        # Chercher les conteneurs de livres avec plusieurs sélecteurs
        conteneurs_livres = []
        
        # Méthode 1: Résultats de recherche standards
        resultats_standards = soup.find_all(attrs={'data-component-type': 's-search-result'})
        conteneurs_livres.extend(resultats_standards)
        
        # Méthode 2: Divs avec data-asin
        conteneurs_asin = soup.find_all('div', attrs={'data-asin': True})
        conteneurs_livres.extend(conteneurs_asin)
        
        # Méthode 3: Articles de produits
        articles_produits = soup.find_all('article', class_=re.compile(r'product|item', re.I))
        conteneurs_livres.extend(articles_produits)
        
        # Méthode 4: Divs génériques avec classes produits
        divs_generiques = soup.find_all('div', class_=re.compile(r'result|product|item', re.I))
        conteneurs_livres.extend(divs_generiques)
        
        # Supprimer les doublons
        conteneurs_uniques = []
        for conteneur in conteneurs_livres:
            if conteneur not in conteneurs_uniques:
                conteneurs_uniques.append(conteneur)
        
        print(f"📦 {len(conteneurs_uniques)} conteneurs trouvés pour extraction")
        print(f"🔍 Extraction des informations des livres...")
        
        for i, conteneur in enumerate(conteneurs_uniques, 1):
            livre_info = extraire_infos_livre(conteneur, nom_categorie, urls_traitees)
            if livre_info:
                livres_page.append(livre_info)
                if i <= 3:  # Afficher les 3 premiers
                    titre = livre_info.get('titre', 'Sans titre')[:50]
                    print(f"   {len(livres_page)}. ✅ {titre}...")
        
        print(f"✅ PAGE {page_num} TERMINÉE: {len(livres_page)} livres extraits")
        
    except Exception as e:
        print(f"❌ ERREUR PAGE {page_num}: {e}")
        print(f"⚠️ Continuation du scraping...")
    
    if livres_page:
        print(f"🎉 PAGE {page_num} RÉUSSIE: {len(livres_page)} nouveaux livres ajoutés")
    else:
        print(f"⚠️ PAGE {page_num}: Aucun livre récupéré")
    
    return livres_page