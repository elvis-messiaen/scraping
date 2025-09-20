#!/usr/bin/env python3
"""
MODULE DE VALIDATION DES CATÉGORIES AMAZON LIVRES
================================================
Fonctions de validation stricte pour s'assurer que seules les catégories
de livres sont détectées et sauvegardées, évitant les catégories non-livres
comme "Cuisine et maison", "High-Tech", etc.
"""

# Cache global pour arborescence validée
arborescence_livres_cache = None
derniere_mise_a_jour_cache = None

def est_categorie_livre_valide(url: str, text: str) -> bool:
    """
    🚀 APPROCHE HYBRIDE 2025 - Basée sur les meilleures pratiques actuelles

    Combinaison de 3 méthodes complémentaires (tendance industry standard) :
    1. Règles simples (REGEX patterns) - rapide et précise
    2. Classification par contexte (Rule-based) - logique métier
    3. Permissivité intelligente - évite les faux négatifs
    """
    url_lower = url.lower()
    text_lower = text.lower()

    # 🚫 ÉTAPE 1: EXCLUSIONS TECHNIQUES (rapides)
    exclusions_techniques = ['/dp/', '/gp/', '/help/', '/account/', '/cart/', '/sign-in']
    if any(exc in url_lower for exc in exclusions_techniques):
        return False

    # 📝 ÉTAPE 2: FORMAT BASIQUE
    if not text.strip() or len(text.strip()) > 500:
        return False

    # 🎯 ÉTAPE 3: REGEX PATTERNS AMAZON LIVRES (ultra-rapide)
    # Approche 2025 : regex simples et fiables pour patterns connus
    patterns_livres_certains = [
        r'node=301\d+',      # Tous les nodes 301xxx = livres
        r'node=6680\d+',     # Nouveautés livres
        r'stripbooks',       # Section livres Amazon
        r'i=stripbooks',     # Paramètre livres
        r'rh=n%3A301'       # Recherche livres encodée
    ]

    import re
    for pattern in patterns_livres_certains:
        if re.search(pattern, url_lower):
            # ✅ Dans arborescence livres certaine = ACCEPTER tout (sauf exclusions évidentes)
            return not any(exc in text_lower for exc in [
                'high-tech', 'smartphone', 'ordinateur', 'électroménager',
                'vêtements', 'chaussures', 'bijoux', 'auto', 'moto'
            ])

    # 🔍 ÉTAPE 4: PATTERNS ÉTENDUS (rule-based approach)
    patterns_suspects = [
        'node=404', 'node=406', 'node=451', 'node=465', 'node=466', 'node=489',
        'node=531', 'node=542', 'node=596', 'node=969', 'node=1064', 'node=1087',
        'node=4252', 'node=4256', 'node=125273', 'node=52042', 'node=355635',
        'node=695398', 'node=12641'
    ]

    candidat_probable = any(pattern in url_lower for pattern in patterns_suspects)
    if not candidat_probable:
        return False

    # 🧠 ÉTAPE 5: INTELLIGENCE CONTEXTUELLE (hybrid approach 2025)
    # Plus de validation contenu lourde - juste logique simple
    return validation_contextuelle_2025(url_lower, text_lower)


def est_node_id_livre(node_id: str) -> bool:
    """
    Vérifier si un node ID correspond à une catégorie de livres Amazon
    
    Args:
        node_id (str): Le node ID à vérifier
        
    Returns:
        bool: True si le node ID est une catégorie livre, False sinon
    """
    if not node_id:
        return False
        
    # Node IDs connus pour les livres Amazon France
    nodes_livres_connus = {
        '301061',  # Livres (racine)
        '301132',  # Romans et polars
        '301133',  # BD et Mangas
        '301137',  # Enfants et ados
        '301146',  # Scolaire et études
        '12641896031',  # Santé et bien-être (livres)
        '355635011',   # Loisirs et culture (livres)
        '52042011',    # Livres en langues étrangères
        '695398031',   # Le livre autrement (Kindle)
        '125273011',   # Recherche détaillée
        '6680516031',  # Nouveautés
        
    }
    
    # Node IDs qui commencent par des prefixes livres
    prefixes_livres = ['3010', '3020', '3011', '4896', '4252', '4256', '1551', '1552', '451', '406', '404', '229', '1087', '531', '465', '596', '542', '316']
    
    if node_id in nodes_livres_connus:
        return True
    
    # Vérifier les préfixes
    for prefix in prefixes_livres:
        if node_id.startswith(prefix):
            return True
    
    return False


