#!/usr/bin/env python3
"""
PLAYWRIGHT STEALTH ENGINE - MODE ANTI-503 #1
=============================================

Simulation complète d'un navigateur réel avec Playwright
- Supprime les traces d'automation (navigator.webdriver, etc.)
- Plus efficace que requests + rotation headers
- Basé sur playwright-stealth pour 2025

Installation requise:
pip install playwright playwright-stealth
playwright install chromium
"""

import asyncio
import random
import time
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import json
import os

try:
    from playwright.async_api import async_playwright
    from playwright_stealth import stealth_async
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright non installé. Installez avec: pip install playwright playwright-stealth")

class PlaywrightStealthEngine:
    """
    Moteur Playwright Stealth pour éviter complètement les erreurs 503 Amazon
    """

    def __init__(self):
        """
        Initialise le moteur Playwright Stealth
        """
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

        # Configuration stealth optimisée
        self.stealth_config = {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'fr-FR',
            'timezone_id': 'Europe/Paris',
            'geolocation': {'latitude': 48.8566, 'longitude': 2.3522},  # Paris
        }

        # Délais réalistes humains
        self.human_delays = {
            'page_load': (2, 5),
            'scroll': (1, 3),
            'click': (0.5, 2),
            'type': (0.1, 0.3)
        }

    async def initialiser_navigateur(self) -> bool:
        """
        Initialise le navigateur Playwright avec stealth

        Returns:
            bool: True si succès, False sinon
        """
        if not PLAYWRIGHT_AVAILABLE:
            return False

        try:
            self.playwright = await async_playwright().start()

            # Lancer Chrome avec options stealth
            self.browser = await self.playwright.chromium.launch(
                headless=True,  # Mode invisible
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-web-security'
                ]
            )

            # Créer contexte avec empreinte humaine
            self.context = await self.browser.new_context(
                user_agent=self.stealth_config['user_agent'],
                viewport=self.stealth_config['viewport'],
                locale=self.stealth_config['locale'],
                timezone_id=self.stealth_config['timezone_id'],
                geolocation=self.stealth_config['geolocation'],
                permissions=['geolocation']
            )

            # Nouvelle page
            self.page = await self.context.new_page()

            # Appliquer stealth (supprime traces automation)
            await stealth_async(self.page)

            print("✅ Navigateur Playwright Stealth initialisé")
            return True

        except Exception as e:
            print(f"❌ Erreur initialisation Playwright: {e}")
            return False

    async def naviguer_url(self, url: str) -> Optional[BeautifulSoup]:
        """
        Navigue vers une URL avec comportement humain

        Args:
            url (str): URL à visiter

        Returns:
            Optional[BeautifulSoup]: Page parsée ou None
        """
        try:
            if not self.page:
                await self.initialiser_navigateur()

            print(f"🌐 Navigation Playwright Stealth: {url[:60]}...")

            # Navigation avec timeout long
            response = await self.page.goto(
                url,
                wait_until='domcontentloaded',
                timeout=30000
            )

            # Vérifier le statut
            if response.status != 200:
                print(f"⚠️  Statut HTTP {response.status} pour {url}")
                return None

            # Comportement humain: attendre et scroller
            await self.simuler_comportement_humain()

            # Récupérer le HTML
            html_content = await self.page.content()

            # Parser avec BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            print(f"✅ Page récupérée avec succès ({len(html_content)} chars)")
            return soup

        except Exception as e:
            print(f"❌ Erreur navigation Playwright: {e}")
            return None

    async def simuler_comportement_humain(self):
        """
        Simule un comportement humain réaliste
        """
        try:
            # Attendre chargement
            await asyncio.sleep(random.uniform(*self.human_delays['page_load']))

            # Scroller comme un humain
            for _ in range(random.randint(2, 5)):
                await self.page.evaluate("""
                    window.scrollBy(0, Math.floor(Math.random() * 300) + 100);
                """)
                await asyncio.sleep(random.uniform(*self.human_delays['scroll']))

            # Revenir en haut
            await self.page.evaluate("window.scrollTo(0, 0);")
            await asyncio.sleep(random.uniform(*self.human_delays['scroll']))

        except Exception as e:
            print(f"⚠️  Erreur simulation comportement: {e}")

    async def fermer_navigateur(self):
        """
        Ferme proprement le navigateur
        """
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("🔒 Navigateur Playwright fermé")
        except Exception as e:
            print(f"⚠️  Erreur fermeture navigateur: {e}")

# Fonction helper pour utilisation simple
async def scraper_avec_playwright_stealth(url: str) -> Optional[BeautifulSoup]:
    """
    Fonction helper pour scraper une URL avec Playwright Stealth

    Args:
        url (str): URL à scraper

    Returns:
        Optional[BeautifulSoup]: Page parsée ou None
    """
    engine = PlaywrightStealthEngine()
    try:
        soup = await engine.naviguer_url(url)
        return soup
    finally:
        await engine.fermer_navigateur()

# Fonction synchrone pour compatibilité
def scraper_playwright_stealth_sync(url: str) -> Optional[BeautifulSoup]:
    """
    Version synchrone pour compatibilité avec les scrapers existants

    Args:
        url (str): URL à scraper

    Returns:
        Optional[BeautifulSoup]: Page parsée ou None
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright non disponible")
        return None

    return asyncio.run(scraper_avec_playwright_stealth(url))

if __name__ == "__main__":
    # Test
    test_url = "https://www.amazon.fr/s?k=science+fiction&i=stripbooks"
    print("🧪 Test Playwright Stealth Engine...")

    soup = scraper_playwright_stealth_sync(test_url)
    if soup:
        print(f"✅ Test réussi ! Page récupérée: {len(str(soup))} caractères")
        # Chercher des livres
        livres = soup.select('.s-result-item[data-component-type="s-search-result"]')
        print(f"📚 {len(livres)} livres détectés")
    else:
        print("❌ Test échoué")