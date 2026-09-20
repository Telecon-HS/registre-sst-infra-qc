"""Génère le plan d'action du comité : PDF de trois pages, format lettre paysage.

    python scripts/generer_plan_action.py     → sortie/Plan_action_SST_comite_Infra_QC.pdf

Page 1 : les 39 risques, le calendrier, les récurrences et les réserves.
Page 2 : dossiers en cours et documents du comité.
Page 3 : activités de prévention, alignement stratégique et reconnaissance.

Le texte vient de donnees/plan_action.json ; la priorité de chaque risque (la
couleur) vient de donnees/registre_html.json, pour qu'une seule source la porte.
Rendu : HTML + CSS imprimé par Chromium (paquet Python « playwright »).
"""
import base64
import html
import json

from commun import (DONNEES, GABARITS, SORTIE, ligne_version, lire_json, nom_versionne,
                    prive_disponible, remplacer_jetons, table_des_noms)

COULEURS = {"p1": "#C01B1A", "p2": "#B97900", "p3": "#2E6C4F", "navy": "#1F3864"}

CSS = """
@page { size: 11in 8.5in; margin: 0 }
* { box-sizing: border-box }
body { margin: 0; font-family: 'Liberation Sans', Arial, Helvetica, sans-serif; color: #1a1a1a; font-size: 8.4px; line-height: 1.25 }
.page { width: 11in; height: 8.5in; position: relative; overflow: hidden; page-break-after: always; background: #fff }
.page:last-child { page-break-after: auto }
header { background: #1F3864; color: #fff; height: 82px; display: flex; align-items: center; padding: 0 30px 0 30px }
header img { height: 30px; margin-right: 16px }
header .sep { width: 1px; align-self: stretch; margin: 12px 16px 12px 0; background: rgba(255,255,255,.35) }
header .t { flex: 1 }
header h1 { margin: 0; font-size: 25px; font-weight: 700; letter-spacing: -.2px; line-height: 1.05 }
header .st { font-size: 10.6px; margin-top: 2px; line-height: 1.3 }
header .dr { text-align: right; font-size: 10.2px; line-height: 1.35 }
header .dr b { font-size: 11.6px }
.corps { padding: 7px 30px 0 30px }
.kpis { display: flex; gap: 12px; margin-bottom: 6px }
.kpi { flex: 1; background: #F3F4F6; border: 1px solid #D9DDE3; border-radius: 4px; height: 52px; display: flex; align-items: center; padding: 0 12px }
.kpi b { font-size: 23px; color: #1F3864; margin-right: 8px; font-weight: 700 }
.kpi span { font-size: 9px; color: #555; line-height: 1.2 }
.kpis.bas .kpi { align-items: flex-start; padding-top: 7px }
h2 { font-size: 12.6px; margin: 4px 0 5px 0; font-weight: 700; color: #111 }
h2 small { font-size: 8.6px; font-weight: 400; color: #666; margin-left: 4px }
.cols { display: flex; gap: 11px }
.col { flex: 1; min-width: 0 }
.colh { background: #1F3864; color: #fff; font-weight: 700; font-size: 8.4px; padding: 5px 8px; margin-bottom: 5px }
.rk { border: 1px solid #D9DDE3; border-left-width: 4px; border-radius: 3px; padding: 3px 5px 3px 7px; margin-bottom: 4px; height: 30.5px }
.rk .l1 { display: flex; align-items: center; gap: 4px }
.rk .ref { font-weight: 700; font-size: 10px }
.rk .tt { font-size: 8.3px; color: #222; margin-top: 1px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis }
.bdg { margin-left: auto; color: #fff; font-weight: 700; font-size: 7.3px; padding: 1px 5px; border-radius: 2px }
.bul { background: #1F3864; color: #fff; font-size: 7px; font-weight: 700; width: 11px; height: 11px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center }
.inc { background: #C01B1A; color: #fff; font-size: 6.5px; font-weight: 700; padding: 1px 3px; border-radius: 2px }
.cal { display: flex; gap: 11px }
.cal > div { flex: 1; border: 1px solid #D9DDE3; border-radius: 3px; height: 128px; position: relative }
.cal .h { color: #fff; font-weight: 700; font-size: 9px; padding: 5px 8px; display: flex; justify-content: space-between }
.chips { padding: 6px 8px; display: flex; flex-wrap: wrap; gap: 3px 4px }
.chip { width: calc(25% - 3px); text-align: center; background: #E9EEF3; color: #1F3864; font-weight: 700; font-size: 8px; padding: 1.5px 5px; border-radius: 2px }
.cal .n { position: absolute; bottom: 6px; left: 8px; right: 8px; font-size: 7.8px; color: #555 }
.duo { display: flex; gap: 11px; margin-top: 7px }
.box { border: 1px solid #D0D5DC; border-radius: 4px; padding: 7px 12px }
.rec { flex: 0 0 38.5%; background: #F3F4F6 }
.rec h3, .res h3 { margin: 0 0 1px 0; font-size: 10.4px }
.res h3 { color: #C01B1A }
.rec .i { font-size: 7.8px; color: #666; margin-bottom: 5px }
.rec .ln { display: flex; align-items: center; gap: 6px; margin: 2.5px 0; font-size: 8.4px }
.rec .ln b.r { color: #1F3864; width: 32px }
.res { flex: 1 }
.res .ln { display: flex; gap: 8px; margin: 3px 0; font-size: 8.3px }
.res .ln b { color: #1F3864; flex: 0 0 106px }
.pied { position: absolute; left: 30px; right: 30px; bottom: 9px; font-size: 7.4px; color: #555 }
.pied .l1 { display: flex; align-items: center; gap: 5px }
.pied .sq { width: 8px; height: 8px; display: inline-block; margin-left: 10px }
.pied .rd { margin-left: auto; font-style: italic }
.pied .l2 { font-style: italic; margin-top: 2px }
.pied .l3 { margin-top: 2px; color: #777; font-size: 6.9px }
.dot { width: 7px; height: 7px; border-radius: 50%; display: inline-block; flex: 0 0 7px; margin-top: 2px }
/* page 2 */
.cartes { display: grid; grid-template-columns: repeat(4, 1fr); gap: 11px 11px }
.carte { border: 1px solid #D9DDE3; border-left-width: 4px; border-radius: 3px; padding: 6px 9px; height: 150px; position: relative }
.carte .l1 { display: flex; align-items: center }
.carte .id { font-weight: 700; font-size: 9.6px }
.carte h4 { margin: 1px 0 3px 0; font-size: 10.6px }
.carte .k { font-size: 7.2px; font-weight: 700; color: #555; margin-top: 2px }
.carte .v { font-size: 8.2px }
.carte .refs { position: absolute; bottom: 6px; left: 9px; font-weight: 700; color: #1F3864; font-size: 8px }
.docs { display: flex; gap: 11px }
.docs .g { flex: 1; border: 1px solid #D9DDE3; border-radius: 3px; height: 285px }
.docs .h { background: #1F3864; color: #fff; font-weight: 700; font-size: 8.4px; padding: 5px 10px }
.docs .d { display: flex; gap: 7px; padding: 0 12px; margin-top: 6px }
.docs .d b { font-size: 8.4px; display: block }
.docs .d span { font-size: 7.6px; color: #666 }
/* page 3 */
table.vol { width: 100%; border-collapse: collapse; font-size: 8.4px }
table.vol th { background: #1F3864; color: #fff; text-align: left; padding: 4px 8px; font-size: 8px }
table.vol td { padding: 6px 8px; border-bottom: 1px solid #D9DDE3; vertical-align: top }
table.vol td.n { text-align: center; width: 36px }
table.vol td.tot { font-weight: 700; color: #1F3864; text-align: center; width: 40px }
table.vol td.lib { font-weight: 700; width: 245px }
table.vol td.lec { color: #444; font-size: 7.8px }
.reserve { margin: 5px 0 0; font-size: 7.8px; color: #C01B1A; font-weight: 700 }
.axes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px }
.axe { border: 1px solid #D9DDE3; border-radius: 4px; padding: 6px 10px; height: 97px }
.axe .t { display: flex; gap: 6px; align-items: baseline }
.axe .t b.n { font-size: 15px; color: #1F3864 }
.axe .t b.x { font-size: 8.8px }
.axe p { margin: 2px 0 0 0; font-size: 7.9px; color: #444 }
h2.vert { color: #2E6C4F }
.recos { display: flex; gap: 11px }
.reco { flex: 1; border: 1px solid #2E6C4F; border-radius: 4px; background: #EEF5F1; padding: 7px 11px; height: 136px }
.reco h4 { margin: 0 0 3px 0; color: #2E6C4F; font-size: 8.8px }
.reco p { margin: 0; font-size: 7.8px }
.reco p.c { font-style: italic; color: #555; margin-top: 2px }
"""


