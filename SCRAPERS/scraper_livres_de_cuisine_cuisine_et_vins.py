#!/usr/bin/env python3
"""
SCRAPER AMAZON - LIVRES DE CUISINE, CUISINE ET VINS
============================================
Catégorie: Livres de cuisine, cuisine et vins
URL: https://www.amazon.fr/b/?node=302050&ref_=Oct_d_odnav_d_301061_11&pd_rd_w=3p5y2&content-id=amzn1.sym.a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_p=a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_r=TYFHHGC958M2P8FVDWP4&pd_rd_wg=6ZrKU&pd_rd_r=6c6eeffb-bf94-44d5-adde-e7f37855774f
Généré automatiquement par le scraper de catégories principales
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
import re
import os
from datetime import datetime
from typing import Dict, List, Optional

class ScraperAmazon_LivresDeCuisineCuisineEtVins:
    """
    Scraper spécialisé pour la catégorie: Livres de cuisine, cuisine et vins

    Fonctionnalités:
    - Scraper les livres de la catégorie Livres de cuisine, cuisine et vins
    - Extraire titre, auteur, prix, note, etc.
    - Sauvegarder en JSON dans le dossier LIVRES correspondant
    - Gestion anti-détection et délais
    """

    def __init__(self):
        """Initialisation du scraper pour Livres de cuisine, cuisine et vins"""
        self.nom_categorie = "Livres de cuisine, cuisine et vins"
        self.url_categorie = "https://www.amazon.fr/b/?node=302050&ref_=Oct_d_odnav_d_301061_11&pd_rd_w=3p5y2&content-id=amzn1.sym.a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_p=a8245108-78c6-431b-abe0-8766f5c902d4&pf_rd_r=TYFHHGC958M2P8FVDWP4&pd_rd_wg=6ZrKU&pd_rd_r=6c6eeffb-bf94-44d5-adde-e7f37855774f"
        self.url_base = "https://www.amazon.fr"

        # Configuration
        self.delay_min = 1.0
        self.delay_max = 3.0
        self.timeout = 10

        # Headers anti-détection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

        # Setup chemins
        self.setup_chemins()

    def setup_chemins(self):
        """Configuration des chemins de sauvegarde"""
        base_dir = "/Users/Simplon/Cours/workspacePython/Scraping"
        self.dossier_livres = os.path.join(base_dir, "LIVRES", "livres_de_cuisine_cuisine_et_vins")
        os.makedirs(self.dossier_livres, exist_ok=True)

        nom_fichier = self.nettoyer_nom_fichier(self.nom_categorie)
        self.fichier_livres = os.path.join(
            self.dossier_livres,
            f"livres_{nom_fichier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

    def nettoyer_nom_fichier(self, nom: str) -> str:
        """Nettoie un nom pour l'utiliser comme nom de fichier"""
        nom_nettoye = re.sub(r'[^\w\s-]', '', nom)
        nom_nettoye = re.sub(r'[-\s]+', '_', nom_nettoye)
        return nom_nettoye.lower().strip('_')

    def faire_requete(self, url: str) -> Optional[BeautifulSoup]:
        """Effectuer une requête HTTP avec gestion d'erreurs"""
        try:
            time.sleep(random.uniform(self.delay_min, self.delay_max))
            response = requests.get(url, headers=self.headers, timeout=self.timeout)

            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {url}")
                return None

        except Exception as e:
            print(f"❌ Erreur requête: {e}")
            return None

    def extraire_livres_page(self, soup: BeautifulSoup) -> List[Dict]:
        """Extraire les informations des livres depuis une page"""
        livres = []

        # Sélecteurs pour les livres Amazon
        selecteurs_livres = [
            # Pages de catégorie Amazon 2024 (NOUVEAUX - TROUVENT LES LIVRES!)
            '.octopus-pc-item',
            '.octopus-pc-asin-block',
            'li.octopus-pc-item-v3',

            # Pages de recherche Amazon (anciens de secours)
            '.s-result-item[data-component-type="s-search-result"]',
            '.a-section.a-spacing-base',
            '[data-cy="title-recipe-review"]'
        ]

        for selecteur in selecteurs_livres:
            try:
                items = soup.select(selecteur)
                print(f"  📚 Sélecteur '{selecteur}': {len(items)} livres trouvés")

                for item in items:
                    livre_data = self.extraire_infos_livre(item)
                    if livre_data:
                        livres.append(livre_data)

            except Exception as e:
                print(f"    ❌ Erreur sélecteur '{selecteur}': {e}")

        return livres

    def extraire_infos_livre(self, item) -> Optional[Dict]:
        """Extraire TOUTES les informations complètes d'un livre depuis un élément HTML"""
        try:
            # TITRE - Méthode corrigée pour .octopus-pc-item
            titre = self.extraire_titre_correct(item)
            if titre == "Titre non trouvé" or len(titre) < 10:
                return None

            # URL - Méthode corrigée
            url = self.extraire_url_correct(item)
            if not url:
                return None

            # TOUTES LES DONNÉES COMPLÈTES
            prix = self.extraire_prix_correct(item)
            auteur = self.extraire_auteur_correct(item)
            note = self.extraire_note_correct(item)
            image = self.extraire_image_complete(item)
            description = self.extraire_description_complete(item)
            nombre_avis = self.extraire_nombre_avis(item)
            editeur = self.extraire_editeur_complet(item)
            format_livre = self.extraire_format_complet(item)
            date_publication = self.extraire_date_publication(item)
            nombre_pages = self.extraire_nombre_pages(item)
            isbn = self.extraire_isbn_complet(item)
            dimensions = self.extraire_dimensions(item)
            disponibilite = self.extraire_disponibilite(item)

            # STRUCTURE COMPLÈTE DU LIVRE
            livre = {
                'titre': titre,
                'auteur': auteur,
                'prix': prix,
                'note': note,
                'nombre_avis': nombre_avis,
                'image': image,
                'description': description,
                'editeur': editeur,
                'format': format_livre,
                'date_publication': date_publication,
                'nombre_pages': nombre_pages,
                'isbn': isbn,
                'dimensions': dimensions,
                'disponibilite': disponibilite,
                'url': url,
                'categorie': self.nom_categorie,
                'scrape_date': datetime.now().isoformat()
            }

            return livre

        except Exception as e:
            print(f"    ❌ Erreur extraction livre: {e}")
            return None

    def extraire_titre_correct(self, item) -> str:
        """Extraire le titre avec la méthode qui fonctionne"""
        try:
            # Méthode 1: Lien principal avec classe octopus-pc-item-link
            link = item.select_one('a.octopus-pc-item-link')
            if link:
                text = link.get_text(strip=True)
                # Nettoyer le texte (enlever le prix au début)
                if '€' in text:
                    parts = text.split('€')
                    if len(parts) > 1:
                        titre_clean = parts[-1].strip()
                        if len(titre_clean) > 10:
                            return titre_clean

                # Si pas de €, retourner le texte complet
                if len(text) > 10:
                    return text

            # Méthode 2: Chercher tout lien avec /dp/
            links = item.find_all('a', href=True)
            for link in links:
                if '/dp/' in link.get('href', ''):
                    text = link.get_text(strip=True)
                    if '€' in text and len(text) > 20:
                        parts = text.split('€')
                        if len(parts) > 1:
                            titre_clean = parts[-1].strip()
                            if len(titre_clean) > 10:
                                return titre_clean

            return "Titre non trouvé"
        except Exception:
            return "Titre non trouvé"

    def extraire_prix_correct(self, item) -> str:
        """Extraire le prix correctement"""
        try:
            # Chercher le texte avec €
            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                if '€' in text_clean and any(c.isdigit() for c in text_clean):
                    parts = text_clean.split('€')
                    if parts[0].strip():
                        prix_part = parts[0].strip()
                        if any(c.isdigit() for c in prix_part):
                            return prix_part + ' €'
            return "Prix non trouvé"
        except Exception:
            return "Prix non trouvé"

    def extraire_url_correct(self, item) -> Optional[str]:
        """Extraire l'URL correctement"""
        try:
            # Chercher le lien principal
            link = item.select_one('a.octopus-pc-item-link')
            if link and link.get('href'):
                href = link.get('href')
                if '/dp/' in href:
                    if href.startswith('/'):
                        return self.url_base + href
                    elif href.startswith('http'):
                        return href

            # Sinon chercher tout lien avec /dp/
            links = item.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if '/dp/' in href:
                    if href.startswith('/'):
                        return self.url_base + href
                    elif href.startswith('http'):
                        return href
            return None
        except Exception:
            return None

    def extraire_auteur_correct(self, item) -> str:
        """Extraire l'auteur - version basique pour l'instant"""
        try:
            # Chercher les éléments de texte qui pourraient contenir l'auteur
            elements = item.find_all(['span', 'div'], string=True)
            for elem in elements:
                text = elem.get_text(strip=True) if hasattr(elem, 'get_text') else str(elem).strip()
                if text and ('de ' in text.lower() or 'par ' in text.lower()) and len(text) < 100:
                    return text
            return "Auteur non trouvé"
        except Exception:
            return "Auteur non trouvé"

    def extraire_note_correct(self, item) -> str:
        """Extraire la note - version basique pour l'instant"""
        try:
            # Chercher les éléments étoiles
            star_elem = item.select_one('[class*="star"], [title*="étoile"]')
            if star_elem:
                title = star_elem.get('title', '')
                if title and 'étoile' in title:
                    return title
            return "Note non trouvée"
        except Exception:
            return "Note non trouvée"

    def extraire_image_complete(self, item) -> str:
        """Extraire l'URL de l'image/couverture du livre"""
        try:
            # Méthode 1: Image principale avec classe octopus
            img = item.select_one('img.octopus-pc-item-image, img[src*="images-amazon"]')
            if img and img.get('src'):
                return img.get('src')

            # Méthode 2: Toute image dans l'item
            imgs = item.find_all('img', src=True)
            for img in imgs:
                src = img.get('src', '')
                if 'images-amazon' in src or 'amazonaws' in src:
                    return src

            return "Image non trouvée"
        except Exception:
            return "Image non trouvée"

    def extraire_description_complete(self, item) -> str:
        """Extraire la description/résumé du livre"""
        try:
            # Chercher les éléments de description
            desc_selectors = [
                '.a-size-base-plus',
                '.a-size-small .a-color-secondary',
                '[data-cy="title-recipe-review"] .a-size-small'
            ]

            for selector in desc_selectors:
                desc_elem = item.select_one(selector)
                if desc_elem:
                    text = desc_elem.get_text(strip=True)
                    if text and len(text) > 20:
                        return text

            return "Description non trouvée"
        except Exception:
            return "Description non trouvée"

    def extraire_nombre_avis(self, item) -> str:
        """Extraire le nombre d'avis/commentaires"""
        try:
            # Chercher les éléments avec le nombre d'avis
            avis_patterns = [
                r'(\d+(?:,\d+)?)\s*avis',
                r'(\d+(?:,\d+)?)\s*commentaire',
                r'(\d+(?:,\d+)?)\s*évaluation'
            ]

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                for pattern in avis_patterns:
                    import re
                    match = re.search(pattern, text_clean, re.IGNORECASE)
                    if match:
                        return match.group(0)

            return "Nombre d'avis non trouvé"
        except Exception:
            return "Nombre d'avis non trouvé"

    def extraire_editeur_complet(self, item) -> str:
        """Extraire l'éditeur du livre"""
        try:
            # Chercher dans les textes pour l'éditeur
            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                # Patterns pour éditeur
                if any(word in text_clean.lower() for word in ['éditions', 'éditeur', 'publisher']):
                    if len(text_clean) < 100:  # Éviter les longs textes
                        return text_clean

            return "Éditeur non trouvé"
        except Exception:
            return "Éditeur non trouvé"

    def extraire_format_complet(self, item) -> str:
        """Extraire le format du livre (broché, Kindle, etc.)"""
        try:
            # Chercher les formats dans le texte
            formats_possibles = ['broché', 'relié', 'kindle', 'poche', 'ebook', 'audio', 'numérique']

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip().lower()
                for format_type in formats_possibles:
                    if format_type in text_clean:
                        return format_type.capitalize()

            return "Format non trouvé"
        except Exception:
            return "Format non trouvé"

    def extraire_date_publication(self, item) -> str:
        """Extraire la date de publication"""
        try:
            import re
            # Pattern pour dates (jour mois année)
            date_pattern = r'(\d{1,2}\s+\w+\s+\d{4})'

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                match = re.search(date_pattern, text_clean)
                if match:
                    return match.group(1)

            return "Date de publication non trouvée"
        except Exception:
            return "Date de publication non trouvée"

    def extraire_nombre_pages(self, item) -> str:
        """Extraire le nombre de pages"""
        try:
            import re
            # Pattern pour nombre de pages
            page_pattern = r'(\d+)\s*pages?'

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                match = re.search(page_pattern, text_clean, re.IGNORECASE)
                if match:
                    return f"{match.group(1)} pages"

            return "Nombre de pages non trouvé"
        except Exception:
            return "Nombre de pages non trouvé"

    def extraire_isbn_complet(self, item) -> str:
        """Extraire l'ISBN du livre"""
        try:
            import re
            # Pattern pour ISBN
            isbn_pattern = r'ISBN[-:\s]*(\d{10}|\d{13}|\d{3}-\d{10})'

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                match = re.search(isbn_pattern, text_clean, re.IGNORECASE)
                if match:
                    return match.group(0)

            return "ISBN non trouvé"
        except Exception:
            return "ISBN non trouvé"

    def extraire_dimensions(self, item) -> str:
        """Extraire les dimensions du livre"""
        try:
            import re
            # Pattern pour dimensions (cm x cm)
            dim_pattern = r'(\d+(?:,\d+)?\s*x\s*\d+(?:,\d+)?\s*(?:x\s*\d+(?:,\d+)?)?\s*cm)'

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip()
                match = re.search(dim_pattern, text_clean, re.IGNORECASE)
                if match:
                    return match.group(1)

            return "Dimensions non trouvées"
        except Exception:
            return "Dimensions non trouvées"

    def extraire_disponibilite(self, item) -> str:
        """Extraire la disponibilité du livre"""
        try:
            # Mots clés de disponibilité
            dispo_keywords = [
                'en stock', 'disponible', 'expédié par', 'livraison',
                'rupture', 'indisponible', 'temporairement', 'bientôt'
            ]

            texts = item.find_all(string=True)
            for text in texts:
                text_clean = str(text).strip().lower()
                for keyword in dispo_keywords:
                    if keyword in text_clean and len(text_clean) < 100:
                        return str(text).strip()

            return "Disponibilité non trouvée"
        except Exception:
            return "Disponibilité non trouvée"

    def sauvegarder_livres(self, livres: List[Dict]):
        """Sauvegarder les livres dans un fichier JSON"""
        try:
            data_finale = {
                'metadata': {
                    'categorie': self.nom_categorie,
                    'url_source': self.url_categorie,
                    'date_scraping': datetime.now().isoformat(),
                    'total_livres': len(livres),
                    'scraper_version': '1.0'
                },
                'livres': livres
            }

            with open(self.fichier_livres, 'w', encoding='utf-8') as f:
                json.dump(data_finale, f, indent=2, ensure_ascii=False)

            print(f"💾 Sauvegardé: {self.fichier_livres}")
            print(f"📊 {len(livres)} livres sauvegardés")

        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")

    def run(self):
        """Exécution principale du scraper"""
        print(f"🚀 SCRAPER AMAZON - {self.nom_categorie.upper()}")
        print("=" * 60)
        print(f"🎯 URL: {self.url_categorie}")

        try:
            # Étape 1: Scraper la première page
            print(f"\n🔹 SCRAPING PAGE 1")
            soup = self.faire_requete(self.url_categorie)

            if not soup:
                print("❌ Impossible de charger la page")
                return 0

            # Étape 2: Extraire les livres
            livres = self.extraire_livres_page(soup)

            if not livres:
                print("❌ Aucun livre trouvé")
                return 0

            print(f"✅ {len(livres)} livres extraits")

            # Étape 3: Sauvegarde
            print(f"\n💾 SAUVEGARDE")
            self.sauvegarder_livres(livres)

            print(f"\n🎉 SCRAPING TERMINÉ - {len(livres)} livres pour {self.nom_categorie}")
            return len(livres)

        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            return 0

if __name__ == "__main__":
    scraper = ScraperAmazon_LivresDeCuisineCuisineEtVins()
    total = scraper.run()

    if total > 0:
        print(f"\n✅ SUCCÈS: {total} livres scrapés pour Livres de cuisine, cuisine et vins")
    else:
        print(f"\n❌ ÉCHEC: Aucun livre trouvé pour Livres de cuisine, cuisine et vins")
