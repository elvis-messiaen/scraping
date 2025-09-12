#!/usr/bin/env python3
"""
TEST DU LANCEUR MULTI - Mode test avec 3 scrapers seulement
"""

import multiprocessing as mp
from lanceur_multi import LanceurMulti

if __name__ == "__main__":
    # Configuration multiprocessing
    mp.set_start_method('spawn', force=True)
    
    # Lancer en mode test
    lanceur = LanceurMulti(mode_test=True)
    lanceur.run()