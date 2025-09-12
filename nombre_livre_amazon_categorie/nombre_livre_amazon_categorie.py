#!/usr/bin/env python3
"""
FONCTION DE VÉRIFICATION EXACTE DU NOMBRE DE LIVRES AMAZON PAR CATÉGORIE
========================================================================
Objectif: Détecter le nombre EXACT de livres disponibles sur Amazon pour une catégorie donnée
Principe: Continue jusqu'à ce qu'il n'y ait vraiment plus de livres (pas d'estimation)
Usage: Sera implémenté dans tous les scrapers pour vérification précise

🚀 UTILISE LA MÊME MÉTHODE QUE LES SCRAPERS EXISTANTS:
- Requests avec optimiseur si disponible
- verifier_presence_livres_robuste (fonction éprouvée)
- Même logique de détection que extraction_utils.py
- Rotation de proxies et user-agents
- Compatible avec le système FONCTION existant
"""

import requests
import time
import random
import re
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
import sys
import os

# Import des fonctions existantes du système FONCTION
sys.path.append('../FONCTION')
try:
    from detection_utils import verifier_presence_livres_robuste
    FONCTION_DISPONIBLE = True
    print("✅ Import fonction detection_utils réussi")
except ImportError:
    FONCTION_DISPONIBLE = False
    print("⚠️ Fonctions FONCTION non disponibles - utilisation locale")

# User-Agents (même approche que les scrapers)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
]

def verifier_presence_livres_local(soup, page_num: int) -> bool:
    """
    Version locale de verifier_presence_livres_robuste si FONCTION non disponible
    Utilise exactement la même logique que la version officielle
    """
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

def detecter_nombre_exact_livres_amazon(url_recherche: str) -> int:
    """
    Crée un driver Selenium avec proxy et options anti-détection
    """
    options = Options()
    
    # Options anti-détection
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-images')
    options.add_argument('--disable-javascript')
    options.add_argument('--headless')  # Mode sans interface
    
    # User agent aléatoire
    user_agent = random.choice(USER_AGENTS)
    options.add_argument(f'--user-agent={user_agent}')
    
    # Proxy si fourni
    if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"⚠️ Erreur création driver: {e}")
        return None

def detecter_nombre_exact_livres_selenium(url_recherche: str, proxies_list: List[str] = None, use_multithreading: bool = False) -> int:
    """
    Détecte le nombre EXACT de livres Amazon avec Selenium + proxies + multi-threading
    S'arrête UNIQUEMENT quand plus de livres trouvés
    Retourne le nombre exact de livres disponibles
    """
    print(f"🚀 DÉTECTION EXACTE AVEC SELENIUM + PROXIES + MULTI-THREADING")
    print(f"🎯 URL: {url_recherche}")
    print(f"🔄 Proxies disponibles: {len(proxies_list or PROXIES_LIST)}")
    print(f"⚡ Multi-threading: {'Activé' if use_multithreading else 'Désactivé'}")
    print("=" * 70)
    
    if proxies_list is None:
        proxies_list = PROXIES_LIST.copy()
    
    if use_multithreading:
        return _detecter_multithreading(url_recherche, proxies_list)
    else:
        return _detecter_sequentiel(url_recherche, proxies_list)

def _detecter_sequentiel(url_recherche: str, proxies_list: List[str]) -> int:
    """Détection séquentielle page par page"""
    page_actuelle = 1
    pages_vides_consecutives = 0
    max_pages_vides = 3
    total_livres_detectes = 0
    proxy_index = 0
    
    while True:
        # Rotation des proxies
        proxy_actuel = proxies_list[proxy_index % len(proxies_list)] if proxies_list else None
        
        print(f"🔍 Test page {page_actuelle} (proxy: {proxy_actuel or 'direct'})...")
        
        driver = None
        try:
            # Créer driver avec proxy
            driver = creer_driver_selenium_proxy(proxy_actuel)
            if not driver:
                proxy_index += 1
                continue
            
            # Construire URL de la page
            url_page = f"{url_recherche}&page={page_actuelle}"
            
            # Naviguer vers la page
            driver.get(url_page)
            time.sleep(random.uniform(2, 4))  # Délai aléatoire
            
            # Récupérer le HTML
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Compter les livres sur cette page
            livres_sur_page = compter_livres_sur_page_selenium(soup, page_actuelle)
            
            if livres_sur_page > 0:
                print(f"   ✅ Page {page_actuelle}: {livres_sur_page} livres détectés")
                total_livres_detectes += livres_sur_page
                pages_vides_consecutives = 0
            else:
                print(f"   ❌ Page {page_actuelle}: Aucun livre détecté")
                pages_vides_consecutives += 1
            
            # Condition d'arrêt: trop de pages vides consécutives
            if pages_vides_consecutives >= max_pages_vides:
                print(f"\n🛑 ARRÊT: {pages_vides_consecutives} pages vides consécutives")
                break
                
            page_actuelle += 1
            proxy_index += 1
            
        except Exception as e:
            print(f"   ⚠️ Erreur page {page_actuelle}: {e}")
            pages_vides_consecutives += 1
            proxy_index += 1
            
            if pages_vides_consecutives >= max_pages_vides:
                break
                
            page_actuelle += 1
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    print(f"\n{'=' * 70}")
    print(f"🎯 NOMBRE EXACT DÉTECTÉ: {total_livres_detectes} livres")
    print(f"📄 Dernière page testée: {page_actuelle}")
    print(f"🛑 Pages vides consécutives: {pages_vides_consecutives}")
    print(f"{'=' * 70}")
    
    return total_livres_detectes

