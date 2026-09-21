"""Projet d'ordre du jour de la prochaine séance du comité SST — markdown et PDF.

    python scripts/ordre_du_jour.py
      → sortie/Ordre_du_jour_comite_SST_projet_v8_AAAA-MM-JJ.md
      → sortie/Ordre_du_jour_comite_SST_projet_v8_AAAA-MM-JJ.pdf

Les points viennent des données, dans cet ordre :
  1. Ouverture — quorum, adoption de l'ordre du jour.
  2. Dossiers dont le jalon tombe avant ou à la séance (plan d'action, page 2).
  3. Risques dont le délai proposé est « prochaine séance ».
  4. Réserves à trancher (plan d'action, page 1).
  5. Documents du comité absents.
  6. Varia et date de la prochaine séance.

Durées : aucune n'existe dans les données. Elles restent « à confirmer » tant que
donnees/ordre_du_jour.json ne fixe pas une durée par type de point. Même chose pour
la date, le lieu et la composition du comité.

Aucun nom de personne : les porteurs sont désignés par leur rôle.
"""
import base64
import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import (DONNEES, GABARITS, SORTIE, lire_json, ligne_version, nom_versionne,  # noqa: E402
                    remplacer_jetons, table_des_noms)

JALONS_SEANCE = ("avant la séance", "prochaine séance", "immédiat")
A_CONFIRMER = "à confirmer"


def config():
    f = DONNEES / "ordre_du_jour.json"
    return lire_json(f) if f.exists() else {}


def duree(type_point, cfg):
    d = (cfg.get("durees") or {}).get(type_point)
    return d if isinstance(d, (int, float)) and d > 0 else None


def construire_points(cfg=None):
    """Liste de points : {num, section, titre, type, decision, renvoi, duree}."""
    cfg = cfg if cfg is not None else config()
    sans_noms = table_des_noms(avec_prive=False)
    D = remplacer_jetons(lire_json(DONNEES / "registre_html.json"), sans_noms)
    P = remplacer_jetons(lire_json(DONNEES / "plan_action.json"), sans_noms)
    points = []

    def ajouter(section, titre, type_point, decision, renvoi=""):
        points.append({"section": section, "titre": titre, "type": type_point, "decision": decision,
                       "renvoi": renvoi, "duree": duree(type_point, cfg)})

    ajouter("Ouverture", "Constat du quorum", "ouverture",
            "Constater la composition présente. La composition du comité n'est pas arrêtée : à confirmer.")
    ajouter("Ouverture", "Adoption de l'ordre du jour", "ouverture", "Adopter ou modifier le présent projet.")

    for c in P["pages"][1]["dossiers"]["cartes"]:
        if c["jalon"].lower() in JALONS_SEANCE:
            porteur = c["porteur"].replace("[nom retiré], ", "").replace("[nom retiré]", "rôle à confirmer")
            ajouter("Dossiers en cours", f"{c['id']} — {c['titre']}", "decision",
                    f"{c['prochaine']}. État : {c['etat']}. Porteur : {porteur}.", c["refs"])

    for r in D["risques"]:
        if r["bucket"] == "seance":
            ajouter("Risques à trancher en séance", f"{r['ref']} — {r['titre']}", "decision",
                    r["decision"], f"Priorité {r['prio']} · {r['famille']}")

    for titre, texte in P["pages"][0]["reserves"]["lignes"]:
        ajouter("Réserves à trancher", titre, "decision", texte)

    for groupe in P["pages"][1]["documents"]["groupes"]:
        for couleur, doc, etat in groupe["docs"]:
            if couleur == "p1":
                ajouter("Documents du comité absents", doc, "information",
                        f"État relevé : {etat}. Désigner, s'il y a lieu, qui le produit et pour quand. "
                        "Exigence indicative, à confirmer auprès de la CNESST.", groupe["titre"])

    ajouter("Clôture", "Varia", "information", "Points ajoutés en début de séance.")
    ajouter("Clôture", "Date et lieu de la prochaine séance", "ouverture",
            "Fixer la date. La fréquence minimale dépend de la charte, non adoptée : à confirmer.")

    for i, p in enumerate(points, 1):
        p["num"] = i
    return points


def total(points):
    if any(p["duree"] is None for p in points):
        return None
    return sum(p["duree"] for p in points)


def fmt_duree(d):
    return f"{int(d)} min" if d is not None else A_CONFIRMER


def markdown(points, cfg=None):
    cfg = cfg if cfg is not None else config()
    v = lire_json(DONNEES / "version.json")
    t = [f"# Projet d'ordre du jour — comité SST Infra Québec", "",
         f"**Date** : {cfg.get('date_seance') or A_CONFIRMER} · **Lieu** : {cfg.get('lieu') or A_CONFIRMER} · "
         f"**Durée totale** : {fmt_duree(total(points))}", "",
         f"Projet établi à partir du registre, version {v['version']} du {v['date_longue']}. "
         "Aucun verdict de conformité : chaque point appelle une décision ou une information, pas un constat.", ""]
    section = None
    for p in points:
        if p["section"] != section:
            section = p["section"]
            t += [f"## {section}", ""]
        t.append(f"**{p['num']}. {p['titre']}** — {fmt_duree(p['duree'])}")
        t.append(f"  {'Décision demandée' if p['type'] == 'decision' else 'Objet'} : {p['decision']}")
        if p["renvoi"]:
            t.append(f"  Renvoi : {p['renvoi']}")
        t.append("")
    t += ["---", "",
          "Les durées, la date, le lieu et la composition restent à confirmer tant qu'ils ne sont pas fixés "
          "dans `donnees/ordre_du_jour.json` ou par la charte du comité.", "",
          "**Validation humaine requise.** Ce projet est proposé par le secrétariat ; l'ordre du jour est adopté "
          "par le comité en ouverture de séance."]
    return "\n".join(t) + "\n"


