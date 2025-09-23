import requests
from bs4 import BeautifulSoup
import time
import random
import os
import sqlite3
import threading
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import hashlib

# Imports pour undetected-chromedriver
try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    UNDETECTED_AVAILABLE = False

# Imports pour Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

def recuperation_description(item):
    """Extraction de la description pour nouveaux livres lors du scraping"""
    try:
        # Sélecteurs optimisés pour Amazon 2025
        desc_selectors = [
            # Description dans les résultats de recherche - Nouveaux 2025
            '[data-cy="reviews-block"] .a-size-small',
            '[data-cy="title-recipe-review"] .a-size-small',
            '.puis-card-container .a-size-small',
            '.s-card-container .a-size-small',

            # Sélecteurs classiques maintenus
            '.a-size-base-plus',
            '.s-size-base-plus',
            '.a-size-small .a-color-secondary',
            '.product-description',

            # Nouveaux sélecteurs Amazon 2025
            '.a-row .a-size-base',
            '.s-prose .s-color-base',
            '.a-section .a-spacing-none .a-color-base',
            '.a-row .a-spacing-mini .a-size-small',
            '.s-color-secondary .a-size-small',

            # Sélecteurs de contenu descriptif
            '[data-testid*="review"] .a-size-small',
            '.s-card-border .a-size-small:not([class*="price"])',

            # Fallback sur du texte général mais filtré
            '.a-spacing-top-micro .a-size-base'
        ]

        for selector in desc_selectors:
            desc_elem = item.select_one(selector)
            if desc_elem:
                text = desc_elem.get_text(strip=True)
                # Filtrer les textes non pertinents
                if (text and len(text) > 15 and
                    not text.startswith('Autres formats') and
                    not text.startswith('€') and
                    not text.startswith('Livraison') and
                    not text.startswith('En apprendre plus') and
                    'étoiles' not in text.lower() and
                    'avis' not in text.lower() and
                    'résultats' not in text.lower()):
                    return text

        return "Description non trouvée"
    except:
        return "Description non trouvée"

def mettre_a_jour_descriptions_existantes(livres_existants):
    """
    Met à jour les descriptions des livres existants dans le JSON

    Args:
        livres_existants (list): Liste des livres existants

    Returns:
        list: Liste des livres avec descriptions mises à jour
    """
    livres_mis_a_jour = []

    for livre in livres_existants:
        if not livre.get('description') or livre.get('description') == "Description non trouvée":
            # Le livre n'a pas de description, essayer de la récupérer
            if livre.get('url') and livre['url'] != "URL non trouvée":
                description = recuperer_description_depuis_url(livre['url'])
                livre['description'] = description
                print(f"Description mise à jour pour: {livre.get('titre', 'Titre inconnu')[:50]}...")
            else:
                livre['description'] = "Description non trouvée"

        livres_mis_a_jour.append(livre)

        # Pas de limite - traiter TOUS les livres

        # Délai pour éviter la détection
        time.sleep(random.uniform(1.0, 2.0))

    return livres_mis_a_jour

def generer_user_agents_rotation():
    """
    Génère une liste de User-Agents pour rotation anti-détection

    Returns:
        list: Liste de User-Agents variés
    """
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
    ]
    return user_agents

def generer_viewports_rotation():
    """
    Génère une liste de résolutions d'écran pour rotation anti-détection

    Returns:
        list: Liste de tuples (largeur, hauteur)
    """
    viewports = [
        (1920, 1080),  # Full HD
        (1366, 768),   # Laptop standard
        (1440, 900),   # MacBook
        (1536, 864),   # Windows standard
        (1280, 720),   # HD
        (1600, 900),   # 16:9 wide
        (1680, 1050),  # 16:10
        (1024, 768),   # 4:3 classic
        (1280, 1024),  # 5:4
        (1920, 1200)   # Full HD wide
    ]
    return viewports

def simuler_comportement_humain(driver):
    """
    Simule un comportement humain sur la page

    Args:
        driver: Driver Selenium
    """
    try:
        # Scroll aléatoire
        for _ in range(random.randint(2, 5)):
            scroll_y = random.randint(200, 800)
            driver.execute_script(f"window.scrollTo(0, {scroll_y});")
            time.sleep(random.uniform(0.5, 1.5))

        # Retour en haut
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(random.uniform(0.8, 2.0))

        # Simulation mouvement souris
        driver.execute_script("""
            var event = new MouseEvent('mousemove', {
                'view': window,
                'bubbles': true,
                'cancelable': true,
                'clientX': Math.random() * window.innerWidth,
                'clientY': Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        """)

        # Pause humaine
        time.sleep(random.uniform(1.0, 3.0))

    except Exception as e:
        print(f"⚠️ Erreur simulation comportement: {e}")

