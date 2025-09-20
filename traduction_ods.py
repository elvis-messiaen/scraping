#!/usr/bin/env python3
"""
TRADUCTION FICHIER ODS - RAIDER 3 YEAR ANNIVERSARY PROGRAMS
==========================================================
Traduit le fichier .ods de l'anglais vers le français
"""

import pandas as pd
import os

def traductions_musculation():
    """
    Dictionnaire COMPLET de traductions musculation anglais -> français
    """
    return {
        # Exercices principaux
        "Bench": "Développé couché",
        "Bench Press": "Développé couché",
        "Deadlift": "Soulevé de terre",
        "Squat": "Squat",
        "OHP": "Développé militaire",
        "Overhead Press": "Développé militaire",
        "Press": "Développé",
        "Pull": "Traction",
        "Push": "Poussée",
        "Row": "Tirage",
        "Curl": "Curl",
        "Dip": "Dips",
        "Dips": "Dips",

        # Termes d'entraînement
        "Set": "Série",
        "Sets": "Séries",
        "Rep": "Répétition",
        "Reps": "Répétitions",
        "Weight": "Poids",
        "Load": "Charge",
        "Program": "Programme",
        "Training": "Entraînement",
        "Workout": "Séance",
        "Exercise": "Exercice",

        # Temps
        "Week": "Semaine",
        "Weeks": "Semaines",
        "Day": "Jour",
        "Days": "Jours",
        "Year": "Année",
        "Anniversary": "Anniversaire",

        # Instructions
        "Read": "Lire",
        "Follow": "Suivre",
        "Complete": "Terminer",
        "Start": "Commencer",
        "Finish": "Finir",
        "Continue": "Continuer",
        "Perform": "Effectuer",

        # Niveaux
        "Beginner": "Débutant",
        "Intermediate": "Intermédiaire",
        "Advanced": "Avancé",

        # Progression
        "Progression": "Progression",
        "Progress": "Progrès",
        "Strength": "Force",
        "Power": "Puissance",
        "Hypertrophy": "Hypertrophie",
        "Endurance": "Endurance",

        # Termes spécifiques
        "Guidelines": "Directives",
        "Instructions": "Instructions",
        "Notes": "Notes",
        "Important": "Important",
        "Form": "Technique",
        "Failure": "Échec",
        "Rest": "Repos",
        "Recovery": "Récupération",

        # Expressions courantes
        "Happy": "Joyeux",
        "New": "Nouveau",
        "Original": "Original",
        "Better": "Meilleur",
        "Good": "Bon",
        "Great": "Excellent",
        "Easy": "Facile",
        "Hard": "Difficile",
        "Heavy": "Lourd",
        "Light": "Léger",

        # AJOUTS MASSIFS POUR 100%
        "Welcome": "Bienvenue",
        "Thank": "Merci",
        "you": "vous",
        "for": "pour",
        "checking": "vérifier",
        "this": "ceci",
        "out": "dehors",
        "There": "Il y a",
        "are": "sont",
        "versions": "versions",
        "of": "de",
        "the": "le",
        "to": "à",
        "enjoy": "profiter",
        "pick": "choisir",
        "version": "version",
        "that": "qui",
        "fits": "convient",
        "best": "mieux",
        "For": "Pour",
        "frequently": "fréquemment",
        "asked": "demandées",
        "questions": "questions",
        "refer": "référer",
        "document": "document",
        "click": "cliquer",
        "link": "lien",
        "view": "voir",
        "as": "comme",
        "well": "bien",
        "documentation": "documentation",
        "below": "ci-dessous",
        "left": "gauche",
        "over": "sur",
        "from": "de",
        "kept": "gardé",
        "it": "il",
        "in": "dans",
        "there": "là",
        "legacy": "héritage",
        "reasons": "raisons",
        "sheet": "feuille",
        "is": "est",
        "pre": "pré",
        "programmed": "programmé",
        "with": "avec",
        "all": "tous",
        "equations": "équations",
        "need": "besoin",
        "Simply": "Simplement",
        "input": "saisir",
        "where": "où",
        "tells": "dit",
        "delete": "supprimer",
        "ENTIRE": "ENTIÈRE",
        "cell": "cellule",
        "and": "et",
        "then": "puis",
        "replace": "remplacer",
        "number": "nombre",
        "spreadsheet": "tableur",
        "auto": "auto",
        "populate": "remplir",
        "afterwards": "après",
        "EXAMPLE": "EXEMPLE",
        "HERE": "ICI",
        "watch": "regarder",
        "video": "vidéo",
        "If": "Si",
        "want": "voulez",
        "add": "ajouter",
        "volume": "volume",
        "bodybuilding": "culturisme",
        "portion": "partie",
        "AS": "COMME",
        "NEEDED": "NÉCESSAIRE",
        "not": "pas",
        "WANTED": "VOULU",
        "Before": "Avant",
        "adding": "ajouter",
        "ensure": "assurer",
        "doing": "faire",
        "HIGH": "HAUTE",
        "quality": "qualité",
        "first": "premier",
        "Aim": "Viser",
        "accurately": "précisément",
        "match": "correspondre",
        "reserve": "réserve",
        "were": "étaient",
        "supposed": "supposé",
        "hit": "frapper",
        "Record": "Enregistrer",
        "each": "chaque",
        "your": "votre",
        "lifts": "mouvements",
        "Being": "Être",
        "off": "décalé",
        "rep": "répétition",
        "FINE": "BIEN",
        "but": "mais",
        "being": "être",
        "isn't": "n'est pas",
        "set": "série",
        "was": "était",
        "too": "trop",
        "easy": "facile",
        "rest": "repos",
        "try": "essayer",
        "again": "encore",
        "back": "retour",
        "automatically": "automatiquement",
        "calculated": "calculé",
        "on": "sur",
        "Dynamic": "Dynamique",
        "Double": "Double",
        "Progression": "Progression",
        "link": "lien",
        "if": "si",
        "familiar": "familier",
        "used": "utilisé",
        "exercises": "exercices",
        "Effort": "Effort",
        "name": "nom",
        "game": "jeu",
        "here": "ici",
        "When": "Quand",
        "reach": "atteindre",
        "top": "haut",
        "end": "fin",
        "range": "gamme",
        "repeat": "répéter",
        "same": "même",
        "The": "Le",
        "get": "obtenir",
        "huge": "énorme",
        "driver": "moteur",
        "progress": "progrès",
        "so": "donc",
        "put": "mettre",
        "foot": "pied",
        "forward": "avant",
        "Follow": "Suivre",
        "progressions": "progressions",
        "otherwise": "autrement",
        "detailed": "détaillé",
        "Enter": "Entrer",
        "rep": "répétition",
        "maxes": "maximums",
        "main": "principal",
        "lifts": "mouvements",
        "https": "https",
        "com": "com",
        "one": "un",
        "max": "max",
        "calculator": "calculateur",
        "use": "utiliser",
        "estimated": "estimé",
        "calculate": "calculer",
        "percentages": "pourcentages",
        "most": "plus",
        "accurate": "précis",
        "at": "à",
        "predicting": "prédire",
        "don't": "ne pas",
        "know": "savoir",
        "what": "quoi",
        "rm": "rm",
        "test": "tester",
        "We": "Nous",
        "won't": "ne serons pas",
        "be": "être",
        "peaking": "culminer",
        "we're": "nous sommes",
        "just": "juste",
        "using": "utiliser",
        "data": "données",
        "point": "point",
        "more": "plus",
        "than": "que",
        "unlikely": "improbable",
        "followed": "suivi",
        "minutes": "minutes",
        "lbs": "livres",
        "every": "chaque",
        "above": "au-dessus",
        "performed": "effectué",
        "ex": "ex",
        "did": "fait",
        "pounds": "livres",
        "Hit": "Frapper",
        "s": "s",
        "NOTE": "NOTE",
        "Test": "Tester",
        "variation": "variation",
        "press": "développé",
        "already": "déjà",
        "Use": "Utiliser",
        "this": "ce",
        "number": "nombre",
        "program": "programmer",
        "next": "prochain",
        "couple": "couple",
        "months": "mois",
        "training": "entraînement",
        "Choice": "Choix",
        "controlled": "contrôlé",
        "eccentric": "excentrique",
        "Vertical": "Vertical",
        "Of": "De",
        "Horizontal": "Horizontal",
        "Full": "Complet",
        "You'll": "Vous allez",
        "work": "travailler",
        "muscle": "muscle",
        "Tricep": "Triceps",
        "Extension": "Extension",
        "or": "ou",
        "Pressdown": "Développé vers le bas",
        "choice": "choix",
        "Supinated": "Supination",
        "Bicep": "Biceps",
        "can": "pouvez",
        "superset": "superset",
        "Calisthenics": "Calisthénie",
        "Chest": "Poitrine",
        "Conventional": "Conventionnel",
        "Sumo": "Sumo",
        "Trap": "Trap",
        "Bar": "Barre",
        "limit": "limiter",
        "re": "re",
        "Unilateral": "Unilatéral",
        "Quad": "Quadriceps",
        "Incline": "Incliné",
        "OR": "OU",
        "Hammer": "Marteau",
        "pick": "choisir",
        "ext": "etc",
        "leg": "jambe",
        "Main": "Principal",
        "Percentages": "Pourcentages",
        "Flat": "Plat",
        "while": "pendant",
        "trying": "essayer",
        "keep": "garder",
        "tank": "réservoir",
        "Shoulder": "Épaule",
        "Pressing": "Pression",
        "Movement": "Mouvement",
        "machines": "machines",
        "rec": "rec",
        "around": "autour",
        "Isolation": "Isolation",
        "Pick": "Choisir",
        "Variation": "Variation",
        "Here": "Ici",
        "related": "lié",
        "Upper": "Supérieur",
        "different": "différent",
        "optionally": "optionnellement",
        "do": "faire",
        "Select": "Sélectionner",
        "muscles": "muscles",
        "Supported": "Supporté",
        "Back": "Dos",
        "superset": "superset",
        "one": "un",
        "these": "ces",
        "movements": "mouvements",
        "Finisher": "Finisseur",
        "dumbbells": "haltères",
        "calisthenics": "calisthénie",
        "PR": "RP",
        "Scoreboard": "Tableau de bord",

        # Phrases spécifiques observées
        "EACH COLUMN IS A NEW WEEK": "CHAQUE COLONNE EST UNE NOUVELLE SEMAINE",
        "full training cycle is 12 weeks": "cycle d'entraînement complet est de 12 semaines",
        "a full training cycle is 12 weeks": "un cycle d'entraînement complet est de 12 semaines"
    }

