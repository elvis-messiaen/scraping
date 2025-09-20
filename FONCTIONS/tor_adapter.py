#!/usr/bin/env python3
"""
ADAPTATEUR TOR POUR SCRAPING ANONYME
===================================
Remplace les proxies gratuits par le réseau TOR
Plus fiable et complètement gratuit
"""

import requests
import socks
import socket
import time
from typing import Optional, Dict
import logging

class TorAdapter:
    """
    Adaptateur TOR pour requests anonymes

    Utilise le réseau TOR pour masquer l'IP et éviter la détection.
    Plus fiable que les proxies gratuits.
    """

    def __init__(self, tor_port: int = 9050, control_port: int = 9051):
        """
        Initialiser l'adaptateur TOR

        Args:
            tor_port (int): Port SOCKS de TOR (défaut: 9050)
            control_port (int): Port de contrôle TOR (défaut: 9051)
        """
        self.tor_port = tor_port
        self.control_port = control_port
        self.session = None
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'total_requetes': 0,
            'requetes_reussies': 0,
            'rotations_effectuees': 0,
            'temps_moyen_reponse': 0.0
        }

    def configurer_session_tor(self) -> requests.Session:
        """
        Configurer une session requests pour utiliser TOR

        Returns:
            requests.Session: Session configurée pour TOR
        """
        try:
            # Créer une session
            session = requests.Session()

            # Configurer les proxies TOR
            session.proxies = {
                'http': f'socks5://127.0.0.1:{self.tor_port}',
                'https': f'socks5://127.0.0.1:{self.tor_port}'
            }

            # Headers réalistes
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })

            self.session = session
            self.logger.info("Session TOR configurée avec succès")
            return session

        except Exception as e:
            self.logger.error(f"Erreur configuration TOR: {e}")
            return None

    def tester_connexion_tor(self) -> bool:
        """
        Tester la connexion TOR

        Returns:
            bool: True si TOR fonctionne
        """
        try:
            if not self.session:
                self.session = self.configurer_session_tor()

            if not self.session:
                return False

            # Test avec un service qui montre l'IP
            response = self.session.get(
                'http://httpbin.org/ip',
                timeout=10
            )

            if response.status_code == 200:
                ip_info = response.json()
                print(f"✅ TOR actif - IP: {ip_info.get('origin', 'N/A')}")
                return True
            else:
                print(f"❌ Erreur test TOR: HTTP {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Erreur test TOR: {e}")
            return False

    def nouvelle_identite(self) -> bool:
        """
        Obtenir une nouvelle identité TOR (nouvelle IP)

        Returns:
            bool: True si succès
        """
        try:
            # Envoyer signal NEWNYM au contrôleur TOR
            from stem import Signal
            from stem.control import Controller

            with Controller.from_port(port=self.control_port) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                self.stats['rotations_effectuees'] += 1
                self.logger.info("Nouvelle identité TOR obtenue")

                # Attendre que le changement prenne effet
                time.sleep(2)
                return True

        except ImportError:
            self.logger.warning("Stem non installé - rotation manuelle impossible")
            return False
        except Exception as e:
            self.logger.error(f"Erreur rotation TOR: {e}")
            return False

    def faire_requete(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Faire une requête via TOR

        Args:
            url (str): URL à requêter
            **kwargs: Arguments pour requests.get()

        Returns:
            Optional[requests.Response]: Réponse ou None si erreur
        """
        try:
            if not self.session:
                self.session = self.configurer_session_tor()

            if not self.session:
                return None

            debut = time.time()
            self.stats['total_requetes'] += 1

            # Faire la requête
            response = self.session.get(url, **kwargs)

            temps_reponse = time.time() - debut

            if response.status_code == 200:
                self.stats['requetes_reussies'] += 1

                # Mettre à jour temps moyen
                if self.stats['temps_moyen_reponse'] == 0:
                    self.stats['temps_moyen_reponse'] = temps_reponse
                else:
                    self.stats['temps_moyen_reponse'] = (
                        self.stats['temps_moyen_reponse'] * 0.9 + temps_reponse * 0.1
                    )

                self.logger.info(f"Requête TOR réussie: {url} ({temps_reponse:.2f}s)")

            return response

        except Exception as e:
            self.logger.error(f"Erreur requête TOR {url}: {e}")
            return None

    def obtenir_ip_actuelle(self) -> Optional[str]:
        """
        Obtenir l'IP actuelle via TOR

        Returns:
            Optional[str]: IP actuelle ou None
        """
        try:
            response = self.faire_requete('http://httpbin.org/ip', timeout=10)
            if response and response.status_code == 200:
                return response.json().get('origin')
        except Exception as e:
            self.logger.error(f"Erreur obtention IP: {e}")
        return None

    def obtenir_statistiques(self) -> Dict:
        """
        Obtenir les statistiques TOR

        Returns:
            Dict: Statistiques complètes
        """
        taux_succes = 0
        if self.stats['total_requetes'] > 0:
            taux_succes = (self.stats['requetes_reussies'] / self.stats['total_requetes']) * 100

        return {
            **self.stats,
            'taux_succes_pct': taux_succes,
            'ip_actuelle': self.obtenir_ip_actuelle()
        }

def creer_adaptateur_tor() -> TorAdapter:
    """
    Factory function pour créer un adaptateur TOR

    Returns:
        TorAdapter: Instance configurée
    """
    return TorAdapter()

def tester_tor_complet():
    """Test complet de l'adaptateur TOR"""
    print("🧅 TEST COMPLET TOR NETWORK")
    print("=" * 50)

    # Créer adaptateur
    tor = creer_adaptateur_tor()

    # Test configuration
    print("1. Configuration session TOR...")
    session = tor.configurer_session_tor()
    if session:
        print("   ✅ Session configurée")
    else:
        print("   ❌ Échec configuration")
        return False

    # Test connexion
    print("2. Test connexion TOR...")
    if tor.tester_connexion_tor():
        print("   ✅ Connexion TOR active")
    else:
        print("   ❌ Connexion TOR échouée")
        return False

    # Test requête
    print("3. Test requête Amazon...")
    response = tor.faire_requete('https://www.amazon.fr', timeout=15)
    if response and response.status_code == 200:
        print(f"   ✅ Amazon accessible via TOR (HTTP {response.status_code})")
    else:
        print("   ❌ Échec requête Amazon")
        return False

    # Test rotation (optionnel)
    print("4. Test rotation IP...")
    ip_avant = tor.obtenir_ip_actuelle()
    print(f"   IP avant: {ip_avant}")

    if tor.nouvelle_identite():
        time.sleep(3)
        ip_apres = tor.obtenir_ip_actuelle()
        print(f"   IP après: {ip_apres}")
        if ip_avant != ip_apres:
            print("   ✅ Rotation IP réussie")
        else:
            print("   ⚠️ Rotation IP échouée (même IP)")
    else:
        print("   ⚠️ Rotation non disponible")

    # Statistiques
    stats = tor.obtenir_statistiques()
    print(f"\n📊 STATISTIQUES TOR:")
    print(f"   Requêtes totales: {stats['total_requetes']}")
    print(f"   Taux de succès: {stats['taux_succes_pct']:.1f}%")
    print(f"   Temps moyen: {stats['temps_moyen_reponse']:.2f}s")

    return True

if __name__ == "__main__":
    tester_tor_complet()