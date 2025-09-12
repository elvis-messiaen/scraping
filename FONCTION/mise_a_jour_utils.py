#!/usr/bin/env python3
"""
Fonctions utilitaires pour la mise à jour automatique des livres
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

def mise_a_jour_automatique_demarrage(livres_scraped: list, extraction_utils):
    """MISE À JOUR AUTOMATIQUE au démarrage de tous les livres existants"""
    if not livres_scraped:
        print("📚 Aucun livre existant à mettre à jour")
        return 0
    
    total_existants = len(livres_scraped)
    print(f"🔄 MISE À JOUR AUTOMATIQUE: {total_existants:,} livres existants")
    print(f"   ⚡ Mise à jour des informations (prix, stock, nouveaux détails)")
    
    # Initialiser les métriques de mise à jour
    debut_maj = datetime.now()
    livres_mis_a_jour = 0
    batch_size = 20
    
    for i in range(0, len(livres_scraped), batch_size):
        batch = livres_scraped[i:i + batch_size]
        batch_num = i//batch_size + 1
        total_batches = (len(livres_scraped) + batch_size - 1)//batch_size
        
        # Calcul et affichage des métriques en temps réel
        temps_ecoule = (datetime.now() - debut_maj).total_seconds()
        progression_pct = (livres_mis_a_jour / total_existants) * 100
        
        print(f"   🔄 Batch {batch_num}/{total_batches}")
        print(f"      📊 MÉTRIQUES MAJ: {livres_mis_a_jour:,}/{total_existants:,} livres ({progression_pct:.1f}%)")
        print(f"      ⏱️  Temps écoulé: {str(timedelta(seconds=int(temps_ecoule)))}")
        
        if livres_mis_a_jour > 0 and temps_ecoule > 0:
            vitesse_maj = livres_mis_a_jour / temps_ecoule
            livres_restants = total_existants - livres_mis_a_jour
            temps_restant = int(livres_restants / vitesse_maj) if vitesse_maj > 0 else 0
            temps_restant_str = str(timedelta(seconds=temps_restant))
            print(f"      ⏰ Temps restant: {temps_restant_str}")
            print(f"      🚀 Vitesse: {vitesse_maj:.1f} livres/sec ({vitesse_maj*60:.0f} livres/min)")
        else:
            print(f"      ⏰ Temps restant: Calcul en cours...")
            print(f"      🚀 Vitesse: Initialisation...")
        
        for j, livre in enumerate(batch):
            url = livre.get('url')
            if url:
                # Scraper à nouveau ce livre pour mise à jour
                try:
                    # Scraper à nouveau cette page pour ce livre
                    try:
                        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            elements = soup.find_all(['div', 'span'], attrs={'data-asin': True})
                            if elements:
                                # Utiliser la fonction d'extraction depuis extraction_utils
                                nouveau_livre = extraction_utils.extraire_infos_livre_url(url)
                            else:
                                nouveau_livre = None
                        else:
                            nouveau_livre = None
                    except:
                        nouveau_livre = None
                    if nouveau_livre:
                        # Conserver l'ancien timestamp et ajouter timestamp de MAJ
                        nouveau_livre['date_scraping_initial'] = livre.get('date_scraping', '')
                        nouveau_livre['date_derniere_maj'] = datetime.now().isoformat()
                        nouveau_livre['maj_automatique'] = True
                        
                        livres_scraped[i + j] = nouveau_livre
                        livres_mis_a_jour += 1
                        
                        if livres_mis_a_jour % 50 == 0:
                            print(f"      ✅ {livres_mis_a_jour} livres mis à jour...")
                            
                except Exception as e:
                    print(f"      ⚠️ Erreur MAJ {livre.get('titre', 'Livre')[:30]}: {e}")
        
        # Pause entre batches
        time.sleep(0.5)
    
    print(f"✅ MISE À JOUR TERMINÉE: {livres_mis_a_jour}/{total_existants} livres mis à jour")
    return livres_mis_a_jour