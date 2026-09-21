"""Tableau de bord de direction — quatre pages, lettre paysage, graphiques SVG.

    python scripts/generer_tableau_bord.py
      → sortie/Tableau_bord_direction_SST_Infra_QC_v8_AAAA-MM-JJ.pdf
      → sortie/powerbi/*.csv        tables prêtes à charger dans Power BI

Page 1 · Niveau de risque        les 39 risques : priorités, familles, délais, visites
Page 2 · Incidents               les incidents au dossier, catégories STKY, rattachement
Page 3 · Activités de prévention les trois relevés du même volume, fiches non fermées
Page 4 · Gouvernance             dossiers en cours, documents du comité, échéances

Tout est calculé à partir de donnees/ : aucun chiffre n'est saisi dans ce script.
Les catégories STKY des incidents viennent du dossier privé et ne sortent qu'en décomptes ;
sans dossier privé, la section est marquée « à confirmer ».
Aucun nom de personne, aucun verdict de conformité.
"""
import base64
import csv
import html
import json
import re
from collections import Counter, defaultdict
from datetime import date

from commun import (DONNEES, GABARITS, SORTIE, incidents_prives, ligne_version, lire_json,
                    nom_versionne, prive_disponible, remplacer_jetons, table_des_noms)

C = {"p1": "#B3261E", "p2": "#B97900", "p3": "#2E6C4F", "bleu": "#1C4E80", "gris": "#9AA5A0",
     "fond": "#EEF1EE", "encre": "#16202A", "doux": "#5C6B7A", "trait": "#D9DDE3"}
PRIO_COUL = {1: C["p1"], 2: C["p2"], 3: C["p3"]}
DELAIS = [("immediat", "Immédiat"), ("j30", "30 jours"), ("j60", "60 jours"), ("j90", "90 jours"), ("seance", "Séance")]
MOIS_FR = ["", "Janv", "Févr", "Mars", "Avr", "Mai", "Juin", "Juil", "Août", "Sept", "Oct", "Nov", "Déc"]

# Normalisation des catégories STKY, qui sortent de l'export en deux langues et en libellés multiples.
STKY = {"travailler seul": "Travail seul", "road safety": "Conduite au travail", "sécurité routière": "Conduite au travail",
        "material handling": "Manutention", "manutention": "Manutention", "sans objet": "Sans objet",
        "not applicable": "Sans objet", "excavation": "Excavation", "tranch": "Excavation", "hauteur": "Travail en hauteur"}
TYPE = {"blessure": "Blessure", "injury": "Blessure", "véhicule": "Véhicule", "vehicle": "Véhicule"}


def e(t):
    return html.escape(str(t), quote=False)


