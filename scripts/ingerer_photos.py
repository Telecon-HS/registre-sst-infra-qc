#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ingestion d'un dossier de photos de visite.

    python scripts/ingerer_photos.py /chemin/vers/photos --lieu INF-QC-ANJOU-COUR

Comme ingerer_exports.py : le script lit, il rapporte, il n'écrit jamais dans
donnees/ et ne porte aucun verdict. Ce qu'il faut retenir s'inscrit au
registre à la main, sourcé.

Aucune image n'est copiée dans le dépôt. Le script ne produit que :

    rapports/rapport_photos_AAAA-MM-JJ.md     lecture humaine
    rapports/index_photos_AAAA-MM-JJ.json     index conforme à
                                              donnees/schemas/photo.schema.json

L'index sert d'entrée à l'agent de lecture, et de preuve : chaque photo y
porte son empreinte SHA-256.

Options utiles :
    --reduire DOSSIER   écrit hors du dépôt des copies sous 5 Mo des photos
                        trop lourdes, sans toucher aux originaux
    --coupure 240       secondes séparant deux séquences de prise de vue
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

try:
    from PIL import Image, ExifTags
except ImportError:  # Pillow figure déjà dans requirements.txt
    Image = None

EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic"}
LIMITE_LECTURE = 5 * 1024 * 1024  # au-delà, la photo n'est pas lisible par l'agent
HORODATAGE_NOM = re.compile(r"(\d{8})[_-](\d{6})")


