"""Régénère les trois livrables, puis vérifie la confidentialité du dépôt.

    python scripts/tout_generer.py                 → livrables complets (avec le dossier privé)
    python scripts/tout_generer.py --sans-prive    → livrables sans noms, sans photos, sans détail d'incidents

Les livrables sont écrits dans sortie/ (jamais versé au dépôt).
"""
import sys

import generer_classeur
import generer_page
import generer_plan_action
import generer_tableau_bord
import generer_presentation
import verifier_confidentialite
from commun import mode, prive_disponible

avec_prive = "--sans-prive" not in sys.argv
print(f"Mode : {mode() if avec_prive else 'sans données privées (demandé)'}")
if avec_prive and not prive_disponible():
    print("Dossier privé introuvable : livrables produits sans noms ni photos.")
generer_classeur.generer(avec_prive)
generer_page.generer(avec_prive)
generer_page.generer_terrain()
generer_plan_action.generer(avec_prive)
generer_tableau_bord.generer(avec_prive)
generer_presentation.generer()
verifier_confidentialite.main()
