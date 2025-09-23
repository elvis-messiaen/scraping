#!/usr/bin/env python3
"""
SELENIUM UNDETECTED ENGINE - MODE ANTI-503 #2
==============================================

Version modifiée de Chrome qui évite la détection
- Built-in stealth features intégrées
- Proven success rate élevé
- Basé sur undetected-chromedriver pour 2025

Installation requise:
pip install undetected-chromedriver selenium
"""

import random
import time
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import json
import os

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium/undetected-chromedriver non installé. Installez avec: pip install undetected-chromedriver selenium")

class SeleniumUndetectedEngine:
    """
    Moteur Selenium Undetected pour éviter complètement les erreurs 503 Amazon
    """

    def __init__(self):
        """
        Initialise le moteur Selenium Undetected
        """
        self.driver = None

        # Configuration undetected optimisée
        self.chrome_options = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # Pas besoin d'images pour scraper
            '--disable-javascript',  # Parfois aide à éviter détection
            '--window-size=1920,1080',
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]

        # Délais réalistes humains
        self.human_delays = {
            'page_load': (3, 8),
            'scroll': (1, 4),
            'wait': (2, 5)
        }

    def initialiser_driver(self) -> bool:
        """
        Initialise le driver Chrome undetected

        Returns:
            bool: True si succès, False sinon
        """
        if not SELENIUM_AVAILABLE:
            return False

        try:
            # Options Chrome
            options = uc.ChromeOptions()

            # Ajouter les options stealth
            for option in self.chrome_options:
                options.add_argument(option)

            # Désactiver les notifications, géolocalisation, etc.
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "geolocation": 2,
                    "media_stream": 2,
                }
            }
            options.add_experimental_option("prefs", prefs)

            # Initialiser driver undetected
            self.driver = uc.Chrome(
                options=options,
                headless=True,  # Mode invisible
                version_main=None  # Auto-detect Chrome version
            )

            # Configuration timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)

            print("✅ Driver Selenium Undetected initialisé")
            return True

        except Exception as e:
            print(f"❌ Erreur initialisation Selenium: {e}")
            return False

    def naviguer_url(self, url: str) -> Optional[BeautifulSoup]:
        """
        Navigue vers une URL avec comportement humain

        Args:
            url (str): URL à visiter

        Returns:
            Optional[BeautifulSoup]: Page parsée ou None
        """
        try:
            if not self.driver:
                if not self.initialiser_driver():
                    return None

            print(f"🌐 Navigation Selenium Undetected: {url[:60]}...")

            # Navigation
            self.driver.get(url)

            # Comportement humain: attendre
            time.sleep(random.uniform(*self.human_delays['page_load']))

            # Vérifier si on a été bloqué
            if self.detecter_blocage():
                print("❌ Blocage détecté par Amazon")
                return None

            # Simuler scroll humain
            self.simuler_comportement_humain()

            # Récupérer le HTML
            html_content = self.driver.page_source

            # Parser avec BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            print(f"✅ Page récupérée avec succès ({len(html_content)} chars)")
            return soup

        except TimeoutException:
            print("⏰ Timeout lors du chargement")
            return None
        except WebDriverException as e:
            print(f"❌ Erreur WebDriver: {e}")
            return None
        except Exception as e:
            print(f"❌ Erreur navigation Selenium: {e}")
            return None

    def detecter_blocage(self) -> bool:
        """
        Détecte si on a été bloqué par Amazon

        Returns:
            bool: True si bloqué, False sinon
        """
        try:
            # Vérifier les indicateurs de blocage
            page_source = self.driver.page_source.lower()

            blocage_indicators = [
                'captcha',
                'robot',
                'automated',
                'blocked',
                'access denied',
                'error 503',
                'service unavailable'
            ]

            for indicator in blocage_indicators:
                if indicator in page_source:
                    print(f"🚫 Indicateur de blocage détecté: {indicator}")
                    return True

            # Vérifier le titre
            title = self.driver.title.lower()
            if 'error' in title or 'captcha' in title:
                print(f"🚫 Titre suspect: {title}")
                return True

            return False

        except Exception:
            return True

    def simuler_comportement_humain(self):
        """
        Simule un comportement humain réaliste
        """
        try:
            # Scroll graduellement
            for i in range(random.randint(3, 7)):
                scroll_height = random.randint(200, 500)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
                time.sleep(random.uniform(*self.human_delays['scroll']))

            # Revenir en haut
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(*self.human_delays['wait']))

        except Exception as e:
            print(f"⚠️  Erreur simulation comportement: {e}")

    def fermer_driver(self):
        """
        Ferme proprement le driver
        """
        try:
            if self.driver:
                self.driver.quit()
                print("🔒 Driver Selenium fermé")
        except Exception as e:
            print(f"⚠️  Erreur fermeture driver: {e}")

# Fonction helper pour utilisation simple
def scraper_avec_selenium_undetected(url: str) -> Optional[BeautifulSoup]:
    """
    Fonction helper pour scraper une URL avec Selenium Undetected

    Args:
        url (str): URL à scraper

    Returns:
        Optional[BeautifulSoup]: Page parsée ou None
    """
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium undetected non disponible")
        return None

    engine = SeleniumUndetectedEngine()
    try:
        soup = engine.naviguer_url(url)
        return soup
    finally:
        engine.fermer_driver()

if __name__ == "__main__":
    # Test
    test_url = "https://www.amazon.fr/s?k=science+fiction&i=stripbooks"
    print("🧪 Test Selenium Undetected Engine...")

    soup = scraper_avec_selenium_undetected(test_url)
    if soup:
        print(f"✅ Test réussi ! Page récupérée: {len(str(soup))} caractères")
        # Chercher des livres
        livres = soup.select('.s-result-item[data-component-type="s-search-result"]')
        print(f"📚 {len(livres)} livres détectés")
    else:
        print("❌ Test échoué")