def creer_driver_selenium_anti_detection():
    """
    Crée un driver Selenium avec anti-détection maximale et simulation humaine

    Returns:
        webdriver.Chrome: Driver configuré avec anti-détection
    """
    try:
        # Configuration anti-détection maximale
        options = Options()

        # User-Agent et viewport rotatifs
        user_agents = generer_user_agents_rotation()
        user_agent = random.choice(user_agents)
        viewport = random.choice(generer_viewports_rotation())

        options.add_argument(f"--user-agent={user_agent}")
        options.add_argument(f"--window-size={viewport[0]},{viewport[1]}")

        # Headers avancés
        options.add_argument("--accept-lang=fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7")
        options.add_argument("--accept-charset=utf-8")

        # Anti-détection basique
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-logging")
        options.add_argument("--silent")

        # Anti-détection avancée
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-component-extensions-with-background-pages")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-extensions-file-access-check")
        options.add_argument("--disable-extensions-http-throttling")
        options.add_argument("--disable-field-trial-config")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-first-run")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--enable-automation")
        options.add_argument("--password-store=basic")
        options.add_argument("--use-mock-keychain")

        # Anti-fingerprinting WebRTC
        options.add_argument("--disable-webrtc")
        options.add_argument("--disable-webrtc-hw-decoding")
        options.add_argument("--disable-webrtc-hw-encoding")
        options.add_argument("--disable-webrtc-multiple-routes")
        options.add_argument("--disable-webrtc-hw-vp8-encoding")

        # Désactiver la détection WebDriver
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # Préférences anti-détection avancées
        prefs = {
            "profile.default_content_setting_values": {
                "images": 2,
                "plugins": 2,
                "popups": 2,
                "geolocation": 2,
                "notifications": 2,
                "media_stream": 2,
            },
            "profile.managed_default_content_settings": {
                "images": 2
            },
            "profile.content_settings.exceptions.webrtc": {
                "*": {
                    "setting": 2
                }
            }
        }
        options.add_experimental_option("prefs", prefs)

        # Créer le driver
        driver = webdriver.Chrome(options=options)

        # Scripts anti-détection WebDriver avancés
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("window.navigator.chrome = {runtime: {}};")
        driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['fr-FR', 'fr', 'en-US', 'en']});")
        driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});")

        # Anti-fingerprinting avancé
        driver.execute_script("""
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'platform', {get: () => 'MacIntel'});
            Object.defineProperty(screen, 'colorDepth', {get: () => 24});
        """)

        # Timeouts optimisés
        driver.set_page_load_timeout(20)
        driver.implicitly_wait(5)

        print(f"🚀 Driver Selenium créé - UA: {user_agent[:40]}... - Viewport: {viewport[0]}x{viewport[1]}")
        return driver

    except Exception as e:
        print(f"❌ Erreur création driver: {e}")
        return None

