#!/usr/bin/env python3
"""
MÉTRIQUES TEMPS RÉEL POUR SCRAPING
=================================
Affichage des métriques en temps réel :
- Temps écoulé / estimé / restant
- Nombre scrappé / total estimé
- Vitesse de scraping
- Liens Amazon en cours
- Pourcentage de progression
"""

import time
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class MetriquesTempsReel:
    """
    Gestionnaire de métriques temps réel pour le scraping
    """

    def __init__(self):
        """
        Initialisation des métriques
        """
        # Temps
        self.debut_scraping = None
        self.dernier_update = None

        # Compteurs
        self.total_estime = 0
        self.nombre_scrappe = 0
        self.erreurs = 0
        self.categories_traitees = 0

        # Performance
        self.vitesse_scraping = 0.0  # items/seconde
        self.temps_moyen_par_item = 0.0  # secondes/item

        # Liens en cours
        self.lien_amazon_actuel = ""
        self.categorie_actuelle = ""

        # Historique pour calcul vitesse
        self.historique_timings = []
        self.max_historique = 10

    def demarrer(self, total_estime: int = 0):
        """
        Démarrer le suivi des métriques

        Args:
            total_estime (int): Nombre total estimé d'éléments à scraper
        """
        self.debut_scraping = datetime.now()
        self.dernier_update = self.debut_scraping
        self.total_estime = total_estime
        self.nombre_scrappe = 0
        self.erreurs = 0
        self.categories_traitees = 0

        print("🚀 DÉBUT SCRAPING - MÉTRIQUES TEMPS RÉEL")
        print("=" * 80)
        self._afficher_entete()

    def _afficher_entete(self):
        """
        Afficher l'en-tête des métriques
        """
        print(f"{'TEMPS':<12} {'PROG':<8} {'SCRAPPÉ':<10} {'VITESSE':<12} {'RESTANT':<12} {'LIEN AMAZON'}")
        print("-" * 80)

    def update_item(self, categorie: str, lien_amazon: str, success: bool = True):
        """
        Mettre à jour les métriques pour un item scrappé

        Args:
            categorie (str): Nom de la catégorie en cours
            lien_amazon (str): Lien Amazon actuel
            success (bool): True si succès, False si erreur
        """
        maintenant = datetime.now()

        # Mise à jour compteurs
        if success:
            self.nombre_scrappe += 1
        else:
            self.erreurs += 1

        self.categorie_actuelle = categorie
        self.lien_amazon_actuel = lien_amazon

        # Calcul vitesse
        if self.dernier_update:
            duree_item = (maintenant - self.dernier_update).total_seconds()
            self.historique_timings.append(duree_item)

            # Garder seulement les N derniers timings
            if len(self.historique_timings) > self.max_historique:
                self.historique_timings.pop(0)

            # Calcul temps moyen et vitesse
            if self.historique_timings:
                self.temps_moyen_par_item = sum(self.historique_timings) / len(self.historique_timings)
                self.vitesse_scraping = 1.0 / self.temps_moyen_par_item if self.temps_moyen_par_item > 0 else 0

        self.dernier_update = maintenant
        self._afficher_metrics()

    def update_categorie(self, categorie: str):
        """
        Mettre à jour la catégorie en cours de traitement

        Args:
            categorie (str): Nom de la nouvelle catégorie
        """
        self.categories_traitees += 1
        self.categorie_actuelle = categorie

        print(f"\n🎯 [{self.categories_traitees}] NOUVELLE CATÉGORIE: {categorie}")
        print("-" * 80)

    def _afficher_metrics(self):
        """
        Afficher les métriques en temps réel sur une ligne
        """
        if not self.debut_scraping:
            return

        maintenant = datetime.now()

        # Temps écoulé
        temps_ecoule = maintenant - self.debut_scraping
        temps_str = self._formater_duree(temps_ecoule)

        # Pourcentage progression
        if self.total_estime > 0:
            pourcentage = (self.nombre_scrappe / self.total_estime) * 100
            prog_str = f"{pourcentage:.1f}%"
        else:
            prog_str = "N/A"

        # Nombre scrappé
        if self.total_estime > 0:
            scrappe_str = f"{self.nombre_scrappe}/{self.total_estime}"
        else:
            scrappe_str = f"{self.nombre_scrappe}"

        # Vitesse
        if self.vitesse_scraping > 0:
            vitesse_str = f"{self.vitesse_scraping:.2f}/s"
        else:
            vitesse_str = "calc..."

        # Temps restant estimé
        if self.vitesse_scraping > 0 and self.total_estime > 0:
            items_restants = self.total_estime - self.nombre_scrappe
            secondes_restantes = items_restants / self.vitesse_scraping
            temps_restant = timedelta(seconds=int(secondes_restantes))
            restant_str = self._formater_duree(temps_restant)
        else:
            restant_str = "calc..."

        # Lien Amazon (tronqué pour affichage)
        lien_affiche = self._tronquer_lien(self.lien_amazon_actuel)

        # Affichage (écrase la ligne précédente)
        print(f"\r{temps_str:<12} {prog_str:<8} {scrappe_str:<10} {vitesse_str:<12} {restant_str:<12} {lien_affiche}",
              end="", flush=True)

    def _formater_duree(self, duree):
        """
        Formater une durée en format HH:MM:SS

        Args:
            duree: timedelta object

        Returns:
            str: Durée formatée
        """
        if isinstance(duree, timedelta):
            total_seconds = int(duree.total_seconds())
        else:
            total_seconds = int(duree)

        heures = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secondes = total_seconds % 60

        if heures > 0:
            return f"{heures:02d}:{minutes:02d}:{secondes:02d}"
        else:
            return f"{minutes:02d}:{secondes:02d}"

    def _tronquer_lien(self, lien: str, max_length: int = 35) -> str:
        """
        Tronquer un lien pour affichage

        Args:
            lien (str): Lien complet
            max_length (int): Longueur maximale

        Returns:
            str: Lien tronqué
        """
        if not lien:
            return "N/A"

        if len(lien) <= max_length:
            return lien

        # Garder le début et la fin
        debut = lien[:15]
        fin = lien[-15:]
        return f"{debut}...{fin}"

    def afficher_bilan_final(self):
        """
        Afficher le bilan final du scraping
        """
        if not self.debut_scraping:
            return

        print("\n")  # Nouvelle ligne après les métriques temps réel
        print("=" * 80)
        print("🏁 BILAN FINAL SCRAPING")
        print("=" * 80)

        maintenant = datetime.now()
        duree_totale = maintenant - self.debut_scraping

        print(f"⏱️  Durée totale      : {self._formater_duree(duree_totale)}")
        print(f"✅ Items scrappés   : {self.nombre_scrappe}")
        print(f"❌ Erreurs          : {self.erreurs}")
        print(f"📁 Catégories       : {self.categories_traitees}")

        if self.nombre_scrappe > 0:
            vitesse_moyenne = self.nombre_scrappe / duree_totale.total_seconds()
            print(f"🚀 Vitesse moyenne  : {vitesse_moyenne:.2f} items/seconde")
            print(f"⚡ Temps par item   : {duree_totale.total_seconds()/self.nombre_scrappe:.2f} sec/item")

        if self.total_estime > 0:
            pourcentage_final = (self.nombre_scrappe / self.total_estime) * 100
            print(f"📊 Progression      : {pourcentage_final:.1f}% ({self.nombre_scrappe}/{self.total_estime})")

        print("=" * 80)

    def afficher_erreur(self, message: str, lien_amazon: str = ""):
        """
        Afficher une erreur avec le lien Amazon

        Args:
            message (str): Message d'erreur
            lien_amazon (str): Lien Amazon en cause
        """
        print(f"\n❌ ERREUR: {message}")
        if lien_amazon:
            print(f"🔗 Lien: {lien_amazon}")
        print()

    def afficher_succes(self, message: str, lien_amazon: str = ""):
        """
        Afficher un succès avec le lien Amazon

        Args:
            message (str): Message de succès
            lien_amazon (str): Lien Amazon
        """
        print(f"\n✅ SUCCÈS: {message}")
        if lien_amazon:
            print(f"🔗 Lien: {lien_amazon}")
        print()

    def mettre_a_jour_total_estime(self, nouveau_total: int):
        """
        Mettre à jour le total estimé (utile quand on découvre plus d'éléments)

        Args:
            nouveau_total (int): Nouveau total estimé
        """
        self.total_estime = nouveau_total


