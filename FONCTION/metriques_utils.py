#!/usr/bin/env python3
"""
Fonctions utilitaires pour les métriques et le calcul de progression
"""

from datetime import datetime, timedelta
from typing import List

def calculer_metriques_completes(debut_scraping: datetime, historique_vitesse: List[float], 
                                livres_scraped: list, page_actuelle: int, total_amazon: int):
    """Calcule et affiche TOUTES les métriques demandées"""
    if not debut_scraping:
        debut_scraping = datetime.now()
        temps_derniere_metrique = debut_scraping
    
    maintenant = datetime.now()
    temps_ecoule = (maintenant - debut_scraping).total_seconds()
    livres_possedes = len(livres_scraped)
    
    # Vitesse actuelle (livres/seconde)
    if temps_ecoule > 0:
        vitesse_moyenne = livres_possedes / temps_ecoule
        historique_vitesse.append(vitesse_moyenne)
        
        # Garder seulement les 10 dernières mesures pour vitesse actuelle
        if len(historique_vitesse) > 10:
            historique_vitesse = historique_vitesse[-10:]
        
        vitesse_actuelle = sum(historique_vitesse) / len(historique_vitesse)
    else:
        vitesse_moyenne = 0
        vitesse_actuelle = 0
    
    # Calcul temps restant
    if total_amazon > livres_possedes and vitesse_actuelle > 0:
        livres_restants = total_amazon - livres_possedes
        secondes_restantes = livres_restants / vitesse_actuelle
        temps_restant = str(timedelta(seconds=int(secondes_restantes)))
    else:
        temps_restant = "Calcul en cours..."
    
    # Temps écoulé formaté  
    temps_ecoule_str = str(timedelta(seconds=int(temps_ecoule)))
    
    # Pourcentage de progression
    if total_amazon > 0:
        progression_pct = (livres_possedes / total_amazon) * 100
    else:
        progression_pct = 0
    
    # AFFICHAGE COMPLET DES MÉTRIQUES
    print(f"   📚 LIVRES AMAZON: {total_amazon:,} livres (estimation)")
    print(f"   📖 LIVRES POSSÉDÉS: {livres_possedes:,} livres")
    print(f"   📈 PROGRESSION: {progression_pct:.1f}% ({livres_possedes:,}/{total_amazon:,})")
    print(f"   ⏱️  TEMPS ÉCOULÉ: {temps_ecoule_str}")
    print(f"   ⏰ TEMPS RESTANT: {temps_restant}")
    print(f"   🚀 VITESSE: {vitesse_actuelle:.1f} livres/seconde ({vitesse_actuelle*60:.0f}/minute)")
    if livres_possedes > 0:
        print(f"   📊 MOYENNE: {vitesse_moyenne:.1f} livres/seconde depuis le début")
    print(f"")
    
    return historique_vitesse, vitesse_actuelle, vitesse_moyenne

def calculer_metriques(debut_scraping: datetime, livres_scraped: list, page_actuelle: int, 
                      total_amazon: int, calculer_metriques_completes_func):
    """Calcule et affiche les métriques de progression"""
    if not debut_scraping:
        return
        
    temps_ecoule = datetime.now() - debut_scraping
    livres_actuels = len(livres_scraped)
    
    if temps_ecoule.total_seconds() > 0 and page_actuelle > 1:
        # Vitesse de scraping
        pages_par_seconde = (page_actuelle - 1) / temps_ecoule.total_seconds()
        livres_par_seconde = livres_actuels / temps_ecoule.total_seconds()
        
        # Progression en pourcentage
        if total_amazon > 0:
            progression_pct = (livres_actuels / total_amazon) * 100
        else:
            progression_pct = 0
        
        # Temps restant estimé
        if pages_par_seconde > 0 and livres_actuels > 0:
            livres_restants = max(0, total_amazon - livres_actuels)
            if livres_par_seconde > 0:
                secondes_restantes = livres_restants / livres_par_seconde
                temps_restant = timedelta(seconds=int(secondes_restantes))
            else:
                temps_restant = "Calcul en cours..."
        else:
            temps_restant = "Calcul en cours..."
        
        calculer_metriques_completes_func(page_actuelle, total_amazon)
        print(f"   📚 Livres: {livres_actuels:,}/{total_amazon:,} ({progression_pct:.1f}%)")
        print(f"   ⏱️  Vitesse: {livres_par_seconde:.1f} livres/sec, {pages_par_seconde:.2f} pages/sec")
        print(f"   ⏳ Temps écoulé: {str(temps_ecoule).split('.')[0]}")
        print(f"   🎯 Temps restant estimé: {temps_restant}")