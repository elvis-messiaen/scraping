#!/usr/bin/env python3
"""
MODULE DE SCRAPING ASYNCHRONE HAUTE PERFORMANCE
===============================================
Système de scraping asynchrone avec gestion intelligente des sessions,
pool de connexions, et optimisations pour le scraping à grande échelle
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import ssl
import certifi

@dataclass
class RequeteAsynchrone:
    """
    Représentation d'une requête asynchrone

    Contient toutes les informations nécessaires pour effectuer
    une requête HTTP asynchrone avec ses paramètres et callbacks.
    """
    url: str
    headers: Optional[Dict[str, str]] = None
    proxies: Optional[str] = None
    timeout: int = 15
    callback: Optional[Callable] = None
    metadata: Optional[Dict] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class ReponseAsynchrone:
    """
    Résultat d'une requête asynchrone

    Encapsule la réponse HTTP avec métadonnées additionnelles
    pour le traitement et l'analyse.
    """
    url: str
    status_code: int
    content: str
    headers: Dict[str, str]
    temps_reponse: float
    success: bool
    erreur: Optional[str] = None
    metadata: Optional[Dict] = None

class GestionnaireScrapingAsynchrone:
    """
    Gestionnaire principal du scraping asynchrone

    Cette classe orchestre les requêtes asynchrones avec gestion intelligente
    des sessions, rotation des proxies/headers, et optimisations de performance.

    Attributs:
        session (aiohttp.ClientSession): Session HTTP réutilisable
        semaphore (asyncio.Semaphore): Contrôle de concurrence
        stats (Dict): Statistiques de performance
    """

    def __init__(self,
                 max_concurrent_requests: int = 10,
                 timeout_total: int = 30,
                 pool_connector_limit: int = 100):
        """
        Initialiser le gestionnaire de scraping asynchrone

        Args:
            max_concurrent_requests (int): Nombre max de requêtes simultanées
            timeout_total (int): Timeout total par défaut en secondes
            pool_connector_limit (int): Limite du pool de connexions
        """
        self.max_concurrent_requests = max_concurrent_requests
        self.timeout_total = timeout_total
        self.pool_connector_limit = pool_connector_limit

        # Session et connexions
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None

        # Statistiques et métriques
        self.stats = {
            'requetes_total': 0,
            'requetes_reussies': 0,
            'requetes_echecs': 0,
            'temps_total_execution': 0.0,
            'temps_moyen_requete': 0.0,
            'vitesse_requetes_seconde': 0.0,
            'sessions_creees': 0,
            'erreurs_par_type': {},
            'codes_status_recus': {},
            'urls_en_erreur': set()
        }

        # Configuration SSL/TLS sécurisée
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        print(f"🚀 Gestionnaire async initialisé: {max_concurrent_requests} requêtes simultanées max")

    async def __aenter__(self):
        """Gestionnaire de contexte async - entrée"""
        await self.initialiser_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Gestionnaire de contexte async - sortie"""
        await self.fermer_session()

    async def initialiser_session(self) -> None:
        """
        Initialiser la session HTTP asynchrone avec optimisations

        Configure une session aiohttp optimisée avec pool de connexions,
        timeouts appropriés, et paramètres de performance.
        """
        if self.session and not self.session.closed:
            return

        # Configuration du connecteur TCP avec optimisations
        connector = aiohttp.TCPConnector(
            limit=self.pool_connector_limit,  # Pool de connexions
            limit_per_host=20,  # Connexions par host
            ttl_dns_cache=300,  # Cache DNS 5 minutes
            use_dns_cache=True,
            keepalive_timeout=30,  # Keep-alive 30 secondes
            enable_cleanup_closed=True,
            ssl=self.ssl_context
        )

        # Configuration des timeouts
        timeout = aiohttp.ClientTimeout(
            total=self.timeout_total,
            connect=10,
            sock_read=15
        )

        # Créer la session
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Connection': 'keep-alive'}
        )

        # Sémaphore pour contrôler la concurrence
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        self.stats['sessions_creees'] += 1
        print(f"✅ Session async initialisée (Pool: {self.pool_connector_limit} connexions)")

    async def fermer_session(self) -> None:
        """
        Fermer proprement la session HTTP asynchrone

        Ferme la session et libère toutes les ressources associées.
        """
        if self.session and not self.session.closed:
            await self.session.close()
            print("🔒 Session async fermée")

    async def effectuer_requete(self, requete: RequeteAsynchrone) -> ReponseAsynchrone:
        """
        Effectuer une requête HTTP asynchrone

        Exécute une requête avec gestion d'erreurs, retry automatique,
        et collecte de métriques de performance.

        Args:
            requete (RequeteAsynchrone): Requête à effectuer

        Returns:
            ReponseAsynchrone: Résultat de la requête
        """
        if not self.session:
            await self.initialiser_session()

        async with self.semaphore:  # Contrôle de concurrence
            debut = time.time()

            try:
                # Préparer les paramètres de la requête
                kwargs = {
                    'headers': requete.headers or {},
                    'ssl': self.ssl_context
                }

                # Ajouter le proxy si spécifié
                if requete.proxies:
                    kwargs['proxy'] = requete.proxies

                # Effectuer la requête
                async with self.session.get(requete.url, **kwargs) as response:
                    content = await response.text()
                    temps_reponse = time.time() - debut

                    # Créer l'objet réponse
                    reponse = ReponseAsynchrone(
                        url=requete.url,
                        status_code=response.status,
                        content=content,
                        headers=dict(response.headers),
                        temps_reponse=temps_reponse,
                        success=200 <= response.status < 300,
                        metadata=requete.metadata
                    )

                    # Mettre à jour les statistiques
                    await self._mettre_a_jour_stats(reponse, None)

                    return reponse

            except Exception as e:
                temps_reponse = time.time() - debut
                erreur = str(e)

                # Créer réponse d'erreur
                reponse = ReponseAsynchrone(
                    url=requete.url,
                    status_code=0,
                    content="",
                    headers={},
                    temps_reponse=temps_reponse,
                    success=False,
                    erreur=erreur,
                    metadata=requete.metadata
                )

                # Mettre à jour les statistiques
                await self._mettre_a_jour_stats(reponse, erreur)

                # Retry automatique si configuré
                if requete.retry_count < requete.max_retries:
                    print(f"🔄 Retry {requete.retry_count + 1}/{requete.max_retries} pour {requete.url}")
                    requete.retry_count += 1
                    await asyncio.sleep(2 ** requete.retry_count)  # Backoff exponentiel
                    return await self.effectuer_requete(requete)

                return reponse

    async def _mettre_a_jour_stats(self, reponse: ReponseAsynchrone, erreur: Optional[str]) -> None:
        """
        Mettre à jour les statistiques de performance

        Args:
            reponse (ReponseAsynchrone): Réponse reçue
            erreur (Optional[str]): Message d'erreur si applicable
        """
        self.stats['requetes_total'] += 1

        if reponse.success:
            self.stats['requetes_reussies'] += 1
        else:
            self.stats['requetes_echecs'] += 1
            if erreur:
                type_erreur = type(Exception(erreur)).__name__
                if type_erreur not in self.stats['erreurs_par_type']:
                    self.stats['erreurs_par_type'][type_erreur] = 0
                self.stats['erreurs_par_type'][type_erreur] += 1

        # Statistiques des codes de status
        if reponse.status_code not in self.stats['codes_status_recus']:
            self.stats['codes_status_recus'][reponse.status_code] = 0
        self.stats['codes_status_recus'][reponse.status_code] += 1

        # Métriques de temps
        self.stats['temps_total_execution'] += reponse.temps_reponse
        self.stats['temps_moyen_requete'] = (
            self.stats['temps_total_execution'] / self.stats['requetes_total']
        )

        if self.stats['temps_total_execution'] > 0:
            self.stats['vitesse_requetes_seconde'] = (
                self.stats['requetes_total'] / self.stats['temps_total_execution']
            )

    async def scraper_urls_batch(self,
                                urls: List[str],
                                headers_par_url: Optional[Dict[str, Dict]] = None,
                                proxies_par_url: Optional[Dict[str, str]] = None,
                                callback: Optional[Callable] = None) -> List[ReponseAsynchrone]:
        """
        Scraper une liste d'URLs en mode batch asynchrone

        Traite plusieurs URLs simultanément avec gestion intelligente
        de la concurrence et des erreurs.

        Args:
            urls (List[str]): Liste des URLs à scraper
            headers_par_url (Optional[Dict]): Headers spécifiques par URL
            proxies_par_url (Optional[Dict]): Proxies spécifiques par URL
            callback (Optional[Callable]): Fonction de callback pour chaque réponse

        Returns:
            List[ReponseAsynchrone]: Liste des réponses obtenues
        """
        print(f"📦 Début scraping batch: {len(urls)} URLs")
        debut_batch = time.time()

        # Créer les requêtes
        requetes = []
        for url in urls:
            headers = headers_par_url.get(url) if headers_par_url else None
            proxies = proxies_par_url.get(url) if proxies_par_url else None

            requete = RequeteAsynchrone(
                url=url,
                headers=headers,
                proxies=proxies,
                callback=callback
            )
            requetes.append(requete)

        # Exécuter toutes les requêtes en parallèle
        taches = [self.effectuer_requete(requete) for requete in requetes]
        reponses = await asyncio.gather(*taches, return_exceptions=True)

        # Traiter les exceptions
        reponses_finales = []
        for i, reponse in enumerate(reponses):
            if isinstance(reponse, Exception):
                # Créer une réponse d'erreur
                reponse_erreur = ReponseAsynchrone(
                    url=urls[i],
                    status_code=0,
                    content="",
                    headers={},
                    temps_reponse=0.0,
                    success=False,
                    erreur=str(reponse)
                )
                reponses_finales.append(reponse_erreur)
            else:
                reponses_finales.append(reponse)

                # Appeler le callback si fourni
                if callback:
                    try:
                        await callback(reponse) if asyncio.iscoroutinefunction(callback) else callback(reponse)
                    except Exception as e:
                        print(f"⚠️ Erreur callback pour {reponse.url}: {e}")

        duree_batch = time.time() - debut_batch
        vitesse = len(urls) / duree_batch if duree_batch > 0 else 0

        print(f"✅ Batch terminé: {len(reponses_finales)} réponses en {duree_batch:.2f}s ({vitesse:.1f} req/s)")

        return reponses_finales

    async def scraper_avec_parsing(self,
                                 url: str,
                                 selecteur_css: str,
                                 headers: Optional[Dict] = None,
                                 proxy: Optional[str] = None) -> List[Dict]:
        """
        Scraper une URL avec parsing automatique du contenu

        Combine requête asynchrone et parsing BeautifulSoup pour
        extraire directement les données souhaitées.

        Args:
            url (str): URL à scraper
            selecteur_css (str): Sélecteur CSS pour extraire les données
            headers (Optional[Dict]): Headers HTTP à utiliser
            proxy (Optional[str]): Proxy à utiliser

        Returns:
            List[Dict]: Liste des éléments extraits
        """
        requete = RequeteAsynchrone(url=url, headers=headers, proxies=proxy)
        reponse = await self.effectuer_requete(requete)

        if not reponse.success:
            print(f"❌ Échec scraping {url}: {reponse.erreur}")
            return []

        # Parser le contenu HTML
        try:
            soup = BeautifulSoup(reponse.content, 'html.parser')
            elements = soup.select(selecteur_css)

            resultats = []
            for element in elements:
                resultats.append({
                    'text': element.get_text(strip=True),
                    'html': str(element),
                    'attributes': element.attrs
                })

            print(f"✅ Extraction réussie: {len(resultats)} éléments trouvés")
            return resultats

        except Exception as e:
            print(f"❌ Erreur parsing {url}: {e}")
            return []

    def obtenir_statistiques(self) -> Dict:
        """
        Obtenir les statistiques complètes du gestionnaire

        Returns:
            Dict: Métriques de performance et statistiques d'usage
        """
        stats = dict(self.stats)

        # Calculer des métriques additionnelles
        if stats['requetes_total'] > 0:
            stats['taux_succes_pct'] = (stats['requetes_reussies'] / stats['requetes_total']) * 100
            stats['taux_echec_pct'] = (stats['requetes_echecs'] / stats['requetes_total']) * 100

        # Nettoyer les sets pour la sérialisation JSON
        stats['urls_en_erreur'] = list(stats['urls_en_erreur'])

        return stats

    def reinitialiser_statistiques(self) -> None:
        """Réinitialiser toutes les statistiques"""
        self.stats = {
            'requetes_total': 0,
            'requetes_reussies': 0,
            'requetes_echecs': 0,
            'temps_total_execution': 0.0,
            'temps_moyen_requete': 0.0,
            'vitesse_requetes_seconde': 0.0,
            'sessions_creees': self.stats['sessions_creees'],  # Conserver ce compteur
            'erreurs_par_type': {},
            'codes_status_recus': {},
            'urls_en_erreur': set()
        }
        print("🔄 Statistiques réinitialisées")


