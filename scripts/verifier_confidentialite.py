"""Contrôle à lancer avant chaque dépôt (commit) : aucune donnée privée dans le dépôt.

    python scripts/verifier_confidentialite.py

Vérifie tous les fichiers du dépôt, sauf sortie/ et prive/ (exclus par .gitignore) :
  - aucun nom de personne connu (si prive/noms.json est disponible) ;
  - aucun détail d'incident privé (lieux, lectures) ;
  - aucune photo, ni en fichier ni encodée dans un texte ;
  - aucun fichier d'export eCompliance ;
  - aucun fichier de plus de 1 Mo.
Code de sortie 1 si un problème est trouvé.
"""
import re
import sys

from commun import PRIVE, RACINE, lire_json

EXCLUS = {"sortie", "prive", ".git", "__pycache__"}
PERMIS_IMAGES = {RACINE / "gabarits" / "assets" / "logo_telecon.png"}
EXPORTS = re.compile(r"(Public_Inspections|Report_On_|dashboard-|\.csv$)", re.I)
JPEG_B64 = re.compile("/9j/" + "4AAQSkZJRg")  # en-tête JPEG encodé (écrit en deux morceaux pour ne pas se détecter)


def fichiers():
    for f in RACINE.rglob("*"):
        if f.is_file() and not (EXCLUS & set(f.relative_to(RACINE).parts)):
            yield f


def mots_interdits():
    mots = []
    if (PRIVE / "noms.json").exists():
        for graphies in lire_json(PRIVE / "noms.json")["variantes"].values():
            mots += graphies
    if (PRIVE / "incidents.json").exists():
        for inc in lire_json(PRIVE / "incidents.json").values():
            mots += [inc[k] for k in ("lieu", "lecture") if len(inc.get(k, "").strip()) > 8]
    return mots


def main():
    problemes = []
    mots = mots_interdits()
    for f in fichiers():
        rel = f.relative_to(RACINE)
        if f.stat().st_size > 1_000_000:
            problemes.append(f"{rel} : plus de 1 Mo")
        if EXPORTS.search(f.name):
            problemes.append(f"{rel} : ressemble à un export eCompliance")
        if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".heic", ".gif", ".webp"} and f not in PERMIS_IMAGES:
            problemes.append(f"{rel} : image hors des gabarits")
        try:
            texte = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if JPEG_B64.search(texte):
            problemes.append(f"{rel} : photo encodée dans le texte")
        for m in mots:
            if m in texte:
                problemes.append(f"{rel} : contient « {m[:40]} »")
    if not mots:
        print("Avertissement : dossier privé introuvable, les noms n'ont pas pu être vérifiés un par un.")
    if problemes:
        print("À CORRIGER AVANT LE DÉPÔT :")
        for p in problemes:
            print("  -", p)
        sys.exit(1)
    print(f"Confidentialité : aucun problème ({len(mots)} termes privés vérifiés).")


if __name__ == "__main__":
    main()
