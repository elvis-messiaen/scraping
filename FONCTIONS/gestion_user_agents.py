#!/usr/bin/env python3
"""
MODULE DE GESTION DES USER-AGENTS POUR SCRAPING
===============================================
Fonctions pour gérer la rotation des User-Agents et headers associés
Évite la détection en simulant différents navigateurs et appareils
"""

import random
import json
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import threading

class GestionnaireUserAgents:
    """
    Gestionnaire de User-Agents avec rotation intelligente

    Cette classe gère une base de données de User-Agents réalistes,
    effectue des rotations cohérentes avec les headers associés,
    et maintient la cohérence entre les différents headers du navigateur.

    Attributs:
        user_agents (List[Dict]): Base de données des User-Agents
        user_agent_actuel (Dict): User-Agent actuellement utilisé
        derniere_rotation (datetime): Horodatage de la dernière rotation
        stats (Dict): Statistiques d'utilisation
    """

    def __init__(self):
        """
        Initialiser le gestionnaire de User-Agents

        Configure la base de données de User-Agents avec leurs headers
        associés et initialise le système de rotation.
        """
        self.user_agents = []
        self.user_agent_actuel_index = 0
        self.derniere_rotation = datetime.now()
        self.intervalle_rotation = timedelta(minutes=2)  # Rotation toutes les 2 minutes
        self.lock = threading.Lock()

        # Statistiques d'utilisation
        self.stats = {
            'total_rotations': 0,
            'user_agents_utilises': set(),
            'navigateurs_simules': {}
        }

        # Charger la base de données de User-Agents
        self.charger_user_agents()

    def charger_user_agents(self) -> None:
        """
        Charger une base de données complète de User-Agents réalistes

        Crée une collection de User-Agents authentiques avec leurs headers
        associés pour différents navigateurs, OS et appareils.
        """
        print("🔄 Chargement de la base de données User-Agents...")

        # User-Agents Chrome (Windows, Mac, Linux)
        chrome_agents = [
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'navigateur': 'Chrome',
                'os': 'Windows 10',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Windows"'
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'navigateur': 'Chrome',
                'os': 'macOS',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"macOS"'
            },
            {
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'navigateur': 'Chrome',
                'os': 'Linux',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Linux"'
            },
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'navigateur': 'Chrome',
                'os': 'Windows 10',
                'sec_ch_ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Windows"'
            }
        ]

        # User-Agents Firefox (Windows, Mac, Linux)
        firefox_agents = [
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'navigateur': 'Firefox',
                'os': 'Windows 10',
                'sec_ch_ua': None,  # Firefox n'utilise pas les client hints
                'sec_ch_ua_mobile': None,
                'sec_ch_ua_platform': None
            },
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
                'navigateur': 'Firefox',
                'os': 'macOS',
                'sec_ch_ua': None,
                'sec_ch_ua_mobile': None,
                'sec_ch_ua_platform': None
            },
            {
                'user_agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'navigateur': 'Firefox',
                'os': 'Linux',
                'sec_ch_ua': None,
                'sec_ch_ua_mobile': None,
                'sec_ch_ua_platform': None
            }
        ]

        # User-Agents Safari (Mac, iPhone, iPad)
        safari_agents = [
            {
                'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
                'navigateur': 'Safari',
                'os': 'macOS',
                'sec_ch_ua': None,  # Safari n'utilise pas les client hints
                'sec_ch_ua_mobile': None,
                'sec_ch_ua_platform': None
            },
            {
                'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
                'navigateur': 'Safari',
                'os': 'iOS',
                'sec_ch_ua': None,
                'sec_ch_ua_mobile': '?1',
                'sec_ch_ua_platform': '"iOS"'
            }
        ]

        # User-Agents Edge (Windows)
        edge_agents = [
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                'navigateur': 'Edge',
                'os': 'Windows 10',
                'sec_ch_ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Windows"'
            },
            {
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
                'navigateur': 'Edge',
                'os': 'Windows 10',
                'sec_ch_ua': '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
                'sec_ch_ua_mobile': '?0',
                'sec_ch_ua_platform': '"Windows"'
            }
        ]

        # Combiner tous les User-Agents
        self.user_agents = chrome_agents + firefox_agents + safari_agents + edge_agents

        # Mélanger la liste pour plus de randomisation
        random.shuffle(self.user_agents)

        print(f"✅ {len(self.user_agents)} User-Agents chargés")

    def obtenir_user_agent_actuel(self) -> Dict:
        """
        Obtenir le User-Agent actuellement sélectionné avec rotation automatique

        Retourne le User-Agent actuel et effectue une rotation si l'intervalle
        de temps est dépassé. Thread-safe pour utilisation concurrente.

        Returns:
            Dict: User-Agent actuel avec ses headers associés
        """
        with self.lock:
            # Vérifier s'il faut effectuer une rotation
            if datetime.now() - self.derniere_rotation > self.intervalle_rotation:
                self.effectuer_rotation()

            return self.user_agents[self.user_agent_actuel_index]

    def effectuer_rotation(self) -> None:
        """
        Effectuer une rotation vers le User-Agent suivant

        Passe au User-Agent suivant dans la liste et met à jour les statistiques.
        Cette méthode doit être appelée avec le verrou lock acquis.
        """
        ancien_index = self.user_agent_actuel_index
        self.user_agent_actuel_index = (self.user_agent_actuel_index + 1) % len(self.user_agents)
        self.derniere_rotation = datetime.now()
        self.stats['total_rotations'] += 1

        # Mettre à jour les statistiques
        user_agent_actuel = self.user_agents[self.user_agent_actuel_index]
        self.stats['user_agents_utilises'].add(user_agent_actuel['user_agent'])

        navigateur = user_agent_actuel['navigateur']
        if navigateur not in self.stats['navigateurs_simules']:
            self.stats['navigateurs_simules'][navigateur] = 0
        self.stats['navigateurs_simules'][navigateur] += 1

        print(f"🔄 User-Agent rotation: {user_agent_actuel['navigateur']} ({user_agent_actuel['os']})")

    def obtenir_user_agent_aleatoire(self) -> Dict:
        """
        Obtenir un User-Agent complètement aléatoire

        Sélectionne un User-Agent au hasard sans affecter la rotation normale.
        Utile pour des requêtes ponctuelles nécessitant une randomisation maximale.

        Returns:
            Dict: User-Agent aléatoire avec ses headers associés
        """
        return random.choice(self.user_agents)

    def creer_headers_complets(self, user_agent_data: Optional[Dict] = None, referer: Optional[str] = None) -> Dict:
        """
        Créer un ensemble complet de headers HTTP réalistes

        Génère des headers cohérents basés sur le User-Agent sélectionné,
        incluant tous les headers nécessaires pour simuler un navigateur réel.

        Args:
            user_agent_data (Optional[Dict]): User-Agent à utiliser (actuel si None)
            referer (Optional[str]): URL de référence (optionnel)

        Returns:
            Dict: Headers HTTP complets et cohérents
        """
        if user_agent_data is None:
            user_agent_data = self.obtenir_user_agent_actuel()

        # Headers de base communs
        headers = {
            'User-Agent': user_agent_data['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': random.choice([
                'fr-FR,fr;q=0.9,en;q=0.8',
                'en-US,en;q=0.9,fr;q=0.8',
                'fr,en-US;q=0.9,en;q=0.8'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': random.choice(['1', '0']),
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        # Ajouter le referer si fourni
        if referer:
            headers['Referer'] = referer

        # Headers spécifiques selon le navigateur
        if user_agent_data['navigateur'] in ['Chrome', 'Edge']:
            # Headers Client Hints pour Chromium
            if user_agent_data['sec_ch_ua']:
                headers['Sec-Ch-Ua'] = user_agent_data['sec_ch_ua']
                headers['Sec-Ch-Ua-Mobile'] = user_agent_data['sec_ch_ua_mobile']
                headers['Sec-Ch-Ua-Platform'] = user_agent_data['sec_ch_ua_platform']

            headers['Sec-Fetch-Site'] = random.choice(['same-origin', 'cross-site', 'none'])
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Sec-Fetch-User'] = '?1'
            headers['Sec-Fetch-Dest'] = 'document'

        elif user_agent_data['navigateur'] == 'Firefox':
            # Headers spécifiques à Firefox
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8'
            headers['Sec-Fetch-Site'] = random.choice(['same-origin', 'cross-site', 'none'])
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Sec-Fetch-Dest'] = 'document'

        elif user_agent_data['navigateur'] == 'Safari':
            # Headers spécifiques à Safari
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            if 'iPhone' in user_agent_data['user_agent'] or 'iPad' in user_agent_data['user_agent']:
                headers['Accept-Language'] = 'fr-fr'

        return headers

    def obtenir_statistiques(self) -> Dict:
        """
        Obtenir les statistiques d'utilisation des User-Agents

        Returns:
            Dict: Statistiques complètes incluant rotations et navigateurs utilisés
        """
        with self.lock:
            return {
                'total_rotations': self.stats['total_rotations'],
                'user_agents_uniques_utilises': len(self.stats['user_agents_utilises']),
                'total_user_agents_disponibles': len(self.user_agents),
                'navigateurs_simules': dict(self.stats['navigateurs_simules']),
                'user_agent_actuel': self.user_agents[self.user_agent_actuel_index]['user_agent'][:50] + '...'
            }

    def forcer_rotation(self) -> Dict:
        """
        Forcer une rotation immédiate du User-Agent

        Effectue une rotation immédiate sans attendre l'intervalle normal.
        Utile en cas de blocage détecté ou pour randomiser ponctuellement.

        Returns:
            Dict: Nouveau User-Agent après rotation
        """
        with self.lock:
            self.effectuer_rotation()
            return self.user_agents[self.user_agent_actuel_index]


def creer_gestionnaire_user_agents() -> GestionnaireUserAgents:
    """
    Créer et initialiser un gestionnaire de User-Agents

    Factory function pour créer une instance du gestionnaire
    avec configuration par défaut.

    Returns:
        GestionnaireUserAgents: Instance configurée du gestionnaire
    """
    return GestionnaireUserAgents()


def obtenir_headers_realistes(gestionnaire: Optional[GestionnaireUserAgents] = None,
                             referer: Optional[str] = None) -> Dict:
    """
    Obtenir des headers HTTP réalistes pour une requête

    Fonction utilitaire pour obtenir rapidement des headers authentiques
    avec User-Agent et headers associés cohérents.

    Args:
        gestionnaire (Optional[GestionnaireUserAgents]): Gestionnaire à utiliser
        referer (Optional[str]): URL de référence (optionnel)

    Returns:
        Dict: Headers HTTP complets et réalistes
    """
    if gestionnaire is None:
        gestionnaire = creer_gestionnaire_user_agents()

    return gestionnaire.creer_headers_complets(referer=referer)


if __name__ == "__main__":
    # Test du gestionnaire de User-Agents
    print("🧪 Test du gestionnaire de User-Agents")
    gestionnaire = creer_gestionnaire_user_agents()

    # Test de récupération de headers
    headers = obtenir_headers_realistes(gestionnaire, referer="https://www.amazon.fr")
    print(f"✅ Headers générés:")
    for key, value in headers.items():
        print(f"  {key}: {value}")

    # Test des statistiques
    stats = gestionnaire.obtenir_statistiques()
    print(f"\n📊 Statistiques: {stats}")

    # Test de rotation forcée
    print("\n🔄 Test de rotation forcée...")
    nouveau_ua = gestionnaire.forcer_rotation()
    print(f"Nouveau User-Agent: {nouveau_ua['navigateur']} ({nouveau_ua['os']})")