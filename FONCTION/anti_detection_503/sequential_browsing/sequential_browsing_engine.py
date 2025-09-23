#!/usr/bin/env python3
"""
SEQUENTIAL BROWSING ENGINE - MODE ANTI-503 #4
==============================================

Navigation séquentielle réaliste simulant un utilisateur humain
- Simuler un comportement utilisateur réel
- Commencer par la page d'accueil Amazon
- Naviguer vers les catégories progressivement
- Basé sur les patterns de navigation humains 2025

Utilise requests avec simulation comportementale avancée
"""

import requests
import random
import time
import json
from typing import Optional, Dict, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import re
from datetime import datetime

class SequentialBrowsingEngine:
    """
    Moteur de navigation séquentielle pour simuler un comportement humain réel
    """

    def __init__(self):
        """
        Initialise le moteur de navigation séquentielle
        """
        # Session persistante
        self.session = requests.Session()

        # Historique de navigation (comme un vrai navigateur)
        self.navigation_history = []
        self.current_referer = None

        # Headers évolutifs (changent selon le contexte)
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]

        # Timing humain réaliste
        self.human_timing = {
            'page_reading': (8, 20),      # Temps de lecture d'une page
            'menu_navigation': (2, 5),     # Temps pour naviguer dans un menu
            'search_typing': (3, 8),       # Temps pour "taper" une recherche
            'link_clicking': (1, 3),       # Temps entre voir un lien et cliquer
            'scroll_pause': (0.5, 2),      # Pause entre scrolls
            'category_browsing': (5, 12)   # Temps dans une catégorie
        }

        # Parcours de navigation Amazon typiques
        self.amazon_journey_paths = [
            # Parcours 1: Navigation directe livres
            ['accueil', 'livres', 'categorie'],
            # Parcours 2: Navigation avec recherche
            ['accueil', 'recherche', 'resultats'],
            # Parcours 3: Navigation via menu
            ['accueil', 'menu_livres', 'sous_categorie', 'categorie']
        ]

        # URLs Amazon de base
        self.amazon_urls = {
            'accueil': 'https://www.amazon.fr',
            'livres': 'https://www.amazon.fr/livres-neufs-occasion/b?ie=UTF8&node=301061',
            'livres_neufs': 'https://www.amazon.fr/b?node=301061',
            'categories': 'https://www.amazon.fr/b?node=301061'
        }

        self.session_id = f"session_{int(time.time())}"
        print(f"Session navigation séquentielle initialisée: {self.session_id}")

    def generer_headers_contextuels(self, url: str, action: str = 'navigate') -> Dict[str, str]:
        """
        Génère des headers contextuels selon l'action et l'historique

        Args:
            url (str): URL cible
            action (str): Type d'action ('navigate', 'search', 'click', etc.)

        Returns:
            Dict[str, str]: Headers contextuels
        """
        # Headers de base évoluant selon contexte
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

        # Referer selon historique
        if self.current_referer:
            headers['Referer'] = self.current_referer

        # Headers selon action
        if action == 'search':
            headers.update({
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1'
            })
        elif action == 'click':
            headers.update({
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin'
            })
        elif action == 'navigate':
            headers.update({
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none' if not self.current_referer else 'same-origin',
                'Sec-Fetch-User': '?1'
            })

        return headers

    def simuler_temps_humain(self, action: str):
        """
        Simule des temps d'attente humains selon l'action

        Args:
            action (str): Type d'action
        """
        if action in self.human_timing:
            wait_time = random.uniform(*self.human_timing[action])
            print(f"Simulation humaine ({action}): {wait_time:.1f}s")
            time.sleep(wait_time)

    def visiter_page(self, url: str, action: str = 'navigate', description: str = '') -> Optional[BeautifulSoup]:
        """
        Visite une page avec simulation comportementale

        Args:
            url (str): URL à visiter
            action (str): Type d'action
            description (str): Description de l'action

        Returns:
            Optional[BeautifulSoup]: Page parsée ou None
        """
        try:
            print(f"{description}: {url[:60]}...")

            # Headers contextuels
            headers = self.generer_headers_contextuels(url, action)

            # Simulation délai humain avant requête
            if action != 'navigate' or self.navigation_history:
                self.simuler_temps_humain(action)

            # Requête
            response = self.session.get(
                url,
                headers=headers,
                timeout=30,
                allow_redirects=True
            )

            # Vérifier succès
            if response.status_code == 200:
                # Enregistrer dans historique
                self.navigation_history.append({
                    'url': url,
                    'action': action,
                    'timestamp': datetime.now().isoformat(),
                    'status': response.status_code,
                    'description': description
                })

                # Mettre à jour referer
                self.current_referer = url

                # Parser page
                soup = BeautifulSoup(response.text, 'html.parser')

                # Simulation lecture de page
                if action in ['navigate', 'search']:
                    self.simuler_lecture_page(soup)

                print(f"Page visitée avec succès ({len(response.text)} chars)")
                return soup

            else:
                print(f"Statut HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"Erreur visite page: {e}")
            return None

    def simuler_lecture_page(self, soup: BeautifulSoup):
        """
        Simule la lecture/exploration d'une page

        Args:
            soup (BeautifulSoup): Page à "lire"
        """
        try:
            # Analyser contenu (simulation)
            links = soup.find_all('a', href=True)
            images = soup.find_all('img')
            text_length = len(soup.get_text())

            # Temps de lecture basé sur le contenu
            base_time = min(max(text_length / 1000, 2), 15)  # 2-15 secondes
            reading_time = base_time + random.uniform(-1, 3)

            print(f"Simulation lecture page: {reading_time:.1f}s")
            time.sleep(reading_time)

        except Exception:
            # Fallback: temps aléatoire
            time.sleep(random.uniform(2, 8))

    def parcours_navigation_amazon(self, url_finale: str) -> Optional[BeautifulSoup]:
        """
        Effectue un parcours de navigation Amazon réaliste

        Args:
            url_finale (str): URL de destination finale

        Returns:
            Optional[BeautifulSoup]: Page finale ou None
        """
        print("Début parcours navigation Amazon réaliste...")

        try:
            # Étape 1: Page d'accueil Amazon (point d'entrée naturel)
            print("\nÉTAPE 1: Page d'accueil Amazon")
            soup_accueil = self.visiter_page(
                self.amazon_urls['accueil'],
                'navigate',
                'Visite page d\'accueil Amazon'
            )

            if not soup_accueil:
                print("Échec page d'accueil")
                return None

            # Étape 2: Navigation vers section Livres
            print("\nÉTAPE 2: Navigation section Livres")
            soup_livres = self.visiter_page(
                self.amazon_urls['livres'],
                'click',
                'Navigation vers section Livres'
            )

            if not soup_livres:
                print("Échec section livres")
                return None

            # Étape 3: Exploration catégories (optionnel)
            print("\nÉTAPE 3: Exploration catégories")
            categories_url = self.amazon_urls['categories']
            soup_categories = self.visiter_page(
                categories_url,
                'click',
                'Exploration des catégories de livres'
            )

            if soup_categories:
                # Simulation navigation dans les catégories
                self.simuler_temps_humain('category_browsing')

            # Étape 4: Navigation finale vers URL cible
            print("\nÉTAPE 4: Navigation vers catégorie spécifique")
            soup_finale = self.visiter_page(
                url_finale,
                'search',
                'Navigation vers catégorie cible'
            )

            if soup_finale:
                print("Parcours navigation complet avec succès !")
                self.afficher_historique_navigation()
                return soup_finale
            else:
                print("Échec navigation finale")
                return None

        except Exception as e:
            print(f"Erreur parcours navigation: {e}")
            return None

    def afficher_historique_navigation(self):
        """
        Affiche l'historique de navigation pour debug
        """
        print("\nHISTORIQUE DE NAVIGATION:")
        for i, step in enumerate(self.navigation_history, 1):
            print(f"   {i}. {step['description']} ({step['action']}) - Status: {step['status']}")

    def fermer_session(self):
        """
        Ferme la session et affiche les statistiques
        """
        try:
            stats = {
                'pages_visitees': len(self.navigation_history),
                'session_duree': time.time(),
                'session_id': self.session_id
            }

            print(f"\nStatistiques session:")
            print(f"   Pages visitées: {stats['pages_visitees']}")
            print(f"   Session ID: {stats['session_id']}")

            self.session.close()
            print("Session de navigation séquentielle fermée")

        except Exception as e:
            print(f"Erreur fermeture session: {e}")

# Fonction helper pour utilisation simple
def scraper_avec_sequential_browsing(url: str) -> Optional[BeautifulSoup]:
    """
    Fonction helper pour scraper avec navigation séquentielle

    Args:
        url (str): URL à scraper

    Returns:
        Optional[BeautifulSoup]: Page parsée ou None
    """
    engine = SequentialBrowsingEngine()
    try:
        soup = engine.parcours_navigation_amazon(url)
        return soup
    finally:
        engine.fermer_session()

if __name__ == "__main__":
    # Test
    test_url = "https://www.amazon.fr/s?k=science+fiction&i=stripbooks"
    print("Test Sequential Browsing Engine...")

    soup = scraper_avec_sequential_browsing(test_url)
    if soup:
        print(f"Test réussi ! Page récupérée: {len(str(soup))} caractères")
        # Chercher des livres
        livres = soup.select('.s-result-item[data-component-type="s-search-result"]')
        print(f"{len(livres)} livres détectés")
    else:
        print("Test échoué")