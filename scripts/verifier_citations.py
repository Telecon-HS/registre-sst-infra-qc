"""Vérifie les citations normatives du registre contre l'index des procédures d'ANCRAGE.

    python scripts/verifier_citations.py
    python scripts/verifier_citations.py --strict      # code de sortie 1 s'il reste des réserves

L'index vient du dépôt Telecon-SST-Agents (ANCRAGE) : corpus/index-procedures.csv,
colonnes numero, titre, section, statut, page_manuel, niveau_confiance.
Il n'est pas recopié ici : le chemin se donne par la variable ANCRAGE_INDEX,
sinon ../Telecon-SST-Agents/corpus/index-procedures.csv.

Ce que le contrôle fait, et ne fait pas :
  - il dit si la procédure citée existe à l'index, et à quel niveau de confiance ;
  - il ne vérifie PAS le contenu d'une section. L'index ne descend pas à ce niveau.
    Une section reste donc à vérifier au manuel, comme les 18 et 19 septembre 2026.
Les préfixes SSE- et HSE- désignent la même procédure : seul le numéro compte.
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import DONNEES, lire_json  # noqa: E402

INDEX_DEFAUT = Path(__file__).resolve().parent.parent.parent / "Telecon-SST-Agents" / "corpus" / "index-procedures.csv"

# SSE-1801, HSE-1302, SSE.TEL-PRG-600, HSE-600-F01… : on retient le numéro de procédure
PROCEDURE = re.compile(r"\b(?:SSE|HSE)[.\-](?:TEL[.\-])?(?:[A-Z]{3}[.\-])?(\d{3,4})(?:\.\d+)?\b")
# ce qui ne vient pas du manuel Telecon et ne peut donc pas être vérifié ici
EXTERNE = re.compile(r"\b(CSTC|décret|RSST|LSST|LMRSST|RMPPE|CNESST|CSA|ISO|ASTM|ANSI|Altec|Hilti|Fluke)\b", re.I)


def index_procedures(chemin):
    chemin = Path(chemin)
    if not chemin.exists():
        sys.exit(f"Index introuvable : {chemin}\nDonnez son chemin avec --index ou la variable ANCRAGE_INDEX.")
    with open(chemin, encoding="utf-8-sig") as f:
        return {l["numero"].split("-")[-1]: l for l in csv.DictReader(f)}


def citations(texte):
    """Numéros de procédure cités dans un champ « norme », dans l'ordre d'apparition."""
    vus = []
    for m in PROCEDURE.finditer(texte or ""):
        if m.group(1) not in vus:
            vus.append(m.group(1))
    return vus


def verifier(index, risques):
    lignes = []
    for r in risques:
        norme = r.get("norme", "")
        numeros = citations(norme)
        if not numeros:
            etat = "hors index" if EXTERNE.search(norme) else "aucune procédure citée"
            lignes.append((r["ref"], "—", etat, norme[:70]))
            continue
        for n in numeros:
            entree = index.get(n)
            if entree is None:
                lignes.append((r["ref"], n, "ABSENTE DE L'INDEX", norme[:70]))
            else:
                lignes.append((r["ref"], f"{entree['numero']}", entree["niveau_confiance"], entree["titre"][:70]))
    return lignes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index", default=os.environ.get("ANCRAGE_INDEX", INDEX_DEFAUT))
    p.add_argument("--strict", action="store_true", help="code de sortie 1 si une citation est absente ou à valider")
    a = p.parse_args()

    index = index_procedures(a.index)
    risques = lire_json(DONNEES / "registre_html.json")["risques"]
    lignes = verifier(index, risques)

    compte = Counter(e for _, _, e, _ in lignes)
    a_revoir = [l for l in lignes if l[2] in ("ABSENTE DE L'INDEX", "a_valider", "partiel")]

    print(f"Citations vérifiées : {len(lignes)} sur {len(risques)} risques, index de {len(index)} procédures.\n")
    for etat, n in compte.most_common():
        print(f"  {n:3d}  {etat}")

    if a_revoir:
        print("\nÀ revoir avant publication :")
        for ref, num, etat, detail in a_revoir:
            print(f"  {ref:5s} {num:10s} {etat:20s} {detail}")

    print("\nRappel : l'index confirme l'existence d'une procédure et son niveau de confiance,")
    print("jamais le contenu d'une section. Les §  restent à vérifier au manuel.")

    if a.strict and a_revoir:
        sys.exit(1)


if __name__ == "__main__":
    main()
