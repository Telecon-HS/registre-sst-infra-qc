#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrôle des constats proposés par un agent de lecture de photos.

À lancer avant chaque dépôt, comme verifier_confidentialite.py et
verifier_citations.py :

    python scripts/verifier_constats.py rapports/constats_2026-09-09.json

Le contrôle ne corrige pas les constats : il rétrograde ceux qui affirment
plus que la preuve ne permet, en inscrit le motif au journal du constat, et
écrit un rapport daté. Il ne porte aucun verdict de conformité.

Sortie : rapports/rapport_constats_AAAA-MM-JJ.md
Code de retour : 1 si au moins un manquement bloquant subsiste.

Les trois premières règles viennent d'erreurs mesurées sur le dossier
Grenache du 9 septembre 2026. Voir docs/DOCTRINE_REGARD.md.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

# --- vocabulaire des règles ------------------------------------------------

DISPOSITIFS = [
    "cadenas", "sangle", "chaîne", "chaine", "plaque", "garde-corps",
    "extincteur", "protecteur", "support", "ancrage", "goupille",
    "marquage", "signalisation", "bac de rétention", "retenue",
]

MOTS_ABSENCE = [
    "absent", "absence", "aucun", "aucune", "sans ", "non cadenass",
    "non retenu", "non attach", "manquant", "dépourvu", "depourvu",
]

MOTS_EXPOSITION = [
    "toujours", "souvent", "chaque matin", "chaque jour", "fréquemment",
    "frequemment", "habituellement", "régulièrement", "regulierement",
    "en permanence", "tous les jours", "au quotidien",
]

# nombre suivi d'une unité : 2,6 m · 3 mm · 10 km/h · 1350 lb · 3 niveaux
MESURE = re.compile(
    r"\d+(?:[.,]\d+)?\s?(?:mm|cm|m\b|po\b|pi\b|kg|lb|lbs|km/h|niveaux?|étages?|etages?)",
    re.IGNORECASE,
)

BLOQUANT = "bloquant"
AVERTISSEMENT = "avertissement"


def _texte(constat: dict) -> str:
    return (constat.get("enonce") or "").lower()


def _photo(index: dict, pid: str) -> dict:
    return index.get(pid, {})


# --- règles ----------------------------------------------------------------

def regle_absence_sans_preuve(constat: dict, index: dict) -> list[tuple[str, str]]:
    """R1. Ne jamais conclure à l'absence d'un dispositif qu'on ne voit pas.

    Un constat d'absence exige au moins une photo dont
    visibilite_zone_critique est vrai : une photo qui montre, dégagée et
    nette, la place où le dispositif devrait être.
    """
    texte = _texte(constat)
    affirme = bool(constat.get("affirme_absence"))
    if not affirme:
        # filet : l'énoncé affirme une absence sans que le champ soit posé
        if any(m in texte for m in MOTS_ABSENCE) and any(d in texte for d in DISPOSITIFS):
            affirme = True
            constat["affirme_absence"] = True
    if not affirme:
        return []

    manquements = []
    if not constat.get("dispositif_absent"):
        manquements.append((AVERTISSEMENT, "Absence affirmée sans nommer le dispositif."))

    preuve = [p for p in constat.get("photos", [])
              if _photo(index, p).get("visibilite_zone_critique") is True]
    if not preuve:
        constat["statut"] = "a_verifier"
        manquements.append((
            BLOQUANT,
            "Absence affirmée sans photo montrant l'endroit où le dispositif "
            "devrait se trouver. Statut rétrogradé en « à vérifier ».",
        ))
    return manquements


def regle_photo_unique(constat: dict, index: dict) -> list[tuple[str, str]]:
    """R2. Un constat non conforme reposant sur une seule photo est fragile."""
    if constat.get("statut") != "non_conforme":
        return []
    if len(constat.get("photos", [])) <= 1 and "note_vocale" not in constat.get("source", []):
        constat["fragile"] = True
        return [(AVERTISSEMENT,
                 "Constat non conforme reposant sur une seule photo : à confirmer sur place.")]
    return []


def regle_mesure_lue(constat: dict, index: dict) -> list[tuple[str, str]]:
    """R3. Une mesure ne se lit pas sur une photo."""
    trouvee = MESURE.search(constat.get("enonce") or "")
    if not trouvee:
        return []
    sources = set(constat.get("source", []))
    if sources <= {"photo"}:
        constat["statut"] = "a_verifier"
        return [(BLOQUANT,
                 f"Mesure « {trouvee.group(0)} » tirée d'une photo seule. "
                 "Statut rétrogradé en « à vérifier ».")]
    return []


def regle_exposition(constat: dict, index: dict) -> list[tuple[str, str]]:
    """R4. L'exposition ne se photographie pas."""
    texte = _texte(constat)
    mot = next((m for m in MOTS_EXPOSITION if m in texte), None)
    if not mot:
        return []
    sources = set(constat.get("source", []))
    if sources <= {"photo"}:
        constat["statut"] = "a_verifier"
        return [(BLOQUANT,
                 f"Fréquence ou habitude (« {mot.strip()} ») affirmée à partir d'une photo seule. "
                 "Une note vocale ou une entrevue est nécessaire. Statut rétrogradé.")]
    return []


def regle_conformite_humaine(constat: dict, index: dict) -> list[tuple[str, str]]:
    """R5. La machine ne déclare jamais la conformité."""
    if constat.get("statut") == "conforme" and not constat.get("validation_humaine"):
        constat["statut"] = "a_verifier"
        return [(BLOQUANT,
                 "Statut « conforme » sans validation humaine. Rétrogradé en « à vérifier ».")]
    return []


