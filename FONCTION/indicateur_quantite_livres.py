#!/usr/bin/env python3
"""
INDICATEUR PRÉCIS DE QUANTITÉ DE LIVRES PAR CATÉGORIE
====================================================

Mesure et vérifie le nombre RÉEL de livres disponibles sur Amazon par catégorie
pour valider l'efficacité de l'extraction à 100%.

OBJECTIF: Détecter si on atteint vraiment les milliers de livres par catégorie
ou si Amazon limite à ~60-70 livres.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import re
import time

class IndicateurQuantiteLivres:
    """
    Analyseur précis du nombre réel de livres disponibles par catégorie Amazon
    """

    def __init__(self):
        """Initialise l'indicateur avec la configuration de base"""
        self.repertoire_base = Path(__file__).parent.parent
        self.repertoire_livres = self.repertoire_base / "LIVRES"
        self.rapport_indicateur = self.repertoire_base / "RAPPORT_QUANTITE_LIVRES.json"

        # Headers anti-détection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def analyser_quantite_amazon_directe(self, url_categorie: str, nom_categorie: str) -> Dict[str, Any]:
        """
        Analyse directement sur Amazon le nombre RÉEL de livres dans une catégorie

        Args:
            url_categorie: URL de la catégorie Amazon
            nom_categorie: Nom de la catégorie

        Returns:
            Dict avec les métriques détaillées de quantité
        """
        print(f"🔍 ANALYSE DIRECTE AMAZON: {nom_categorie}")
        print(f"   URL: {url_categorie}")

        metriques = {
            'nom_categorie': nom_categorie,
            'url_categorie': url_categorie,
            'timestamp': datetime.now().isoformat(),
            'livres_page_1': 0,
            'indicateur_total_amazon': None,
            'pages_testees': 0,
            'pagination_fonctionne': False,
            'contenu_recycle': False,
            'estimation_total': 0,
            'conclusion': ""
        }

        try:
            # 1. ANALYSER LA PAGE 1
            print(f"   📄 Test page 1...")
            response = requests.get(url_categorie, headers=self.headers, timeout=15)

            if response.status_code not in [200, 405, 503]:
                metriques['conclusion'] = f"Erreur HTTP {response.status_code}"
                return metriques

            soup = BeautifulSoup(response.content, 'html.parser')

            # Compter les livres sur la page 1
            elements_page_1 = soup.select('.octopus-pc-item')
            metriques['livres_page_1'] = len(elements_page_1)
            print(f"      ✅ {len(elements_page_1)} livres trouvés page 1")

            # Chercher des indicateurs de total sur Amazon
            total_amazon = self._extraire_indicateur_total_amazon(soup)
            if total_amazon:
                metriques['indicateur_total_amazon'] = total_amazon
                print(f"      📊 Indicateur Amazon trouvé: {total_amazon}")

            # 2. TESTER LA PAGINATION
            print(f"   🔄 Test pagination...")
            asin_page_1 = self._extraire_asins_page(soup)

            pages_a_tester = [2, 3, 5, 10]
            for page_num in pages_a_tester:
                print(f"      📄 Test page {page_num}...")

                # Construire URL de la page
                if '?' in url_categorie:
                    url_page = f"{url_categorie}&page={page_num}"
                else:
                    url_page = f"{url_categorie}?page={page_num}"

                try:
                    response_page = requests.get(url_page, headers=self.headers, timeout=15)
                    if response_page.status_code == 200:
                        soup_page = BeautifulSoup(response_page.content, 'html.parser')
                        elements_page = soup_page.select('.octopus-pc-item')

                        if elements_page:
                            metriques['pages_testees'] = page_num
                            metriques['pagination_fonctionne'] = True
                            print(f"         ✅ Page {page_num}: {len(elements_page)} livres")

                            # Vérifier si le contenu est recyclé
                            asin_page_n = self._extraire_asins_page(soup_page)
                            if asin_page_1 and asin_page_n:
                                overlap = len(set(asin_page_1) & set(asin_page_n))
                                if overlap > len(asin_page_1) * 0.8:  # Plus de 80% de similarité
                                    metriques['contenu_recycle'] = True
                                    print(f"         🔄 Contenu recyclé détecté ({overlap} ASIN similaires)")
                        else:
                            print(f"         ❌ Page {page_num}: Aucun livre")
                            break
                    else:
                        print(f"         ❌ Page {page_num}: Erreur HTTP {response_page.status_code}")
                        break

                except Exception as e:
                    print(f"         ⚠️  Page {page_num}: Erreur {str(e)}")
                    break

                # Délai anti-détection
                time.sleep(2)

            # 3. CALCULER L'ESTIMATION
            metriques['estimation_total'] = self._calculer_estimation_total(metriques)
            metriques['conclusion'] = self._generer_conclusion(metriques)

            print(f"   📊 RÉSULTAT: {metriques['conclusion']}")

        except Exception as e:
            metriques['conclusion'] = f"Erreur analyse: {str(e)}"
            print(f"   ❌ Erreur: {str(e)}")

        return metriques

    def _extraire_indicateur_total_amazon(self, soup) -> str:
        """
        Extrait l'indicateur de nombre total affiché par Amazon

        Args:
            soup: BeautifulSoup de la page

        Returns:
            str: Indicateur total trouvé ou None
        """
        # Patterns pour trouver le nombre total de résultats
        patterns_total = [
            r'(\d+(?:[\s,]\d{3})*)\s*résultats?',
            r'(\d+(?:[\s,]\d{3})*)\s*results?',
            r'sur\s+(\d+(?:[\s,]\d{3})*)',
            r'of\s+(\d+(?:[\s,]\d{3})*)',
        ]

        # Chercher dans le texte de la page
        text_complet = soup.get_text(' ', strip=True)

        for pattern in patterns_total:
            matches = re.findall(pattern, text_complet, re.IGNORECASE)
            if matches:
                # Nettoyer le nombre (enlever espaces et virgules)
                nombre_str = matches[0].replace(' ', '').replace(',', '')
                try:
                    nombre = int(nombre_str)
                    if nombre > 50:  # Ignorer les petits nombres non pertinents
                        return f"{nombre:,} (via pattern '{pattern}')"
                except ValueError:
                    continue

        # Chercher dans des éléments spécifiques
        selecteurs_total = [
            '.s-result-count',
            '.sg-col-inner .a-section .a-size-base',
            '[data-component-type="s-search-result"] .a-size-base'
        ]

        for selecteur in selecteurs_total:
            elements = soup.select(selecteur)
            for elem in elements:
                text = elem.get_text(strip=True)
                for pattern in patterns_total:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        nombre_str = matches[0].replace(' ', '').replace(',', '')
                        try:
                            nombre = int(nombre_str)
                            if nombre > 50:
                                return f"{nombre:,} (via sélecteur '{selecteur}')"
                        except ValueError:
                            continue

        return None

    def _extraire_asins_page(self, soup) -> List[str]:
        """
        Extrait les ASINs des livres d'une page

        Args:
            soup: BeautifulSoup de la page

        Returns:
            List[str]: Liste des ASINs trouvés
        """
        asins = []

        # Chercher les ASINs dans les liens
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            # Pattern pour ASIN dans URL Amazon
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
            if asin_match:
                asins.append(asin_match.group(1))

        return list(set(asins))  # Supprimer les doublons

    def _calculer_estimation_total(self, metriques: Dict) -> int:
        """
        Calcule l'estimation du nombre total de livres basée sur les métriques

        Args:
            metriques: Métriques collectées

        Returns:
            int: Estimation du nombre total
        """
        # Si Amazon donne une indication directe
        if metriques['indicateur_total_amazon']:
            # Extraire le nombre de l'indicateur
            match = re.search(r'(\d+)', metriques['indicateur_total_amazon'].replace(',', ''))
            if match:
                return int(match.group(1))

        # Si le contenu est recyclé, l'estimation est proche du nombre page 1
        if metriques['contenu_recycle']:
            return metriques['livres_page_1']

        # Si la pagination fonctionne sans recyclage, estimer plus haut
        if metriques['pagination_fonctionne'] and not metriques['contenu_recycle']:
            pages_estimees = min(metriques['pages_testees'] * 10, 100)  # Estimation conservative
            return metriques['livres_page_1'] * pages_estimees

        # Par défaut, seulement ce qui est visible page 1
        return metriques['livres_page_1']

    def _generer_conclusion(self, metriques: Dict) -> str:
        """
        Génère une conclusion basée sur les métriques

        Args:
            metriques: Métriques collectées

        Returns:
            str: Conclusion de l'analyse
        """
        estimation = metriques['estimation_total']

        if metriques['indicateur_total_amazon']:
            return f"INDICATEUR AMAZON: {estimation:,} livres disponibles"

        if metriques['contenu_recycle']:
            return f"CONTENU RECYCLÉ: ~{estimation} livres uniques (pagination inutile)"

        if metriques['pagination_fonctionne']:
            return f"PAGINATION ACTIVE: estimation {estimation:,} livres (à confirmer)"

        if estimation < 100:
            return f"LIMITATION AMAZON: seulement {estimation} livres visibles"

        return f"ESTIMATION: {estimation:,} livres potentiels"

    def analyser_categories_existantes(self) -> Dict[str, Any]:
        """
        Analyse toutes les catégories existantes dans le dossier LIVRES

        Returns:
            Dict: Rapport complet d'analyse
        """
        print("🔍 ANALYSE GLOBALE DES QUANTITÉS PAR CATÉGORIE")
        print("=" * 60)

        rapport = {
            'timestamp': datetime.now().isoformat(),
            'categories_analysees': {},
            'statistiques_globales': {},
            'recommandations': []
        }

        if not self.repertoire_livres.exists():
            print("❌ Dossier LIVRES introuvable")
            return rapport

        # Analyser chaque dossier de catégorie
        categories_dirs = [d for d in self.repertoire_livres.iterdir() if d.is_dir()]
        print(f"📂 {len(categories_dirs)} catégories détectées")

        for categorie_dir in categories_dirs:
            nom_categorie = categorie_dir.name
            print(f"\n📋 Analyse: {nom_categorie}")

            # Compter les livres dans le JSON local
            fichier_json = categorie_dir / f"livres_{nom_categorie}.json"
            livres_locaux = 0

            if fichier_json.exists():
                try:
                    with open(fichier_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        livres_locaux = len(data.get('livres', []))
                    print(f"   📚 Livres locaux: {livres_locaux:,}")
                except Exception as e:
                    print(f"   ⚠️  Erreur lecture JSON: {e}")

            rapport['categories_analysees'][nom_categorie] = {
                'livres_locaux': livres_locaux,
                'fichier_json_existe': fichier_json.exists(),
                'analyse_amazon': None  # À remplir si besoin d'analyse Amazon
            }

        # Calculer les statistiques globales
        total_livres = sum(cat['livres_locaux'] for cat in rapport['categories_analysees'].values())
        categories_avec_donnees = sum(1 for cat in rapport['categories_analysees'].values() if cat['livres_locaux'] > 0)

        rapport['statistiques_globales'] = {
            'total_categories': len(categories_dirs),
            'categories_avec_donnees': categories_avec_donnees,
            'total_livres_scrapes': total_livres,
            'moyenne_livres_par_categorie': total_livres / len(categories_dirs) if categories_dirs else 0
        }

        # Génération des recommandations
        moyenne = rapport['statistiques_globales']['moyenne_livres_par_categorie']
        if moyenne < 100:
            rapport['recommandations'].append("⚠️  MOYENNE FAIBLE: Moins de 100 livres/catégorie - vérifier l'extraction")
        elif moyenne < 1000:
            rapport['recommandations'].append("🔄 MOYENNE MODÉRÉE: Moins de 1000 livres/catégorie - pagination à optimiser")
        else:
            rapport['recommandations'].append("✅ BONNE EXTRACTION: Plus de 1000 livres/catégorie en moyenne")

        if total_livres < 50000:
            rapport['recommandations'].append("🎯 OBJECTIF 7M: Actuellement très loin de l'objectif 7 millions")

        print(f"\n📊 STATISTIQUES GLOBALES:")
        print(f"   🏷️  Catégories totales: {rapport['statistiques_globales']['total_categories']}")
        print(f"   📚 Total livres scrapés: {rapport['statistiques_globales']['total_livres_scrapes']:,}")
        print(f"   📈 Moyenne/catégorie: {rapport['statistiques_globales']['moyenne_livres_par_categorie']:.1f}")

        # Sauvegarder le rapport
        self._sauvegarder_rapport(rapport)

        return rapport

    def _sauvegarder_rapport(self, rapport: Dict):
        """
        Sauvegarde le rapport d'analyse

        Args:
            rapport: Rapport à sauvegarder
        """
        try:
            with open(self.rapport_indicateur, 'w', encoding='utf-8') as f:
                json.dump(rapport, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Rapport sauvegardé: {self.rapport_indicateur}")
        except Exception as e:
            print(f"⚠️  Erreur sauvegarde rapport: {e}")

def main():
    """Fonction principale pour lancer l'analyse des quantités"""

    print("🎯 INDICATEUR PRÉCIS DE QUANTITÉ DE LIVRES")
    print("=" * 50)
    print("Objectif: Vérifier l'atteinte de 100% d'extraction")
    print("Critère: Milliers de livres par catégorie, pas 60-70")
    print("=" * 50)

    indicateur = IndicateurQuantiteLivres()

    # Analyser toutes les catégories existantes
    rapport = indicateur.analyser_categories_existantes()

    # Affichage des recommandations
    print(f"\n🎯 RECOMMANDATIONS:")
    for recommandation in rapport['recommandations']:
        print(f"   {recommandation}")

    print(f"\n📋 Rapport complet disponible dans: RAPPORT_QUANTITE_LIVRES.json")

if __name__ == "__main__":
    main()