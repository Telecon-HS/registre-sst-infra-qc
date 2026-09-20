"""Génère les deux pages HTML autonomes.

    python scripts/generer_page.py
      → sortie/registre_risques_sst_falcon.html   page COMITÉ : toutes les vues, noms,
                                                   photos et incidents (avec le dossier privé)
      → sortie/consignes_terrain_falcon.html      page TERRAIN : superviseurs et travailleurs
                                                   seulement, jamais de nom, de photo ni d'incident

Le sélecteur de rôle d'une page n'est pas une protection : tout ce qui est dans le
fichier peut être lu. C'est pourquoi la page Terrain est un fichier distinct qui
ne contient que les consignes (décision du 20 septembre 2026).
"""
import base64
import json

from commun import (DONNEES, GABARITS, PRIVE, SORTIE, incidents_prives, ligne_version,
                    lire_json, mode, nom_versionne, prive_disponible, remplacer_jetons,
                    table_des_noms)

ORDRE_INCIDENT = ["id", "date", "titre", "type", "stky", "prepare", "lieu", "gest", "ref", "lecture"]
REPLI_INCIDENT = {"type": "", "stky": "", "prepare": "", "lieu": "", "gest": "",
                  "lecture": "Détail conservé hors dépôt (dossier privé)."}


def completer_incident(inc, detail):
    complet = {**inc, **detail.get(inc["id"], REPLI_INCIDENT)}
    return {k: complet[k] for k in ORDRE_INCIDENT}


def generer(avec_prive=True, sortie=None):
    avec_prive = avec_prive and prive_disponible()
    data = lire_json(DONNEES / "registre_html.json")
    table = table_des_noms(avec_prive)

    detail = incidents_prives() if avec_prive else {}
    data["incidents"] = [completer_incident(x, detail) for x in data["incidents"]]
    for r in data["risques"]:
        r["incidents"] = [completer_incident(x, detail) for x in r["incidents"]]

    for site in data["sites"]:
        garder = []
        for ph in site["photos"]:
            f = PRIVE / "photos" / ph["src"].removeprefix("photo:")
            if avec_prive and f.exists():
                ph["src"] = base64.b64encode(f.read_bytes()).decode("ascii")
                garder.append(ph)
        site["photos"] = garder

    data = remplacer_jetons(data, table)
    gabarit = remplacer_jetons((GABARITS / "page_registre.html").read_text(encoding="utf-8"), table)
    logo = base64.b64encode((GABARITS / "assets" / "logo_telecon.png").read_bytes()).decode("ascii")
    page = (gabarit.replace("__LOGO__", "data:image/png;base64," + logo)
                   .replace("__VERSION__", ligne_version("page Comité — contient des noms, des photographies et le détail des incidents ; à diffuser au comité seulement"))
                   .replace("__DATA__", json.dumps(data, ensure_ascii=False)))

    sortie = sortie or SORTIE / nom_versionne("registre_risques_sst_falcon", ".html")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(page, encoding="utf-8")
    print(f"page → {sortie} [{mode() if avec_prive else 'sans données privées'}]")
    return sortie


def generer_terrain(sortie=None):
    """Page Terrain : ne reçoit que les consignes superviseurs et travailleurs.
    Les jetons de personnes sont toujours remplacés par le repli, même si le
    dossier privé est disponible, et la page est vérifiée avant d'être écrite."""
    roles = lire_json(DONNEES / "registre_html.json")["roles"]
    data = remplacer_jetons({"superviseurs": roles["superviseurs"], "travailleurs": roles["travailleurs"]},
                            table_des_noms(avec_prive=False))
    registre = (GABARITS / "page_registre.html").read_text(encoding="utf-8")
    css = registre[registre.index("<style>"):registre.index("</style>") + len("</style>")]
    logo = base64.b64encode((GABARITS / "assets" / "logo_telecon.png").read_bytes()).decode("ascii")
    page = ((GABARITS / "page_terrain.html").read_text(encoding="utf-8")
            .replace("__CSS__", css)
            .replace("__LOGO__", "data:image/png;base64," + logo)
            .replace("__VERSION__", ligne_version("page Terrain — aucune donnée nominative ; peut circuler sur le terrain"))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False)))

    # garde-fou : aucun nom connu, aucune photo, aucun jeton dans la page Terrain
    interdits = []
    if prive_disponible():
        interdits = [g for gs in lire_json(PRIVE / "noms.json")["variantes"].values() for g in gs]
    trouves = [n for n in interdits if n in page]
    if trouves or "⟦" in page or "/9j/" in page:
        raise SystemExit(f"Page Terrain refusée : données privées détectées {trouves[:3]}")

    sortie = sortie or SORTIE / nom_versionne("consignes_terrain_falcon", ".html")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(page, encoding="utf-8")
    print(f"page terrain → {sortie} [sans aucune donnée privée]")
    return sortie


if __name__ == "__main__":
    import sys
    generer(avec_prive="--sans-prive" not in sys.argv)
    generer_terrain()
