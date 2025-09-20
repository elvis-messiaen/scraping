#!/usr/bin/env python3
"""
MODULE DE GESTION DES PROXIES POUR SCRAPING
==========================================
Fonctions pour gérer la rotation de proxies et éviter la détection
Utilise des proxies gratuits avec rotation automatique
"""

import requests
import random
import time
from typing import List, Dict, Optional
import threading
from datetime import datetime, timedelta
import logging
import sys
import os

# Importer l'adaptateur TOR
try:
    from tor_adapter import TorAdapter
    TOR_DISPONIBLE = True
except ImportError:
    TOR_DISPONIBLE = False

class GestionnaireProxies:
    """
    Gestionnaire de proxies pour scraping avec rotation automatique

    Cette classe gère une liste de proxies gratuits, teste leur validité,
    et effectue une rotation automatique pour éviter les blocages.

    Attributs:
        proxies_actifs (List[Dict]): Liste des proxies fonctionnels
        proxy_actuel_index (int): Index du proxy actuellement utilisé
        stats (Dict): Statistiques d'utilisation des proxies
        lock (threading.Lock): Verrou pour thread safety
    """

    def __init__(self, mode_sans_proxy=False):
        """
        Initialiser le gestionnaire de proxies

        Configure la liste initiale de proxies gratuits et initialise
        les statistiques de performance.

        Args:
            mode_sans_proxy (bool): Si True, ne charge pas de proxies (mode direct)
        """
        self.proxies_actifs = []
        self.proxies_blacklistes = set()
        self.proxy_actuel_index = 0
        self.derniere_rotation = datetime.now()
        self.intervalle_rotation = timedelta(minutes=5)  # Rotation toutes les 5 minutes
        self.lock = threading.Lock()
        self.mode_sans_proxy = mode_sans_proxy

        # Statistiques de performance
        self.stats = {
            'total_requetes': 0,
            'requetes_reussies': 0,
            'proxies_bloques': 0,
            'rotations_effectuees': 0,
            'temps_moyen_reponse': 0.0
        }

        # Sources de proxies totalement gratuits (HTTP, HTTPS, SOCKS)
        self.sources_proxies_gratuits = [
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://www.proxy-list.download/api/v1/get?type=https",
            "https://www.proxy-list.download/api/v1/get?type=socks4",
            "https://www.proxy-list.download/api/v1/get?type=socks5",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/proxy.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt"
        ]

        # TOR Adapter
        self.tor_adapter = None
        self.mode_tor = False

        # Initialiser la liste de proxies seulement si pas en mode sans proxy
        if not self.mode_sans_proxy:
            # Essayer TOR en premier
            if self.essayer_tor():
                print("🧅 TOR activé avec succès")
                self.mode_tor = True
            else:
                print("⚠️ TOR non disponible, tentative proxies gratuits...")
                self.charger_proxies_gratuits()
        else:
            print("🚀 Mode sans proxy activé - connexion directe")

    def charger_proxies_gratuits(self) -> bool:
        """
        Charger une liste de proxies gratuits depuis diverses sources

        Récupère les proxies depuis plusieurs sources gratuites en ligne,
        les teste et ne garde que ceux qui fonctionnent.

        Returns:
            bool: True si au moins un proxy a été chargé avec succès
        """
        print("🔄 Chargement des proxies gratuits...")
        proxies_candidats = []

        # Proxies gratuits statiques (mise à jour avec proxies plus fiables)
        proxies_statiques = [
            # Proxies publics souvent fonctionnels
            {"http": "http://proxy.server.com:80", "https": "http://proxy.server.com:80"},
            {"http": "http://free-proxy.cz:80", "https": "http://free-proxy.cz:80"},
            {"http": "http://proxy-list.org:80", "https": "http://proxy-list.org:80"},
        ]

        # Ajouter les proxies statiques
        for proxy in proxies_statiques:
            proxies_candidats.append(proxy)

        # Tenter de récupérer depuis les sources en ligne (limité pour économiser la bande passante)
        for source in self.sources_proxies_gratuits:
            try:
                print(f"  📥 Récupération depuis: {source}")
                response = requests.get(source, timeout=5)
                if response.status_code == 200:
                    # Limiter le téléchargement à 25 lignes seulement pour économiser la bande passante
                    lignes = response.text.strip().split('\n')[:25]
                    for ligne in lignes:
                        if ':' in ligne:
                            ip, port = ligne.strip().split(':')
                            proxy_dict = {
                                "http": f"http://{ip}:{port}",
                                "https": f"http://{ip}:{port}"
                            }
                            proxies_candidats.append(proxy_dict)
            except Exception as e:
                print(f"    ⚠️ Erreur source {source}: {e}")
                continue

        # Tester les proxies et ne garder que les fonctionnels (limité à 15 pour aller plus vite)
        print(f"🧪 Test de {len(proxies_candidats)} proxies (testing first 15)...")
        proxies_valides = self.tester_proxies(proxies_candidats[:15])

        self.proxies_actifs = proxies_valides

        if len(self.proxies_actifs) == 0:
            print("⚠️ Aucun proxy fonctionnel trouvé")
            print("🚀 Passage en mode connexion directe pour continuer")
            self.mode_sans_proxy = True
            return True  # Continuer en mode direct
        else:
            print(f"✅ {len(self.proxies_actifs)} proxies actifs chargés")
            return True

    def tester_proxies(self, liste_proxies: List[Dict]) -> List[Dict]:
        """
        Tester une liste de proxies pour vérifier leur fonctionnalité

        Envoie une requête de test à chaque proxy pour vérifier
        s'il fonctionne correctement et mesurer son temps de réponse.

        Args:
            liste_proxies (List[Dict]): Liste des proxies à tester

        Returns:
            List[Dict]: Liste des proxies fonctionnels avec leurs métriques
        """
        proxies_fonctionnels = []
        url_test = "http://httpbin.org/ip"  # Service simple pour tester les proxies

        for i, proxy in enumerate(liste_proxies):
            try:
                print(f"  🔍 Test proxy {i+1}/{len(liste_proxies)}: {proxy.get('http', 'N/A')}")
                debut = time.time()

                response = requests.get(
                    url_test,
                    proxies=proxy,
                    timeout=3,  # Timeout réduit pour tester plus rapidement
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )

                temps_reponse = time.time() - debut

                if response.status_code == 200:
                    proxy['temps_reponse'] = temps_reponse
                    proxy['derniere_verification'] = datetime.now()
                    proxy['nb_echecs_consecutifs'] = 0
                    proxies_fonctionnels.append(proxy)
                    print(f"    ✅ OK ({temps_reponse:.2f}s)")
                else:
                    print(f"    ❌ Erreur HTTP {response.status_code}")

            except Exception as e:
                print(f"    ❌ Échec: {e}")
                continue

        return proxies_fonctionnels

    def obtenir_proxy_actuel(self) -> Optional[Dict]:
        """
        Obtenir le proxy actuellement sélectionné

        Retourne le proxy actuel avec rotation automatique si nécessaire.
        Thread-safe pour utilisation concurrent.

        Returns:
            Optional[Dict]: Proxy actuel ou None si aucun disponible ou mode sans proxy
        """
        # Si mode sans proxy, retourner None (connexion directe)
        if self.mode_sans_proxy:
            return None

        with self.lock:
            if not self.proxies_actifs:
                print("⚠️ Aucun proxy disponible, rechargement...")
                if not self.charger_proxies_gratuits():
                    return None

            # Vérifier s'il faut effectuer une rotation
            if datetime.now() - self.derniere_rotation > self.intervalle_rotation:
                self.effectuer_rotation()

            if self.proxies_actifs:
                return self.proxies_actifs[self.proxy_actuel_index]
            return None

    def effectuer_rotation(self) -> None:
        """
        Effectuer une rotation vers le proxy suivant

        Passe au proxy suivant dans la liste et met à jour les statistiques.
        Cette méthode doit être appelée avec le verrou lock acquis.
        """
        if len(self.proxies_actifs) > 1:
            self.proxy_actuel_index = (self.proxy_actuel_index + 1) % len(self.proxies_actifs)
            self.derniere_rotation = datetime.now()
            self.stats['rotations_effectuees'] += 1

            proxy_actuel = self.proxies_actifs[self.proxy_actuel_index]
            print(f"🔄 Rotation vers proxy: {proxy_actuel.get('http', 'N/A')}")

    def marquer_proxy_comme_defaillant(self, proxy: Dict) -> None:
        """
        Marquer un proxy comme défaillant et le retirer temporairement

        Incrémente le compteur d'échecs du proxy et le blackliste
        s'il dépasse le seuil d'échecs autorisés.

        Args:
            proxy (Dict): Le proxy à marquer comme défaillant
        """
        with self.lock:
            if proxy in self.proxies_actifs:
                proxy['nb_echecs_consecutifs'] = proxy.get('nb_echecs_consecutifs', 0) + 1

                # Si trop d'échecs, blacklister temporairement
                if proxy['nb_echecs_consecutifs'] >= 3:
                    print(f"🚫 Proxy blacklisté: {proxy.get('http', 'N/A')}")
                    self.proxies_actifs.remove(proxy)
                    self.proxies_blacklistes.add(proxy.get('http', ''))
                    self.stats['proxies_bloques'] += 1

                    # Si plus de proxies, recharger
                    if len(self.proxies_actifs) == 0:
                        print("📥 Rechargement des proxies...")
                        self.charger_proxies_gratuits()

    def enregistrer_requete_reussie(self, temps_reponse: float) -> None:
        """
        Enregistrer une requête réussie et mettre à jour les statistiques

        Met à jour les compteurs de succès et les temps de réponse moyens
        pour le monitoring des performances.

        Args:
            temps_reponse (float): Temps de réponse de la requête en secondes
        """
        with self.lock:
            self.stats['total_requetes'] += 1
            self.stats['requetes_reussies'] += 1

            # Calcul de la moyenne mobile du temps de réponse
            if self.stats['temps_moyen_reponse'] == 0:
                self.stats['temps_moyen_reponse'] = temps_reponse
            else:
                self.stats['temps_moyen_reponse'] = (
                    self.stats['temps_moyen_reponse'] * 0.9 + temps_reponse * 0.1
                )

    def obtenir_statistiques(self) -> Dict:
        """
        Obtenir les statistiques d'utilisation des proxies

        Returns:
            Dict: Statistiques complètes incluant taux de succès et performances
        """
        with self.lock:
            taux_succes = 0
            if self.stats['total_requetes'] > 0:
                taux_succes = (self.stats['requetes_reussies'] / self.stats['total_requetes']) * 100

            return {
                **self.stats,
                'proxies_actifs': len(self.proxies_actifs),
                'proxies_blacklistes': len(self.proxies_blacklistes),
                'taux_succes_pct': taux_succes,
                'proxy_actuel': self.proxies_actifs[self.proxy_actuel_index].get('http', 'N/A') if self.proxies_actifs else 'Aucun'
            }

    def reinitialiser_proxies(self) -> bool:
        """
        Réinitialiser complètement la liste des proxies

        Vide les listes actuelles et recharge une nouvelle liste
        de proxies depuis les sources.

        Returns:
            bool: True si le rechargement a réussi
        """
        with self.lock:
            self.proxies_actifs.clear()
            self.proxies_blacklistes.clear()
            self.proxy_actuel_index = 0
            self.derniere_rotation = datetime.now()

        return self.charger_proxies_gratuits()

    def essayer_tor(self) -> bool:
        """
        Essayer d'initialiser TOR comme proxy principal

        Returns:
            bool: True si TOR est disponible et fonctionnel
        """
        if not TOR_DISPONIBLE:
            print("⚠️ Module TOR non disponible")
            return False

        try:
            print("🧅 Initialisation TOR...")
            self.tor_adapter = TorAdapter()

            # Configurer la session TOR
            session = self.tor_adapter.configurer_session_tor()
            if not session:
                print("❌ Échec configuration session TOR")
                return False

            # Tester la connexion TOR
            if not self.tor_adapter.tester_connexion_tor():
                print("❌ Échec test connexion TOR")
                return False

            print("✅ TOR configuré et fonctionnel")
            return True

        except Exception as e:
            print(f"❌ Erreur initialisation TOR: {e}")
            return False

    def faire_requete_tor(self, url: str, **kwargs):
        """
        Faire une requête via TOR si disponible

        Args:
            url (str): URL à requêter
            **kwargs: Arguments pour la requête

        Returns:
            Response ou None
        """
        if self.mode_tor and self.tor_adapter:
            return self.tor_adapter.faire_requete(url, **kwargs)
        return None


