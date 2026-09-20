"""Fonctions partagées par les générateurs.

Règle du dépôt : aucune donnée nominative ni aucune photo n'y est versée.
Les personnes y figurent sous forme de jetons ⟦P01⟧, ⟦P02⟧… Le détail des
incidents et les photos vivent dans un dossier privé, hors dépôt
(par défaut ../prive, ou le chemin donné par la variable REGISTRE_PRIVE).

Avec le dossier privé  : les livrables sont complets, noms et photos compris.
Sans le dossier privé  : les livrables sont produits sans noms (repli), sans
                         photos et sans le détail des incidents.
"""
import json
import os
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"
GABARITS = RACINE / "gabarits"
SORTIE = RACINE / "sortie"
PRIVE = Path(os.environ.get("REGISTRE_PRIVE", RACINE.parent / "prive")).resolve()

JETON = re.compile(r"⟦(P\d{2})(?:~(\d+))?⟧")  # ~n : n-ième graphie du nom dans les sources


def lire_json(chemin):
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def prive_disponible():
    return (PRIVE / "noms.json").exists()


def table_des_noms(avec_prive=True):
    """Jeton → texte à afficher : le nom (dans sa graphie d'origine) si le fichier
    privé est là, sinon le repli. Renvoie une fonction (jeton, graphie) → texte."""
    replis = {k: v["repli"] for k, v in lire_json(DONNEES / "personnes.json")["personnes"].items()}
    if avec_prive and prive_disponible():
        graphies = lire_json(PRIVE / "noms.json")["variantes"]
        return lambda j, n: graphies[j][n] if j in graphies else replis.get(j, "[nom retiré]")
    return lambda j, n: replis.get(j, "[nom retiré]")


def remplacer_jetons(obj, table):
    """Remplace récursivement les jetons dans chaînes, listes et dictionnaires."""
    if isinstance(obj, str):
        return JETON.sub(lambda m: table(m.group(1), int(m.group(2) or 0)), obj)
    if isinstance(obj, list):
        return [remplacer_jetons(x, table) for x in obj]
    if isinstance(obj, dict):
        return {k: remplacer_jetons(v, table) for k, v in obj.items()}
    return obj


def incidents_prives():
    """Détail des incidents (type, lieu, personnes, lecture), indexé par Id. {} si absent."""
    f = PRIVE / "incidents.json"
    return lire_json(f) if f.exists() else {}


def mode():
    return "complet (dossier privé trouvé)" if prive_disponible() else "sans données privées"
