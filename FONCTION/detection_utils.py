#!/usr/bin/env python3
"""
Fonctions utilitaires pour la détection de livres et pages Amazon
"""

import requests
import time
from bs4 import BeautifulSoup
import re

def verifier_presence_livres_robuste(soup, page_num: int) -> bool:
    """DÉTECTION AMÉLIORÉE: Vérifier plusieurs types d'éléments Amazon"""
    print(f"🔍 Vérification page {page_num}...")
    
    # MÉTHODE 1: Liens /dp/ directs
    liens_dp = soup.find_all('a', href=True)
    liens_dp_valides = []
    for link in liens_dp:
        href = link.get('href', '')
        if '/dp/' in href and len(href) > 10:
            liens_dp_valides.append(href)
    
    print(f"   🔗 {len(liens_dp_valides)} liens /dp/ trouvés")
    
    # MÉTHODE 2: Résultats de recherche Amazon
    resultats_recherche = soup.find_all(attrs={'data-component-type': 's-search-result'})
    print(f"   📦 {len(resultats_recherche)} résultats de recherche")
    
    # MÉTHODE 3: Conteneurs de produits
    conteneurs_produits = soup.find_all(['div', 'article'], attrs={'data-asin': True})
    print(f"   📚 {len(conteneurs_produits)} conteneurs avec ASIN")
    
    # MÉTHODE 4: Titres de livres
    titres_livres = soup.find_all(['h2', 'h3'], class_=re.compile(r'title|name', re.I))
    print(f"   📖 {len(titres_livres)} titres potentiels")
    
    # Critère de succès: au moins 5 liens /dp/ OU 10 résultats de recherche
    if len(liens_dp_valides) >= 5:
        print(f"   🎯 Page {page_num}: LIVRES CONFIRMÉS ({len(liens_dp_valides)} liens /dp/)")
        return True
    elif len(resultats_recherche) >= 10:
        print(f"   🎯 Page {page_num}: LIVRES CONFIRMÉS ({len(resultats_recherche)} résultats)")
        return True
    elif len(conteneurs_produits) >= 8:
        print(f"   🎯 Page {page_num}: LIVRES CONFIRMÉS ({len(conteneurs_produits)} ASIN)")
        return True
    elif len(liens_dp_valides) >= 2:
        print(f"   ✅ Page {page_num}: ACCEPTÉE ({len(liens_dp_valides)} liens)")
        return True
    
    # Sinon, probablement fin de catalogue
    print(f"   ❌ Page {page_num}: PAS ASSEZ DE LIVRES")
    return False

def tester_page_rapide(url_recherche: str, page: int) -> bool:
    """Test ultra-rapide d'une page pour détecter présence de livres (ISBN, images, titres)"""
    try:
        url_page = f"{url_recherche}&page={page}"
        response = requests.get(url_page, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }, timeout=8)
        
        if response.status_code != 200:
            return False
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Test 1: ISBN via liens /dp/ (le plus fiable)
        liens_isbn = soup.find_all('a', href=lambda x: x and '/dp/' in x)
        isbn_count = len([l for l in liens_isbn if '/dp/' in l.get('href', '')])
        
        # Test 2: Images de couvertures
        images_livres = soup.find_all('img', {'data-image-latency': True})
        if not images_livres:
            images_livres = soup.find_all('img', src=lambda x: x and 'images-amazon' in str(x))
        
        # Test 3: Titres de livres 
        titres_livres = soup.find_all(['h2', 'h3'], class_=lambda x: x and 'title' in str(x).lower())
        if not titres_livres:
            titres_livres = soup.find_all(['span'], class_=lambda x: x and 'title' in str(x).lower())
        
        # Test 4: Prix
        prix_elements = soup.find_all('span', class_='a-price-symbol')
        if not prix_elements:
            prix_elements = soup.find_all(['span'], class_=lambda x: x and 'price' in str(x).lower())
        
        # Debug info
        print(f"       ISBN/dp: {isbn_count}, Images: {len(images_livres)}, Titres: {len(titres_livres)}, Prix: {len(prix_elements)}")
        
        # Critères de validation stricts
        tests_resultats = [
            isbn_count >= 8,                # Au moins 8 liens ISBN/dp
            len(images_livres) >= 4,        # Au moins 4 images 
            len(titres_livres) >= 3,        # Au moins 3 titres
            len(prix_elements) >= 2         # Au moins 2 prix
        ]
        
        criteres_valides = sum(tests_resultats)
        
        # Au moins 3 des 4 critères pour considérer qu'il y a des livres
        return criteres_valides >= 3
        
    except Exception as e:
        print(f"       Erreur test page {page}: {e}")
        return False

