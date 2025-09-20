#!/usr/bin/env python3
"""
MODULE DE GESTION DES DÉLAIS ANTI-DÉTECTION
===========================================
Fonctions pour gérer les délais intelligents entre les requêtes
Simule un comportement humain naturel pour éviter la détection
"""

import time
import random
import threading
from typing import Optional, Dict, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import math

class TypeDelai(Enum):
    """
    Types de délais pour différents scénarios de scraping

    Définit les différents modes de temporisation selon l'intensité
    souhaitée et le niveau de furtivité requis.
    """
    RAPIDE = "rapide"           # Délais courts, risque plus élevé
    NORMAL = "normal"           # Délais modérés, équilibré
    PRUDENT = "prudent"         # Délais longs, maximum de furtivité
    ADAPTATIF = "adaptatif"     # Délais qui s'adaptent aux réponses

@dataclass
class ConfigurationDelai:
    """
    Configuration des paramètres de délai

    Définit les bornes et paramètres pour calculer les délais
    selon différents critères et situations.
    """
    delai_min: float            # Délai minimum en secondes
    delai_max: float            # Délai maximum en secondes
    variation: float            # Facteur de variation aléatoire (0-1)
    progression: float          # Facteur d'augmentation progressive
    delai_erreur: float         # Délai supplémentaire après erreur
    seuil_acceleration: int     # Nb succès avant accélération
    seuil_ralentissement: int   # Nb erreurs avant ralentissement