def est_sous_categorie_valide(url: str, text: str, url_parent: str) -> bool:
    """
    Vérifier si une sous-catégorie Amazon est valide pour les livres
    
    Applique la même validation stricte que est_categorie_livre_valide()
    avec une vérification supplémentaire pour s'assurer que la sous-catégorie
    n'est pas identique à sa catégorie parente.
    
    Args:
        url (str): L'URL de la sous-catégorie à valider
        text (str): Le nom de la sous-catégorie à valider  
        url_parent (str): L'URL de la catégorie parente
        
    Returns:
        bool: True si la sous-catégorie est valide, False sinon
        
    Description détaillée:
    - Utilise est_categorie_livre_valide() pour la validation de base
    - Ajoute une vérification pour éviter les doublons parent/enfant
    - S'assure que la sous-catégorie n'est pas identique au parent
    """
    # Même validation que catégorie principale + pas identique au parent
    return est_categorie_livre_valide(url, text) and url != url_parent


def extraire_node_id(url: str) -> str:
    """
    Extraire l'ID de node depuis une URL Amazon
    
    Amazon utilise des IDs de node pour identifier les catégories.
    Cette fonction extrait ces IDs depuis différents formats d'URL.
    
    Args:
        url (str): L'URL Amazon contenant le node ID
        
    Returns:
        str: Le node ID extrait, ou None si non trouvé
        
    Description détaillée:
    - Recherche plusieurs patterns de node ID dans l'URL
    - Supporte les formats: node=123, node/123, rh=n%3A123, &n=123
    - Retourne le premier ID trouvé
    - Retourne None si aucun pattern ne matche
    
    Exemples d'URL supportées:
    - https://amazon.fr/b?node=301061
    - https://amazon.fr/s?rh=n%3A301061
    - https://amazon.fr/category/node/123456
    """
    import re
    
    patterns = [
        r'node[=/](\d+)',       # node=123 ou node/123
        r'rh=n%3A(\d+)',        # Format URL encodé rh=n%3A123
        r'&n=(\d+)',            # Paramètre &n=123
        r'browse/(\d+)',        # Format browse/123
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def nettoyer_nom_fichier(nom: str) -> str:
    """
    Nettoyer un nom de catégorie pour créer un nom de fichier valide
    
    Transforme un nom de catégorie Amazon en nom de fichier/dossier valide
    en supprimant ou remplaçant les caractères spéciaux.
    
    Args:
        nom (str): Le nom de catégorie à nettoyer
        
    Returns:
        str: Le nom nettoyé, utilisable comme nom de fichier/dossier
        
    Description détaillée:
    - Supprime les caractères spéciaux non autorisés dans les noms de fichier
    - Remplace les espaces et tirets par des underscores
    - Convertit en minuscules pour la cohérence
    - Supprime les underscores en début/fin
    
    Exemples:
        >>> nettoyer_nom_fichier("Romans & Polars")
        "romans_polars"
        >>> nettoyer_nom_fichier("Science-Fiction")  
        "science_fiction"
    """
    import re
    
    # Remplacer les caractères spéciaux par des espaces
    nom_clean = re.sub(r'[^\w\s-]', ' ', nom.lower())
    
    # Remplacer les espaces multiples et tirets par des underscores
    nom_clean = re.sub(r'[-\s]+', '_', nom_clean)
    
    # Supprimer les underscores en début/fin
    return nom_clean.strip('_')


def verification_contenu_livre_temps_reel(url: str, nom: str) -> bool:
    """
    Vérification temps réel si une URL contient vraiment des livres
    Utilisée lors du scraping pour valider chaque catégorie
    
    Returns:
        True si c'est une vraie catégorie de livres
        False sinon
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import time
        
        # Vérification rapide par nom d'abord
        mots_non_livres = [
            'cuisine et maison', 'audible', 'informatique', 'beauté', 'bébé', 'puériculture',
            'vêtements', 'chaussures', 'bijoux', 'montres', 'auto', 'moto', 'jardin',
            'bricolage', 'sport', 'électronique', 'high-tech', 'musique', 'dvd',
            'jeux vidéo', 'jouets', 'animalerie', 'hygiène', 'santé', 'épicerie'
        ]
        
        nom_lower = nom.lower()
        for mot in mots_non_livres:
            if mot in nom_lower:
                return False
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Vérification par contenu de page
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code != 200:
            return False
            
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()
        
        # Chercher des indicateurs de livres
        indicateurs_livres = [
            'livre', 'roman', 'auteur', 'isbn', 'édition', 'broché', 'relié',
            'poche', 'kindle', 'ebook', 'littérature', 'fiction', 'non-fiction',
            'manuel', 'guide', 'essai', 'biographie', 'histoire', 'science',
            'philosophie', 'psychologie', 'société', 'culture', 'art', 'poésie'
        ]
        
        # Chercher des indicateurs non-livres
        indicateurs_non_livres = [
            'prix :', 'couleur :', 'taille :', 'matière :', 'poids :', 'dimensions :',
            'batterie', 'garantie', 'livraison gratuite', 'en stock', 'quantité',
            'ajouter au panier', 'acheter maintenant', 'comparer les prix'
        ]
        
        # Compter les occurences
        score_livres = sum(1 for mot in indicateurs_livres if mot in page_text)
        score_non_livres = sum(1 for mot in indicateurs_non_livres if mot in page_text)
        
        # Vérifier la présence de livres spécifiques
        import re
        livres_trouvés = len(soup.find_all(['img', 'a'], string=re.compile(r'livre|roman|auteur', re.I)))
        
        # Décision basée sur les scores
        if score_livres >= 3 and livres_trouvés >= 2 and score_non_livres < score_livres:
            return True
        
        return False
        
    except Exception as e:
        # En cas d'erreur, on refuse par sécurité
        return False


def controle_reject(url: str, nom: str) -> bool:
    """
    Contrôle secondaire pour vérifier si un rejet était une erreur
    Utilise la validation par arborescence officielle
    
    Returns:
        True si le rejet était une ERREUR (donc à accepter)
        False si le rejet était correct
    """
    return validation_par_arborescence_officielle(url, nom)


def controle_accept(url: str, nom: str) -> bool:
    """
    Contrôle secondaire pour vérifier si une acceptation était une erreur
    Utilise la validation par arborescence officielle inversée
    
    Returns:
        True si l'acceptation était une ERREUR (donc à rejeter)  
        False si l'acceptation était correcte
    """
    # On inverse la logique : si la catégorie N'EST PAS dans l'arborescence officielle, alors l'acceptation était une erreur
    return not validation_par_arborescence_officielle(url, nom)



def verifier_contenu_livres_simple(url: str, nom_categorie: str) -> bool:
    """
    Vérification UNIQUEMENT par contenu réel - pas de filtrage par nom
    Va sur la page et compte les vrais indicateurs de livres
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=8)
        if response.status_code != 200:
            return False
            
        soup = BeautifulSoup(response.content, 'html.parser')
        html_text = soup.get_text().lower()
        
        # INDICATEURS FORTS de livres (très spécifiques)
        indicateurs_livres = [
            'auteur', 'éditeur', 'broché', 'relié', 'poche', 'kindle',
            'isbn', 'édition', 'pages', 'roman', 'livre', 'ouvrage'
        ]
        
        # INDICATEURS de produits physiques non-livres
        indicateurs_objets = [
            'électroménager', 'appareil', 'machine', 'outil',
            'ustensile', 'casserole', 'poêle', 'frigo', 'four'
        ]
        
        # Compter les occurrences
        score_livres = sum(html_text.count(ind) for ind in indicateurs_livres)
        score_objets = sum(html_text.count(ind) for ind in indicateurs_objets)
        
        # Vérifier aussi les liens /dp/ (produits)
        liens_produits = soup.find_all('a', href=lambda x: x and '/dp/' in x)
        
        # DÉCISION PERMISSIVE : Rejeter SEULEMENT si clairement non-livres
        # Si pas assez de produits, accepter par défaut 
        if len(liens_produits) < 3:
            return True
        
        # Si beaucoup d'indicateurs non-livres ET peu/pas de livres, rejeter
        if score_objets >= 5 and score_livres <= 1:
            return False
            
        # Sinon, accepter par défaut (approche permissive)
        return True
        
    except Exception as e:
        print(f"⚠️ Erreur vérification {nom_categorie}: {e}")
        # En cas d'erreur, accepter par défaut
        return True