def e(t):
    return html.escape(str(t), quote=False)


def entete(h, logo):
    st = "<br>".join(e(x) for x in h["sous_titre"])
    dr = "<br>".join(f"<b>{e(x)}</b>" if i == 0 else e(x) for i, x in enumerate(h["droite"]))
    return (f'<header><img src="data:image/png;base64,{logo}"><div class="sep"></div>'
            f'<div class="t"><h1>{e(h["titre"])}</h1><div class="st">{st}</div></div>'
            f'<div class="dr">{dr}</div></header>')


def kpis(liste, bas=False):
    return f'<div class="kpis{" bas" if bas else ""}">' + "".join(
        f'<div class="kpi"><b>{e(n)}</b><span>{t}</span></div>' for n, t in liste) + "</div>"


def page1(p, prio, logo):
    out = [entete(p["entete"], logo), '<div class="corps">', kpis(p["chiffres"])]
    r = p["risques"]
    out.append(f'<h2>{e(r["titre"])}<small>{e(r["legende"])}</small></h2><div class="cols">')
    for col in r["colonnes"]:
        out.append(f'<div class="col"><div class="colh">{e(col["titre"])}</div>')
        for k in col["risques"]:
            c = COULEURS[f"p{prio[k['ref']]}"]
            extra = ""
            if k.get("visites"):
                extra += f'<span class="bul">{k["visites"]}</span>'
            if k.get("incidents"):
                extra += f'<span class="inc">{k["incidents"]} inc.</span>'
            out.append(f'<div class="rk" style="border-left-color:{c}"><div class="l1"><span class="ref" style="color:{c}">{e(k["ref"])}</span>'
                       f'{extra}<span class="bdg" style="background:{c}">{e(k["echeance"])}</span></div><div class="tt">{e(k["titre"])}</div></div>')
        out.append("</div>")
    out.append("</div>")
    c = p["calendrier"]
    out.append(f'<h2 style="margin-top:6px">{e(c["titre"])}<small>{e(c["legende"])}</small></h2><div class="cal">')
    for g in c["groupes"]:
        n = len(g["refs"])
        out.append(f'<div><div class="h" style="background:{COULEURS[g["couleur"]]}"><span>{e(g["titre"])}</span><span>{n} risque{"s" if n > 1 else ""}</span></div>'
                   '<div class="chips">' + "".join(f'<span class="chip">{e(x)}</span>' for x in g["refs"]) + f'</div><div class="n">{e(g["note"])}</div></div>')
    out.append("</div>")
    rc, rs = p["recurrences"], p["reserves"]
    out.append(f'<div class="duo"><div class="box rec"><h3>{e(rc["titre"])}</h3><div class="i">{e(rc["intro"])}</div>')
    for n, ref, t in rc["lignes"]:
        out.append(f'<div class="ln"><span class="bul">{n}</span><b class="r">{e(ref)}</b><span>{e(t)}</span></div>')
    out.append(f'</div><div class="box res"><h3>{e(rs["titre"])}</h3>')
    for k, t in rs["lignes"]:
        out.append(f'<div class="ln"><b>{e(k)}</b><span>{e(t)}</span></div>')
    out.append("</div></div></div>")
    pd = p["pied"]
    leg = "".join(f'<span class="sq" style="background:{COULEURS[c]}"></span>{e(t)}' for c, t in pd["legende"])
    out.append(f'<div class="pied"><div class="l1">Priorité :{leg}<span class="rd">{e(pd["droite"])}</span></div><div class="l2">{e(pd["note"])}</div><div class="l3">{e(VERSION)}</div></div>')
    return "".join(out)