class GestionnaireDelais:
    """
    Gestionnaire intelligent des délais anti-détection

    Cette classe calcule des délais réalistes entre les requêtes
    en simulant un comportement humain naturel avec variations,
    pauses, et adaptation selon les réponses du serveur.

    Attributs:
        configuration (ConfigurationDelai): Configuration actuelle
        historique_requetes (List[Dict]): Historique des requêtes récentes
        stats (Dict): Statistiques de performance
        lock (threading.Lock): Verrou pour thread safety
    """

    def __init__(self, type_delai: TypeDelai = TypeDelai.NORMAL):
        """
        Initialiser le gestionnaire de délais

        Args:
            type_delai (TypeDelai): Type de délai à utiliser par défaut
        """
        self.type_delai_actuel = type_delai
        self.configuration = self._obtenir_configuration(type_delai)
        self.historique_requetes = []
        self.derniere_requete = None
        self.facteur_adaptation = 1.0  # Facteur multiplicateur adaptatif
        self.lock = threading.Lock()

        # Statistiques et métriques
        self.stats = {
            'total_delais': 0,
            'temps_total_attente': 0.0,
            'delai_moyen': 0.0,
            'succès_consecutifs': 0,
            'erreurs_consecutives': 0,
            'adaptations_effectuees': 0,
            'type_delai_actuel': type_delai.value
        }

        print(f"🕐 Gestionnaire de délais initialisé: mode {type_delai.value}")

    def _obtenir_configuration(self, type_delai: TypeDelai) -> ConfigurationDelai:
        """
        Obtenir la configuration pour un type de délai donné

        Args:
            type_delai (TypeDelai): Type de délai souhaité

        Returns:
            ConfigurationDelai: Configuration correspondante
        """
        configurations = {
            TypeDelai.RAPIDE: ConfigurationDelai(
                delai_min=0.5,
                delai_max=2.0,
                variation=0.3,
                progression=1.05,
                delai_erreur=3.0,
                seuil_acceleration=10,
                seuil_ralentissement=3
            ),
            TypeDelai.NORMAL: ConfigurationDelai(
                delai_min=1.0,
                delai_max=5.0,
                variation=0.5,
                progression=1.1,
                delai_erreur=5.0,
                seuil_acceleration=8,
                seuil_ralentissement=2
            ),
            TypeDelai.PRUDENT: ConfigurationDelai(
                delai_min=2.0,
                delai_max=10.0,
                variation=0.7,
                progression=1.2,
                delai_erreur=8.0,
                seuil_acceleration=15,
                seuil_ralentissement=1
            ),
            TypeDelai.ADAPTATIF: ConfigurationDelai(
                delai_min=0.8,
                delai_max=8.0,
                variation=0.6,
                progression=1.15,
                delai_erreur=6.0,
                seuil_acceleration=5,
                seuil_ralentissement=2
            )
        }
        return configurations[type_delai]

    def calculer_delai(self,
                      succes_requete: Optional[bool] = None,
                      temps_reponse: Optional[float] = None,
                      code_status: Optional[int] = None) -> float:
        """
        Calculer le délai optimal avant la prochaine requête

        Utilise plusieurs facteurs pour déterminer un délai réaliste:
        - Réussite/échec de la requête précédente
        - Temps de réponse du serveur
        - Code de status HTTP
        - Historique récent des performances
        - Facteurs de variation aléatoire

        Args:
            succes_requete (Optional[bool]): True si la requête a réussi
            temps_reponse (Optional[float]): Temps de réponse en secondes
            code_status (Optional[int]): Code de status HTTP reçu

        Returns:
            float: Délai calculé en secondes
        """
        with self.lock:
            config = self.configuration
            delai_base = random.uniform(config.delai_min, config.delai_max)

            # Appliquer la variation aléatoire (simulation comportement humain)
            variation = random.uniform(-config.variation, config.variation)
            delai_base *= (1 + variation)

            # Adapter selon le succès/échec de la requête
            if succes_requete is not None:
                if succes_requete:
                    self.stats['succès_consecutifs'] += 1
                    self.stats['erreurs_consecutives'] = 0

                    # Accélération progressive après succès répétés
                    if self.stats['succès_consecutifs'] >= config.seuil_acceleration:
                        self.facteur_adaptation *= 0.95  # Réduction du délai
                        self.stats['adaptations_effectuees'] += 1

                else:
                    self.stats['erreurs_consecutives'] += 1
                    self.stats['succès_consecutifs'] = 0

                    # Ralentissement après erreurs
                    delai_base += config.delai_erreur
                    if self.stats['erreurs_consecutives'] >= config.seuil_ralentissement:
                        self.facteur_adaptation *= config.progression
                        self.stats['adaptations_effectuees'] += 1

            # Adapter selon le temps de réponse du serveur
            if temps_reponse is not None:
                if temps_reponse > 5.0:  # Serveur lent
                    delai_base *= 1.3  # Attendre plus longtemps
                elif temps_reponse < 1.0:  # Serveur rapide
                    delai_base *= 0.8  # Peut aller un peu plus vite

            # Adapter selon le code de status
            if code_status is not None:
                if code_status == 429:  # Too Many Requests
                    delai_base *= 3.0  # Attendre beaucoup plus longtemps
                elif code_status in [502, 503, 504]:  # Erreurs serveur
                    delai_base *= 2.0  # Attendre plus longtemps
                elif code_status in [403, 401]:  # Erreurs d'accès
                    delai_base *= 1.5  # Attendre un peu plus

            # Appliquer le facteur d'adaptation
            delai_final = delai_base * self.facteur_adaptation

            # Borner le délai final
            delai_final = max(config.delai_min * 0.5, min(delai_final, config.delai_max * 2))

            # Mettre à jour les statistiques
            self.stats['total_delais'] += 1
            self.stats['temps_total_attente'] += delai_final
            self.stats['delai_moyen'] = self.stats['temps_total_attente'] / self.stats['total_delais']

            return delai_final

    def attendre(self,
                succes_requete: Optional[bool] = None,
                temps_reponse: Optional[float] = None,
                code_status: Optional[int] = None,
                afficher_progress: bool = True) -> float:
        """
        Effectuer une pause calculée avant la prochaine requête

        Calcule et exécute le délai approprié, avec affichage optionnel
        du progrès pour informer l'utilisateur.

        Args:
            succes_requete (Optional[bool]): Résultat de la requête précédente
            temps_reponse (Optional[float]): Temps de réponse du serveur
            code_status (Optional[int]): Code HTTP reçu
            afficher_progress (bool): Afficher le progrès de l'attente

        Returns:
            float: Durée réelle de l'attente
        """
        delai = self.calculer_delai(succes_requete, temps_reponse, code_status)

        if afficher_progress and delai > 1.0:
            print(f"⏳ Attente anti-détection: {delai:.1f}s", end="")

            # Affichage progressif pour les longs délais
            if delai > 3.0:
                segments = min(int(delai), 20)  # Max 20 segments
                temps_segment = delai / segments

                for i in range(segments):
                    time.sleep(temps_segment)
                    if i % 3 == 0:  # Afficher des points tous les 3 segments
                        print(".", end="", flush=True)
                print(" ✓")
            else:
                time.sleep(delai)
                print(" ✓")
        else:
            time.sleep(delai)

        # Enregistrer la requête dans l'historique
        self.derniere_requete = {
            'timestamp': datetime.now(),
            'delai': delai,
            'succes': succes_requete,
            'temps_reponse': temps_reponse,
            'code_status': code_status
        }

        return delai

    def simuler_pause_lecture(self, duree_lecture: Optional[float] = None) -> None:
        """
        Simuler une pause de lecture humaine

        Simule le temps qu'un humain prendrait pour lire une page
        avant de naviguer vers la suivante.

        Args:
            duree_lecture (Optional[float]): Durée de lecture spécifique
        """
        if duree_lecture is None:
            # Durée de lecture aléatoire réaliste (2-15 secondes)
            duree_lecture = random.uniform(2.0, 15.0)
            # Distribution plus réaliste avec biais vers les durées courtes
            duree_lecture = duree_lecture * random.uniform(0.3, 1.0)

        print(f"📖 Pause de lecture simulée: {duree_lecture:.1f}s")
        time.sleep(duree_lecture)

    def simuler_navigation_humaine(self) -> None:
        """
        Simuler un pattern de navigation humaine complexe

        Introduit des pauses variées qui simulent différentes actions
        d'un utilisateur réel: scroll, clic, réflexion, etc.
        """
        actions = [
            ("scroll", random.uniform(0.3, 1.2)),
            ("reflexion", random.uniform(0.5, 2.0)),
            ("lecture_rapide", random.uniform(1.0, 3.0)),
            ("clic", random.uniform(0.1, 0.5))
        ]

        # Sélectionner 1-3 actions aléatoires
        nb_actions = random.randint(1, 3)
        actions_selectionnees = random.sample(actions, nb_actions)

        for action, duree in actions_selectionnees:
            print(f"🎭 Action humaine simulée: {action} ({duree:.1f}s)")
            time.sleep(duree)

    def changer_type_delai(self, nouveau_type: TypeDelai) -> None:
        """
        Changer le type de délai utilisé

        Permet de modifier dynamiquement la stratégie de délai,
        utile pour s'adapter à différents sites ou situations.

        Args:
            nouveau_type (TypeDelai): Nouveau type de délai à utiliser
        """
        with self.lock:
            ancien_type = self.type_delai_actuel
            self.type_delai_actuel = nouveau_type
            self.configuration = self._obtenir_configuration(nouveau_type)
            self.stats['type_delai_actuel'] = nouveau_type.value

            print(f"🔄 Type de délai changé: {ancien_type.value} → {nouveau_type.value}")

    def obtenir_statistiques(self) -> Dict:
        """
        Obtenir les statistiques d'utilisation des délais

        Returns:
            Dict: Statistiques complètes sur les délais et performances
        """
        with self.lock:
            stats_completes = dict(self.stats)

            if self.historique_requetes:
                delais_recents = [req['delai'] for req in self.historique_requetes[-10:]]
                stats_completes['delai_median_recent'] = sorted(delais_recents)[len(delais_recents)//2]

            stats_completes['facteur_adaptation_actuel'] = self.facteur_adaptation
            stats_completes['configuration_actuelle'] = {
                'delai_min': self.configuration.delai_min,
                'delai_max': self.configuration.delai_max,
                'variation': self.configuration.variation
            }

            return stats_completes

    def reinitialiser_adaptation(self) -> None:
        """
        Réinitialiser le facteur d'adaptation

        Remet à zéro les compteurs adaptatifs, utile lors du changement
        de site ou de session de scraping.
        """
        with self.lock:
            self.facteur_adaptation = 1.0
            self.stats['succès_consecutifs'] = 0
            self.stats['erreurs_consecutives'] = 0
            self.stats['adaptations_effectuees'] = 0

        print("🔄 Facteur d'adaptation réinitialisé")


def creer_gestionnaire_delais(type_delai: TypeDelai = TypeDelai.NORMAL) -> GestionnaireDelais:
    """
    Créer et initialiser un gestionnaire de délais

    Args:
        type_delai (TypeDelai): Type de délai à utiliser

    Returns:
        GestionnaireDelais: Instance configurée du gestionnaire
    """
    return GestionnaireDelais(type_delai)


def attendre_intelligemment(gestionnaire: GestionnaireDelais,
                          succes: bool = True,
                          temps_reponse: Optional[float] = None,
                          code_status: Optional[int] = None) -> float:
    """
    Fonction utilitaire pour attendre intelligemment

    Args:
        gestionnaire (GestionnaireDelais): Gestionnaire à utiliser
        succes (bool): Succès de la requête précédente
        temps_reponse (Optional[float]): Temps de réponse du serveur
        code_status (Optional[int]): Code de status HTTP

    Returns:
        float: Durée de l'attente effectuée
    """
    return gestionnaire.attendre(succes, temps_reponse, code_status)


if __name__ == "__main__":
    # Test du gestionnaire de délais
    print("🧪 Test du gestionnaire de délais")

    # Test mode normal
    gestionnaire = creer_gestionnaire_delais(TypeDelai.NORMAL)

    print("\n📊 Test de plusieurs requêtes simulées...")
    for i in range(5):
        succes = random.choice([True, True, True, False])  # 75% succès
        temps_reponse = random.uniform(0.5, 3.0)
        code = random.choice([200, 200, 200, 429, 503])

        print(f"\nRequête {i+1}: succès={succes}, temps={temps_reponse:.2f}s, code={code}")
        duree = attendre_intelligemment(gestionnaire, succes, temps_reponse, code)
        print(f"Délai appliqué: {duree:.2f}s")

    # Afficher les statistiques
    stats = gestionnaire.obtenir_statistiques()
    print(f"\n📈 Statistiques finales:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")