#!/usr/bin/env python3
"""
FONCTION DE MISE À JOUR DU FICHIER COMPLET.JSON
Centralise tous les livres des fichiers individuels vers complet.json
"""

import os
import json
import glob
from typing import List, Dict, Any
from datetime import datetime

def mettre_a_jour_complet_json(dossier_livres: str = None) -> bool:
    """
    Met à jour le fichier complet.json avec tous les livres des fichiers individuels
    
    Args:
        dossier_livres: Chemin vers le dossier LIVRES (optionnel)
    
    Returns:
        bool: True si succès, False sinon
    """
    
    if dossier_livres is None:
        # Détecter automatiquement le dossier LIVRES
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dossier_livres = os.path.join(os.path.dirname(script_dir), 'LIVRES')
    
    if not os.path.exists(dossier_livres):
        print(f"❌ Dossier LIVRES introuvable: {dossier_livres}")
        return False
    
    print("🔄 MISE À JOUR DU FICHIER COMPLET.JSON")
    print("=" * 50)
    
    try:
        # Récupérer tous les livres existants
        tous_livres = []
        urls_existantes = set()
        fichiers_traites = 0
        total_livres = 0
        
        # Parcourir tous les fichiers *_livres.json
        pattern = os.path.join(dossier_livres, '**', '*_livres.json')
        fichiers_json = glob.glob(pattern, recursive=True)
        
        print(f"🔍 Analyse de {len(fichiers_json)} fichiers JSON...")
        
        for fichier_json in fichiers_json:
            try:
                # Ignorer le fichier complet.json lui-même
                if 'complet.json' in fichier_json:
                    continue
                
                with open(fichier_json, 'r', encoding='utf-8') as f:
                    livres = json.load(f)
                
                if isinstance(livres, list) and livres:
                    livres_valides = 0
                    for livre in livres:
                        if isinstance(livre, dict):
                            url_livre = livre.get('url', '')
                            if url_livre and url_livre not in urls_existantes:
                                # Ajouter métadonnées de source
                                livre['source_fichier'] = os.path.basename(fichier_json)
                                livre['source_dossier'] = os.path.basename(os.path.dirname(fichier_json))
                                livre['derniere_maj'] = datetime.now().isoformat()
                                
                                tous_livres.append(livre)
                                urls_existantes.add(url_livre)
                                livres_valides += 1
                    
                    if livres_valides > 0:
                        print(f"   ✅ {os.path.basename(fichier_json)}: {livres_valides} livres")
                        total_livres += livres_valides
                        fichiers_traites += 1
                    
            except Exception as e:
                print(f"   ❌ {os.path.basename(fichier_json)}: {e}")
        
        print(f"\n📊 RÉSULTATS:")
        print(f"   📁 Fichiers traités: {fichiers_traites}")
        print(f"   📚 Total livres: {total_livres:,}")
        print(f"   🔗 URLs uniques: {len(urls_existantes):,}")
        
        # Créer/mettre à jour le fichier complet.json
        fichier_complet = os.path.join(dossier_livres, 'complet.json')
        
        # Ajouter métadonnées globales
        metadata = {
            "metadata": {
                "total_livres": len(tous_livres),
                "total_fichiers": fichiers_traites,
                "derniere_mise_a_jour": datetime.now().isoformat(),
                "version": "1.0"
            },
            "livres": tous_livres
        }
        
        with open(fichier_complet, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ MISE À JOUR TERMINÉE")
        print(f"💾 Fichier: {fichier_complet}")
        print(f"📚 {len(tous_livres):,} livres centralisés")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour: {e}")
        return False

def compter_livres_complet(dossier_livres: str = None) -> int:
    """
    Compte le nombre de livres dans complet.json
    
    Args:
        dossier_livres: Chemin vers le dossier LIVRES (optionnel)
    
    Returns:
        int: Nombre de livres ou 0 si erreur
    """
    
    if dossier_livres is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dossier_livres = os.path.join(os.path.dirname(script_dir), 'LIVRES')
    
    fichier_complet = os.path.join(dossier_livres, 'complet.json')
    
    try:
        if os.path.exists(fichier_complet):
            with open(fichier_complet, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, dict) and 'livres' in data:
                return len(data['livres'])
            elif isinstance(data, list):
                return len(data)
        
        return 0
        
    except Exception as e:
        print(f"❌ Erreur comptage: {e}")
        return 0

if __name__ == "__main__":
    # Test de la fonction
    succes = mettre_a_jour_complet_json()
    if succes:
        nb_livres = compter_livres_complet()
        print(f"🎉 Succès - {nb_livres:,} livres dans complet.json")
    else:
        print("❌ Échec de la mise à jour")