def empreinte(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def horodatage(chemin: Path) -> tuple[str | None, str]:
    """Renvoie (horodatage ISO, source). L'EXIF prime sur le nom de fichier."""
    if Image is not None:
        try:
            with Image.open(chemin) as im:
                exif = im.getexif() or {}
            tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
            brut = tags.get("DateTimeOriginal") or tags.get("DateTime")
            if brut:
                d = dt.datetime.strptime(str(brut), "%Y:%m:%d %H:%M:%S")
                return d.isoformat(), "exif"
        except Exception:
            pass
    m = HORODATAGE_NOM.search(chemin.name)
    if m:
        d = dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
        return d.isoformat(), "nom_fichier"
    return None, "nom_fichier"


def sequencer(photos: list[dict], coupure: int) -> None:
    """Regroupe les photos en séquences de prise de vue. Le temps fait le
    travail que le contenu ferait mal : une coupure de plusieurs minutes
    sépare presque toujours deux zones."""
    datees = sorted((p for p in photos if p["pris_le"]), key=lambda p: p["pris_le"])
    numero, precedent = 1, None
    for p in datees:
        courant = dt.datetime.fromisoformat(p["pris_le"])
        if precedent and (courant - precedent).total_seconds() > coupure:
            numero += 1
        p["sequence"] = f"S{numero:02d}"
        precedent = courant
    for p in photos:
        p.setdefault("sequence", "S00")


def reduire(chemin: Path, destination: Path, limite: int = LIMITE_LECTURE) -> Path | None:
    """Écrit une copie allégée hors du dépôt. L'original n'est jamais modifié."""
    if Image is None:
        return None
    destination.mkdir(parents=True, exist_ok=True)
    cible = destination / chemin.name
    with Image.open(chemin) as im:
        im = im.convert("RGB")
        for qualite in (85, 75, 65, 55):
            im.save(cible, "JPEG", quality=qualite, optimize=True)
            if cible.stat().st_size <= limite:
                return cible
        largeur, hauteur = im.size
        im.resize((largeur // 2, hauteur // 2)).save(cible, "JPEG", quality=80, optimize=True)
    return cible if cible.stat().st_size <= limite else None


def ingerer(dossier: Path, lieu: str, coupure: int, destination: Path | None) -> list[dict]:
    photos = []
    for chemin in sorted(dossier.iterdir()):
        if not chemin.is_file() or chemin.suffix.lower() not in EXTENSIONS:
            continue
        taille = chemin.stat().st_size
        pris_le, source = horodatage(chemin)
        non_traitee = None
        if taille > LIMITE_LECTURE:
            non_traitee = f"fichier de {taille / 1048576:.1f} Mo, au-delà de la limite de lecture"
            if destination and reduire(chemin, destination):
                non_traitee = None
        photos.append({
            "id": chemin.name,
            "empreinte": empreinte(chemin),
            "pris_le": pris_le,
            "horodatage_source": source,
            "lieu": lieu,
            "zone_presumee": None,
            "objets": [],
            "texte_lu": [],
            "visibilite_zone_critique": None,
            "sol_examine": False,
            "passage_examine": False,
            "renseignement_personnel": False,
            "constats": [],
            "non_traitee": non_traitee,
            "_taille_octets": taille,
        })
    sequencer(photos, coupure)
    return photos


def rapport(photos: list[dict], dossier: Path, lieu: str) -> str:
    datees = [p for p in photos if p["pris_le"]]
    sans_date = [p for p in photos if not p["pris_le"]]
    non_traitees = [p for p in photos if p["non_traitee"]]
    exif = [p for p in photos if p["horodatage_source"] == "exif"]
    doublons = {}
    for p in photos:
        doublons.setdefault(p["empreinte"], []).append(p["id"])
    doublons = {k: v for k, v in doublons.items() if len(v) > 1}

    sequences = {}
    for p in datees:
        sequences.setdefault(p["sequence"], []).append(p)

    lignes = [
        f"# Ingestion de photos — {dt.date.today().isoformat()}",
        "",
        f"Dossier : `{dossier}` · Lieu : **{lieu}**",
        "",
        f"{len(photos)} photos · {len(exif)} horodatées par l'EXIF · "
        f"{len(sans_date)} sans horodatage · {len(non_traitees)} non lisibles · "
        f"{len(doublons)} empreintes en double",
        "",
        "Aucune image n'a été copiée dans le dépôt. Ce rapport ne porte aucun",
        "verdict : il décrit ce qui a été trouvé.",
        "",
        "## Séquences de prise de vue",
        "",
        "| Séquence | Début | Fin | Photos | Durée |",
        "|---|---|---|---|---|",
    ]
    for nom in sorted(sequences):
        lot = sorted(sequences[nom], key=lambda p: p["pris_le"])
        debut = dt.datetime.fromisoformat(lot[0]["pris_le"])
        fin = dt.datetime.fromisoformat(lot[-1]["pris_le"])
        duree = (fin - debut).total_seconds() / 60
        lignes.append(f"| {nom} | {debut:%H:%M:%S} | {fin:%H:%M:%S} | {len(lot)} | {duree:.1f} min |")

    lignes += ["", "## À traiter avant la lecture", ""]
    if non_traitees:
        for p in non_traitees:
            lignes.append(f"- `{p['id']}` — {p['non_traitee']}")
    else:
        lignes.append("Rien : toutes les photos sont lisibles.")
    if sans_date:
        lignes += ["", "Photos sans horodatage, à rattacher à une séquence à la main :", ""]
        lignes += [f"- `{p['id']}`" for p in sans_date]
    if doublons:
        lignes += ["", "Empreintes identiques, donc doublons :", ""]
        lignes += [f"- {', '.join(v)}" for v in doublons.values()]

    lignes += [
        "",
        "## Rappel de méthode",
        "",
        "Une séquence n'est pas une zone : elle en est une présomption. Seule une",
        "photo de repère ou une note vocale confirme la zone.",
        "",
        "L'exposition — qui circule, quand, combien — ne figure sur aucune photo.",
        "Sans note vocale, elle reste inconnue.",
    ]
    return "\n".join(lignes) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingestion d'un dossier de photos de visite.")
    ap.add_argument("dossier", type=Path)
    ap.add_argument("--lieu", required=True, help="code du lieu, voir donnees/lieux.json")
    ap.add_argument("--coupure", type=int, default=240,
                    help="secondes séparant deux séquences (240 par défaut)")
    ap.add_argument("--reduire", type=Path, default=None,
                    help="dossier hors dépôt où écrire les copies allégées")
    ap.add_argument("--sortie", type=Path, default=Path("rapports"))
    args = ap.parse_args()

    photos = ingerer(args.dossier, args.lieu, args.coupure, args.reduire)
    if not photos:
        print("Aucune photo trouvée.")
        return 1

    args.sortie.mkdir(parents=True, exist_ok=True)
    jour = dt.date.today().isoformat()
    (args.sortie / f"rapport_photos_{jour}.md").write_text(
        rapport(photos, args.dossier, args.lieu), encoding="utf-8")
    index = [{k: v for k, v in p.items() if not k.startswith("_")} for p in photos]
    (args.sortie / f"index_photos_{jour}.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Rapport : {args.sortie / f'rapport_photos_{jour}.md'}")
    print(f"Index   : {args.sortie / f'index_photos_{jour}.json'}")
    print(f"{len(photos)} photos · {len([p for p in photos if p['non_traitee']])} non lisibles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
