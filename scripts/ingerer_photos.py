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
    --lieux FICHIER     donnees/lieux.json : l'ingestion propose alors un lieu
                        par photo, d'après le GPS de l'EXIF, quand le lieu
                        porte une reference_gps. La proposition reste une
                        proposition : elle n'écrase jamais --lieu.

Les séquences sont numérotées par journée : une visite est une journée. Une
photo prise la veille forme sa propre visite, elle ne décale pas les autres.
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


def _degres(valeur) -> float:
    """Convertit une coordonnée EXIF (degrés, minutes, secondes) en degrés décimaux."""
    d, m, sec = [float(x) for x in valeur]
    return d + m / 60 + sec / 3600


def gps(chemin: Path) -> list[float] | None:
    """Coordonnées de la photo, si l'appareil les a enregistrées."""
    if Image is None:
        return None
    try:
        with Image.open(chemin) as im:
            exif = im.getexif()
            brut = exif.get_ifd(0x8825) if exif else None
        if not brut:
            return None
        lat = _degres(brut[2])
        lon = _degres(brut[4])
        if str(brut.get(1, "N")).upper().startswith("S"):
            lat = -lat
        if str(brut.get(3, "E")).upper().startswith("W"):
            lon = -lon
        return [round(lat, 6), round(lon, 6)]
    except Exception:
        return None


def distance_m(a: list[float], b: list[float]) -> float:
    """Distance approximative en mètres. Suffisant pour distinguer deux espaces
    d'un même site ; ce n'est pas de la géodésie."""
    import math
    lat = math.radians((a[0] + b[0]) / 2)
    dx = (b[1] - a[1]) * 111320 * math.cos(lat)
    dy = (b[0] - a[0]) * 110540
    return math.hypot(dx, dy)


def proposer_lieu(coord: list[float] | None, lieux: list[dict]) -> tuple[str | None, float | None]:
    """Lieu le plus proche parmi ceux qui portent une reference_gps."""
    if not coord:
        return None, None
    candidats = [(l["code"], distance_m(coord, l["reference_gps"]))
                 for l in lieux if l.get("reference_gps")]
    if not candidats:
        return None, None
    code, d = min(candidats, key=lambda c: c[1])
    return code, round(d, 1)


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
    """Regroupe les photos en visites, puis en séquences de prise de vue.

    Une visite est une journée : une photo prise la veille forme sa propre
    visite et ne décale pas la numérotation des autres. À l'intérieur d'une
    journée, le temps fait le travail que le contenu ferait mal : une coupure
    de plusieurs minutes sépare presque toujours deux zones."""
    datees = sorted((p for p in photos if p["pris_le"]), key=lambda p: p["pris_le"])
    journees: dict[str, list[dict]] = {}
    for p in datees:
        journees.setdefault(p["pris_le"][:10], []).append(p)
    for jour, lot in journees.items():
        numero, precedent = 1, None
        for p in lot:
            courant = dt.datetime.fromisoformat(p["pris_le"])
            if precedent and (courant - precedent).total_seconds() > coupure:
                numero += 1
            p["visite"] = jour
            p["sequence"] = f"S{numero:02d}"
            precedent = courant
    for p in photos:
        p.setdefault("visite", None)
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


def ingerer(dossier: Path, lieu: str, coupure: int, destination: Path | None,
            lieux: list[dict] | None = None) -> list[dict]:
    photos = []
    for chemin in sorted(dossier.iterdir()):
        if not chemin.is_file() or chemin.suffix.lower() not in EXTENSIONS:
            continue
        taille = chemin.stat().st_size
        pris_le, source = horodatage(chemin)
        coord = gps(chemin)
        propose, ecart = proposer_lieu(coord, lieux or [])
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
            "gps": coord,
            "lieu_propose": propose,
            "lieu_propose_ecart_m": ecart,
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

    avec_gps = [p for p in photos if p.get("gps")]
    proposes = {}
    for p in photos:
        if p.get("lieu_propose") and p["lieu_propose"] != p["lieu"]:
            proposes.setdefault(p["lieu_propose"], []).append(p["id"])

    visites = {}
    for p in datees:
        visites.setdefault(p.get("visite") or "sans date", {}).setdefault(p["sequence"], []).append(p)

    lignes = [
        f"# Ingestion de photos — {dt.date.today().isoformat()}",
        "",
        f"Dossier : `{dossier}` · Lieu : **{lieu}**",
        "",
        f"{len(photos)} photos · {len(exif)} horodatées par l'EXIF · "
        f"{len(sans_date)} sans horodatage · {len(non_traitees)} non lisibles · "
        f"{len(doublons)} empreintes en double · {len(avec_gps)} avec coordonnées GPS",
        "",
        "Aucune image n'a été copiée dans le dépôt. Ce rapport ne porte aucun",
        "verdict : il décrit ce qui a été trouvé.",
        "",
        "## Visites et séquences de prise de vue",
        "",
    ]
    for jour in sorted(visites):
        total = sum(len(v) for v in visites[jour].values())
        lignes += [f"### Visite du {jour} — {total} photos", "",
                   "| Séquence | Début | Fin | Photos | Durée |", "|---|---|---|---|---|"]
        for nom in sorted(visites[jour]):
            lot = sorted(visites[jour][nom], key=lambda p: p["pris_le"])
            debut = dt.datetime.fromisoformat(lot[0]["pris_le"])
            fin = dt.datetime.fromisoformat(lot[-1]["pris_le"])
            duree = (fin - debut).total_seconds() / 60
            lignes.append(f"| {nom} | {debut:%H:%M:%S} | {fin:%H:%M:%S} | {len(lot)} | {duree:.1f} min |")
        lignes.append("")
    if proposes:
        lignes += ["## Lieu proposé d'après le GPS", "",
                   f"Le lieu déclaré est **{lieu}**. D'après les coordonnées, ces photos",
                   "semblent appartenir à un autre lieu du même site. Proposition, pas verdict :",
                   "à trancher avant de lire les photos.", ""]
        for code, ids in proposes.items():
            lignes.append(f"- **{code}** : {len(ids)} photos — {', '.join(ids[:6])}"
                          + (" …" if len(ids) > 6 else ""))
        lignes.append("")

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
    ap.add_argument("--lieux", type=Path, default=Path("donnees/lieux.json"),
                    help="registre des lieux, pour proposer un lieu d'après le GPS")
    ap.add_argument("--sortie", type=Path, default=Path("rapports"))
    args = ap.parse_args()

    lieux = []
    if args.lieux and args.lieux.exists():
        lieux = json.loads(args.lieux.read_text(encoding="utf-8")).get("lieux", [])

    photos = ingerer(args.dossier, args.lieu, args.coupure, args.reduire, lieux)
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
    visites = sorted({p.get("visite") for p in photos if p.get("visite")})
    print(f"{len(photos)} photos · {len(visites)} visite(s) : {', '.join(visites)} · "
          f"{len([p for p in photos if p['non_traitee']])} non lisibles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