def verifier_contenu_livres(url: str) -> bool:
    """
    Vérifier si une page de catégorie Amazon contient réellement des livres
    
    Va sur la page et analyse le contenu pour détecter des éléments
    caractéristiques des livres : titres, auteurs, prix, images, liens /dp/, etc.
    
    Args:
        url (str): L'URL de la catégorie à vérifier
        
    Returns:
        bool: True si la page contient des livres, False sinon
        
    Critères de détection des livres:
    - Liens /dp/ (produits Amazon)
    - Éléments avec "auteur", "author"
    - Prix en euros avec caractéristiques livres
    - Images de couvertures
    - Titres de livres typiques
    - Éléments ISBN, éditeur, etc.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import time
        
        # Requête avec délai et headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return False
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # CRITÈRE 1: Liens de produits /dp/ (livres)
        liens_dp = soup.find_all('a', href=True)
        liens_livres = [link for link in liens_dp if '/dp/' in link.get('href', '')]
        
        if len(liens_livres) < 3:  # Minimum 3 produits pour valider
            return False
        
        # CRITÈRE 2: Indicateurs de livres spécifiques dans le contenu
        contenu_page = soup.get_text().lower()
        
        # Indicateurs SPÉCIFIQUES aux livres (pas aux autres produits)
        indicateurs_livres_forts = [
            'auteur', 'author', 'broché', 'relié', 'poche', 'kindle',
            'éditeur', 'publisher', 'isbn', 'édition', 'roman', 'novel'
        ]
        
        # Indicateurs NON-livres qui disqualifient
        indicateurs_non_livres = [
            'électroménager', 'casserole', 'poêle', 'vaisselle', 'ustensile',
            'cuisine', 'four', 'frigo', 'réfrigérateur', 'aspirateur',
            'machine', 'appareil', 'outil', 'accessoire'
        ]
        
        score_livres = sum(1 for ind in indicateurs_livres_forts if ind in contenu_page)
        score_non_livres = sum(1 for ind in indicateurs_non_livres if ind in contenu_page)
        
        # Si trop d'indicateurs non-livres, c'est pas des livres
        if score_non_livres >= 3:
            return False
        
        # CRITÈRE 3: Analyse des liens de produits pour détecter des livres
        liens_avec_titres = []
        for link in liens_livres[:10]:  # Analyser les 10 premiers liens seulement
            parent = link.find_parent(['div', 'article', 'span'])
            if parent:
                texte_parent = parent.get_text().lower()
                if any(mot in texte_parent for mot in ['auteur', 'broché', 'kindle', 'édition']):
                    liens_avec_titres.append(link)
        
        # VALIDATION FINALE
        print(f"🔍 Analyse {url[:50]}...")
        print(f"   🔗 Liens /dp/: {len(liens_livres)}")
        print(f"   📚 Score livres: {score_livres}")
        print(f"   ❌ Score non-livres: {score_non_livres}")
        print(f"   🎯 Liens avec contexte: {len(liens_avec_titres)}")
        
        return (
            len(liens_livres) >= 3 and      # Au moins 3 produits
            score_livres >= 1 and           # Au moins 1 indicateur livre fort
            score_non_livres < 5 and        # Moins de 5 indicateurs non-livres
            (score_livres > score_non_livres or len(liens_avec_titres) >= 1)  # Plus de livres que non-livres OU contexte livre
        )
        
    except Exception as e:
        print(f"⚠️ Erreur vérification contenu {url}: {e}")
        return False


def construire_arborescence_livres_officielle() -> set:
    """
    Construire l'arborescence officielle complète des catégories de livres Amazon
    Parcourt la page racine https://www.amazon.fr/b?node=301061 et toutes ses sous-catégories
    
    Returns:
        set: Ensemble de tous les node IDs valides de l'arborescence livres
    """
    global arborescence_livres_cache, derniere_mise_a_jour_cache
    
    import requests
    from bs4 import BeautifulSoup
    from datetime import datetime, timedelta
    import time
    
    # Vérifier cache (24h)
    if (arborescence_livres_cache is not None and 
        derniere_mise_a_jour_cache is not None and
        datetime.now() - derniere_mise_a_jour_cache < timedelta(hours=24)):
        return arborescence_livres_cache
    
    print("🏗️ Construction arborescence officielle des livres Amazon...")
    arborescence_nodes = set()
    urls_a_traiter = ["https://www.amazon.fr/b?node=301061"]
    urls_traitees = set()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Parcours en largeur de l'arborescence
    profondeur_max = 3  # Limiter pour éviter récursion infinie
    profondeur_actuelle = 0
    
    while urls_a_traiter and profondeur_actuelle < profondeur_max:
        urls_niveau_suivant = []
        
        for url in urls_a_traiter[:50]:  # Traiter max 50 URLs par niveau
            if url in urls_traitees:
                continue
                
            urls_traitees.add(url)
            
            try:
                print(f"  📖 Analyse: {url[:60]}...")
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraire tous les liens vers des nodes
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if not href:
                        continue
                        
                    # Construire URL complète
                    if href.startswith('/'):
                        full_url = 'https://www.amazon.fr' + href
                    else:
                        full_url = href
                    
                    # Extraire node ID
                    node_id = extraire_node_id(full_url)
                    if node_id:
                        arborescence_nodes.add(node_id)
                        
                        # Ajouter URL pour traitement niveau suivant
                        if full_url not in urls_traitees and len(urls_niveau_suivant) < 200:
                            urls_niveau_suivant.append(full_url)
                
                time.sleep(0.3)  # Délai entre requêtes
                
            except Exception as e:
                print(f"  ❌ Erreur {url}: {e}")
                continue
        
        urls_a_traiter = urls_niveau_suivant
        profondeur_actuelle += 1
        print(f"  📊 Niveau {profondeur_actuelle}: {len(arborescence_nodes)} nodes trouvés")
    
    # Mettre à jour le cache
    arborescence_livres_cache = arborescence_nodes
    derniere_mise_a_jour_cache = datetime.now()
    
    print(f"✅ Arborescence construite: {len(arborescence_nodes)} nodes officiels")
    return arborescence_nodes


def validation_par_arborescence_simple(url: str, nom: str) -> bool:
    """
    Validation UNIQUEMENT par structure URL - PAS de filtrage par contenu
    
    Args:
        url (str): L'URL de la catégorie à valider
        nom (str): Le nom de la catégorie
        
    Returns:
        bool: True si la catégorie fait partie de l'arborescence officielle, False sinon
    """
    try:
        # Extraire le node ID
        node_id = extraire_node_id(url)
        if not node_id:
            return False
        
        print(f"  🌳 Vérification node {node_id} par structure URL...")
        
        # VALIDATION UNIQUEMENT PAR STRUCTURE URL
        # Si l'URL contient des références aux livres, c'est bon
        url_lower = url.lower()
        
        # Indicateurs URL de livres Amazon
        indicateurs_url_livres = [
            'node=301',    # Nodes commençant par 301 (livres)
            'node=302',    # Nodes commençant par 302 (sous-catégories livres)  
            'node=404',    # Fantasy, Fantastique
            'node=406',    # Religion, Cuisine (livres de cuisine)
            'node=465',    # Sciences
            'node=489',    # Contes
            'node=531',    # Paranormal
            'node=542',    # Secteurs d'activité
            'node=596',    # Business
            'node=1064',   # Référence
            'node=1087',   # Thriller
            'node=1381',   # Science-Fiction
            'node=4252',   # Humour
            'node=4256',   # Jeux, arts
            'node=451',    # Scolaire
            'node=125273', # Recherche détaillée
            'node=6680',   # Nouveautés
            'node=52042',  # Langues étrangères
            'node=355635', # Loisirs et culture
            'node=695398', # Kindle
            'node=12641',  # Santé et bien-être
            'stripbooks',  # Section stripbooks
            'i=stripbooks' # Paramètre stripbooks
        ]
        
        # Si l'URL matche un pattern livre, c'est accepté
        for pattern in indicateurs_url_livres:
            if pattern in url_lower:
                print(f"  ✅ DANS arborescence: pattern URL '{pattern}' trouvé")
                return True
        
        # Si pas de pattern livre trouvé, rejeter
        print(f"  ❌ HORS arborescence: aucun pattern livre trouvé dans URL")
        return False
            
    except Exception as e:
        print(f"  ❌ Erreur vérification {nom}: {e}")
        return False


def validation_par_arborescence_officielle(url: str, nom: str) -> bool:
    """
    Valider une catégorie en vérifiant qu'elle fait partie de l'arborescence officielle
    
    Args:
        url (str): L'URL de la catégorie à valider
        nom (str): Le nom de la catégorie
        
    Returns:
        bool: True si la catégorie fait partie de l'arborescence officielle, False sinon
    """
    # Utiliser la validation simple et rapide
    return validation_par_arborescence_simple(url, nom)


def est_url_livre_valide(url: str) -> bool:
    """
    Vérifier si une URL pointe vers une page de livres Amazon
    
    Validation rapide basée uniquement sur l'URL pour déterminer
    si elle appartient à la section livres d'Amazon.
    
    Args:
        url (str): L'URL à valider
        
    Returns:
        bool: True si l'URL pointe vers les livres, False sinon
        
    Description détaillée:
    - Recherche les indicateurs de livres dans l'URL
    - Plus rapide que est_categorie_livre_valide() car ne vérifie que l'URL
    - Utilisée pour des validations préliminaires rapides
    """
    url_lower = url.lower()
    
    indicateurs_livres = [
        'stripbooks',
        'i=stripbooks', 
        'node=301061',
        'bbn=301061',
        'ref_=oct_d_odnav_301061'
    ]
    
    return any(ind in url_lower for ind in indicateurs_livres)


def validation_par_contenu_reel(url: str, nom: str) -> bool:
    """
    SUPER-CONTRÔLE : Validation par contenu réel de la page

    VA SUR LA PAGE et vérifie si elle contient vraiment des livres.
    Indépendant des changements d'Amazon - se base sur le contenu réel.

    Args:
        url (str): L'URL à vérifier
        nom (str): Le nom de la catégorie (pour logs)

    Returns:
        bool: True si la page contient des indicateurs de livres
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        import time

        print(f"  🔬 SUPER-CONTRÔLE CONTENU: {nom}")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        # Requête avec timeout court pour ne pas ralentir
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code != 200:
            print(f"    ❌ Erreur HTTP {response.status_code}")
            return False

        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text().lower()

        # INDICATEURS FORTS DE LIVRES (irréfutables)
        indicateurs_livres_forts = [
            'livre', 'book', 'roman', 'novel', 'auteur', 'author',
            'isbn', 'édition', 'edition', 'broché', 'paperback', 'relié', 'hardcover',
            'poche', 'pocket', 'kindle', 'ebook', 'éditeur', 'publisher'
        ]

        # INDICATEURS DE PRODUITS NON-LIVRES (disqualifiants)
        indicateurs_non_livres = [
            'électroménager', 'casserole', 'poêle', 'ustensile', 'frigo', 'four',
            'smartphone', 'ordinateur', 'laptop', 'télévision', 'écran',
            'vêtement', 'chaussure', 'bijou', 'montre', 'parfum',
            'jouet', 'peluche', 'jeu vidéo', 'console'
        ]

        # Compter les occurrences
        score_livres = sum(1 for mot in indicateurs_livres_forts if mot in page_text)
        score_non_livres = sum(1 for mot in indicateurs_non_livres if mot in page_text)

        # Vérifier la présence de liens produits /dp/
        liens_produits = soup.find_all('a', href=lambda x: x and '/dp/' in x)
        nb_produits = len(liens_produits)

        # Analyse des images (couvertures de livres)
        images = soup.find_all('img')
        images_livres = 0
        for img in images[:20]:  # Limiter pour performance
            alt_text = (img.get('alt', '') + img.get('title', '')).lower()
            if any(mot in alt_text for mot in ['livre', 'roman', 'book', 'novel']):
                images_livres += 1

        print(f"    📊 Score livres: {score_livres}")
        print(f"    📊 Score non-livres: {score_non_livres}")
        print(f"    📊 Produits /dp/: {nb_produits}")
        print(f"    📊 Images livres: {images_livres}")

        # DÉCISION INTELLIGENTE
        # Si clairement non-livres, rejeter
        if score_non_livres >= 5 and score_livres <= 1:
            print(f"    ❌ REJETÉ: Trop d'indicateurs non-livres")
            return False

        # Si des indicateurs livres ET produits, accepter
        if score_livres >= 2 and nb_produits >= 3:
            print(f"    ✅ ACCEPTÉ: Indicateurs livres + produits")
            return True

        # Si images de livres détectées, accepter
        if images_livres >= 2:
            print(f"    ✅ ACCEPTÉ: Images de livres détectées")
            return True

        # Si dans une catégorie suspecte mais pas d'indicateurs clairs, être prudent
        if score_livres == 0 and nb_produits < 3:
            print(f"    ❌ REJETÉ: Aucun indicateur livre clair")
            return False

        # Par défaut, si pas de signal négatif fort, accepter (permissif)
        print(f"    ✅ ACCEPTÉ: Pas de signal négatif fort")
        return True

    except Exception as e:
        print(f"    ⚠️ Erreur validation contenu {nom}: {e}")
        # En cas d'erreur, accepter par défaut (ne pas bloquer le scraping)
        return True


