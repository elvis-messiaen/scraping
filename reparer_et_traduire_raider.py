#!/usr/bin/env python3
"""
RÉPARATION ET TRADUCTION DU FICHIER RAIDER ORIGINAL
==================================================
Modifie directement le fichier original sans en créer de nouveaux
"""

import pandas as pd
import os
import re
from typing import Dict

def traductions_essentielles() -> Dict[str, str]:
    """
    Traductions essentielles et simples pour éviter la corruption
    """
    return {
        # Termes de base musculation
        "Bench": "Développé couché",
        "Deadlift": "Soulevé de terre",
        "Squat": "Squat",
        "OHP": "Développé militaire",
        "Sets": "Séries",
        "Reps": "Répétitions",
        "Week": "Semaine",
        "Weeks": "Semaines",
        "Program": "Programme",
        "Training": "Entraînement",
        "Progression": "Progression",
        "Recovery": "Récupération",
        "Strength": "Force",
        "Weight": "Poids",

        # Instructions de base
        "Read": "Lire",
        "Follow": "Suivre",
        "Complete": "Terminer",
        "Start": "Commencer",
        "Finish": "Finir",

        # Niveaux
        "Beginner": "Débutant",
        "Intermediate": "Intermédiaire",
        "Advanced": "Avancé",

        # Temps
        "Day": "Jour",
        "Days": "Jours",
        "Year": "Année",
        "Anniversary": "Anniversaire",

        # Expressions courantes
        "Happy": "Joyeux",
        "New": "Nouveau",
        "Original": "Original",
        "Better": "Meilleur",
        "Good": "Bon",
        "Great": "Excellent"
    }

def reparer_et_traduire_original():
    """
    Répare et traduit le fichier original directement
    """
    print("🔧 RÉPARATION ET TRADUCTION DU FICHIER ORIGINAL")
    print("=" * 50)

    fichier_original = "/Users/Simplon/Cours/workspacePython/Scraping/ Raider 3 Year Anniversary Programs.xlsx"

    if not os.path.exists(fichier_original):
        print(f"❌ Fichier introuvable: {fichier_original}")
        return

    # Faire une sauvegarde d'abord
    fichier_backup = "/Users/Simplon/Cours/workspacePython/Scraping/Raider_BACKUP.xlsx"
    import shutil
    shutil.copy2(fichier_original, fichier_backup)
    print(f"💾 Sauvegarde créée: {os.path.basename(fichier_backup)}")

    try:
        # Charger les traductions simples
        traductions = traductions_essentielles()
        print(f"📚 {len(traductions)} traductions chargées")

        # Lire le fichier avec des paramètres sûrs
        excel_data = pd.read_excel(fichier_original, sheet_name=None, engine='openpyxl')
        print(f"📋 {len(excel_data)} feuilles lues")

        # Créer un nouvel Excel Writer avec des paramètres sûrs
        with pd.ExcelWriter(fichier_original, engine='openpyxl', mode='w') as writer:
            for nom_feuille, df in excel_data.items():
                print(f"\n🔄 Traitement: {nom_feuille}")

                # Faire une copie simple
                df_modifie = df.copy()

                # Traduire seulement le contenu des cellules (pas les noms de colonnes/feuilles)
                cellules_traduites = 0
                for i, row in df_modifie.iterrows():
                    for col in df_modifie.columns:
                        valeur = df_modifie.at[i, col]
                        if pd.notna(valeur) and isinstance(valeur, str):
                            valeur_traduite = valeur
                            for anglais, francais in traductions.items():
                                # Remplacement simple mot par mot
                                if anglais.lower() in valeur.lower():
                                    valeur_traduite = valeur_traduite.replace(anglais, francais)
                                    valeur_traduite = valeur_traduite.replace(anglais.lower(), francais)
                                    valeur_traduite = valeur_traduite.replace(anglais.upper(), francais.upper())

                            if valeur_traduite != valeur:
                                df_modifie.at[i, col] = valeur_traduite
                                cellules_traduites += 1

                print(f"   ✅ {cellules_traduites} cellules traduites")

                # Sauvegarder avec le nom original
                df_modifie.to_excel(writer, sheet_name=nom_feuille, index=False)

        print(f"\n🎉 FICHIER ORIGINAL MODIFIÉ AVEC SUCCÈS!")
        print(f"📁 Fichier: {os.path.basename(fichier_original)}")
        print(f"💾 Sauvegarde disponible: {os.path.basename(fichier_backup)}")

    except Exception as e:
        print(f"❌ Erreur: {e}")
        # Restaurer la sauvegarde en cas d'erreur
        shutil.copy2(fichier_backup, fichier_original)
        print("🔄 Fichier original restauré depuis la sauvegarde")

if __name__ == "__main__":
    reparer_et_traduire_original()