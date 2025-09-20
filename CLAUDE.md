# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ RÈGLES OBLIGATOIRES AVANT TOUTE MODIFICATION ⚠️
**TOUJOURS regarder le fichier FONCTION et les fonctions avant de faire des modifications**
- Vérifier les fonctions existantes dans le dossier FONCTION/
- Comprendre l'architecture avant de modifier
- Ne jamais dupliquer une fonctionnalité qui existe déjà
- Respecter les patterns et conventions établies
- ❌ **INTERDICTION ABSOLUE** de créer de nouvelles versions (v4, v5, etc.)
- ✅ **OBLIGATION** de modifier/mettre à jour les scrapers EXISTANTS uniquement
- 📝 **RÈGLE**: Toujours éditer les fichiers existants, jamais en créer de nouveaux

## Architecture du Projet

Ce projet est un système massif de scraping Amazon avec des scrapers Python automatiquement générés pour extraire des informations de livres par catégorie.
Il doit génerer les dossiers de scraper automatique lors de la récuperation des catégories et ou sous catégories
Il vérifie avant que les fichier son pas existant, afin de ne pas faire de doublon.
Il créer aussi les dossier de livres si pas existant pour que les fichier de sauvegarde json soit créer en se moment

Il y a différents types de scraper différent :
    - scraper de catégorie
    - scraper de sous catégorie
    - scraper de livre par catégorie

### Structure Principale

- **`SCRAPERS/`** - Un ensemble de scrapers individuels générés automatiquement
- **`FONCTION/`** - Modules utilitaires partagés pour extraction et traitement
- **`CATEGORIES/`** - Fichiers JSON contenant les catégories détectées
- **`LIVRES/`** - Données extraites organisées par catégorie avec fichiers de progression
- **`SCRAPY_AMAZON/`** - Framework Scrapy-Playwright moderne (alternative recommandée)

### Fonctions Utilitaires Centralisées

Le dossier `FONCTION/` contient des modules Python importants :
- **`extraction_utils.py`** - Fonctions d'extraction d'informations de livres
- **`detection_utils.py`** - Utilitaires de détection de catégories
- **`fichiers_utils.py`** - Gestion des fichiers et chemins
- **`metriques_utils.py`** - Calcul de métriques et statistiques
- **`mise_a_jour_utils.py`** - Utilitaires de mise à jour

### Pattern des Scrapers

Chaque scraper suit un modèle standardisé avec :
- Configuration des chemins avec base `/Users/Simplon/Cours/workspacePython/Scraping`
- Headers rotatifs pour éviter la détection
- Extraction d'informations de livres (titre, prix, auteur, ASIN)
- Sauvegarde en JSON avec métadonnées et progression
- Gestion d'erreurs et logging

## Commandes Principales

### Scraping Moderne (Recommandé)
```bash
# Utiliser le framework Scrapy-Playwright moderne
cd SCRAPY_AMAZON
python run_spider.py

# Ou directement via Scrapy
cd SCRAPY_AMAZON
scrapy crawl amazon_categories
```

### Scrapers Individuels
```bash
# Exécuter un scraper spécifique
python scraper_[nom_categorie].py

# Scraper des catégories principales
python SCRAPERS/scraper_category_principal.py
```

### Scripts d'Administration
```bash
# Générer tous les scrapers automatiquement
python generer_tous_scrapers.py

# Optimiser les scrapers existants
python SCRAPERS/OPTIMISER_SCRAPERS_MAC.py

# Réécrire tous les scrapers
python SCRAPERS/REECRIRE_TOUS_SCRAPERS_COMPLETS.py
```

### Utilitaires de Données

## Architecture de Données

### Structure JSON des Catégories
```json
{
  "metadata": {
    "timestamp": "ISO datetime",
    "total_categories": "number",
    "duree_seconde": "execution time"
  },
  "categories": ["liste", "des", "catégories"]
}
```

### Structure JSON des Livres
```json
{
  "metadata": {
    "page_actuelle": "number",
    "total_livres": "number",
    "timestamp": "ISO datetime"
  },
  "livres": [
    {
      "titre": "string",
      "prix": "string",
      "auteur": "string",
      "url": "string",
      "asin": "string"
    }
  ]
}
```

## Configuration Anti-Détection

Les scrapers utilisent plusieurs techniques :
- **Headers rotatifs** avec User-Agents multiples
- **Délais aléatoires** entre les requêtes
- **URL base Amazon** : `https://www.amazon.fr`
- **Node principal livres** : `https://www.amazon.fr/b?node=301061`

## Technologies Utilisées

- **Python 3** - Langage principal
- **requests + BeautifulSoup** - Scrapers classiques
- **Scrapy + Playwright** - Framework moderne (SCRAPY_AMAZON/)
- **JSON** - Format de données
- **CSS Selectors** - Extraction ciblée

## Notes Importantes

- Le projet contient plus de 11,000 scrapers générés automatiquement
- Chaque scraper cible une catégorie spécifique Amazon
- Les données sont sauvées dans `/LIVRES/[categorie]/` avec fichiers de progression
- Le framework Scrapy-Playwright est recommandé pour de nouveaux développements
- Respecter les délais entre requêtes pour éviter le blocage par Amazon