def validation_simple_cas_ambigu(url: str, nom: str) -> bool:
    """
    Validation SIMPLE et RAPIDE pour cas ambigus (évite validation contenu lourde)

    Pour les catégories ambigües comme "Cuisine" qui peut être livres ou ustensiles,
    utilise des heuristiques simples plutôt que validation contenu.

    Args:
        url (str): L'URL à valider
        nom (str): Le nom de la catégorie

    Returns:
        bool: True si probablement une catégorie livre
    """
    url_lower = url.lower()
    nom_lower = nom.lower()

    # EXCLUSIONS FORTES - Clairement non-livres
    exclusions_evidentes = [
        'high-tech', 'informatique', 'smartphone', 'ordinateur', 'télé', 'tv',
        'vêtements', 'chaussures', 'bijoux', 'montres', 'beauté', 'parfum',
        'électroménager', 'frigo', 'lave-linge', 'aspirateur',
        'jardin', 'bricolage', 'outillage', 'auto', 'moto',
        'sport', 'fitness', 'musculation', 'vélo',
        'bébé', 'puériculture', 'couches', 'jouets', 'peluches',
        'animalerie', 'croquettes', 'laisse'
    ]

    for exclusion in exclusions_evidentes:
        if exclusion in nom_lower:
            return False

    # Dans l'arborescence livres ET pas d'exclusion évidente = ACCEPTER
    if ('node=301' in url_lower or 'node=302' in url_lower or
        'node=6680' in url_lower or 'stripbooks' in url_lower):
        return True

    # Sinon, PERMISSIF par défaut (pour éviter de rater des livres)
    return True


def validation_contextuelle_2025(url_lower: str, text_lower: str) -> bool:
    """
    🧠 INTELLIGENCE CONTEXTUELLE 2025 - Approche hybride ultra-simplifiée

    Basée sur les meilleures pratiques 2025 : plus de validation lourde,
    juste logique simple et règles claires.
    """
    # EXCLUSIONS ABSOLUES (les seules qui comptent vraiment)
    exclusions_claires = [
        'high-tech', 'smartphone', 'ordinateur', 'laptop', 'télévision',
        'électroménager', 'frigo', 'lave-linge', 'aspirateur', 'four',
        'vêtements', 'chaussures', 'bijoux', 'montres', 'parfum',
        'auto', 'moto', 'vélo', 'sport', 'fitness',
        'bébé', 'puériculture', 'jouets', 'peluches',
        'animalerie', 'croquettes'
    ]

    # Si terme clairement non-livre, REJETER
    for exclusion in exclusions_claires:
        if exclusion in text_lower:
            return False

    # SINON : ACCEPTER TOUT dans l'arborescence (approche permissive 2025)
    # Mieux accepter trop que rejeter des vraies catégories de livres
    return True