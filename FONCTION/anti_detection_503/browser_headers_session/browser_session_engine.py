#!/usr/bin/env python3
"""
BROWSER HEADERS + SESSION ENGINE - MODE ANTI-503 #3
===================================================

Headers complets comme un vrai navigateur + Session persistante
- Headers complets comme un vrai navigateur (Accept, Accept-Language, DNT, etc.)
- Session requests avec cookies persistants
- Séquence de navigation réaliste
- Basé sur les best practices 2025

Aucune installation supplémentaire requise (utilise requests)
"""

import requests
import random
import time
import json
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

class BrowserSessionEngine:
    """
    Moteur Session avec headers complets pour éviter les erreurs 503 Amazon
    """

    def __init__(self):
        """
        Initialise le moteur Session avec headers réalistes
        """
        # Session persistante avec cookies
        self.session = requests.Session()

        # Pool de User-Agents réalistes 2025
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]

        # Headers complets comme un vrai navigateur
        self.base_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Cache-Control': 'max-age=0'
        }

        # Délais réalistes
        self.human_delays = {
            'between_requests': (5, 15),
            'page_load': (2, 5),
            'retry': (30, 60)
        }

        # Configuration session
        self.session.headers.update(self.base_headers)
        self.timeout = 30

        # Initialiser avec page d'accueil Amazon
        self.initialiser_session()

    def initialiser_session(self) -> bool:
        """
        Initialise la session en visitant la page d'accueil Amazon

        Returns:
            bool: True si succès, False sinon
        """
        try:
            print("🏠 Initialisation session avec page d'accueil Amazon...")

            # Visiter page d'accueil Amazon pour obtenir cookies
            accueil_url = "https://www.amazon.fr"
            headers = self.generer_headers_complets(accueil_url)

            response = self.session.get(
                accueil_url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )

            if response.status_code == 200:
                print(f"✅ Session initialisée avec {len(self.session.cookies)} cookies")

                # Attendre comme un humain
                time.sleep(random.uniform(*self.human_delays['page_load']))
                return True
            else:
                print(f"⚠️  Statut {response.status_code} sur page d'accueil")
                return False

        except Exception as e:
            print(f"❌ Erreur initialisation session: {e}")
            return False

    def generer_headers_complets(self, url: str, referer: Optional[str] = None) -> Dict[str, str]:
        """
        Génère des headers complets et réalistes pour une URL

        Args:
            url (str): URL cible
            referer (Optional[str]): URL de référence

        Returns:
            Dict[str, str]: Headers complets
        """
        headers = self.base_headers.copy()

        # Rotation User-Agent
        headers['User-Agent'] = random.choice(self.user_agents)

        # Referer si fourni
        if referer:
            headers['Referer'] = referer

        # Headers spécifiques selon URL
        if 'amazon.fr' in url:
            # Headers spécifiques Amazon
            headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Sec-Fetch-Site': 'same-origin' if referer and 'amazon.fr' in referer else 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Dest': 'document'
            })

            # Headers de recherche Amazon
            if '/s?' in url:
                headers.update({
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-User': '?1'
                })

        return headers

    def naviguer_url(self, url: str, referer: Optional[str] = None, retry_count: int = 3) -> Optional[BeautifulSoup]:
        """
        Navigue vers une URL avec comportement humain et retry

        Args:
            url (str): URL à visiter
            referer (Optional[str]): URL de référence
            retry_count (int): Nombre de tentatives

        Returns:
            Optional[BeautifulSoup]: Page parsée ou None
        """
        for tentative in range(retry_count):
            try:
                print(f"🌐 Navigation Session (tentative {tentative+1}/{retry_count}): {url[:60]}...")

                # Délai anti-détection
                if tentative > 0:
                    wait_time = random.uniform(*self.human_delays['retry'])
                    print(f"⏳ Attente anti-détection: {wait_time:.1f}s")
                    time.sleep(wait_time)
                else:
                    time.sleep(random.uniform(*self.human_delays['between_requests']))

                # Headers pour cette requête
                headers = self.generer_headers_complets(url, referer)

                # Requête
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True
                )

                # Vérifier le statut
                if response.status_code == 200:
                    # Vérifier si contenu valide (pas de blocage)
                    if self.valider_contenu(response.text):
                        soup = BeautifulSoup(response.text, 'html.parser')
                        print(f"✅ Page récupérée avec succès ({len(response.text)} chars)")
                        return soup
                    else:
                        print("🚫 Contenu suspect détecté (possible blocage)")
                        continue

                elif response.status_code == 503:
                    print(f"⚠️  Erreur 503 (tentative {tentative+1}/{retry_count})")
                    continue

                else:
                    print(f"⚠️  Statut HTTP {response.status_code}")
                    continue

            except requests.exceptions.Timeout:
                print(f"⏰ Timeout (tentative {tentative+1}/{retry_count})")
                continue

            except requests.exceptions.ConnectionError:
                print(f"🌐 Erreur connexion (tentative {tentative+1}/{retry_count})")
                continue

            except Exception as e:
                print(f"❌ Erreur requête: {e}")
                continue

        print("❌ Toutes les tentatives ont échoué")
        return None

    def valider_contenu(self, html: str) -> bool:
        """
        Valide que le contenu n'est pas un blocage

        Args:
            html (str): Contenu HTML

        Returns:
            bool: True si contenu valide, False si blocage
        """
        html_lower = html.lower()

        # Indicateurs de blocage
        blocage_indicators = [
            'captcha',
            'robot check',
            'automated traffic',
            'blocked',
            'access denied',
            'service unavailable',
            'temporarily unavailable',
            'error 503',
            'error occurred'
        ]

        for indicator in blocage_indicators:
            if indicator in html_lower:
                return False

        # Vérifier présence d'éléments Amazon normaux
        amazon_indicators = [
            'amazon',
            's-result-item',
            'nav-logo',
            'product',
            'price'
        ]

        has_amazon_content = any(indicator in html_lower for indicator in amazon_indicators)

        return has_amazon_content and len(html) > 10000  # Page suffisamment complète

    def navigation_sequentielle_amazon(self, url_finale: str) -> Optional[BeautifulSoup]:
        """
        Navigation séquentielle réaliste vers l'URL finale

        Args:
            url_finale (str): URL de destination

        Returns:
            Optional[BeautifulSoup]: Page finale parsée ou None
        """
        try:
            print("🎯 Navigation séquentielle Amazon...")

            # Étape 1: Page d'accueil (déjà fait dans __init__)

            # Étape 2: Aller vers les livres
            livres_url = "https://www.amazon.fr/livres-neufs-occasion/b?ie=UTF8&node=301061"
            print("📚 Navigation vers section Livres...")

            referer = "https://www.amazon.fr"
            soup_livres = self.naviguer_url(livres_url, referer=referer)

            if not soup_livres:
                print("❌ Échec navigation section livres")
                return None

            # Étape 3: Navigation finale
            print("🎯 Navigation vers URL finale...")
            soup_finale = self.naviguer_url(url_finale, referer=livres_url)

            return soup_finale

        except Exception as e:
            print(f"❌ Erreur navigation séquentielle: {e}")
            return None

    def fermer_session(self):
        """
        Ferme proprement la session
        """
        try:
            self.session.close()
            print("🔒 Session fermée")
        except Exception as e:
            print(f"⚠️  Erreur fermeture session: {e}")

# Fonction helper pour utilisation simple
def scraper_avec_browser_session(url: str, navigation_sequentielle: bool = True) -> Optional[BeautifulSoup]:
    """
    Fonction helper pour scraper une URL avec Browser Session

    Args:
        url (str): URL à scraper
        navigation_sequentielle (bool): Utiliser navigation séquentielle

    Returns:
        Optional[BeautifulSoup]: Page parsée ou None
    """
    engine = BrowserSessionEngine()
    try:
        if navigation_sequentielle:
            soup = engine.navigation_sequentielle_amazon(url)
        else:
            soup = engine.naviguer_url(url)
        return soup
    finally:
        engine.fermer_session()

if __name__ == "__main__":
    # Test
    test_url = "https://www.amazon.fr/s?k=science+fiction&i=stripbooks"
    print("🧪 Test Browser Session Engine...")

    soup = scraper_avec_browser_session(test_url, navigation_sequentielle=True)
    if soup:
        print(f"✅ Test réussi ! Page récupérée: {len(str(soup))} caractères")
        # Chercher des livres
        livres = soup.select('.s-result-item[data-component-type="s-search-result"]')
        print(f"📚 {len(livres)} livres détectés")
    else:
        print("❌ Test échoué")