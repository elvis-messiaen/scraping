#!/usr/bin/env python3
"""
MODULE DE ROTATION AVANCÉE DES HEADERS HTTP
===========================================
Système sophistiqué de rotation et génération de headers HTTP
pour simuler différents navigateurs et éviter la détection
"""

import random
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import threading
import hashlib

@dataclass
class ProfilNavigateur:
    """
    Profil complet d'un navigateur avec ses caractéristiques

    Contient toutes les informations nécessaires pour simuler
    fidèlement un navigateur spécifique avec ses headers cohérents.
    """
    nom: str
    user_agent: str
    accept: str
    accept_language: List[str]
    accept_encoding: str
    sec_ch_ua: Optional[str] = None
    sec_ch_ua_mobile: Optional[str] = None
    sec_ch_ua_platform: Optional[str] = None
    dnt_support: bool = True
    connection: str = "keep-alive"
    upgrade_insecure: bool = True
    cache_control_preferences: List[str] = field(default_factory=list)
    os: str = "Unknown"
    version: str = "Unknown"

class RotateurHeaders:
    """
    Gestionnaire avancé de rotation des headers HTTP

    Cette classe maintient une collection de profils de navigateurs
    authentiques et génère des headers cohérents et réalistes pour
    chaque requête, en évitant les patterns détectables.

    Attributs:
        profils_navigateurs (List[ProfilNavigateur]): Base de profils
        profil_actuel (ProfilNavigateur): Profil actuellement utilisé
        historique_headers (List[Dict]): Historique des headers générés
        stats (Dict): Statistiques d'utilisation
    """

    def __init__(self):
        """
        Initialiser le rotateur de headers

        Configure la base de données de profils de navigateurs et
        initialise le système de rotation intelligent.
        """
        self.profils_navigateurs = []
        self.profil_actuel_index = 0
        self.derniere_rotation = datetime.now()
        self.intervalle_rotation = timedelta(minutes=3)  # Rotation toutes les 3 minutes
        self.historique_headers = []
        self.lock = threading.Lock()

        # Statistiques et métriques
        self.stats = {
            'total_headers_generes': 0,
            'rotations_effectuees': 0,
            'navigateurs_utilises': {},
            'headers_uniques_generes': 0,
            'profils_detectes_comme_suspects': 0
        }

        # Charger les profils de navigateurs
        self.charger_profils_navigateurs()

        # Configuration de rotation avancée
        self.patterns_rotation = {
            'referer_chains': [],  # Chaînes de referers cohérentes
            'session_consistency': True,  # Maintenir cohérence dans session
            'fingerprint_variation': 0.3  # Variation du fingerprinting
        }

        print(f"🔄 Rotateur de headers initialisé avec {len(self.profils_navigateurs)} profils")

    def charger_profils_navigateurs(self) -> None:
        """
        Charger une base complète de profils de navigateurs authentiques

        Crée une collection exhaustive de profils représentant fidèlement
        les navigateurs les plus utilisés avec leurs versions récentes.
        """
        print("📚 Chargement des profils de navigateurs...")

        # Profils Chrome Desktop (Windows, Mac, Linux)
        profils_chrome = [
            ProfilNavigateur(
                nom="Chrome 120 Windows",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                accept_language=["fr-FR,fr;q=0.9,en;q=0.8", "en-US,en;q=0.9,fr;q=0.8"],
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"Windows"',
                cache_control_preferences=["no-cache", "max-age=0"],
                os="Windows 10",
                version="120.0.0.0"
            ),
            ProfilNavigateur(
                nom="Chrome 121 macOS",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                accept_language=["fr-FR,fr;q=0.9,en;q=0.8", "en-US,en;q=0.9"],
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"macOS"',
                os="macOS",
                version="121.0.0.0"
            ),
            ProfilNavigateur(
                nom="Chrome 120 Linux",
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                accept_language=["en-US,en;q=0.9", "fr-FR,fr;q=0.9,en;q=0.8"],
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"Linux"',
                os="Linux",
                version="120.0.0.0"
            )
        ]

        # Profils Firefox Desktop
        profils_firefox = [
            ProfilNavigateur(
                nom="Firefox 121 Windows",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                accept_language=["fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3", "en-US,en;q=0.5"],
                accept_encoding="gzip, deflate, br",
                cache_control_preferences=["no-cache"],
                os="Windows 10",
                version="121.0"
            ),
            ProfilNavigateur(
                nom="Firefox 120 macOS",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                accept_language=["fr,en-US;q=0.7,en;q=0.3", "en-US,en;q=0.5"],
                accept_encoding="gzip, deflate, br",
                os="macOS",
                version="120.0"
            ),
            ProfilNavigateur(
                nom="Firefox 121 Linux",
                user_agent="Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                accept_language=["en-US,en;q=0.5", "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3"],
                accept_encoding="gzip, deflate, br",
                os="Linux",
                version="121.0"
            )
        ]

        # Profils Safari
        profils_safari = [
            ProfilNavigateur(
                nom="Safari 17.1 macOS",
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                accept_language=["fr-fr", "en-us", "fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3"],
                accept_encoding="gzip, deflate, br",
                cache_control_preferences=["max-age=0"],
                os="macOS",
                version="17.1"
            ),
            ProfilNavigateur(
                nom="Safari Mobile iOS",
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                accept_language=["fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3", "en-us"],
                accept_encoding="gzip, deflate, br",
                sec_ch_ua_mobile="?1",
                os="iOS",
                version="17.1"
            )
        ]

        # Profils Edge
        profils_edge = [
            ProfilNavigateur(
                nom="Edge 120 Windows",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                accept="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                accept_language=["fr-FR,fr;q=0.9,en;q=0.8", "en-US,en;q=0.9"],
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"Windows"',
                os="Windows 10",
                version="120.0.0.0"
            )
        ]

        # Combiner tous les profils
        self.profils_navigateurs = profils_chrome + profils_firefox + profils_safari + profils_edge

        # Mélanger pour la randomisation
        random.shuffle(self.profils_navigateurs)

        print(f"✅ {len(self.profils_navigateurs)} profils de navigateurs chargés")

    def obtenir_profil_actuel(self) -> ProfilNavigateur:
        """
        Obtenir le profil de navigateur actuellement sélectionné

        Retourne le profil actuel avec rotation automatique selon
        l'intervalle configuré. Thread-safe.

        Returns:
            ProfilNavigateur: Profil actuel avec rotation si nécessaire
        """
        with self.lock:
            # Vérifier s'il faut effectuer une rotation
            if datetime.now() - self.derniere_rotation > self.intervalle_rotation:
                self.effectuer_rotation_profil()

            return self.profils_navigateurs[self.profil_actuel_index]

    def effectuer_rotation_profil(self) -> None:
        """
        Effectuer une rotation vers le profil suivant

        Change le profil de navigateur actuel et met à jour les statistiques.
        Cette méthode doit être appelée avec le verrou lock acquis.
        """
        ancien_profil = self.profils_navigateurs[self.profil_actuel_index]
        self.profil_actuel_index = (self.profil_actuel_index + 1) % len(self.profils_navigateurs)
        nouveau_profil = self.profils_navigateurs[self.profil_actuel_index]

        self.derniere_rotation = datetime.now()
        self.stats['rotations_effectuees'] += 1

        # Mettre à jour les statistiques de navigateurs utilisés
        if nouveau_profil.nom not in self.stats['navigateurs_utilises']:
            self.stats['navigateurs_utilises'][nouveau_profil.nom] = 0
        self.stats['navigateurs_utilises'][nouveau_profil.nom] += 1

        print(f"🔄 Rotation profil: {ancien_profil.nom} → {nouveau_profil.nom}")

    def generer_headers_complets(self,
                               url_cible: str,
                               referer: Optional[str] = None,
                               profil: Optional[ProfilNavigateur] = None,
                               personnalisation: Optional[Dict] = None) -> Dict[str, str]:
        """
        Générer un ensemble complet de headers HTTP authentiques

        Crée des headers cohérents et réalistes basés sur le profil
        de navigateur sélectionné, avec personnalisations possibles.

        Args:
            url_cible (str): URL de destination de la requête
            referer (Optional[str]): URL de référence (page précédente)
            profil (Optional[ProfilNavigateur]): Profil à utiliser (actuel si None)
            personnalisation (Optional[Dict]): Headers personnalisés à ajouter

        Returns:
            Dict[str, str]: Headers HTTP complets et cohérents
        """
        if profil is None:
            profil = self.obtenir_profil_actuel()

        # Headers de base du profil
        headers = {
            'User-Agent': profil.user_agent,
            'Accept': profil.accept,
            'Accept-Language': random.choice(profil.accept_language),
            'Accept-Encoding': profil.accept_encoding,
            'Connection': profil.connection,
            'Upgrade-Insecure-Requests': '1' if profil.upgrade_insecure else '0'
        }

        # Ajouter les headers Client Hints si supportés (Chrome/Edge)
        if profil.sec_ch_ua:
            headers['Sec-Ch-Ua'] = profil.sec_ch_ua
            headers['Sec-Ch-Ua-Mobile'] = profil.sec_ch_ua_mobile
            headers['Sec-Ch-Ua-Platform'] = profil.sec_ch_ua_platform

        # Gestion du DNT (Do Not Track)
        if profil.dnt_support and random.choice([True, False]):  # 50% chance
            headers['DNT'] = random.choice(['1', '0'])

        # Ajouter le referer si fourni
        if referer:
            headers['Referer'] = referer

        # Headers Sec-Fetch pour navigateurs modernes
        if 'Chrome' in profil.nom or 'Edge' in profil.nom or 'Firefox' in profil.nom:
            headers['Sec-Fetch-Site'] = self._determiner_sec_fetch_site(url_cible, referer)
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Sec-Fetch-User'] = '?1'
            headers['Sec-Fetch-Dest'] = 'document'

        # Cache Control selon les préférences du navigateur
        if profil.cache_control_preferences:
            cache_control = random.choice(profil.cache_control_preferences)
            headers['Cache-Control'] = cache_control

        # Ajouter des headers de priorité (Chrome)
        if 'Chrome' in profil.nom:
            headers['Sec-Ch-Ua-Arch'] = '"x86"'
            headers['Sec-Ch-Ua-Bitness'] = '"64"'

        # Headers de timing et performance
        if random.choice([True, False, False]):  # 33% chance
            headers['Viewport-Width'] = str(random.choice([1920, 1366, 1536, 1440, 1280]))

        # Personnalisations supplémentaires
        if personnalisation:
            headers.update(personnalisation)

        # Enregistrer dans l'historique et mettre à jour les stats
        with self.lock:
            self.stats['total_headers_generes'] += 1

            # Vérifier l'unicité (basé sur le hash des headers)
            headers_hash = hashlib.md5(json.dumps(headers, sort_keys=True).encode()).hexdigest()
            if not any(h['hash'] == headers_hash for h in self.historique_headers[-100:]):
                self.stats['headers_uniques_generes'] += 1

            # Ajouter à l'historique
            self.historique_headers.append({
                'timestamp': datetime.now(),
                'profil': profil.nom,
                'url_cible': url_cible,
                'headers': headers.copy(),
                'hash': headers_hash
            })

            # Limiter la taille de l'historique
            if len(self.historique_headers) > 1000:
                self.historique_headers = self.historique_headers[-500:]

        return headers

    def _determiner_sec_fetch_site(self, url_cible: str, referer: Optional[str]) -> str:
        """
        Déterminer la valeur appropriée pour Sec-Fetch-Site

        Analyse la relation entre l'URL cible et le referer pour
        déterminer la valeur correcte du header Sec-Fetch-Site.

        Args:
            url_cible (str): URL de destination
            referer (Optional[str]): URL de référence

        Returns:
            str: Valeur pour Sec-Fetch-Site
        """
        if not referer:
            return 'none'

        try:
            from urllib.parse import urlparse

            domaine_cible = urlparse(url_cible).netloc
            domaine_referer = urlparse(referer).netloc

            if domaine_cible == domaine_referer:
                return 'same-origin'
            elif domaine_cible.split('.')[-2:] == domaine_referer.split('.')[-2:]:
                return 'same-site'
            else:
                return 'cross-site'
        except:
            return 'cross-site'

    def creer_session_coherente(self, nb_requetes: int = 5) -> List[Dict[str, str]]:
        """
        Créer une série de headers cohérents pour une session

        Génère plusieurs sets de headers qui maintiennent une cohérence
        de session, simulant un utilisateur naviguant sur plusieurs pages.

        Args:
            nb_requetes (int): Nombre de sets de headers à générer

        Returns:
            List[Dict[str, str]]: Liste des headers pour chaque requête
        """
        profil_session = self.obtenir_profil_actuel()
        headers_session = []

        referer_actuel = None

        for i in range(nb_requetes):
            # URL simulée pour la requête
            url_simulee = f"https://www.amazon.fr/page{i+1}"

            headers = self.generer_headers_complets(
                url_cible=url_simulee,
                referer=referer_actuel,
                profil=profil_session  # Utiliser le même profil pour toute la session
            )

            headers_session.append(headers)
            referer_actuel = url_simulee  # Mettre à jour le referer pour la prochaine requête

        print(f"🎭 Session cohérente créée: {nb_requetes} requêtes avec {profil_session.nom}")
        return headers_session

    def obtenir_statistiques(self) -> Dict:
        """
        Obtenir les statistiques d'utilisation du rotateur

        Returns:
            Dict: Statistiques complètes sur l'utilisation des profils
        """
        with self.lock:
            stats_completes = dict(self.stats)
            stats_completes['profil_actuel'] = self.profils_navigateurs[self.profil_actuel_index].nom
            stats_completes['total_profils_disponibles'] = len(self.profils_navigateurs)

            if self.historique_headers:
                stats_completes['derniere_generation'] = self.historique_headers[-1]['timestamp'].isoformat()

            # Calcul du taux d'unicité
            if stats_completes['total_headers_generes'] > 0:
                stats_completes['taux_unicite'] = (
                    stats_completes['headers_uniques_generes'] /
                    stats_completes['total_headers_generes']
                ) * 100

            return stats_completes

    def forcer_changement_profil(self, nom_profil: Optional[str] = None) -> ProfilNavigateur:
        """
        Forcer un changement de profil immédiat

        Args:
            nom_profil (Optional[str]): Nom du profil à utiliser (aléatoire si None)

        Returns:
            ProfilNavigateur: Nouveau profil sélectionné
        """
        with self.lock:
            if nom_profil:
                # Rechercher le profil par nom
                for i, profil in enumerate(self.profils_navigateurs):
                    if profil.nom == nom_profil:
                        self.profil_actuel_index = i
                        break
            else:
                # Sélection aléatoire
                self.profil_actuel_index = random.randint(0, len(self.profils_navigateurs) - 1)

            self.derniere_rotation = datetime.now()
            self.stats['rotations_effectuees'] += 1

            nouveau_profil = self.profils_navigateurs[self.profil_actuel_index]
            print(f"🔄 Changement forcé vers: {nouveau_profil.nom}")

            return nouveau_profil