CSS = """
@page{size:letter;margin:16mm 16mm 18mm}
body{font-family:'Liberation Sans',Arial,sans-serif;color:#16202A;font-size:10.2px;line-height:1.42}
.bande{background:#1F3864;color:#fff;padding:12px 16px;display:flex;align-items:center;gap:14px}
.bande img{height:22px}.bande h1{margin:0;font-size:17px}.bande small{display:block;font-size:10px;opacity:.85}
.meta{display:flex;gap:18px;margin:10px 0 4px;font-size:10.5px}.meta b{color:#1F3864}
.intro{color:#5C6B7A;margin:0 0 8px}
h2{font-size:11px;text-transform:uppercase;letter-spacing:.3px;color:#1F3864;border-bottom:1.5px solid #1F3864;padding-bottom:2px;margin:12px 0 4px}
table{width:100%;border-collapse:collapse}
td{border-bottom:1px solid #E3E7EC;padding:5px 4px;vertical-align:top}
td.n{width:24px;font-weight:700;color:#1F3864}td.d{width:70px;text-align:right;white-space:nowrap;color:#5C6B7A}
td b{display:block;font-size:10.6px}.dec{color:#2A3540}.ren{color:#7A8796;font-size:9px;margin-top:1px}
.conf{color:#B3261E;font-style:italic}
.fin{margin-top:14px;padding-top:8px;border-top:1px solid #D9DDE3;font-size:9.2px;color:#5C6B7A}
.fin b{color:#16202A}
"""


def page_html(points, cfg=None):
    cfg = cfg if cfg is not None else config()
    e = lambda s: html.escape(str(s), quote=False)  # noqa: E731
    d = lambda x: e(fmt_duree(x)) if x is not None else f'<span class="conf">{A_CONFIRMER}</span>'  # noqa: E731
    logo = base64.b64encode((GABARITS / "assets" / "logo_telecon.png").read_bytes()).decode("ascii")
    corps, section = [], None
    for p in points:
        if p["section"] != section:
            if section is not None:
                corps.append("</table>")
            section = p["section"]
            corps.append(f"<h2>{e(section)}</h2><table>")
        lib = "Décision demandée" if p["type"] == "decision" else "Objet"
        corps.append(f'<tr><td class="n">{p["num"]}</td><td><b>{e(p["titre"])}</b><div class="dec">{lib} : {e(p["decision"])}</div>'
                     + (f'<div class="ren">{e(p["renvoi"])}</div>' if p["renvoi"] else "") + f'</td><td class="d">{d(p["duree"])}</td></tr>')
    corps.append("</table>")
    date_s = e(cfg.get("date_seance")) if cfg.get("date_seance") else f'<span class="conf">{A_CONFIRMER}</span>'
    lieu = e(cfg.get("lieu")) if cfg.get("lieu") else f'<span class="conf">{A_CONFIRMER}</span>'
    return (f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="bande"><img src="data:image/png;base64,{logo}"><h1>Projet d’ordre du jour<small>Comité SST — Infra Québec</small></h1></div>'
            f'<div class="meta"><span><b>Date</b> {date_s}</span><span><b>Lieu</b> {lieu}</span><span><b>Durée totale</b> {d(total(points))}</span></div>'
            f'<p class="intro">Projet établi à partir du registre des risques. Aucun verdict de conformité : chaque point appelle une décision ou une information, pas un constat.</p>'
            + "".join(corps)
            + f'<div class="fin"><b>Validation humaine requise.</b> Ce projet est proposé par le secrétariat ; l’ordre du jour est adopté par le comité en ouverture de séance. '
            f'Durées, date, lieu et composition restent à confirmer tant qu’ils ne sont pas fixés.<br>{e(ligne_version("projet d’ordre du jour du comité"))}</div>'
            "</body></html>")


def generer(sortie=None):
    points = construire_points()
    base = sortie or SORTIE / nom_versionne("Ordre_du_jour_comite_SST_projet", "")
    base.parent.mkdir(parents=True, exist_ok=True)
    md = base.with_suffix(".md")
    md.write_text(markdown(points), encoding="utf-8")
    source = base.with_suffix(".html")
    source.write_text(page_html(points), encoding="utf-8")
    pdf = base.with_suffix(".pdf")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page()
        pg.goto(source.resolve().as_uri())
        pg.pdf(path=str(pdf), format="Letter", print_background=True)
        nav.close()
    print(f"{len(points)} points · durée totale : {fmt_duree(total(points))}")
    print(f"ordre du jour → {md}\nordre du jour → {pdf}")
    print("Validation humaine requise : projet à adopter par le comité.")
    return md, pdf


if __name__ == "__main__":
    generer()