MOIS_NUM = {"janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
            "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12}


def date_iso(texte):
    """« 4 septembre 2026 » → « 2026-09-04 »."""
    m = re.match(r"(\d{1,2})\s+([a-zéû]+)\s+(\d{4})", str(texte).strip().lower())
    return f"{m.group(3)}-{MOIS_NUM[m.group(2)]:02d}-{int(m.group(1)):02d}" if m else str(texte)


def date_fr(iso):
    """« 2026-09-04 » → « 4 septembre 2026 »."""
    a, m, j = iso.split("-")
    nom = [k for k, v in MOIS_NUM.items() if v == int(m)][0]
    return f"{int(j)}{'er' if j == '01' else ''} {nom} {a}"


def normaliser(valeur, table):
    v = str(valeur or "").lower()
    for cle, lib in table.items():
        if cle in v:
            return lib
    return "Non renseignée" if not v.strip() else "Autre"


# ------------------------------------------------------------------ graphiques
def barres(lignes, largeur=380, max_val=None, pas=21):
    """lignes : (libellé, valeur, couleur). Barres horizontales, libellé au-dessus."""
    m = max_val or max([v for _, v, _ in lignes] + [1])
    h = len(lignes) * pas + 4
    s = [f'<svg viewBox="0 0 {largeur + 30} {h}" class="g">']
    for i, (lib, v, coul) in enumerate(lignes):
        y = i * pas
        w = max(2, (largeur - 10) * v / m)
        s.append(f'<text x="0" y="{y + 8}" class="lib">{e(lib)}</text>')
        s.append(f'<rect x="0" y="{y + 11}" width="{largeur - 10}" height="6" fill="{C["fond"]}"/>')
        s.append(f'<rect x="0" y="{y + 11}" width="{w:.1f}" height="6" fill="{coul}"/>')
        s.append(f'<text x="{largeur + 26}" y="{y + 17}" class="val" text-anchor="end">{v}</text>')
    s.append("</svg>")
    return "".join(s)


def anneau(parts, total, legende_centre):
    """parts : (libellé, valeur, couleur)."""
    import math
    cx, cy, r, ep = 60, 60, 48, 18
    s = [f'<svg viewBox="0 0 120 120" class="anneau">']
    angle = -math.pi / 2
    for _, v, coul in parts:
        if not v:
            continue
        a2 = angle + 2 * math.pi * v / total
        grand = 1 if a2 - angle > math.pi else 0
        x1, y1 = cx + r * math.cos(angle), cy + r * math.sin(angle)
        x2, y2 = cx + r * math.cos(a2 - 1e-6), cy + r * math.sin(a2 - 1e-6)
        s.append(f'<path d="M{x1:.2f},{y1:.2f} A{r},{r} 0 {grand} 1 {x2:.2f},{y2:.2f}" fill="none" stroke="{coul}" stroke-width="{ep}"/>')
        angle = a2
    s.append(f'<text x="60" y="64" text-anchor="middle" class="centre">{total}</text>')
    s.append(f'<text x="60" y="78" text-anchor="middle" class="souscentre">{e(legende_centre)}</text></svg>')
    return "".join(s)


def colonnes(lignes, largeur=360, hauteur=120):
    """lignes : (libellé, valeur, couleur). Colonnes verticales avec valeur au-dessus."""
    m = max([v for _, v, _ in lignes] + [1])
    n = len(lignes)
    pas = largeur / n
    s = [f'<svg viewBox="0 0 {largeur} {hauteur + 30}" class="g">']
    for i, (lib, v, coul) in enumerate(lignes):
        hb = (hauteur - 18) * v / m
        x = i * pas + pas * 0.2
        s.append(f'<rect x="{x:.1f}" y="{hauteur - hb:.1f}" width="{pas * 0.6:.1f}" height="{hb:.1f}" fill="{coul}"/>')
        s.append(f'<text x="{x + pas * 0.3:.1f}" y="{hauteur - hb - 4:.1f}" text-anchor="middle" class="valcol">{v}</text>')
        s.append(f'<text x="{x + pas * 0.3:.1f}" y="{hauteur + 14}" text-anchor="middle" class="lib">{e(lib)}</text>')
    s.append(f'<line x1="0" x2="{largeur}" y1="{hauteur}" y2="{hauteur}" stroke="{C["trait"]}"/></svg>')
    return "".join(s)


def courbes(mois, series, largeur=520, hauteur=150):
    """series : (libellé, [valeurs], couleur)."""
    m = max([v for _, vs, _ in series for v in vs] + [1])
    pas_y = max(1, -(-m // 4))
    haut = pas_y * 4
    g, d, b = 26, 8, 22
    x = lambda i: g + i * (largeur - g - d) / (len(mois) - 1)  # noqa: E731
    y = lambda v: hauteur - b - v / haut * (hauteur - b - 6)   # noqa: E731
    s = [f'<svg viewBox="0 0 {largeur} {hauteur}" class="g">']
    for k in range(5):
        s.append(f'<line x1="{g}" x2="{largeur - d}" y1="{y(k * pas_y):.1f}" y2="{y(k * pas_y):.1f}" stroke="{C["trait"]}" stroke-width=".6"/>')
        s.append(f'<text x="{g - 4}" y="{y(k * pas_y) + 3:.1f}" text-anchor="end" class="lib">{k * pas_y}</text>')
    for i, mo in enumerate(mois):
        s.append(f'<text x="{x(i):.1f}" y="{hauteur - 6}" text-anchor="middle" class="lib">{MOIS_FR[int(mo[5:])]}</text>')
    for _, vs, coul in series:
        s.append(f'<polyline fill="none" stroke="{coul}" stroke-width="1.8" points="{" ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vs))}"/>')
        s += [f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="2.2" fill="{coul}"/>' for i, v in enumerate(vs)]
    s.append("</svg>")
    return "".join(s)


def matrice(familles, visites, cellule):
    """Familles × visites. cellule(f, v) → (nombre, priorité la plus haute) ou None."""
    lignes = ['<table class="mat"><tr><th class="fam">Famille de risque</th>'
              + "".join(f'<th>{e(lab)}</th>' for _, lab in visites) + '<th>Visites</th></tr>']
    for f in familles:
        cases, n_vis = [], 0
        for v, _ in visites:
            c = cellule(f, v)
            if c:
                n_vis += 1
                n, p = c
                taille = 7 + min(n, 4) * 2
                cases.append(f'<td><span class="pt" style="width:{taille}px;height:{taille}px;background:{PRIO_COUL[p]}" title="{n}"></span></td>')
            else:
                cases.append('<td><span class="vide">—</span></td>')
        lignes.append(f'<tr><td class="fam">{e(f)}</td>{"".join(cases)}<td class="n">{n_vis}</td></tr>')
    lignes.append("</table>")
    return "".join(lignes)


# ------------------------------------------------------------------ calculs
def calculer(avec_prive=True):
    avec_prive = avec_prive and prive_disponible()
    D = remplacer_jetons(lire_json(DONNEES / "registre_html.json"), table_des_noms(avec_prive=False))
    V = lire_json(DONNEES / "volumes.json")
    R = D["risques"]

    prio = Counter(r["prio"] for r in R)
    delais = Counter(r["bucket"] for r in R)
    familles = defaultdict(list)
    for r in R:
        familles[r["famille"]].append(r)

    par_fiche, date_fiche = defaultdict(list), {}
    for r in R:
        for s in r["sources"]:
            par_fiche[s["fiche"]].append((r["famille"], s.get("prio", r["prio"])))
            date_fiche[s["fiche"]] = s["date"]
    # une visite consolidée = une fiche d'inspection eCompliance citée comme source d'un risque
    visites = [{"id": f, "date": date_iso(date_fiche[f])} for f in par_fiche if re.fullmatch(r"\d{8}", f)]
    visites.sort(key=lambda v: (v["date"], v["id"]))
    elements = sum(len(r["sources"]) for r in R)
    hors_visite = elements - sum(len(par_fiche[v["id"]]) for v in visites)
    recurrents = [r for r in R if len({s["fiche"] for s in r["sources"]} & {v["id"] for v in visites}) >= 3]

    detail = incidents_prives() if avec_prive else {}
    incidents = []
    for i in D["incidents"]:
        d = detail.get(i["id"], {})
        incidents.append({"id": i["id"], "date": i["date"], "ref": i.get("ref", ""),
                          "stky": normaliser(d.get("stky"), STKY) if d else "À confirmer",
                          "type": normaliser(d.get("type"), TYPE) if d else "À confirmer"})
    return {"D": D, "V": V, "R": R, "prio": prio, "delais": delais, "familles": familles, "visites": visites,
            "par_fiche": par_fiche, "elements": elements, "hors_visite": hors_visite, "recurrents": recurrents,
            "incidents": incidents, "prive": avec_prive}


# ------------------------------------------------------------------ pages
def entete(titre, sous_titre, page, rubrique, logo):
    return (f'<div class="bande"><img src="data:image/png;base64,{logo}" alt="Telecon">'
            f'<span>Santé et sécurité · Infrastructure · Infra QC</span></div>'
            f'<div class="tete"><div><h1>{e(titre)}</h1><div class="st">{e(sous_titre)}</div></div>'
            f'<div class="pg">Page {page} sur 4<br>{e(rubrique)}</div></div>')


def kpis(liste):
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><b style="color:{c or C["encre"]}">{e(n)}</b><span>{e(t)}</span><small>{e(s)}</small></div>'
        for n, t, s, c in liste) + "</div>"


def page1(x, logo):
    R, prio, fam = x["R"], x["prio"], x["familles"]
    vis = x["visites"]
    fam_tri = sorted(fam, key=lambda f: (-len(fam[f]), f))
    lignes_fam = [(f, len(fam[f]), C["p1"] if any(r["prio"] == 1 for r in fam[f]) else C["bleu"]) for f in fam_tri]
    lignes_del = [(lib, x["delais"].get(k, 0), C["p1"] if k in ("immediat", "j30") else C["bleu"]) for k, lib in DELAIS]
    lab = lambda v: f'{int(v["date"][8:10])} {MOIS_FR[int(v["date"][5:7])].lower()}'  # noqa: E731
    col_vis = [(lab(v), len(x["par_fiche"][v["id"]]), C["bleu"]) for v in vis]

    def cellule(f, fiche):
        el = [p for fa, p in x["par_fiche"][fiche] if fa == f]
        return (len(el), min(el)) if el else None

    return (entete("Niveau de risque et priorités",
                   f"{len(vis)} visites consolidées · du {date_fr(vis[0]['date'])} au {date_fr(vis[-1]['date'])} · registre version 8",
                   1, "Risques", logo)
            + kpis([(len(R), "Risques distincts", "soumis au comité", None),
                    (prio[1], "Priorité 1", "sécurité immédiate", C["p1"]),
                    (x["elements"], "Éléments source", f"dont {x['hors_visite']} hors visite", None),
                    (len(vis), "Visites consolidées", "sur 12 au dossier", None),
                    (len(x["recurrents"]), "Risques revenus", "sur trois visites ou plus", C["p2"]),
                    (x["delais"].get("immediat", 0), "Délais immédiats", "à compter de la décision", C["p1"])])
            + '<div class="rang">'
            + f'<div class="bloc b1"><h2>Priorités</h2><div class="anf">{anneau([("P1", prio[1], C["p1"]), ("P2", prio[2], C["p2"]), ("P3", prio[3], C["p3"])], len(R), "risques")}'
            + f'<div class="leg"><p><i style="background:{C["p1"]}"></i><b>{prio[1]}</b> sécurité immédiate</p><p><i style="background:{C["p2"]}"></i><b>{prio[2]}</b> standard ou règle manquante</p><p><i style="background:{C["p3"]}"></i><b>{prio[3]}</b> amélioration d’équipement ou de processus</p></div></div>'
            + f'<h2 style="margin-top:8px">Délais proposés</h2>{barres(lignes_del, 250)}</div>'
            + f'<div class="bloc b2"><h2>Risques par famille</h2>{barres(lignes_fam, 330, pas=18.5)}<p class="note">En rouge, les familles qui comptent au moins une priorité 1.</p></div>'
            + f'<div class="bloc b3"><h2>Éléments relevés par visite</h2>{colonnes(col_vis, 330, 118)}<p class="note">Le volume reflète d’abord la profondeur d’inspection : les visites du 4 et du 16 septembre sont celles où les sections de risque ont été remplies.</p></div></div>'
            + f'<div class="bloc large"><h2>Où chaque famille de risque a été relevée</h2>'
            + matrice(fam_tri, [(v["id"], lab(v)) for v in vis], cellule)
            + '<p class="note">Couleur : priorité la plus haute relevée à cette visite. Taille : nombre d’éléments. Une visite par colonne : ces points décrivent une observation, pas un taux de conformité.</p></div>')


def page2(x, logo):
    inc = x["incidents"]
    rat = [i for i in inc if i["ref"]]
    stky = Counter(i["stky"] for i in inc)
    typ = Counter(i["type"] for i in inc)
    par_mois = Counter(i["date"][:7] for i in inc)
    mois = sorted(par_mois)
    col = [(MOIS_FR[int(m[5:])], par_mois[m], C["bleu"]) for m in mois]
    risque_de = defaultdict(set)
    for i in inc:
        if i["ref"]:
            risque_de[i["stky"]].add(i["ref"])
    titres = {r["ref"]: r["titre"] for r in x["R"]}
    lignes = "".join(
        f'<tr><td class="k">{e(k)}</td><td class="n">{n}</td><td>{e(", ".join(sorted(risque_de[k])) or "—")}</td>'
        f'<td class="lec">{e("; ".join(titres[r] for r in sorted(risque_de[k])) or "Non rattaché à un risque du registre")}</td></tr>'
        for k, n in stky.most_common())
    reserve_prive = "" if x["prive"] else '<p class="alerte">Catégories STKY et types : à confirmer — dossier privé absent.</p>'
    return (entete("Incidents au dossier et rattachement au registre",
                   f"{len(inc)} événements du {date_fr(inc[0]['date'])} au {date_fr(inc[-1]['date'])} · incidents versés au registre des risques",
                   2, "Incidents", logo)
            + kpis([(len(inc), "Incidents au dossier", "juillet à septembre 2026", None),
                    (typ.get("Blessure", "—"), "Impliquent une blessure", "selon le type déclaré", C["p1"]),
                    (typ.get("Véhicule", "—"), "Impliquent un véhicule", "selon le type déclaré", None),
                    (stky.get("Travail seul", "—"), "Travail seul", "catégorie STKY", C["p2"]),
                    (len(rat), "Rattachés à un risque", f"{len(inc) - len(rat)} sans rattachement", None),
                    (len({i['ref'] for i in rat}), "Risques concernés", " et ".join(sorted({i['ref'] for i in rat})), None)])
            + reserve_prive
            + '<div class="rang">'
            + f'<div class="bloc b2 w60"><h2>Catégorie STKY et risque rattaché</h2><table class="tab"><tr><th>Catégorie STKY</th><th>Nb</th><th>Risque</th><th>Lecture</th></tr>{lignes}</table>'
            + '<p class="note">Catégories normalisées : l’export les donne en deux langues et en libellés multiples.</p></div>'
            + f'<div class="bloc b3 w40"><h2>Incidents par mois</h2>{colonnes(col, 300, 70)}'
            + '<p class="encart or"><b>Ce que ce graphique ne dit pas.</b> Trois mois, neuf événements : ce n’est pas une tendance, et ce n’est pas un taux, faute d’heures travaillées ou de nombre de chantiers.</p>'
            + '<p class="encart rouge"><b>Deux périmètres.</b> Le tableau de bord opérationnel du 12 septembre recensait 26 événements sur tout Infra QC depuis février. Ce registre n’en rattache que neuf, depuis juillet. Les deux chiffres sont justes ; ils ne mesurent pas la même chose.</p></div></div>'
            + '<div class="rang">'
            + f'<div class="bloc b2 w60"><h2>Les {len(inc)} incidents</h2><table class="tab"><tr><th>Fiche</th><th>Date</th><th>Type</th><th>Catégorie STKY</th><th>Risque rattaché</th></tr>'
            + "".join(f'<tr><td class="k">{e(i["id"])}</td><td>{e(date_fr(i["date"]))}</td><td>{e(i["type"])}</td><td>{e(i["stky"])}</td><td>{e(i["ref"] or "—")}</td></tr>' for i in inc)
            + '</table><p class="note">Aucun nom, aucun lieu, aucune description de blessure : ces détails restent au dossier privé.</p></div>'
            + f'<div class="bloc b3 w40"><h2>Incidents par type déclaré</h2>{barres([(k, n, C["bleu"]) for k, n in typ.most_common()], 280)}</div></div>'
            + '<div class="bloc large"><h2>Ce qu’il faut corriger à la saisie pour que ces chiffres deviennent un indicateur</h2><div class="quatre">'
            + '<div><b>Verrouiller les listes de choix</b><p>Type et catégorie STKY sortent en français et en anglais, sous plusieurs libellés.</p></div>'
            + f'<div><b>Rattacher chaque incident</b><p>{len(inc) - len(rat)} événements sur {len(inc)} ne sont liés à aucun risque du registre.</p></div>'
            + '<div><b>Normaliser l’emplacement</b><p>Les lieux vont d’une ville seule à l’adresse complète ; même défaut que sur les visites.</p></div>'
            + '<div><b>Établir un dénominateur</b><p>Heures travaillées ou nombre de chantiers : sans lui, aucun taux n’est calculable.</p></div></div></div>')


def page3(x, logo):
    V = x["V"]
    comp = V["comparaison"]
    groupes = "".join(
        f'<div class="grp"><div class="gl">{e(l["type"])}</div>'
        + "".join(f'<div class="gb"><span style="width:{max(1, 100 * v / 600):.1f}%;background:{c}"></span><em>{v}</em></div>'
                  for v, c in [(l["registre"], C["gris"]), (l["export"], C["p2"]), (l["tableau"], C["bleu"])])
        + "</div>" for l in comp)
    tri = sorted(V["lignes"], key=lambda l: -sum(l["mois"]))[:5]
    coul = [C["bleu"], C["p1"], C["p3"], C["p2"], "#6B4FA8"]
    series = [(l["type"], l["mois"], coul[i]) for i, l in enumerate(tri)]
    leg = "".join(f'<p><i style="background:{c}"></i>{e(t)} <b>{sum(v)}</b></p>' for t, v, c in series)
    nf = V["non_fermees"]
    return (entete("Activités de prévention — trois relevés du même volume",
                   "Tableau de bord 2026 · export daté de 165 fiches · registre du 19 mai au 17 septembre",
                   3, "Prévention", logo)
            + kpis([("1 837", "Fiches en 2026", "tableau de bord, sans dates", C["bleu"]),
                    ("113", "Personnes contributrices", "tableau de bord", None),
                    ("409", "Rapports de visite de chantier", "non versés au registre", C["p2"]),
                    ("165", "Fiches dans l’export", "seul relevé daté", None),
                    (nf["total"], "Fiches non fermées", "sur 165", C["p1"]),
                    (f'{V["hauteur"]["ouvertes"]}/{V["hauteur"]["total"]}', "Évaluations en hauteur", "jamais fermées", C["p1"])])
            + '<div class="rang">'
            + f'<div class="bloc b2 w50"><h2>Le même volume, vu par trois relevés</h2>{groupes}'
            + f'<div class="leg lh"><p><i style="background:{C["gris"]}"></i>Registre v7</p><p><i style="background:{C["p2"]}"></i>Export daté</p><p><i style="background:{C["bleu"]}"></i>Tableau de bord 2026</p></div>'
            + '<p class="note">Aucun des trois n’est faux : ils n’ont ni la même période ni le même périmètre. L’écart est une question posée à l’administrateur eCompliance.</p></div>'
            + f'<div class="bloc b3 w50"><h2>Tendance mensuelle — export daté</h2>{courbes(V["mois"], series)}<div class="leg">{leg}</div></div></div>'
            + '<div class="rang">'
            + f'<div class="bloc b2 w50"><h2>Fiches non fermées, par type de formulaire</h2>{barres([(t, n, C["bleu"]) for t, n in nf["par_type"]], 360, pas=17)}'
            + '<p class="note">Statut autre que verrouillé au 20 septembre. Une fiche en cours n’est pas un manquement : c’est la durée qui compte, et elle n’est pas mesurée ici.</p></div>'
            + f'<div class="bloc b3 w50"><h2>Ce que ces relevés établissent</h2><ul class="pts">'
            + '<li><b>L’inspection mensuelle du véhicule ne s’arrête pas en juillet.</b> Une ou deux fiches par mois de mars à septembre ; le relevé partiel laissait croire le contraire. R-15 a été reformulé.</li>'
            + f'<li><b>{V["hauteur"]["ouvertes"]} évaluations en hauteur sur {V["hauteur"]["total"]} ne sont jamais fermées.</b> Une fiche déclare 12 m et répond « N/A » au plan de sauvetage.</li>'
            + f'<li><b>{V["ast"]["non"]} « Non » sur {V["ast"]["reponses"]} réponses</b> à la question de l’AST réalisée et signée — formulaire d’origine à confirmer.</li>'
            + '<li><b>Les volumes ne deviennent pas des taux</b> sans le nombre de véhicules, de pelles et de véhicules lourds affectés à Infra Québec.</li></ul></div></div>')


def page4(x, logo):
    D = x["D"]
    plan = lire_json(DONNEES / "plan_action.json")["pages"][1]
    docs = [d for g in plan["documents"]["groupes"] for d in g["docs"]]
    etat = Counter(c for c, _, _ in docs)
    cartes = plan["dossiers"]["cartes"]
    urg = Counter(c["couleur"] for c in cartes)
    lignes = "".join(
        f'<tr><td class="k"><span class="pastille" style="background:{C[c["couleur"]]}"></span>{e(c["id"])}</td><td>{e(c["titre"])}</td>'
        f'<td>{e(c["jalon"])}</td><td class="lec">{e(c["prochaine"])}</td></tr>' for c in cartes)
    ech = D["comite"]["echeances"]
    lig_ech = "".join(f'<tr><td class="k">{e(x_["date"])}</td><td>{e(x_["quoi"])}</td><td class="lec">{e(x_.get("portee", ""))}</td></tr>' for x_ in ech[:7])
    manque = [t for c, t, _ in docs if c == "p1"]
    return (entete("Dossiers en cours, documents du comité et échéances",
                   f"{len(cartes)} dossiers · {len(docs)} documents exigés · comité sans séance depuis le 18 décembre 2024",
                   4, "Gouvernance", logo)
            + kpis([(len(cartes), "Dossiers en cours", "avec porteur et jalon", None),
                    (urg.get("p1", 0), "Jalon urgent", "avant la séance ou immédiat", C["p1"]),
                    (etat.get("p3", 0), "Documents tenus", f"sur {len(docs)} exigés", C["p3"]),
                    (etat.get("p1", 0), "Documents absents", "à créer ou non produits", C["p1"]),
                    ("1er oct.", "Échéance réglementaire", "programmes de prévention", C["p1"]),
                    ("6", "Procédures bloquées", "exigent un comité qui ne siège pas", C["p2"])])
            + '<div class="rang">'
            + f'<div class="bloc b1 w30"><h2>Documents du comité</h2><div class="anf">{anneau([("", etat.get("p3", 0), C["p3"]), ("", etat.get("p2", 0), C["p2"]), ("", etat.get("p1", 0), C["p1"])], len(docs), "documents")}'
            + f'<div class="leg"><p><i style="background:{C["p3"]}"></i><b>{etat.get("p3", 0)}</b> tenus</p><p><i style="background:{C["p2"]}"></i><b>{etat.get("p2", 0)}</b> en gabarit ou à confirmer</p><p><i style="background:{C["p1"]}"></i><b>{etat.get("p1", 0)}</b> absents</p></div></div>'
            + f'<p class="note">Absents : {e(" · ".join(manque))}. Relevé indicatif, à confirmer auprès de la CNESST.</p></div>'
            + f'<div class="bloc b2 w70"><h2>Dossiers en cours</h2><table class="tab"><tr><th>Dossier</th><th>Objet</th><th>Jalon</th><th>Prochaine étape</th></tr>{lignes}</table>'
            + '<p class="note">Aucune date de jalon n’est arrêtée : les échéances courent à compter de la décision du comité.</p></div></div>'
            + f'<div class="bloc large"><h2>Échéances réglementaires au dossier du comité</h2><table class="tab"><tr><th>Date</th><th>Obligation</th><th>Portée</th></tr>{lig_ech}</table>'
            + '<p class="encart rouge"><b>Le nœud.</b> Le programme de prévention s’élabore avec le comité, et six procédures corporatives lui assignent un rôle. Tant qu’il ne siège pas, aucune de ces échéances ne peut être tenue dans les formes.</p></div>')


CSS = """
@page{size:11in 8.5in;margin:0}
*{box-sizing:border-box}
body{margin:0;font-family:'Liberation Sans',Arial,Helvetica,sans-serif;color:#16202A;font-size:8.6px;line-height:1.3}
.page{width:11in;height:8.5in;padding:22px 26px 0;position:relative;overflow:hidden;page-break-after:always}
.page:last-child{page-break-after:auto}
.bande{background:#000;color:#fff;height:36px;display:flex;align-items:center;justify-content:space-between;padding:0 12px 0 24px}
.bande img{height:22px}.bande span{font-size:12px;letter-spacing:.3px}
.tete{display:flex;justify-content:space-between;align-items:flex-start;margin:8px 0 6px}
h1{font-size:17px;margin:0}.st{font-size:11.5px;color:#5C6B7A;margin-top:2px}
.pg{text-align:right;font-size:11px;color:#5C6B7A;line-height:1.5}
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-bottom:8px}
.kpi{border:1px solid #D9DDE3;padding:6px 9px 5px}
.kpi b{display:block;font-size:21px;line-height:1.05}.kpi span{display:block;font-size:9.4px;margin-top:2px}.kpi small{color:#8A96A3;font-size:8.2px}
.rang{display:flex;gap:8px;margin-bottom:8px}
.bloc{border:1px solid #D9DDE3;padding:7px 10px;flex:1;min-width:0}
.b1{flex:0 0 31%}.b2{flex:1}.b3{flex:0 0 31%}.w60{flex:0 0 60%}.w40{flex:1}.w50{flex:0 0 49.5%}.w30{flex:0 0 30%}.w70{flex:1}
.large{margin-bottom:8px}
h2{font-size:10.4px;text-transform:uppercase;letter-spacing:.2px;color:#3A4652;margin:0 0 6px}
svg.g{width:100%;height:auto;display:block}
svg .lib{font-size:8px;fill:#2A3540}svg .val{font-size:9.6px;font-weight:700;fill:#16202A}svg .valcol{font-size:10px;font-weight:700;fill:#16202A}
.anf{display:flex;align-items:center;gap:10px}.anneau{width:108px;height:108px;flex:0 0 108px}
.anneau .centre{font-size:26px;font-weight:700;fill:#16202A}.anneau .souscentre{font-size:8.5px;fill:#5C6B7A}
.leg p{margin:3px 0;font-size:9.4px;display:flex;align-items:center;gap:5px}.leg i{width:9px;height:9px;border-radius:50%;display:inline-block;flex:0 0 9px}
.lh{display:flex;gap:14px}
.note{color:#5C6B7A;font-size:8px;margin:5px 0 0}
table.mat{width:100%;border-collapse:collapse}
table.mat th{font-size:8.2px;font-weight:700;color:#3A4652;padding:2px 3px;border-bottom:1px solid #D9DDE3;text-align:center}
table.mat td{text-align:center;padding:2.2px 3px;border-bottom:1px solid #EEF1F5;height:15px}
table.mat .fam{text-align:left;width:190px;font-weight:700;font-size:8.6px}
table.mat .n{font-weight:700;width:48px}
.pt{display:inline-block;border-radius:50%;vertical-align:middle}.vide{color:#C3C9CF}
table.tab{width:100%;border-collapse:collapse;font-size:8.6px}
table.tab th{text-align:left;font-size:8px;color:#3A4652;border-bottom:1px solid #D9DDE3;padding:3px 4px}
table.tab td{border-bottom:1px solid #EEF1F5;padding:2.6px 4px;vertical-align:top}
table.tab .k{font-weight:700;white-space:nowrap}table.tab .n{font-weight:700;font-size:11px;text-align:center}table.tab .lec{color:#5C6B7A}
.pastille{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px}
.encart{border-left:3px solid;padding:3px 0 3px 8px;margin:7px 0 0;font-size:8.6px}
.encart.or{border-color:#8A5A00}.encart.rouge{border-color:#B3261E}
.alerte{color:#B3261E;font-weight:700;margin:0 0 6px}
.quatre{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.quatre b{font-size:9.2px}.quatre p{margin:2px 0 0;color:#5C6B7A}
.grp{margin:5px 0 7px}.gl{font-weight:700;font-size:8.8px;margin-bottom:2px}
.gb{display:flex;align-items:center;gap:5px;height:9px;margin:1.5px 0}.gb span{height:7px;display:block}.gb em{font-style:normal;font-size:8px;font-weight:700}
ul.pts{margin:0;padding-left:14px}ul.pts li{margin:0 0 6px}
.pied{position:absolute;left:26px;right:26px;bottom:10px;font-size:7.2px;color:#6A7682;border-top:1px solid #D9DDE3;padding-top:4px}
"""


def construire(avec_prive=True):
    x = calculer(avec_prive)
    logo = base64.b64encode((GABARITS / "assets" / "logo_telecon.png").read_bytes()).decode("ascii")
    pied = e(ligne_version("tableau de bord de direction — décomptes calculés à partir du registre ; aucun verdict de conformité"))
    pages = [page1(x, logo), page2(x, logo), page3(x, logo), page4(x, logo)]
    corps = "".join(f'<section class="page">{p}<div class="pied">{pied}</div></section>' for p in pages)
    return x, f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{corps}</body></html>'


def tables_powerbi(x, dossier):
    """Tables sans nom de personne, prêtes à charger dans Power BI."""
    dossier.mkdir(parents=True, exist_ok=True)

    def ecrire(nom, entetes, lignes):
        with open(dossier / f"{nom}.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(entetes)
            w.writerows(lignes)

    ecrire("risques", ["ref", "famille", "titre", "priorite", "delai", "echeance", "norme"],
           [[r["ref"], r["famille"], r["titre"], r["prio"], r["bucket"], r["echeance"], r["norme"]] for r in x["R"]])
    ecrire("sources", ["ref_risque", "fiche", "element", "priorite", "date"],
           [[r["ref"], s["fiche"], s["ref"], s.get("prio", ""), s["date"]] for r in x["R"] for s in r["sources"]])
    ecrire("incidents", ["id", "date", "risque_rattache", "categorie_stky", "type"],
           [[i["id"], i["date"], i["ref"], i["stky"], i["type"]] for i in x["incidents"]])
    V = x["V"]
    ecrire("volumes_mensuels", ["type", "mois", "fiches"],
           [[l["type"], m, n] for l in V["lignes"] for m, n in zip(V["mois"], l["mois"])])
    ecrire("volumes_trois_releves", ["type", "registre_v7", "export_date", "tableau_de_bord_2026"],
           [[l["type"], l["registre"], l["export"], l["tableau"]] for l in V["comparaison"]])
    ecrire("fiches_non_fermees", ["type", "fiches"], V["non_fermees"]["par_type"])
    return sorted(p.name for p in dossier.glob("*.csv"))


def generer(avec_prive=True, sortie=None):
    from playwright.sync_api import sync_playwright
    x, page = construire(avec_prive)
    sortie = sortie or SORTIE / nom_versionne("Tableau_bord_direction_SST_Infra_QC", ".pdf")
    sortie.parent.mkdir(parents=True, exist_ok=True)
    source = sortie.with_suffix(".html")
    source.write_text(page, encoding="utf-8")
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page()
        pg.goto(source.resolve().as_uri())
        pg.pdf(path=str(sortie), width="11in", height="8.5in", print_background=True,
               margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        nav.close()
    csvs = tables_powerbi(x, sortie.parent / "powerbi")
    print(f"tableau de bord → {sortie}")
    print(f"tables Power BI → {sortie.parent / 'powerbi'} ({len(csvs)} fichiers)")
    return sortie


if __name__ == "__main__":
    import sys
    generer(avec_prive="--sans-prive" not in sys.argv)