def compter_livres_derniere_page(url_recherche: str, page: int) -> int:
    """Compte précisément les livres de la dernière page"""
    try:
        url_page = f"{url_recherche}&page={page}"
        response = requests.get(url_page, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }, timeout=8)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Compter les ASINs uniques (plus précis)
            liens_dp = soup.find_all('a', href=lambda x: x and '/dp/' in x)
            asins_uniques = set()
            for lien in liens_dp:
                href = lien.get('href', '')
                if '/dp/' in href:
                    asin = href.split('/dp/')[1].split('/')[0]
                    if len(asin) == 10:  # ASIN valide
                        asins_uniques.add(asin)
            
            return min(len(asins_uniques), 16)  # Max 16 par page
        return 8  # Défaut conservateur
    except:
        return 8  # Défaut conservateur

def detecter_total_amazon_actuel(url_recherche: str) -> int:
    """Détecte le nombre EXACT de livres Amazon - puis scrape 100% de cette estimation"""
    print("🔍 Détection EXACTE du nombre total de livres Amazon...")
    
    try:
        # Phase 1: Test par tranches fixes 25, 50, 100, 200, 300...
        print("📈 Phase 1: Test par tranches de 25 jusqu'à 400...")
        pages_test = [25, 50, 100, 200, 300]
        derniere_page_valide = 1
        
        for page in pages_test:
            print(f"🔍 Test page {page}...")
            if tester_page_rapide(url_recherche, page):
                print(f"   ✅ Page {page}: livres détectés")
                derniere_page_valide = page
            else:
                print(f"   ❌ Page {page}: vide - limite trouvée")
                break
            time.sleep(0.2)
        
        # Phase 2: Si on arrive à 300+, continuer par tranches de 25 jusqu'à 400
        if derniere_page_valide >= 300:
            print("📈 Phase 1b: Test tranches de 25 de 300 à 400...")
            for page in range(325, 401, 25):
                print(f"🔍 Test page {page}...")
                if tester_page_rapide(url_recherche, page):
                    print(f"   ✅ Page {page}: livres détectés")
                    derniere_page_valide = page
                else:
                    print(f"   ❌ Page {page}: vide - limite trouvée")
                    break
                time.sleep(0.2)
        
        # Phase 3: Recherche binaire précise dans la dernière tranche valide
        if derniere_page_valide >= 25:
            # Définir les bornes pour la recherche binaire
            if derniere_page_valide == 25:
                borne_inf = 1
                borne_sup = 50
            elif derniere_page_valide == 50:
                borne_inf = 26
                borne_sup = 75
            elif derniere_page_valide == 100:
                borne_inf = 51
                borne_sup = 125
            elif derniere_page_valide == 200:
                borne_inf = 101
                borne_sup = 225
            else:
                # Pour 300+ 
                borne_inf = derniere_page_valide - 25
                borne_sup = derniere_page_valide + 25
            
            print(f"🎯 Phase 2: Recherche binaire précise pages {borne_inf}-{borne_sup}")
            page_finale = derniere_page_valide
            
            while borne_inf <= borne_sup:
                milieu = (borne_inf + borne_sup) // 2
                print(f"🔍 Test binaire page {milieu}...")
                
                if tester_page_rapide(url_recherche, milieu):
                    print(f"   ✅ Page {milieu}: livres trouvés")
                    page_finale = milieu
                    borne_inf = milieu + 1
                else:
                    print(f"   ❌ Page {milieu}: vide")
                    borne_sup = milieu - 1
                
                time.sleep(0.2)
            
            # Calcul précis avec dernière page
            nombre_derniere = compter_livres_derniere_page(url_recherche, page_finale)
            total_exact = (page_finale - 1) * 16 + nombre_derniere
            print(f"🎯 ESTIMATION EXACTE: {total_exact:,} livres Amazon")
            print(f"   📊 {page_finale-1} pages complètes + {nombre_derniere} livres (page {page_finale})")
            print(f"🚀 OBJECTIF: Scraper 100% de ces {total_exact:,} livres")
            return total_exact
        
        else:
            print("⚠️ Moins de 25 pages avec livres - estimation conservatrice")
            total_conservateur = derniere_page_valide * 16
            print(f"🎯 ESTIMATION: {total_conservateur:,} livres")
            return total_conservateur
            
    except Exception as e:
        print(f"⚠️ Erreur détection: {e} - estimation par défaut")
        return 1600  # Défaut conservateur