"""Reconstitution des données à partir des livrables existants.

Utilisé une fois, le 20 septembre 2026, pour recréer le dépôt après la perte des
modules de données d'origine. Conservé pour la traçabilité : il montre d'où vient
chaque fichier de données/.

Entrées  : le classeur (.xlsx) et la page HTML publiée du 19 septembre 2026,
           plus prive/noms.json (jetons et variantes d'écriture des noms).
Sorties  : donnees/registre_html.json, donnees/classeur/*.json,
           gabarits/page_registre.html
           et, dans le dossier privé : incidents.json, classeur_prive.json, photos/.

    python outils/extraire_depuis_livrables.py CLASSEUR.xlsx PAGE.html
"""
import base64
import unicodedata
import json
import sys
from pathlib import Path

import openpyxl
from openpyxl.cell.cell import Cell

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from commun import DONNEES, GABARITS, PRIVE, lire_json  # noqa: E402

# Champs d'incident qui restent hors dépôt (type de lésion, lieu, personnes, lecture).
CHAMPS_INCIDENT_PRIVES = ["type", "stky", "prepare", "lieu", "gest", "lecture"]
# Feuille Incidents du classeur : colonnes privées (D à H et J), lignes de données.
COLONNES_INCIDENT_PRIVEES = "DEFGHJ"


def variantes():
    v = lire_json(PRIVE / "noms.json")["variantes"]
    paires = [(nom, jeton if n == 0 else f"{jeton}~{n}") for jeton, noms in v.items() for n, nom in enumerate(noms)]
    return sorted(paires, key=lambda p: -len(p[0]))  # les plus longues d'abord


def jetonner(obj, paires):
    if isinstance(obj, str):
        for nom, jeton in paires:
            obj = obj.replace(nom, f"⟦{jeton}⟧")
        return obj
    if isinstance(obj, list):
        return [jetonner(x, paires) for x in obj]
    if isinstance(obj, dict):
        return {k: jetonner(x, paires) for k, x in obj.items()}
    return obj


