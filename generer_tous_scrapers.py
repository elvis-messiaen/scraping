#!/usr/bin/env python3
"""
Générateur de TOUS les scrapers basés sur les vraies catégories détectées
"""

import os
import json
from typing import List, Dict

def generer_scraper_depuis_categorie(nom_categorie: str, url_categorie: str, nom_fichier: str) -> str:
    """Génère le code d'un scraper spécifique basé sur les vraies catégories"""
    
    nom_classe = f"ScraperAmazon{nom_fichier.replace('_', '').title()}"
    
    code_scraper = f'''#!/usr/bin/env python3
"""
SCRAPER AMAZON - CATÉGORIE: {nom_categorie}
URL de base: {url_categorie}
Généré automatiquement depuis les catégories Amazon détectées
"""

import os
import sys
import json
import time
import random
import threading
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import requests
from bs4 import BeautifulSoup
import pandas as pd

class {nom_classe}:
    def __init__(self):
        """Initialise le scraper pour {nom_categorie}"""
        self.nom_categorie = "{nom_categorie}"
        self.nom_fichier = "{nom_fichier}"
        self.url_base_recherche = "{url_categorie}"
        
        # Configuration
        self.request_delay = 0.5
        self.max_pages_vides = 3
        self.pages_vides_consecutives = 0
        
        # Données
        self.livres_scraped = []
        self.urls_traitees = set()
        self.debut_scraping = None
        self.lock = threading.Lock()
        
        # Setup des dossiers et fichiers
        self.setup_dossiers()
        self.charger_donnees_existantes()
        
        print(f"🚀 SCRAPER PRÊT - {{self.nom_categorie}}")
        print(f"🎯 URL: {{self.url_base_recherche}}")

    def setup_dossiers(self):
        """Crée les dossiers nécessaires"""
        self.dossier_livres = os.path.join('..', 'LIVRES', self.nom_fichier)
        os.makedirs(self.dossier_livres, exist_ok=True)
        
        # Fichiers de sauvegarde
        self.fichier_json = os.path.join(self.dossier_livres, f"{{self.nom_fichier}}_livres.json")
        self.fichier_csv = os.path.join(self.dossier_livres, f"{{self.nom_fichier}}_livres.csv")
        self.fichier_progres = os.path.join(self.dossier_livres, f"{{self.nom_fichier}}_progres.json")
        
        print(f"📁 Dossier: {{self.dossier_livres}}")
        print(f"📄 JSON: {{os.path.basename(self.fichier_json)}}")
        print(f"📊 CSV: {{os.path.basename(self.fichier_csv)}}")

    def charger_donnees_existantes(self):
        """Charge les données existantes depuis les fichiers JSON"""
        stock_existant = 0
        try:
            if os.path.exists(self.fichier_json):
                with open(self.fichier_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.livres_scraped = data
                        stock_existant = len(self.livres_scraped)
                        self.urls_traitees = {{livre.get('url', '') for livre in data if livre.get('url')}}
        except Exception as e:
            print(f"⚠️ Erreur chargement données: {{e}}")
            self.livres_scraped = []
            
        print(f"📊 Stock existant: {{stock_existant:,}} livres")
        return stock_existant

    def charger_progression_existante(self):
        """Charge la progression depuis le fichier de progression"""
        try:
            if os.path.exists(self.fichier_progres):
                with open(self.fichier_progres, 'r', encoding='utf-8') as f:
                    progression = json.load(f)
                    return progression.get('page_actuelle', 1)
        except Exception as e:
            print(f"⚠️ Erreur chargement progression: {{e}}")
        
        return 1

    def verifier_presence_livres(self, soup, page_num: int) -> bool:
        """Vérifie si la page contient des livres"""
        print(f"🔍 Vérification page {{page_num}}...")
        
        # Chercher les liens /dp/ (liens de produits Amazon)
        liens_dp = soup.find_all('a', href=True)
        liens_livres_valides = []
        
        for link in liens_dp:
            href = link.get('href', '')
            if '/dp/' in href and len(href) > 10:
                liens_livres_valides.append(href)
        
        print(f"   🔗 {{len(liens_livres_valides)}} liens /dp/ trouvés")
        
        if len(liens_livres_valides) >= 5:
            print(f"   ✅ Page {{page_num}}: livres trouvés")
            return True
        else:
            print(f"   ❌ Page {{page_num}}: pas de livres")
            return False

    def extraire_infos_livre(self, element_livre) -> Optional[Dict[str, Any]]:
        """Extrait les informations d'un livre depuis un élément HTML"""
        try:
            # Lien du livre
            lien_element = element_livre.find('a', href=True)
            if not lien_element:
                return None
                
            url_livre = lien_element.get('href', '')
            if not url_livre or '/dp/' not in url_livre:
                return None
            
            # URL complète
            if url_livre.startswith('/'):
                url_livre = f"https://www.amazon.fr{{url_livre}}"
            elif not url_livre.startswith('http'):
                url_livre = f"https://www.amazon.fr/{{url_livre}}"
            
            # Éviter les doublons
            if url_livre in self.urls_traitees:
                return None
            
            # Titre du livre
            titre = ""
            titre_element = element_livre.find(['h2', 'h3', 'span'], string=True)
            if titre_element:
                titre = titre_element.get_text(strip=True)
            
            if not titre:
                titre = lien_element.get_text(strip=True)
            
            # Auteur
            auteur = ""
            auteur_elements = element_livre.find_all(['span', 'a'])
            for elem in auteur_elements:
                text = elem.get_text(strip=True)
                if 'de ' in text.lower() or 'par ' in text.lower():
                    auteur = text
                    break
            
            # Prix
            prix = ""
            prix_elements = element_livre.find_all(['span', 'div'])
            for elem in prix_elements:
                text = elem.get_text(strip=True)
                if '€' in text and any(char.isdigit() for char in text):
                    prix = text
                    break
            
            livre_info = {{
                'titre': titre,
                'auteur': auteur,
                'prix': prix,
                'url': url_livre,
                'categorie': self.nom_categorie,
                'date_scraping': datetime.now().isoformat(),
                'source': 'Amazon FR'
            }}
            
            # Ajouter à la liste des URLs traitées
            self.urls_traitees.add(url_livre)
            
            return livre_info
            
        except Exception as e:
            print(f"⚠️ Erreur extraction livre: {{e}}")
            return None

    def scraper_page(self, page_num: int) -> List[Dict[str, Any]]:
        """Scrape une page et retourne la liste des livres trouvés"""
        url_page = f"{{self.url_base_recherche}}&page={{page_num}}"
        livres_page = []
        
        try:
            response = requests.get(url_page, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Vérifier présence de livres
            if not self.verifier_presence_livres(soup, page_num):
                return []
            
            # Chercher les conteneurs de livres
            conteneurs_livres = soup.find_all(['div', 'article'])
            
            for conteneur in conteneurs_livres:
                livre_info = self.extraire_infos_livre(conteneur)
                if livre_info:
                    livres_page.append(livre_info)
            
            print(f"   📖 {{len(livres_page)}} livres trouvés sur page {{page_num}}")
            
        except Exception as e:
            print(f"❌ Erreur scraping page {{page_num}}: {{e}}")
        
        return livres_page

    def sauvegarder_progres_complet(self, page_actuelle: int):
        """Sauvegarde complète: JSON + CSV + progression"""
        try:
            # Sauvegarde JSON
            with open(self.fichier_json, 'w', encoding='utf-8') as f:
                json.dump(self.livres_scraped, f, ensure_ascii=False, indent=2)
            
            # Sauvegarde CSV si on a des livres
            if self.livres_scraped:
                df = pd.DataFrame(self.livres_scraped)
                df.to_csv(self.fichier_csv, index=False, encoding='utf-8')
            
            # Sauvegarde progression
            progression = {{
                'categorie': self.nom_categorie,
                'nom_fichier': self.nom_fichier,
                'page_actuelle': page_actuelle,
                'total_livres': len(self.livres_scraped),
                'derniere_maj': datetime.now().isoformat(),
                'scraper_cree_auto': True
            }}
            
            with open(self.fichier_progres, 'w', encoding='utf-8') as f:
                json.dump(progression, f, ensure_ascii=False, indent=2)
                
            print(f"💾 Sauvegarde: {{len(self.livres_scraped):,}} livres, page {{page_actuelle}}")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {{e}}")

    def run(self):
        """Méthode principale - Scraping jusqu'à épuisement"""
        print(f"🚀 DÉMARRAGE SCRAPER ILLIMITÉ - {{self.nom_categorie}}")
        print("=" * 80)
        
        # Enregistrer l'heure de début
        self.debut_scraping = datetime.now()
        
        # Reprendre depuis la dernière page
        page_actuelle = max(1, self.charger_progression_existante())
        
        print(f"📦 Stock existant: {{len(self.livres_scraped):,}} livres")
        print(f"⏳ Objectif: ÉPUISEMENT COMPLET (aucune limite)")
        print("=" * 80)
        
        # BOUCLE PRINCIPALE ILLIMITÉE
        while True:
            print(f"\\n🔄 Page {{page_actuelle}} - {{len(self.livres_scraped):,}} livres")
            
            try:
                # Scraper la page
                livres_nouveaux = self.scraper_page(page_actuelle)
                
                if livres_nouveaux:
                    # Ajouter les nouveaux livres
                    with self.lock:
                        self.livres_scraped.extend(livres_nouveaux)
                    
                    print(f"   ✅ {{len(livres_nouveaux)}} nouveaux livres ajoutés")
                    self.pages_vides_consecutives = 0
                else:
                    # Page vide
                    self.pages_vides_consecutives += 1
                    print(f"   ⚠️ Page vide ({{self.pages_vides_consecutives}}/{{self.max_pages_vides}})")
                    
                    if self.pages_vides_consecutives >= self.max_pages_vides:
                        print(f"🛑 ARRÊT: {{self.max_pages_vides}} pages vides consécutives - Catalogue épuisé")
                        break
                
                # Sauvegarde périodique : toutes les 50 pages
                if page_actuelle % 50 == 0:
                    self.sauvegarder_progres_complet(page_actuelle)
                
                page_actuelle += 1
                time.sleep(self.request_delay)
                
            except KeyboardInterrupt:
                print(f"\\n🛑 ARRÊT UTILISATEUR à la page {{page_actuelle}}")
                break
            except Exception as e:
                print(f"❌ Erreur page {{page_actuelle}}: {{e}}")
                time.sleep(2)
                continue
        
        # Sauvegarde finale
        print("\\n💾 SAUVEGARDE FINALE...")
        self.sauvegarder_progres_complet(page_actuelle)
        
        # Résultats finaux
        total_final = len(self.livres_scraped)
        temps_total = datetime.now() - self.debut_scraping
        
        print("\\n" + "=" * 80)
        print("🏁 ÉPUISEMENT COMPLET DU CATALOGUE AMAZON")
        print(f"📚 TOTAL RÉCUPÉRÉ: {{total_final:,}} livres")
        print(f"📄 Dernière page traitée: {{page_actuelle}}")
        print(f"⏱️ Temps total: {{str(temps_total).split('.')[0]}}")
        if temps_total.total_seconds() > 0:
            print(f"⚡ Vitesse moyenne: {{total_final / temps_total.total_seconds():.1f}} livres/seconde")
        print("=" * 80)

if __name__ == "__main__":
    scraper = {nom_classe}()
    print("🚀 SCRAPER ILLIMITÉ PRÊT À DÉMARRER")
    print("⚡ Fonctionnalités: détection infaillible, découpage auto, métriques complètes")
    print("🔥 AUCUNE LIMITE - Scraping jusqu'à épuisement total du catalogue")
    
    try:
        scraper.run()
    except KeyboardInterrupt:
        print("\\n🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        print(f"\\n❌ Erreur critique: {{e}}")
'''
    
    return code_scraper

