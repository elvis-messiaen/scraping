#!/usr/bin/env python3
"""
Fonctions utilitaires pour la gestion des fichiers et dossiers
"""

import os
import json
from datetime import datetime
import pandas as pd

def setup_dossiers(nom_fichier: str):
    """Crée les dossiers nécessaires"""
    print(f"🔧 DÉMARRAGE SETUP DOSSIERS POUR: {nom_fichier}")
    print(f"📁 Création de l'arborescence...")
    # Dossier principal de la catégorie
    dossier_livres = os.path.join('..', 'LIVRES', nom_fichier)
    os.makedirs(dossier_livres, exist_ok=True)
    
    # Fichiers de sauvegarde
    fichier_json = os.path.join(dossier_livres, f"{nom_fichier}_livres.json")
    fichier_csv = os.path.join(dossier_livres, f"{nom_fichier}_livres.csv")
    fichier_progres = os.path.join(dossier_livres, f"{nom_fichier}_progres.json")
    
    print(f"✅ DOSSIERS CRÉÉS AVEC SUCCÈS:")
    print(f"   📁 Dossier principal: {dossier_livres}")
    print(f"   📄 Fichier JSON: {os.path.basename(fichier_json)}")
    print(f"   📊 Fichier CSV: {os.path.basename(fichier_csv)}")
    print(f"   🔄 Fichier progression: {os.path.basename(fichier_progres)}")
    
    return dossier_livres, fichier_json, fichier_csv, fichier_progres

def charger_donnees_existantes(fichier_json: str):
    """Charge les données existantes depuis les fichiers JSON"""
    print(f"📚 CHARGEMENT DES DONNÉES EXISTANTES...")
    livres_scraped = []
    urls_traitees = set()
    stock_existant = 0
    
    print(f"🔍 DEBUG: Vérification fichier JSON: {fichier_json}")
    print(f"🔍 DEBUG: Fichier existe? {os.path.exists(fichier_json)}")
    
    try:
        if os.path.exists(fichier_json):
            print(f"📄 Chargement depuis: {fichier_json}")
            with open(fichier_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    livres_scraped = data
                    stock_existant = len(livres_scraped)
                    urls_traitees = {livre.get('url', '') for livre in data if livre.get('url')}
                elif isinstance(data, dict) and 'livres' in data:
                    livres_scraped = data['livres']
                    stock_existant = len(livres_scraped)
                    urls_traitees = {livre.get('url', '') for livre in data['livres'] if livre.get('url')}
            print(f"🎉 CHARGEMENT RÉUSSI: {stock_existant:,} livres depuis {fichier_json}")
            print(f"🔗 {len(urls_traitees):,} URLs uniques chargées")
        else:
            print(f"📄 Aucun fichier JSON à {fichier_json} - démarrage à zéro")
    except Exception as e:
        print(f"⚠️ Erreur chargement données: {e} - démarrage à zéro")
        livres_scraped = []
        urls_traitees = set()
        
    print(f"📊 Stock existant: {stock_existant:,} livres")
    return livres_scraped, urls_traitees, stock_existant

def charger_progression_existante(fichier_progres: str):
    """Charge la progression depuis le fichier de progression"""
    try:
        if os.path.exists(fichier_progres):
            with open(fichier_progres, 'r', encoding='utf-8') as f:
                progression = json.load(f)
                derniere_page_traitee = progression.get('page_actuelle', 0)
                print(f"🔄 Reprise depuis la page {derniere_page_traitee}")
                return derniere_page_traitee
    except Exception as e:
        print(f"⚠️ Erreur chargement progression: {e}")
    
    return 1

def sauvegarder_progres_complet(livres_scraped: list, fichier_json: str, fichier_csv: str, 
                               fichier_progres: str, page_actuelle: int, total_amazon: int, 
                               pages_vides_consecutives: int, urls_traitees: set):
    """Sauvegarde complète: JSON + CSV + progression"""
    try:
        # Sauvegarde JSON
        with open(fichier_json, 'w', encoding='utf-8') as f:
            json.dump(livres_scraped, f, ensure_ascii=False, indent=2)
        
        # Sauvegarde CSV si on a des livres
        if livres_scraped:
            df = pd.DataFrame(livres_scraped)
            df.to_csv(fichier_csv, index=False, encoding='utf-8')
        
        # Sauvegarde progression
        progression = {
            'page_actuelle': page_actuelle,
            'total_livres_scrapes': len(livres_scraped),
            'total_amazon_estime': total_amazon,
            'derniere_sauvegarde': datetime.now().isoformat(),
            'pages_vides_consecutives': pages_vides_consecutives,
            'urls_traitees_count': len(urls_traitees)
        }
        
        with open(fichier_progres, 'w', encoding='utf-8') as f:
            json.dump(progression, f, ensure_ascii=False, indent=2)
            
        print(f"💾 SAUVEGARDE TERMINÉE: {len(livres_scraped):,} livres, page {page_actuelle}")
        print(f"📄 JSON sauvegardé: {os.path.basename(fichier_json)}")
        print(f"📊 CSV sauvegardé: {os.path.basename(fichier_csv)}")
        print(f"🔄 Progression sauvegardée: page {page_actuelle}, {pages_vides_consecutives} pages vides")
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")