# ---------------------------------------------------------------- page HTML
def extraire_page(chemin, paires):
    s = Path(chemin).read_text(encoding="utf-8")
    debut = s.index("const DATA = ") + len("const DATA = ")
    data, fin = json.JSONDecoder().raw_decode(s[debut:])
    gabarit = s[:debut] + "__DATA__" + s[debut + fin:]

    # logo intégré → fichier, remplacé par un repère
    marque = 'src="data:image/png;base64,'
    i = gabarit.index(marque) + len('src="')
    j = gabarit.index('"', i)
    (GABARITS / "assets" / "logo_telecon.png").write_bytes(base64.b64decode(gabarit[i:j].split(",", 1)[1]))
    gabarit = gabarit[:i] + "__LOGO__" + gabarit[j:]
    gabarit = jetonner(gabarit, paires)
    (GABARITS / "page_registre.html").write_text(gabarit, encoding="utf-8")

    # photos → dossier privé
    (PRIVE / "photos").mkdir(parents=True, exist_ok=True)
    for i, site in enumerate(data["sites"], 1):
        for k, ph in enumerate(site["photos"], 1):
            nom = f"site{i}_{k:02d}.jpg"
            (PRIVE / "photos" / nom).write_bytes(base64.b64decode(ph["src"]))
            ph["src"] = f"photo:{nom}"

    # détail des incidents → dossier privé
    prives = {}

    def alleger(inc):
        prives[inc["id"]] = {c: inc[c] for c in CHAMPS_INCIDENT_PRIVES}
        return {k: v for k, v in inc.items() if k not in CHAMPS_INCIDENT_PRIVES}

    data["incidents"] = [alleger(x) for x in data["incidents"]]
    for r in data["risques"]:
        r["incidents"] = [alleger(x) for x in r["incidents"]]
    (PRIVE / "incidents.json").write_text(json.dumps(prives, ensure_ascii=False, indent=1), encoding="utf-8")

    data = jetonner(data, paires)
    (DONNEES / "registre_html.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"page : {len(data['risques'])} risques, {sum(len(s['photos']) for s in data['sites'])} photos sorties, {len(prives)} incidents privés")


# ---------------------------------------------------------------- classeur
def couleur(c):
    if c is None:
        return None
    if c.type == "rgb":
        return {"rgb": c.rgb}
    if c.type == "theme":
        return {"theme": c.theme, "tint": c.tint}
    if c.type == "indexed":
        return {"indexed": c.indexed}
    return None


def style_de(cell):
    f, fl, b, a = cell.font, cell.fill, cell.border, cell.alignment
    cote = lambda s: {"style": s.style, "color": couleur(s.color)} if s and s.style else None  # noqa: E731
    return {
        "font": {"name": f.name, "sz": f.sz, "b": f.b, "i": f.i, "u": f.u, "strike": f.strike, "color": couleur(f.color)},
        "fill": {"type": fl.fill_type, "fg": couleur(fl.fgColor), "bg": couleur(fl.bgColor)} if fl.fill_type else None,
        "border": {k: cote(getattr(b, k)) for k in ("left", "right", "top", "bottom")},
        "align": {"h": a.horizontal, "v": a.vertical, "wrap": a.wrap_text, "indent": a.indent, "rot": a.text_rotation, "shrink": a.shrink_to_fit},
        "numfmt": cell.number_format,
    }


def extraire_classeur(chemin, paires):
    wb = openpyxl.load_workbook(chemin)
    styles, index_styles, ordre, prive = [], {}, [], {}
    dossier = DONNEES / "classeur"
    for fichier in dossier.glob("*.json"):
        fichier.unlink()
    for n, ws in enumerate(wb.worksheets, 1):
        cellules = []
        vide = json.dumps(style_de(Cell(ws)), sort_keys=True)
        for ligne in ws.iter_rows():
            for c in ligne:
                st = json.dumps(style_de(c), sort_keys=True)
                if c.value is None and st == vide:
                    continue
                if st not in index_styles:
                    index_styles[st] = len(styles)
                    styles.append(json.loads(st))
                v = c.value
                if (ws.title == "Incidents" and 5 <= c.row <= 13 and c.column_letter in COLONNES_INCIDENT_PRIVEES and v is not None):
                    prive[f"Incidents!{c.coordinate}"] = v
                    v = None
                if hasattr(v, "isoformat"):
                    v = {"date": v.isoformat()}
                cellules.append([c.coordinate, jetonner(v, paires), index_styles[st]])
        feuille = {
            "titre": ws.title,
            "grille": ws.sheet_view.showGridLines,
            "figer": ws.freeze_panes,
            "filtre": ws.auto_filter.ref,
            "fusions": [str(r) for r in ws.merged_cells.ranges],
            "colonnes": {k: d.width for k, d in ws.column_dimensions.items() if d.width},
            "lignes": {str(k): d.height for k, d in ws.row_dimensions.items() if d.height},
            "validations": [{"type": v.type, "formula1": v.formula1, "sqref": str(v.sqref), "allow_blank": v.allow_blank} for v in ws.data_validations.dataValidation],
            "images": [],
            "cellules": cellules,
        }
        if ws._images:
            feuille["images"] = [{"fichier": "gabarits/assets/logo_telecon.png", "ancre": "B2", "largeur": 156, "hauteur": 51}]
        # noms de fichiers sans accents : Windows et Git les gèrent mal dans une archive
        nom_fichier = unicodedata.normalize("NFKD", f"{n:02d}_{ws.title}.json").encode("ascii", "ignore").decode()
        (dossier / nom_fichier).write_text(json.dumps(feuille, ensure_ascii=False, indent=0), encoding="utf-8")
        ordre.append(nom_fichier)
    (dossier / "_styles.json").write_text(json.dumps(styles, ensure_ascii=False, indent=0), encoding="utf-8")
    (dossier / "_ordre.json").write_text(json.dumps(ordre, ensure_ascii=False, indent=1), encoding="utf-8")
    (PRIVE / "classeur_prive.json").write_text(json.dumps(prive, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"classeur : {len(ordre)} onglets, {len(styles)} styles, {len(prive)} cellules privées")


if __name__ == "__main__":
    paires = variantes()
    extraire_classeur(sys.argv[1], paires)
    extraire_page(sys.argv[2], paires)