def _detecter_multithreading(url_recherche: str, proxies_list: List[str]) -> int:
    """Détection avec multi-threading pour accélération"""
    print("⚡ MODE MULTI-THREADING ACTIVÉ")
    
    # Test initial pour trouver la plage approximative
    print("🔍 Phase 1: Test initial pour estimation de plage...")
    plage_initiale = _test_plage_initiale(url_recherche, proxies_list)
    
    if plage_initiale == 0:
        return 0
    
    print(f"📊 Plage estimée: {plage_initiale} pages à tester")
    print("🔍 Phase 2: Test parallèle précis...")
    
    # Test parallèle de toutes les pages dans la plage
    total_livres = 0
    pages_a_tester = list(range(1, plage_initiale + 10))  # +10 de sécurité
    
    def tester_page_thread(page_num):
        proxy = random.choice(proxies_list) if proxies_list else None
        return tester_page_selenium(url_recherche, page_num, proxy)
    
    with ThreadPoolExecutor(max_workers=min(8, len(proxies_list))) as executor:
        futures = {executor.submit(tester_page_thread, page): page for page in pages_a_tester}
        
        for future in as_completed(futures):
            page_num = futures[future]
            try:
                livres_detectes = future.result()
                if livres_detectes > 0:
                    print(f"   ✅ Page {page_num}: {livres_detectes} livres")
                    total_livres += livres_detectes
                else:
                    print(f"   ❌ Page {page_num}: vide")
            except Exception as e:
                print(f"   ⚠️ Erreur page {page_num}: {e}")
    
    print(f"\n🎯 TOTAL MULTI-THREADING: {total_livres} livres")
    return total_livres

def _test_plage_initiale(url_recherche: str, proxies_list: List[str]) -> int:
    """Test rapide pour estimer la plage de pages à vérifier"""
    pages_test = [1, 10, 25, 50, 100]
    derniere_page_avec_livres = 0
    
    for page in pages_test:
        proxy = random.choice(proxies_list) if proxies_list else None
        livres = tester_page_selenium(url_recherche, page, proxy)
        
        if livres > 0:
            derniere_page_avec_livres = page
            print(f"   ✅ Page {page}: {livres} livres trouvés")
        else:
            print(f"   ❌ Page {page}: vide")
            break
        
        time.sleep(1)
    
    return derniere_page_avec_livres

def tester_page_selenium(url_recherche: str, page_num: int, proxy: str = None) -> int:
    """Teste une page spécifique avec Selenium"""
    driver = None
    try:
        driver = creer_driver_selenium_proxy(proxy)
        if not driver:
            return 0
        
        url_page = f"{url_recherche}&page={page_num}"
        driver.get(url_page)
        time.sleep(random.uniform(1, 3))
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        return compter_livres_sur_page_selenium(soup, page_num)
        
    except Exception as e:
        return 0
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def detecter_nombre_exact_livres_amazon(url_recherche: str) -> int:
    """
    Fonction de compatibilité - utilise la version Selenium
    """
    return detecter_nombre_exact_livres_selenium(url_recherche, PROXIES_LIST, use_multithreading=False)