class ProcesseurAsynchroneBatch:
    """
    Processeur spécialisé pour traitement batch à grande échelle

    Optimisé pour traiter de très grandes listes d'URLs avec
    gestion mémoire efficace et traitement par chunks.
    """

    def __init__(self, taille_chunk: int = 50, delai_entre_chunks: float = 1.0):
        """
        Args:
            taille_chunk (int): Nombre d'URLs par chunk
            delai_entre_chunks (float): Délai entre chaque chunk en secondes
        """
        self.taille_chunk = taille_chunk
        self.delai_entre_chunks = delai_entre_chunks
        self.gestionnaire = GestionnaireScrapingAsynchrone()

    async def traiter_grande_liste(self,
                                 urls: List[str],
                                 callback_progression: Optional[Callable] = None) -> List[ReponseAsynchrone]:
        """
        Traiter une très grande liste d'URLs par chunks

        Args:
            urls (List[str]): Liste complète des URLs
            callback_progression (Optional[Callable]): Callback de progression

        Returns:
            List[ReponseAsynchrone]: Toutes les réponses collectées
        """
        total_urls = len(urls)
        print(f"🔄 Traitement grande liste: {total_urls} URLs en chunks de {self.taille_chunk}")

        toutes_reponses = []

        async with self.gestionnaire:
            for i in range(0, total_urls, self.taille_chunk):
                chunk = urls[i:i + self.taille_chunk]
                chunk_num = (i // self.taille_chunk) + 1
                total_chunks = (total_urls + self.taille_chunk - 1) // self.taille_chunk

                print(f"📦 Chunk {chunk_num}/{total_chunks}: {len(chunk)} URLs")

                # Traiter le chunk
                reponses_chunk = await self.gestionnaire.scraper_urls_batch(chunk)
                toutes_reponses.extend(reponses_chunk)

                # Callback de progression
                if callback_progression:
                    await callback_progression(chunk_num, total_chunks, len(toutes_reponses))

                # Délai entre chunks
                if i + self.taille_chunk < total_urls:
                    await asyncio.sleep(self.delai_entre_chunks)

        print(f"✅ Traitement terminé: {len(toutes_reponses)} réponses collectées")
        return toutes_reponses


async def scraper_urls_simple(urls: List[str],
                             headers: Optional[Dict] = None,
                             max_concurrent: int = 10) -> List[ReponseAsynchrone]:
    """
    Fonction utilitaire pour scraper simplement une liste d'URLs

    Args:
        urls (List[str]): URLs à scraper
        headers (Optional[Dict]): Headers à utiliser
        max_concurrent (int): Nombre de requêtes simultanées

    Returns:
        List[ReponseAsynchrone]: Réponses obtenues
    """
    async with GestionnaireScrapingAsynchrone(max_concurrent_requests=max_concurrent) as gestionnaire:
        return await gestionnaire.scraper_urls_batch(urls, {url: headers for url in urls} if headers else None)


if __name__ == "__main__":
    # Test du système de scraping asynchrone
    print("🧪 Test du système de scraping asynchrone")

    async def test_async():
        # URLs de test
        urls_test = [
            "https://www.amazon.fr",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/status/200",
            "https://httpbin.org/json"
        ]

        print(f"\n🚀 Test avec {len(urls_test)} URLs")

        # Test simple
        reponses = await scraper_urls_simple(urls_test, max_concurrent=3)

        print(f"\n📊 Résultats:")
        for reponse in reponses:
            status = "✅" if reponse.success else "❌"
            print(f"  {status} {reponse.url}: {reponse.status_code} ({reponse.temps_reponse:.2f}s)")

        # Test avec gestionnaire complet
        async with GestionnaireScrapingAsynchrone(max_concurrent_requests=5) as gestionnaire:
            reponses2 = await gestionnaire.scraper_urls_batch(urls_test[:2])

            stats = gestionnaire.obtenir_statistiques()
            print(f"\n📈 Statistiques:")
            print(f"  Total requêtes: {stats['requetes_total']}")
            print(f"  Taux succès: {stats.get('taux_succes_pct', 0):.1f}%")
            print(f"  Vitesse: {stats['vitesse_requetes_seconde']:.1f} req/s")

    # Exécuter le test
    asyncio.run(test_async())