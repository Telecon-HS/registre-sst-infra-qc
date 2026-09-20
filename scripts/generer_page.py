"""Génère la page HTML autonome du registre (sélecteur de rôle, neuf vues).

    python scripts/generer_page.py            → sortie/registre_risques_sst_falcon.html

Avec le dossier privé, la page est identique à celle publiée le 19 septembre 2026
(noms, photos et détail des incidents compris). Sans lui, elle est produite sans
noms, sans photos et sans le détail des incidents.
"""
import base64
import json

from commun import (DONNEES, GABARITS, PRIVE, SORTIE, incidents_prives, lire_json,
                    mode, prive_disponible, remplacer_jetons, table_des_noms)

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
                   .replace("__DATA__", json.dumps(data, ensure_ascii=False)))

    sortie = sortie or SORTIE / "registre_risques_sst_falcon.html"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(page, encoding="utf-8")
    print(f"page → {sortie} [{mode() if avec_prive else 'sans données privées'}]")
    return sortie


if __name__ == "__main__":
    import sys
    generer(avec_prive="--sans-prive" not in sys.argv)