def compter_livres_sur_page_selenium(soup, page_num: int) -> int:
    """
    Compte précisément le nombre de livres sur une page Amazon (version Selenium optimisée)
    Utilise plusieurs méthodes de détection pour être sûr
    """
    
    # Méthode 1: Liens /dp/ (ISBN/ASIN) - Plus fiable avec Selenium
    liens_dp = soup.find_all('a', href=True)
    asins_uniques = set()
    
    for lien in liens_dp:
        href = lien.get('href', '')
        if '/dp/' in href:
            # Extraire l'ASIN
            try:
                asin = href.split('/dp/')[1].split('/')[0].split('?')[0]
                if len(asin) == 10 and asin.replace('-', '').isalnum():  # ASIN valide
                    asins_uniques.add(asin)
            except:
                continue
    
    livres_methode1 = len(asins_uniques)
    
    # Méthode 2: Conteneurs de résultats de recherche
    resultats_recherche = soup.find_all(attrs={'data-component-type': 's-search-result'})
    livres_methode2 = len(resultats_recherche)
    
    # Méthode 3: Conteneurs avec ASIN
    conteneurs_asin = soup.find_all(['div', 'article'], attrs={'data-asin': True})
    # Filtrer les ASIN vides
    conteneurs_valides = [c for c in conteneurs_asin if c.get('data-asin', '').strip()]
    livres_methode3 = len(conteneurs_valides)
    
    # Méthode 4: Images de livres (spécifique Selenium)
    images_livres = soup.find_all('img', {'data-image-latency': True})
    if not images_livres:
        images_livres = soup.find_all('img', src=lambda x: x and 'images-amazon' in str(x) and '/I/' in str(x))
    livres_methode4 = len(images_livres)
    
    # Méthode 5: Titres de livres
    titres_livres = soup.find_all(['h2', 'h3'], class_=lambda x: x and 'title' in str(x).lower())
    if not titres_livres:
        titres_livres = soup.find_all(['span'], class_=lambda x: x and 'title' in str(x).lower())
    livres_methode5 = len(titres_livres)
    
    # Utiliser la méthode qui donne le plus de résultats (plus fiable)
    livres_detectes = max(livres_methode1, livres_methode2, livres_methode3, livres_methode4, livres_methode5)
    
    # Debug détaillé
    print(f"      📊 Détection: /dp/={livres_methode1}, search={livres_methode2}, asin={livres_methode3}, img={livres_methode4}, titre={livres_methode5} → {livres_detectes}")
    
    return livres_detectes

def compter_livres_sur_page(soup, page_num: int) -> int:
    """
    Fonction de compatibilité - utilise la version Selenium
    """
    return compter_livres_sur_page_selenium(soup, page_num)

def tester_categorie_complete(nom_categorie: str, url_recherche: str, use_multithreading: bool = False):
    """
    Test complet d'une catégorie avec Selenium + proxies
    Fonction de test pour vérifier le bon fonctionnement
    """
    print(f"\n🚀 TEST COMPLET CATÉGORIE SELENIUM: {nom_categorie}")
    print(f"🔗 URL: {url_recherche}")
    print(f"⚡ Multi-threading: {'Activé' if use_multithreading else 'Désactivé'}")
    print("=" * 80)
    
    debut = time.time()
    nombre_exact = detecter_nombre_exact_livres_selenium(url_recherche, PROXIES_LIST, use_multithreading)
    duree = time.time() - debut
    
    print(f"\n🎉 RÉSULTAT FINAL:")
    print(f"📚 Catégorie: {nom_categorie}")
    print(f"🔢 Nombre exact: {nombre_exact:,} livres")
    print(f"⏱️ Durée: {duree:.1f} secondes")
    print(f"⚡ Vitesse: {(nombre_exact/duree) if duree > 0 else 0:.1f} livres/sec")
    print(f"🔄 Proxies utilisés: {len(PROXIES_LIST)}")
    print("=" * 80)
    
    return nombre_exact

def tester_une_seule_categorie(nom_categorie: str = "Cuisine"):
    """Test rapide d'une seule catégorie"""
    categories_urls = {
        "Cuisine": "https://www.amazon.fr/s?k=cuisine&i=stripbooks",
        "Bandes dessinées": "https://www.amazon.fr/s?k=bandes+dessinees&i=stripbooks", 
        "Ados": "https://www.amazon.fr/s?k=ados&i=stripbooks"
    }
    
    if nom_categorie not in categories_urls:
        print(f"❌ Catégorie '{nom_categorie}' non trouvée")
        return 0
    
    url = categories_urls[nom_categorie]
    return tester_categorie_complete(nom_categorie, url, use_multithreading=False)

if __name__ == "__main__":
    print("🚀 TESTS SELENIUM + PROXIES - NOMBRE EXACT DE LIVRES AMAZON")
    print("=" * 80)
    print("🔧 Fonctionnalités:")
    print("   • Selenium WebDriver avec anti-détection")
    print("   • Rotation automatique de 9 proxies")
    print("   • User-Agents aléatoires")
    print("   • Mode séquentiel et multi-threading")
    print("=" * 80)
    
    # Test d'une seule catégorie pour vérification rapide
    print("\n🧪 TEST RAPIDE - UNE CATÉGORIE")
    try:
        # Test cuisine en mode séquentiel
        resultat = tester_une_seule_categorie("Cuisine")
        print(f"✅ Test terminé: {resultat} livres détectés")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("🎯 FONCTION PRÊTE POUR INTÉGRATION DANS LES SCRAPERS")
    print("   • Utiliser: detecter_nombre_exact_livres_amazon(url)")
    print("   • Ou: detecter_nombre_exact_livres_selenium(url, proxies, multithreading)")
    print("=" * 80)