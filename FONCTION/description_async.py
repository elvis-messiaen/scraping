#!/usr/bin/env python3
"""
EXTRACTION DESCRIPTIONS ASYNC ULTRA-RAPIDE
==========================================
Système async/await pour extraction parallèle de 100+ descriptions simultanées
"""

import asyncio
import aiohttp
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
import sqlite3
import threading
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import os

# Thread safety pour SQLite
db_lock = threading.Lock()

class QueueDescriptions:
    """
    Système de queue async pour gestion des descriptions
    """
    def __init__(self, max_concurrent=100):
        self.max_concurrent = max_concurrent
        self.queue = asyncio.Queue()
        self.results = {}
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def add_task(self, url: str, titre: str = None, asin: str = None):
        """Ajoute une tâche à la queue"""
        await self.queue.put({
            'url': url,
            'titre': titre,
            'asin': asin,
            'timestamp': time.time()
        })

    async def process_queue(self):
        """Process toutes les tâches de la queue"""
        tasks = []

        while not self.queue.empty():
            task = await self.queue.get()
            coroutine = self._extract_single_description(task)
            tasks.append(coroutine)

        # Lancer toutes les tâches en parallèle
        print(f"🚀 LANCEMENT ASYNC: {len(tasks)} descriptions en parallèle...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def _extract_single_description(self, task: Dict):
        """Extrait une description de manière async"""
        async with self.semaphore:  # Limite la concurrence
            try:
                url = task['url']
                titre = task.get('titre', 'Unknown')

                print(f"🔍 Async: {titre[:20]}...")

                # Extraction async avec aiohttp
                description = await extraire_description_async(url, titre)

                print(f"✅ Async terminé: {titre[:15]}... -> {description[:20]}...")

                return {
                    'url': url,
                    'titre': titre,
                    'description': description,
                    'success': description != "Description non trouvée"
                }

            except Exception as e:
                print(f"❌ Erreur async {task.get('titre', 'Unknown')}: {e}")
                return {
                    'url': task['url'],
                    'titre': task.get('titre', 'Unknown'),
                    'description': "Description non trouvée",
                    'success': False
                }

# Instance globale de la queue
description_queue = QueueDescriptions(max_concurrent=100)

async def extraire_description_async(url: str, titre: str = None) -> str:
    """
    Extraction async ultra-rapide d'une description avec fallback intelligent
    """
    if not url or url == "URL non trouvée":
        return "Description non trouvée"

    try:
        # 1. Vérifier cache SQLite (sync)
        description_cache = obtenir_description_cache_sync(url)
        if description_cache:
            print(f"🎯 Cache: {titre[:20]}... trouvé")
            return description_cache

        # 2. Tentative aiohttp d'abord (plus rapide)
        try:
            description = await extraire_description_aiohttp(url)
            if description and description != "Description non trouvée":
                # Sauvegarder en cache (sync)
                sauvegarder_description_cache_sync(url, description, titre=titre)
                return description
        except Exception as aiohttp_error:
            print(f"⚠️ aiohttp échoué pour {titre[:20]}..., essai Selenium: {aiohttp_error}")

        # 3. Fallback Selenium si aiohttp échoue
        print(f"🔄 Fallback Selenium: {titre[:20]}...")
        description_selenium = await extraire_description_selenium_async(url)
        if description_selenium and description_selenium != "Description non trouvée":
            sauvegarder_description_cache_sync(url, description_selenium, titre=titre)
            return description_selenium

        return "Description non trouvée"

    except Exception as e:
        print(f"❌ Erreur async extraction {titre}: {e}")
        return "Description non trouvée"

async def extraire_description_aiohttp(url: str) -> str:
    """
    Extraction avec aiohttp (async HTTP client) avec gestion SSL
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8'
        }

        timeout = aiohttp.ClientTimeout(total=8)

        # Configuration SSL - Désactiver vérification pour contourner erreurs certificat
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=100, limit_per_host=30)

        async with aiohttp.ClientSession(
            headers=headers,
            timeout=timeout,
            connector=connector
        ) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Sélecteurs optimisés Amazon 2025
                    selectors = [
                        '#dp-container [data-feature-name="bookDescription"]',
                        '#bookDescription_feature_div .a-expander-content span',
                        '#bookDescription_feature_div .a-expander-content p',
                        '#bookDescription_feature_div .a-expander-content',
                        '[data-feature-name="bookDescription"] span',
                        '[data-feature-name="bookDescription"] p',
                        '#productDescription p',
                        '#feature-bullets ul li',
                        '.a-unordered-list .a-list-item'
                    ]

                    for selector in selectors:
                        elements = soup.select(selector)
                        if elements:
                            full_text = ' '.join(elem.get_text(strip=True) for elem in elements)
                            if full_text and len(full_text) > 30:
                                print(f"✅ aiohttp: Description trouvée ({len(full_text)} chars)")
                                return full_text

                    return "Description non trouvée"
                else:
                    print(f"❌ aiohttp: HTTP {response.status}")
                    return "Description non trouvée"

    except Exception as e:
        print(f"❌ Erreur aiohttp: {e}")
        return "Description non trouvée"

async def extraire_description_selenium_async(url: str) -> str:
    """
    Fallback Selenium async (via ThreadPoolExecutor)
    """
    try:
        loop = asyncio.get_event_loop()

        # Exécuter Selenium dans un thread séparé pour ne pas bloquer
        with ThreadPoolExecutor(max_workers=5) as executor:
            description = await loop.run_in_executor(
                executor,
                extraire_description_selenium_sync,
                url
            )
            return description

    except Exception as e:
        print(f"❌ Erreur Selenium async: {e}")
        return "Description non trouvée"

def extraire_description_selenium_sync(url: str) -> str:
    """
    Extraction Selenium synchrone pour ThreadPoolExecutor
    """
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-images")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(8)

        driver.get(url)
        time.sleep(1)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # Mêmes sélecteurs
        selectors = [
            '#dp-container [data-feature-name="bookDescription"]',
            '#bookDescription_feature_div .a-expander-content span',
            '#bookDescription_feature_div .a-expander-content p',
            '#bookDescription_feature_div .a-expander-content'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                full_text = ' '.join(elem.get_text(strip=True) for elem in elements)
                if full_text and len(full_text) > 30:
                    return full_text

        return "Description non trouvée"

    except Exception as e:
        print(f"❌ Erreur Selenium sync: {e}")
        return "Description non trouvée"

def obtenir_description_cache_sync(url: str) -> Optional[str]:
    """
    Obtient description depuis cache SQLite (thread-safe)
    """
    try:
        with db_lock:
            conn = sqlite3.connect('cache_descriptions.db', timeout=5)
            cursor = conn.cursor()

            # Initialiser table si nécessaire
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS descriptions_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    description TEXT,
                    date_extraction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    succes INTEGER DEFAULT 1
                )
            ''')

            cursor.execute('SELECT description FROM descriptions_cache WHERE url = ? AND succes = 1', (url,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0]
            return None

    except Exception as e:
        print(f"❌ Erreur cache lecture: {e}")
        return None

def sauvegarder_description_cache_sync(url: str, description: str, titre: str = None):
    """
    Sauvegarde description en cache SQLite (thread-safe)
    """
    try:
        with db_lock:
            conn = sqlite3.connect('cache_descriptions.db', timeout=5)
            cursor = conn.cursor()

            succes = 1 if description != "Description non trouvée" else 0

            cursor.execute('''
                INSERT OR REPLACE INTO descriptions_cache
                (url, description, succes)
                VALUES (?, ?, ?)
            ''', (url, description, succes))

            conn.commit()
            conn.close()

    except Exception as e:
        print(f"❌ Erreur cache sauvegarde: {e}")

async def extraire_descriptions_batch_async(urls_livres: List[Dict]) -> List[Dict]:
    """
    Extraction en lot de descriptions avec queue async

    Args:
        urls_livres: Liste de dicts avec 'url', 'titre', etc.

    Returns:
        Liste de résultats avec descriptions
    """
    if not urls_livres:
        return []

    print(f"🚀 BATCH ASYNC: {len(urls_livres)} descriptions à traiter...")

    # Créer nouvelle queue pour ce batch
    queue = QueueDescriptions(max_concurrent=100)

    # Ajouter toutes les tâches à la queue
    for livre in urls_livres:
        await queue.add_task(
            url=livre['url'],
            titre=livre.get('titre'),
            asin=livre.get('asin')
        )

    # Traiter toute la queue en parallèle
    start_time = time.time()
    results = await queue.process_queue()
    end_time = time.time()

    print(f"⚡ BATCH TERMINÉ: {len(results)} descriptions en {end_time - start_time:.2f}s")

    # Mapper les résultats aux livres originaux
    results_map = {r['url']: r['description'] for r in results if isinstance(r, dict)}

    # Mettre à jour les livres avec les descriptions
    livres_updated = []
    for livre in urls_livres:
        livre_copy = livre.copy()
        livre_copy['description'] = results_map.get(livre['url'], "Description non trouvée")
        livres_updated.append(livre_copy)

    return livres_updated

# Fonction pour compatibilité avec l'ancien système
async def recuperer_description_depuis_url_async(url: str, asin: str = None, isbn: str = None, titre: str = None) -> str:
    """
    Version async de recuperer_description_depuis_url
    """
    return await extraire_description_async(url, titre)

if __name__ == "__main__":
    # Test rapide
    async def test():
        url_test = "https://www.amazon.fr/dp/2266292617"
        description = await extraire_description_async(url_test, "Test")
        print(f"Test result: {description}")

    asyncio.run(test())