def traduire_fichier_ods():
    """
    Traduit le fichier .ods de Raider en français
    """
    print("TRADUCTION FICHIER ODS - RAIDER")
    print("=" * 40)

    fichier_ods = "/Users/Simplon/Cours/workspacePython/Scraping/ Raider 3 Year Anniversary Programs.ods"

    if not os.path.exists(fichier_ods):
        print("ÉCHEC: Fichier .ods introuvable")
        return False

    try:
        # Charger les traductions
        traductions = traductions_musculation()
        print(f"Traductions chargées: {len(traductions)}")

        # Lire le fichier .ods avec pandas
        excel_data = pd.read_excel(fichier_ods, sheet_name=None, engine='odf')
        print(f"Feuilles lues: {len(excel_data)}")

        modifications_totales = 0

        # Traiter chaque feuille
        with pd.ExcelWriter(fichier_ods, engine='odf') as writer:
            for nom_feuille, df in excel_data.items():
                print(f"\nTraitement feuille: {nom_feuille}")
                df_modifie = df.copy()
                modifications_feuille = 0

                # Traduire cellule par cellule
                for i in range(len(df_modifie)):
                    for col in df_modifie.columns:
                        valeur = df_modifie.iloc[i, df_modifie.columns.get_loc(col)]

                        if pd.notna(valeur) and isinstance(valeur, str):
                            valeur_originale = valeur

                            # Appliquer les traductions
                            for anglais, francais in traductions.items():
                                if anglais in valeur:
                                    valeur = valeur.replace(anglais, francais)

                            if valeur != valeur_originale:
                                df_modifie.iloc[i, df_modifie.columns.get_loc(col)] = valeur
                                modifications_feuille += 1
                                modifications_totales += 1
                                print(f"  Modifié: '{valeur_originale[:50]}...' -> '{valeur[:50]}...'")

                print(f"  {modifications_feuille} modifications dans cette feuille")
                df_modifie.to_excel(writer, sheet_name=nom_feuille, index=False)

        if modifications_totales > 0:
            print(f"\nSUCCÈS: {modifications_totales} modifications réelles effectuées")
            return True
        else:
            print("\nÉCHEC: Aucune modification effectuée")
            return False

    except Exception as e:
        print(f"ÉCHEC: Erreur - {e}")
        return False

if __name__ == "__main__":
    traduire_fichier_ods()