def regle_preuve_minimale(constat: dict, index: dict) -> list[tuple[str, str]]:
    """R6. Un constat non conforme cite au moins une source."""
    if constat.get("statut") != "non_conforme":
        return []
    if not constat.get("photos") and "note_vocale" not in constat.get("source", []):
        return [(BLOQUANT, "Constat non conforme sans photo ni note vocale citée.")]
    return []


def regle_renseignement_personnel(constat: dict, index: dict) -> list[tuple[str, str]]:
    """R7. Une photo porteuse de renseignements personnels relève du dossier privé."""
    touchees = [p for p in constat.get("photos", [])
                if _photo(index, p).get("renseignement_personnel") is True]
    if touchees:
        return [(AVERTISSEMENT,
                 "Photos citées portant un renseignement personnel : "
                 + ", ".join(touchees) + ". Masquage et dossier privé à vérifier.")]
    return []


def regle_angles_morts(constat: dict, index: dict) -> list[tuple[str, str]]:
    """R8. Le sol et le passage sont les deux angles morts connus."""
    photos = [_photo(index, p) for p in constat.get("photos", [])]
    if not photos:
        return []
    if not any(p.get("sol_examine") for p in photos) and not any(p.get("passage_examine") for p in photos):
        return [(AVERTISSEMENT,
                 "Aucune photo de ce constat ne déclare avoir examiné le sol ni le passage.")]
    return []


REGLES = [
    regle_absence_sans_preuve,
    regle_mesure_lue,
    regle_exposition,
    regle_conformite_humaine,
    regle_preuve_minimale,
    regle_photo_unique,
    regle_renseignement_personnel,
    regle_angles_morts,
]


# --- contrôle --------------------------------------------------------------

def verifier(constats: list[dict], photos: list[dict]) -> list[dict]:
    """Applique les règles. Modifie les constats en place, renvoie les manquements."""
    index = {p.get("id"): p for p in photos}
    aujourdhui = dt.date.today().isoformat()
    manquements = []
    for constat in constats:
        for regle in REGLES:
            for gravite, message in regle(constat, index):
                manquements.append({
                    "constat": constat.get("id"),
                    "regle": regle.__name__,
                    "gravite": gravite,
                    "message": message,
                })
                constat.setdefault("journal", []).append(f"{aujourdhui} · {message}")
    return manquements


def rapport(manquements: list[dict], constats: list[dict], photos: list[dict]) -> str:
    bloquants = [m for m in manquements if m["gravite"] == BLOQUANT]
    avertissements = [m for m in manquements if m["gravite"] == AVERTISSEMENT]
    lignes = [
        f"# Contrôle des constats — {dt.date.today().isoformat()}",
        "",
        f"{len(constats)} constats · {len(photos)} photos indexées · "
        f"{len(bloquants)} manquements bloquants · {len(avertissements)} avertissements",
        "",
        "Ce rapport ne porte aucun verdict de conformité. Il vérifie que chaque",
        "constat n'affirme pas plus que sa preuve ne permet.",
        "",
    ]
    for titre, lot in (("Manquements bloquants", bloquants), ("Avertissements", avertissements)):
        lignes += [f"## {titre}", ""]
        if not lot:
            lignes += ["Aucun.", ""]
            continue
        lignes += ["| Constat | Règle | Motif |", "|---|---|---|"]
        for m in lot:
            lignes.append(f"| {m['constat']} | {m['regle'].replace('regle_', '')} | {m['message']} |")
        lignes.append("")
    retro = [c for c in constats if c.get("statut") == "a_verifier"
             and any("Rétrogradé" in j or "rétrogradé" in j for j in c.get("journal", []))]
    lignes += [
        "## Constats rétrogradés en « à vérifier »", "",
        ("Aucun." if not retro else "\n".join(f"- {c['id']} — {c['enonce'][:110]}" for c in retro)),
        "",
        "## Rappel", "",
        "Aucun constat de ce lot n'entre au registre sans validation humaine et sans source.",
    ]
    return "\n".join(lignes) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Contrôle des constats proposés par l'agent.")
    ap.add_argument("constats", type=Path, help="JSON des constats proposés")
    ap.add_argument("--photos", type=Path, default=None, help="JSON de l'index des photos")
    ap.add_argument("--sortie", type=Path, default=Path("rapports"))
    ap.add_argument("--ecrire", action="store_true",
                    help="réécrire le fichier de constats avec les rétrogradations et le journal")
    args = ap.parse_args()

    constats = json.loads(args.constats.read_text(encoding="utf-8"))
    photos = json.loads(args.photos.read_text(encoding="utf-8")) if args.photos else []
    if isinstance(constats, dict):
        constats = constats.get("constats", [])
    if isinstance(photos, dict):
        photos = photos.get("photos", [])

    manquements = verifier(constats, photos)

    args.sortie.mkdir(parents=True, exist_ok=True)
    chemin = args.sortie / f"rapport_constats_{dt.date.today().isoformat()}.md"
    chemin.write_text(rapport(manquements, constats, photos), encoding="utf-8")
    print(f"Rapport écrit : {chemin}")

    if args.ecrire:
        args.constats.write_text(
            json.dumps(constats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Constats mis à jour : {args.constats}")

    bloquants = [m for m in manquements if m["gravite"] == BLOQUANT]
    for m in bloquants:
        print(f"BLOQUANT · {m['constat']} · {m['message']}")
    return 1 if bloquants else 0


if __name__ == "__main__":
    sys.exit(main())