def creer_rotateur_headers() -> RotateurHeaders:
    """
    Créer et initialiser un rotateur de headers

    Returns:
        RotateurHeaders: Instance configurée du rotateur
    """
    return RotateurHeaders()


def generer_headers_pour_requete(rotateur: RotateurHeaders,
                                url: str,
                                referer: Optional[str] = None) -> Dict[str, str]:
    """
    Fonction utilitaire pour générer des headers pour une requête

    Args:
        rotateur (RotateurHeaders): Instance du rotateur à utiliser
        url (str): URL de destination
        referer (Optional[str]): URL de référence

    Returns:
        Dict[str, str]: Headers générés pour la requête
    """
    return rotateur.generer_headers_complets(url, referer)


if __name__ == "__main__":
    # Test du rotateur de headers
    print("🧪 Test du rotateur de headers")

    rotateur = creer_rotateur_headers()

    # Test de génération de headers
    url_test = "https://www.amazon.fr/s?k=livres"
    referer_test = "https://www.amazon.fr"

    print(f"\n📋 Headers générés pour {url_test}:")
    headers = generer_headers_pour_requete(rotateur, url_test, referer_test)

    for nom, valeur in headers.items():
        print(f"  {nom}: {valeur}")

    # Test de session cohérente
    print(f"\n🎭 Test de session cohérente:")
    session_headers = rotateur.creer_session_coherente(3)

    for i, headers in enumerate(session_headers):
        print(f"  Requête {i+1}: User-Agent = {headers['User-Agent'][:50]}...")

    # Statistiques
    print(f"\n📊 Statistiques:")
    stats = rotateur.obtenir_statistiques()
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value}")
        elif isinstance(value, dict) and len(value) < 5:
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: {type(value).__name__}")