def page2(p, logo):
    out = [entete(p["entete"], logo), '<div class="corps">']
    d = p["dossiers"]
    out.append(f'<h2 style="margin-top:8px">{e(d["titre"])}<small>{e(d["legende"])}</small></h2><div class="cartes">')
    for c in d["cartes"]:
        col = COULEURS[c["couleur"]]
        out.append(f'<div class="carte" style="border-left-color:{col}"><div class="l1"><span class="id" style="color:{col}">{e(c["id"])}</span>'
                   f'<span class="bdg" style="background:{col}">{e(c["jalon"])}</span></div><h4>{e(c["titre"])}</h4>'
                   f'<div class="k">Porteur</div><div class="v">{e(c["porteur"])}</div><div class="k">État</div><div class="v">{e(c["etat"])}</div>'
                   f'<div class="k">Jalon</div><div class="v">{e(c["prochaine"])}</div><div class="refs">{e(c["refs"])}</div></div>')
    out.append("</div>")
    d = p["documents"]
    out.append(f'<h2 style="margin-top:14px">{e(d["titre"])}<small>{e(d["legende"])}</small></h2><div class="docs">')
    for g in d["groupes"]:
        out.append(f'<div class="g"><div class="h">{e(g["titre"])}</div>')
        for c, t, s in g["docs"]:
            out.append(f'<div class="d"><span class="dot" style="background:{COULEURS[c]}"></span><div><b>{e(t)}</b><span>{e(s)}</span></div></div>')
        out.append("</div>")
    out.append("</div></div>")
    pd = p["pied"]
    leg = "".join(f'<span class="dot" style="background:{COULEURS[c]};margin:0 3px 0 12px"></span>{e(t)}' for c, t in pd["legende_etat"])
    out.append(f'<div class="pied"><div class="l1">État du document :{leg}<span class="rd">{e(pd["droite"])}</span></div><div class="l3">{e(VERSION)}</div></div>')
    return "".join(out)