# Classe utilitaire pour formater l'affichage
class AffichageTerminal:
    """
    Utilitaires pour l'affichage formaté dans le terminal
    """

    @staticmethod
    def effacer_ligne():
        """Effacer la ligne courante"""
        print("\r" + " " * 80 + "\r", end="", flush=True)

    @staticmethod
    def ligne_separatrice(char="=", length=80):
        """Afficher une ligne de séparation"""
        print(char * length)

    @staticmethod
    def titre_section(titre: str):
        """Afficher un titre de section formaté"""
        print(f"\n🔹 {titre.upper()}")
        print("-" * (len(titre) + 4))


if __name__ == "__main__":
    # Test des métriques
    import time

    print("🧪 TEST MÉTRIQUES TEMPS RÉEL")

    metriques = MetriquesTempsReel()
    metriques.demarrer(total_estime=50)

    # Simulation de scraping
    categories_test = ["Romans", "Sciences", "Histoire"]

    for i, categorie in enumerate(categories_test):
        metriques.update_categorie(categorie)

        for j in range(5):
            lien = f"https://amazon.fr/s?k={categorie.lower()}&page={j+1}"

            time.sleep(0.5)  # Simulation temps scraping
            success = j != 2  # Simulation erreur sur item 3

            metriques.update_item(f"{categorie} item {j+1}", lien, success)

        print()  # Nouvelle ligne après chaque catégorie

    metriques.afficher_bilan_final()