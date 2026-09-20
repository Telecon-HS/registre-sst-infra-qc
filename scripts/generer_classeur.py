"""Génère le classeur du registre (15 onglets) à partir de donnees/classeur/.

    python scripts/generer_classeur.py        → sortie/Registre_risques_SST_Falcon_Infra_QC.xlsx

Chaque onglet est décrit par un fichier JSON : cellules (valeur ou formule, style),
largeurs, hauteurs, fusions, volets figés, filtres et listes déroulantes.
Les styles sont partagés dans _styles.json. Les formules sont conservées telles
quelles : ouvrir le fichier dans Excel ou LibreOffice les recalcule.

Pour modifier le contenu : éditer la valeur de la cellule dans le JSON de l'onglet.
"""
import datetime as dt
from copy import copy

from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Alignment, Border, Color, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from commun import (DONNEES, PRIVE, RACINE, SORTIE, ligne_version, lire_json,
                    nom_versionne, prive_disponible, remplacer_jetons, table_des_noms)

CLASSEUR = DONNEES / "classeur"


def couleur(c):
    if not c:
        return None
    if "rgb" in c:
        return Color(rgb=c["rgb"])
    if "theme" in c:
        return Color(theme=c["theme"], tint=c["tint"])
    return Color(indexed=c["indexed"])


def construire_styles():
    styles = []
    for s in lire_json(CLASSEUR / "_styles.json"):
        f = s["font"]
        font = Font(name=f["name"], sz=f["sz"], b=f["b"], i=f["i"], u=f["u"], strike=f["strike"], color=couleur(f["color"]))
        fill = PatternFill(fill_type=s["fill"]["type"], fgColor=couleur(s["fill"]["fg"]), bgColor=couleur(s["fill"]["bg"])) if s["fill"] else PatternFill()
        cote = lambda d: Side(style=d["style"], color=couleur(d["color"])) if d else Side()  # noqa: E731
        border = Border(**{k: cote(s["border"][k]) for k in ("left", "right", "top", "bottom")})
        a = s["align"]
        align = Alignment(horizontal=a["h"], vertical=a["v"], wrap_text=a["wrap"], indent=a["indent"], text_rotation=a["rot"], shrink_to_fit=a["shrink"])
        styles.append((font, fill, border, align, s["numfmt"]))
    return styles


def valeur(v):
    if isinstance(v, dict) and "date" in v:
        return dt.datetime.fromisoformat(v["date"])
    return v


def generer(avec_prive=True, sortie=None):
    avec_prive = avec_prive and prive_disponible()
    table = table_des_noms(avec_prive)
    cellules_privees = lire_json(PRIVE / "classeur_prive.json") if avec_prive and (PRIVE / "classeur_prive.json").exists() else {}
    styles = construire_styles()

    wb = Workbook()
    wb.remove(wb.active)
    for nom in lire_json(CLASSEUR / "_ordre.json"):
        f = lire_json(CLASSEUR / nom)
        ws = wb.create_sheet(f["titre"])
        for coord, v, si in f["cellules"]:
            c = ws[coord]
            cle = f"{f['titre']}!{coord}"
            v = cellules_privees.get(cle, v)
            c.value = valeur(remplacer_jetons(v, table))
            c.font, c.fill, c.border, c.alignment, c.number_format = styles[si]
        for col, largeur in f["colonnes"].items():
            ws.column_dimensions[col].width = largeur
        for lig, hauteur in f["lignes"].items():
            ws.row_dimensions[int(lig)].height = hauteur
        for plage in f["fusions"]:
            ws.merge_cells(plage)
        ws.sheet_view.showGridLines = f["grille"]
        if f["figer"]:
            ws.freeze_panes = f["figer"]
        if f["filtre"]:
            ws.auto_filter.ref = f["filtre"]
        for v in f["validations"]:
            dv = DataValidation(type=v["type"], formula1=v["formula1"], allow_blank=v["allow_blank"])
            dv.add(v["sqref"])
            ws.add_data_validation(dv)
        for im in f["images"]:
            img = Image(str(RACINE / im["fichier"]))
            img.width, img.height = im["largeur"], im["hauteur"]
            ws.add_image(img, im["ancre"])

    garde = wb["Garde"]
    modele = garde["B34"]            # note de bas de page de la garde
    garde.merge_cells("B38:C39")
    garde["B38"].value = ligne_version("classeur — source de travail")
    garde["B38"]._style = copy(modele._style)

    sortie = sortie or SORTIE / nom_versionne("Registre_risques_SST_Falcon_Infra_QC", ".xlsx")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    wb.save(sortie)
    print(f"classeur → {sortie} [{'complet' if avec_prive else 'sans données privées'}]")
    return sortie


if __name__ == "__main__":
    import sys
    generer(avec_prive="--sans-prive" not in sys.argv)
