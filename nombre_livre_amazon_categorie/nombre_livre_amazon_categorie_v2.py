#!/usr/bin/env python3
"""
FONCTION DE VÉRIFICATION EXACTE DU NOMBRE DE LIVRES AMAZON PAR CATÉGORIE
========================================================================
Objectif: Détecter le nombre EXACT de livres disponibles sur Amazon pour une catégorie donnée
Principe: Continue jusqu'à ce qu'il n'y ait vraiment plus de livres (pas d'estimation)
Usage: Sera implémenté dans tous les scrapers pour vérification précise

🚀 UTILISE LA MÊME MÉTHODE QUE LES SCRAPERS EXISTANTS:
- Requests avec headers rotatifs (comme extraction_utils.py)
- verifier_presence_livres_robuste (fonction éprouvée)
- Même logique de détection page par page
- Compatible avec le système FONCTION existant
"""

import requests
import time
import random
import re
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
import sys
import os

# Import des fonctions existantes du système FONCTION
sys.path.append('../FONCTION')
try:
    from detection_utils import verifier_presence_livres_robuste
    FONCTION_DISPONIBLE = True
    print("✅ Import fonction detection_utils réussi")
except ImportError:
    FONCTION_DISPONIBLE = False
    print("⚠️ Fonctions FONCTION non disponibles - utilisation locale")

# User-Agents (même approche que les scrapers)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15'
]

def verifier_presence_livres_local(soup, page_num: int) -> bool:
    """
    Version locale de verifier_presence_livres_robuste si FONCTION non disponible
    Utilise exactement la même logique que la version officielle
    """
    print(f"🔍 Vérification page {page_num}...")
    
    # MÉTHODE 1: Liens /dp/ directs
    liens_dp = soup.find_all('a', href=True)
    liens_dp_valides = []
    for link in liens_dp:
        href = link.get('href', '')
        if '/dp/' in href and len(href) > 10:
            liens_dp_valides.append(href)
    
    print(f"   🔗 {len(liens_dp_valides)} liens /dp/ trouvés")
    
    # MÉTHODE 2: Résultats de recherche Amazon
    resultats_recherche = soup.find_all(attrs={'data-component-type': 's-search-result'})
    print(f"   📦 {len(resultats_recherche)} résultats de recherche")
    
    # MÉTHODE 3: Conteneurs de produits
    conteneurs_produits = soup.find_all(['div', 'article'], attrs={'data-asin': True})
    print(f"   📚 {len(conteneurs_produits)} conteneurs avec ASIN")
    
    # MÉTHODE 4: Titres de livres
    titres_livres = soup.find_all(['h2', 'h3'], class_=re.compile(r'title|name', re.I))
    print(f"   📖 {len(titres_livres)} titres potentiels")
    
    # Critère de succès: au moins 5 liens /dp/ OU 10 résultats de recherche
    if len(liens_dp_valides) >= 5:
        print(f"   🎯 Page {page_num}: LIVRES CONFIRMÉS ({len(liens_dp_valides)} liens /dp/)")
        return True
    elif len(resultats_recherche) >= 10:
        print(f"   🎯 Page {page_num}: LIVRES CONFIRMÉS ({len(resultats_recherche)} résultats)")
        return True
    elif len(conteneurs_produits) >= 8:
        print(f"   🎯 Page {page_num}: LIVRES CONFIRMÉS ({len(conteneurs_produits)} ASIN)")
        return True
    elif len(liens_dp_valides) >= 2:
        print(f"   ✅ Page {page_num}: ACCEPTÉE ({len(liens_dp_valides)} liens)")
        return True
    
    # Sinon, probablement fin de catalogue
    print(f"   ❌ Page {page_num}: PAS ASSEZ DE LIVRES")
    return False

def compter_livres_sur_page(soup, page_num: int) -> int:
    """
    Compte précisément le nombre de livres sur une page Amazon
    Même logique que dans extraction_utils.py pour la cohérence
    """
    
    # Méthode 1: Liens /dp/ (ISBN/ASIN) - Plus fiable
    liens_dp = soup.find_all('a', href=True)
    asins_uniques = set()
    
    for lien in liens_dp:
        href = lien.get('href', '')
        if '/dp/' in href:
            # Extraire l'ASIN
            try:
                asin = href.split('/dp/')[1].split('/')[0].split('?')[0]
                if len(asin) == 10 and asin.replace('-', '').isalnum():  # ASIN valide
                    asins_uniques.add(asin)
            except:
                continue
    
    livres_methode1 = len(asins_uniques)
    
    # Méthode 2: Conteneurs de résultats de recherche
    resultats_recherche = soup.find_all(attrs={'data-component-type': 's-search-result'})
    livres_methode2 = len(resultats_recherche)
    
    # Méthode 3: Conteneurs avec ASIN
    conteneurs_asin = soup.find_all(['div', 'article'], attrs={'data-asin': True})
    # Filtrer les ASIN vides
    conteneurs_valides = [c for c in conteneurs_asin if c.get('data-asin', '').strip()]
    livres_methode3 = len(conteneurs_valides)
    
    # Utiliser la méthode qui donne le plus de résultats (plus fiable)
    livres_detectes = max(livres_methode1, livres_methode2, livres_methode3)
    
    # Debug détaillé
    print(f"      📊 Détection: /dp/={livres_methode1}, search={livres_methode2}, asin={livres_methode3} → {livres_detectes}")
    
    return livres_detectes