def recuperer_description_selenium_anti_detection(url):
    """
    Récupère la description avec Selenium et anti-détection maximale

    Args:
        url (str): URL de la page produit Amazon

    Returns:
        str: Description du livre
    """
    driver = None
    try:
        # Délai anti-détection avant de commencer
        time.sleep(random.uniform(3.0, 7.0))

        # Créer driver avec anti-détection
        driver = creer_driver_selenium_anti_detection()
        if not driver:
            return "Description non trouvée"

        print(f"🔍 Selenium - Accès à la page: {url[:60]}...")

        # Naviguer vers la page avec délai
        driver.get(url)

        # Attendre le chargement initial
        time.sleep(random.uniform(2.0, 5.0))

        # SIMULATION COMPORTEMENT HUMAIN
        simuler_comportement_humain(driver)

        # Vérifier si on a une page de blocage
        page_source = driver.page_source
        if "robot" in page_source.lower() or "captcha" in page_source.lower() or "503" in page_source:
            print("❌ Détection de blocage Amazon - Simulation humaine intense...")
            # Simulation plus intensive en cas de blocage
            for _ in range(3):
                simuler_comportement_humain(driver)
                time.sleep(random.uniform(1.0, 2.0))

            driver.refresh()
            time.sleep(random.uniform(3.0, 8.0))
            simuler_comportement_humain(driver)
            page_source = driver.page_source

        # Parser avec BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Sélecteurs pour page produit Amazon 2025 - BASÉS SUR LE HTML FOURNI
        desc_selectors = [
            # SÉLECTEUR EXACT basé sur le HTML fourni
            '#bookDescription_feature_div .a-expander-content span',
            '#bookDescription_feature_div .a-expander-content p span',
            '#bookDescription_feature_div .a-expander-content p',

            # Variations du sélecteur principal
            '#bookDescription_feature_div .a-expander-content',
            '#bookDescription_feature_div span',
            '#bookDescription_feature_div p',

            # Sélecteurs par attribut data
            '[data-feature-name="bookDescription"] .a-expander-content span',
            '[data-feature-name="bookDescription"] .a-expander-content p',
            '[data-feature-name="bookDescription"] .a-expander-content',
            '[data-feature-name="bookDescription"] span',
            '[data-feature-name="bookDescription"] p',

            # Classe celwidget
            '.celwidget[data-feature-name="bookDescription"] .a-expander-content span',
            '.celwidget[data-feature-name="bookDescription"] .a-expander-content p',
            '.celwidget[data-feature-name="bookDescription"] .a-expander-content',
            '.celwidget[data-feature-name="bookDescription"] span',
            '.celwidget[data-feature-name="bookDescription"] p',

            # Fallbacks génériques
            '.a-expander-content span',
            '.a-expander-content p',
            '.a-expander-content',
            '#productDescription p',
            '#productDescription span',
            '#feature-bullets .a-list-item'
        ]

        for i, selector in enumerate(desc_selectors):
            try:
                desc_elems = soup.select(selector)
                if desc_elems:
                    # Concaténer tous les spans/p trouvés
                    all_text = ' '.join([elem.get_text(strip=True) for elem in desc_elems])
                    print(f"🔍 Selenium - Sélecteur {i+1}/{len(desc_selectors)} '{selector}' - {len(desc_elems)} éléments trouvés")
                    print(f"📝 Texte extrait: {all_text[:100]}...")

                    # Filtrage moins strict
                    if (all_text and len(all_text) > 30 and
                        not all_text.startswith('Expédié par') and
                        not all_text.startswith('Vendu par') and
                        not all_text.startswith('Retours') and
                        'En apprendre plus' not in all_text):
                        print(f"✅ Description Selenium extraite avec: {selector}")
                        return all_text
                    else:
                        print(f"❌ Texte Selenium filtré (trop court ou non pertinent)")
                else:
                    print(f"🔍 Selenium - Sélecteur {i+1}/{len(desc_selectors)} '{selector}' - AUCUN élément trouvé")
            except Exception as e:
                print(f"❌ Erreur sélecteur {selector}: {e}")

        # DEBUG: Sauvegarder le HTML pour analyser
        print("❌ DEBUG: Sauvegarde du HTML pour analyse...")
        with open('debug_amazon_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("❌ Fichier debug_amazon_page.html créé - vérifiez manuellement les sélecteurs")

        print("❌ Selenium - Aucun sélecteur n'a donné de description valide")
        return "Description non trouvée"

    except Exception as e:
        print(f"❌ Erreur Selenium: {e}")
        return "Description non trouvée"
    finally:
        # Fermer le driver
        if driver:
            try:
                driver.quit()
            except:
                pass

# ===== TECHNIQUE 1: CACHE SQLITE INTELLIGENT =====
def initialiser_cache_descriptions():
    """
    Initialise la base de données SQLite pour le cache des descriptions
    """
    try:
        conn = sqlite3.connect('cache_descriptions.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS descriptions_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                asin TEXT,
                isbn TEXT,
                titre TEXT,
                description TEXT,
                date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                succes INTEGER DEFAULT 1
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erreur initialisation cache: {e}")

def obtenir_description_cache(url, asin=None, isbn=None):
    """
    Récupère une description depuis le cache SQLite
    """
    try:
        conn = sqlite3.connect('cache_descriptions.db')
        cursor = conn.cursor()

        # Recherche par URL d'abord
        cursor.execute('SELECT description FROM descriptions_cache WHERE url = ? AND succes = 1', (url,))
        result = cursor.fetchone()

        if result:
            conn.close()
            return result[0]

        # Recherche par ASIN si disponible
        if asin:
            cursor.execute('SELECT description FROM descriptions_cache WHERE asin = ? AND succes = 1', (asin,))
            result = cursor.fetchone()
            if result:
                conn.close()
                return result[0]

        # Recherche par ISBN si disponible
        if isbn:
            cursor.execute('SELECT description FROM descriptions_cache WHERE isbn = ? AND succes = 1', (isbn,))
            result = cursor.fetchone()
            if result:
                conn.close()
                return result[0]

        conn.close()
        return None
    except Exception as e:
        print(f"❌ Erreur lecture cache: {e}")
        return None

def sauvegarder_description_cache(url, description, asin=None, isbn=None, titre=None):
    """
    Sauvegarde une description dans le cache SQLite
    """
    try:
        conn = sqlite3.connect('cache_descriptions.db')
        cursor = conn.cursor()

        succes = 1 if description != "Description non trouvée" else 0

        cursor.execute('''
            INSERT OR REPLACE INTO descriptions_cache
            (url, asin, isbn, titre, description, succes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (url, asin, isbn, titre, description, succes))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Erreur sauvegarde cache: {e}")

# ===== TECHNIQUE 2: POOL DE DRIVERS PERSISTANTS =====
class PoolDrivers:
    """
    Pool de drivers Chrome persistants pour éviter les créations/destructions
    """
    def __init__(self, taille_pool=5):
        self.taille_pool = taille_pool
        self.drivers = []
        self.disponibles = []
        self.lock = threading.Lock()
        self.initialiser_pool()

    def initialiser_pool(self):
        """
        Initialise le pool de drivers
        """
        for i in range(self.taille_pool):
            driver = self.creer_driver()
            if driver:
                self.drivers.append(driver)
                self.disponibles.append(driver)

    def creer_driver(self):
        """
        Crée un driver optimisé
        """
        try:
            if UNDETECTED_AVAILABLE:
                options = uc.ChromeOptions()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                driver = uc.Chrome(options=options)
            else:
                options = Options()
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                driver = webdriver.Chrome(options=options)

            driver.set_page_load_timeout(10)
            return driver
        except Exception as e:
            print(f"❌ Erreur création driver: {e}")
            return None

    def obtenir_driver(self):
        """
        Obtient un driver depuis le pool
        """
        with self.lock:
            if self.disponibles:
                return self.disponibles.pop()
            else:
                return self.creer_driver()

    def liberer_driver(self, driver):
        """
        Libère un driver vers le pool
        """
        with self.lock:
            if len(self.disponibles) < self.taille_pool:
                self.disponibles.append(driver)
            else:
                try:
                    driver.quit()
                except:
                    pass

    def fermer_pool(self):
        """
        Ferme tous les drivers du pool
        """
        with self.lock:
            for driver in self.drivers:
                try:
                    driver.quit()
                except:
                    pass
            self.drivers.clear()
            self.disponibles.clear()

# Instance globale du pool de drivers
pool_drivers = None

def obtenir_pool_drivers():
    """
    Obtient l'instance globale du pool de drivers
    """
    global pool_drivers
    if pool_drivers is None:
        pool_drivers = PoolDrivers(3)
    return pool_drivers

# ===== TECHNIQUE 3: PLAYWRIGHT INTEGRATION =====
def recuperer_description_playwright(url):
    """
    Utilise Playwright pour extraire la description (plus rapide que Selenium)
    """
    if not PLAYWRIGHT_AVAILABLE:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Headers anti-détection
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

            page.goto(url, timeout=15000)
            page.wait_for_timeout(2000)

            # Sélecteurs optimisés Amazon 2025
            selectors = [
                '[data-cy="book-details-overview"]',
                '[data-testid="book-description"]',
                '#dp-container [data-feature-name="bookDescription"]',
                '#bookDescription_feature_div .a-expander-content',
                '#productDescription p'
            ]

            for selector in selectors:
                element = page.query_selector(selector)
                if element:
                    text = element.inner_text().strip()
                    if text and len(text) > 50:
                        print(f"✅ Playwright - Description trouvée avec: {selector}")
                        browser.close()
                        return text

            browser.close()
            return None

    except Exception as e:
        print(f"❌ Erreur Playwright: {e}")
        return None

# ===== TECHNIQUE 4: API GRAPHQL AMAZON =====
def recuperer_description_api_graphql(url):
    """
    Tente d'extraire la description via l'API GraphQL d'Amazon
    """
    try:
        # Extraire l'ASIN depuis l'URL
        import re
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if not asin_match:
            return None

        asin = asin_match.group(1)

        # Headers pour API
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # URL API GraphQL Amazon (endpoint public)
        api_url = f"https://www.amazon.fr/api/detail/{asin}"

        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()

            # Rechercher dans les champs possibles
            description_fields = ['description', 'productDescription', 'bookDescription', 'summary']
            for field in description_fields:
                if field in data and data[field]:
                    print(f"✅ API GraphQL - Description trouvée")
                    return data[field]

        return None

    except Exception as e:
        print(f"❌ Erreur API GraphQL: {e}")
        return None

# ===== TECHNIQUE 5: THREADING PARALLÈLE =====
def recuperer_descriptions_parallele(urls_livres, max_workers=5):
    """
    Traite plusieurs URLs en parallèle
    """
    def traiter_url(url_info):
        url, asin, isbn, titre = url_info
        return recuperer_description_depuis_url(url, asin, isbn, titre)

    descriptions = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(traiter_url, url_info): url_info[0] for url_info in urls_livres}

        for future in as_completed(futures):
            url = futures[future]
            try:
                description = future.result()
                descriptions[url] = description
            except Exception as e:
                print(f"❌ Erreur parallèle pour {url}: {e}")
                descriptions[url] = "Description non trouvée"

    return descriptions

# ===== TECHNIQUE 6: FONCTION PRINCIPALE OPTIMISÉE =====
def recuperer_description_depuis_url(url, asin=None, isbn=None, titre=None):
    """
    Extraction hybride : Requests puis Selenium rapide si nécessaire

    Args:
        url (str): URL de la page produit
        asin (str, optional): ASIN du livre
        isbn (str, optional): ISBN du livre
        titre (str, optional): Titre du livre

    Returns:
        str: Description du livre
    """
    if not url or url == "URL non trouvée":
        return "Description non trouvée"

    print(f"🔍 Extraction description pour: {titre[:30] if titre else 'livre'}...")

    # 1. TENTATIVE RAPIDE avec requests
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        }

        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Sélecteurs qui fonctionnaient à 100% (Test initial 16:05:00)
            selectors = [
                '#bookDescription_feature_div',  # Sélecteur principal fonctionnel à 100%
                '#bookDescription_feature_div .a-expander-content span',
                '#bookDescription_feature_div .a-expander-content p',
                '#bookDescription_feature_div .a-expander-content',
                '#productDescription p',
                '#dp-container [data-feature-name="bookDescription"]',
                '[data-feature-name="bookDescription"] span',
                '[data-feature-name="bookDescription"] p'
            ]

            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    full_text = ' '.join(elem.get_text(strip=True) for elem in elements)
                    if full_text and len(full_text) > 30:
                        print(f"✅ Requests - Description trouvée: {full_text[:50]}...")
                        return full_text

    except Exception as e:
        print(f"❌ Requests échoué: {e}")

    # 2. FALLBACK : Selenium rapide et optimisé
    print("🔍 Selenium rapide...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-images")
        options.add_argument("--disable-javascript")  # Pas besoin de JS pour HTML statique
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(8)

        driver.get(url)
        time.sleep(1)  # Délai minimal

        # HTML direct sans attendre le JS
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # Mêmes sélecteurs qu'avec requests (100% fonctionnels)
        selectors = [
            '#bookDescription_feature_div',  # Sélecteur principal fonctionnel à 100%
            '#bookDescription_feature_div .a-expander-content span',
            '#bookDescription_feature_div .a-expander-content p',
            '#bookDescription_feature_div .a-expander-content',
            '#productDescription p',
            '#dp-container [data-feature-name="bookDescription"]',
            '[data-feature-name="bookDescription"] span',
            '[data-feature-name="bookDescription"] p'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                full_text = ' '.join(elem.get_text(strip=True) for elem in elements)
                if full_text and len(full_text) > 30:
                    print(f"✅ Selenium - Description trouvée: {full_text[:50]}...")
                    return full_text

    except Exception as e:
        print(f"❌ Selenium échoué: {e}")

    print("❌ Aucune description trouvée")
    return "Description non trouvée"