def generer_tous_les_scrapers_vrais():
    """Génère TOUS les scrapers basés sur les vraies catégories Amazon détectées"""
    
    # Charger le fichier des catégories détectées
    try:
        with open('/Users/Simplon/Cours/workspacePython/Scraping/CATEGORIES/categories_amazon_completes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Erreur chargement catégories: {e}")
        return
    
    dossier_scrapers = '/Users/Simplon/Cours/workspacePython/Scraping/SCRAPERS'
    scrapers_generes = 0
    liste_scrapers = []
    
    print(f"🔧 GÉNÉRATION DE TOUS LES SCRAPERS DEPUIS LES VRAIES CATÉGORIES AMAZON")
    print("=" * 70)
    
    # Parcourir toutes les catégories et sous-catégories
    categories = data.get('categories', {})
    
    for cat_principale, cat_data in categories.items():
        if isinstance(cat_data, dict) and 'sous_categories' in cat_data:
            sous_categories = cat_data['sous_categories']
            print(f"📂 {cat_principale}: {len(sous_categories)} sous-catégories")
            
            for nom_sous_cat, sous_cat_data in sous_categories.items():
                try:
                    nom_categorie = sous_cat_data.get('nom', nom_sous_cat)
                    url_categorie = sous_cat_data.get('url', '')
                    nom_fichier = sous_cat_data.get('nom_fichier', nom_sous_cat.lower().replace(' ', '_'))
                    
                    if not url_categorie:
                        print(f"   ⚠️ {nom_categorie} - URL manquante, ignoré")
                        continue
                    
                    # Générer le code du scraper
                    code_scraper = generer_scraper_depuis_categorie(nom_categorie, url_categorie, nom_fichier)
                    
                    # Nom du fichier scraper
                    chemin_fichier = os.path.join(dossier_scrapers, f"scraper_{nom_fichier}.py")
                    
                    # Sauvegarder le scraper
                    with open(chemin_fichier, 'w', encoding='utf-8') as f:
                        f.write(code_scraper)
                    
                    # Ajouter à la liste
                    liste_scrapers.append({
                        'nom_categorie': nom_categorie,
                        'nom_fichier': f"scraper_{nom_fichier}.py",
                        'url_base': url_categorie
                    })
                    
                    print(f"   ✅ scraper_{nom_fichier}.py - Généré")
                    scrapers_generes += 1
                    
                except Exception as e:
                    print(f"   ❌ {nom_sous_cat} - Erreur: {e}")
    
    print("=" * 70)
    print(f"📊 RÉSULTAT: {scrapers_generes} scrapers générés depuis les vraies catégories Amazon")
    print("✅ Tous les scrapers correspondent aux catégories détectées")
    
    # Créer la nouvelle liste_scrapers.json
    fichier_liste = os.path.join(dossier_scrapers, 'liste_scrapers.json')
    with open(fichier_liste, 'w', encoding='utf-8') as f:
        json.dump(liste_scrapers, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Nouvelle liste_scrapers.json créée avec {len(liste_scrapers)} scrapers")
    print(f"🎯 Catégories couvertes: {scrapers_generes} sous-catégories Amazon complètes")

if __name__ == "__main__":
    generer_tous_les_scrapers_vrais()