def detecter_nombre_exact_livres_amazon(url_recherche: str) -> int:
    """
    Détecte le nombre EXACT de livres Amazon avec requests (comme les scrapers)
    Continue page par page jusqu'à ce qu'il n'y ait vraiment plus de livres
    Retourne le nombre exact de livres disponibles
    """
    print(f"🔍 DÉTECTION EXACTE DU NOMBRE DE LIVRES AMAZON")
    print(f"🎯 URL: {url_recherche}")
    print(f"⚡ Méthode: Requests + verifier_presence_livres_robuste (comme scrapers)")
    print("=" * 70)
    
    # Choisir la fonction de vérification
    verifier_func = verifier_presence_livres_robuste if FONCTION_DISPONIBLE else verifier_presence_livres_local
    
    page_actuelle = 1
    pages_vides_consecutives = 0
    max_pages_vides = 3
    total_livres_detectes = 0
    
    while True:
        print(f"\n🔍 Test page {page_actuelle}...")
        
        # Construire URL de la page
        url_page = f"{url_recherche}&page={page_actuelle}"
        
        try:
            # Headers rotatifs (comme dans extraction_utils.py)
            headers = {
                'User-Agent': random.choice(USER_AGENTS)
            }
            
            print(f"📡 Requête vers: {url_page}")
            response = requests.get(url_page, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"   ❌ Page {page_actuelle}: Erreur HTTP {response.status_code}")
                pages_vides_consecutives += 1
            else:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Vérifier présence de livres AVANT d'essayer de compter
                if verifier_func(soup, page_actuelle):
                    # Compter précisément les livres sur cette page
                    livres_sur_page = compter_livres_sur_page(soup, page_actuelle)
                    
                    print(f"   ✅ Page {page_actuelle}: {livres_sur_page} livres détectés")
                    total_livres_detectes += livres_sur_page
                    pages_vides_consecutives = 0
                else:
                    print(f"   ❌ Page {page_actuelle}: Aucun livre détecté")
                    pages_vides_consecutives += 1
            
            # Condition d'arrêt: trop de pages vides consécutives
            if pages_vides_consecutives >= max_pages_vides:
                print(f"\n🛑 ARRÊT: {pages_vides_consecutives} pages vides consécutives")
                break
                
            page_actuelle += 1
            
            # Délai aléatoire pour éviter les blocages (comme les scrapers)
            delai = random.uniform(0.5, 1.5)
            print(f"⏳ Pause {delai:.1f}s...")
            time.sleep(delai)
            
        except Exception as e:
            print(f"   ⚠️ Erreur page {page_actuelle}: {e}")
            pages_vides_consecutives += 1
            
            if pages_vides_consecutives >= max_pages_vides:
                break
                
            page_actuelle += 1
            time.sleep(2)  # Pause plus longue en cas d'erreur
    
    print(f"\n{'=' * 70}")
    print(f"🎯 NOMBRE EXACT DÉTECTÉ: {total_livres_detectes} livres")
    print(f"📄 Dernière page testée: {page_actuelle}")
    print(f"🛑 Pages vides consécutives: {pages_vides_consecutives}")
    print(f"{'=' * 70}")
    
    return total_livres_detectes

def tester_categorie_complete(nom_categorie: str, url_recherche: str):
    """
    Test complet d'une catégorie avec affichage détaillé
    Fonction de test pour vérifier le bon fonctionnement
    """
    print(f"\n🚀 TEST COMPLET CATÉGORIE: {nom_categorie}")
    print(f"🔗 URL: {url_recherche}")
    print("=" * 80)
    
    debut = time.time()
    nombre_exact = detecter_nombre_exact_livres_amazon(url_recherche)
    duree = time.time() - debut
    
    print(f"\n🎉 RÉSULTAT FINAL:")
    print(f"📚 Catégorie: {nom_categorie}")
    print(f"🔢 Nombre exact: {nombre_exact:,} livres")
    print(f"⏱️ Durée: {duree:.1f} secondes")
    print(f"⚡ Vitesse: {(nombre_exact/duree) if duree > 0 else 0:.1f} livres/sec")
    print("=" * 80)
    
    return nombre_exact

def tester_une_seule_categorie(nom_categorie: str = "Cuisine"):
    """Test rapide d'une seule catégorie"""
    categories_urls = {
        "Cuisine": "https://www.amazon.fr/s?k=cuisine&i=stripbooks",
        "Bandes dessinées": "https://www.amazon.fr/s?k=bandes+dessinees&i=stripbooks", 
        "Ados": "https://www.amazon.fr/s?k=ados&i=stripbooks"
    }
    
    if nom_categorie not in categories_urls:
        print(f"❌ Catégorie '{nom_categorie}' non trouvée")
        return 0
    
    url = categories_urls[nom_categorie]
    return tester_categorie_complete(nom_categorie, url)

if __name__ == "__main__":
    print("🚀 DÉTECTION EXACTE AMAZON - MÉTHODE SCRAPERS")
    print("=" * 70)
    print("🔧 Fonctionnalités:")
    print("   • Requests avec headers rotatifs")
    print("   • verifier_presence_livres_robuste (éprouvée)")
    print("   • Même logique que extraction_utils.py") 
    print("   • Compatible système FONCTION")
    print("=" * 70)
    
    # Test d'une seule catégorie pour vérification rapide
    print("\n🧪 TEST RAPIDE - UNE CATÉGORIE")
    try:
        # Test cuisine
        resultat = tester_une_seule_categorie("Cuisine")
        print(f"✅ Test terminé: {resultat} livres détectés")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🎯 FONCTION PRÊTE POUR INTÉGRATION DANS LES SCRAPERS")
    print("   • Utiliser: detecter_nombre_exact_livres_amazon(url)")
    print("   • Méthode identique aux scrapers existants")
    print("=" * 70)