def creer_gestionnaire_proxies(mode_sans_proxy=False) -> GestionnaireProxies:
    """
    Créer et initialiser un gestionnaire de proxies

    Factory function pour créer une instance du gestionnaire
    de proxies avec configuration par défaut.

    Args:
        mode_sans_proxy (bool): Si True, utilise une connexion directe sans proxy

    Returns:
        GestionnaireProxies: Instance configurée du gestionnaire
    """
    return GestionnaireProxies(mode_sans_proxy=mode_sans_proxy)


def obtenir_proxy_pour_requete(gestionnaire: GestionnaireProxies) -> Optional[Dict]:
    """
    Obtenir un proxy optimisé pour une requête

    Fonction utilitaire pour obtenir le meilleur proxy disponible
    avec gestion automatique des rotations et fallbacks.

    Args:
        gestionnaire (GestionnaireProxies): Instance du gestionnaire de proxies

    Returns:
        Optional[Dict]: Proxy optimisé ou None si indisponible
    """
    return gestionnaire.obtenir_proxy_actuel()


if __name__ == "__main__":
    # Test du gestionnaire de proxies
    print("🧪 Test du gestionnaire de proxies")
    gestionnaire = creer_gestionnaire_proxies()

    # Test de récupération de proxy
    proxy = obtenir_proxy_pour_requete(gestionnaire)
    if proxy:
        print(f"✅ Proxy obtenu: {proxy.get('http', 'N/A')}")

        # Test de statistiques
        stats = gestionnaire.obtenir_statistiques()
        print(f"📊 Statistiques: {stats}")
    else:
        print("❌ Aucun proxy disponible")