def page3(p, logo):
    out = [entete(p["entete"], logo), '<div class="corps">', kpis(p["chiffres"], bas=True)]
    v = p["volume"]
    out.append(f'<h2>{e(v["titre"])}<small>{e(v["legende"])}</small></h2><table class="vol"><tr><th>Type d’activité</th>'
               + "".join(f'<th style="text-align:center">{e(m)}</th>' for m in v["mois"]) + '<th style="text-align:center">Total</th><th>Lecture</th></tr>')
    for lib, vals, tot, lec in v["lignes"]:
        out.append(f'<tr><td class="lib">{e(lib)}</td>' + "".join(f'<td class="n">{"—" if x is None else x}</td>' for x in vals)
                   + f'<td class="tot">{tot}</td><td class="lec">{e(lec)}</td></tr>')
    out.append("</table>")
    if v.get("reserve"):
        out.append(f'<p class="reserve">{e(v["reserve"])}</p>')
    a = p["axes"]
    out.append(f'<h2 style="margin-top:10px">{e(a["titre"])}<small>{e(a["legende"])}</small></h2><div class="axes">')
    for n, t, x in a["cartes"]:
        out.append(f'<div class="axe"><div class="t"><b class="n">{e(n)}</b><b class="x">{e(t)}</b></div><p>{e(x)}</p></div>')
    out.append("</div>")
    r = p["reconnaissance"]
    out.append(f'<h2 class="vert" style="margin-top:10px">{e(r["titre"])}<small>{e(r["legende"])}</small></h2><div class="recos">')
    for t, x, c in r["cartes"]:
        out.append(f'<div class="reco"><h4>{e(t)}</h4><p>{e(x)}</p><p class="c">{e(c)}</p></div>')
    out.append("</div></div>")
    out.append(f'<div class="pied"><div class="l2" style="text-align:right">{e(p["pied"]["droite"])}</div><div class="l3">{e(VERSION)}</div></div>')
    return "".join(out)


VERSION = ligne_version("PDF — pièce de référence, à joindre au procès-verbal")


def construire_html(avec_prive=True):
    avec_prive = avec_prive and prive_disponible()
    plan = remplacer_jetons(lire_json(DONNEES / "plan_action.json"), table_des_noms(avec_prive))
    v = lire_json(DONNEES / "version.json")
    entete_version = f"{v['etat']} — {v['date_longue']}, version {v['version']}"
    plan = json.loads(json.dumps(plan).replace("__VERSION__", entete_version))
    prio = {r["ref"]: r["prio"] for r in lire_json(DONNEES / "registre_html.json")["risques"]}
    logo = base64.b64encode((GABARITS / "assets" / "logo_telecon.png").read_bytes()).decode("ascii")
    p1, p2, p3 = plan["pages"]
    pages = [page1(p1, prio, logo), page2(p2, logo), page3(p3, logo)]
    return ('<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><style>' + CSS + "</style></head><body>"
            + "".join(f'<section class="page">{x}</section>' for x in pages) + "</body></html>")


def generer(avec_prive=True, sortie=None):
    from playwright.sync_api import sync_playwright
    sortie = sortie or SORTIE / nom_versionne("Plan_action_SST_comite_Infra_QC", ".pdf")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    source = sortie.with_suffix(".html")
    source.write_text(construire_html(avec_prive), encoding="utf-8")
    with sync_playwright() as p:
        nav = p.chromium.launch()
        page = nav.new_page()
        page.goto(source.resolve().as_uri())
        page.pdf(path=str(sortie), width="11in", height="8.5in", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        nav.close()
    print(f"plan d'action → {sortie}")
    return sortie


if __name__ == "__main__":
    import sys
    generer(avec_prive="--sans-prive" not in sys.argv)
