"""Présentation du projet, divisée par acteur — HTML autonome et PDF.

    python scripts/generer_presentation.py
      → sortie/Presentation_par_acteur_v8_AAAA-MM-JJ.html   un sélecteur d'acteur, une section par auditoire
      → sortie/Presentation_par_acteur_v8_AAAA-MM-JJ.pdf    toutes les sections, une par page

Auditoires : directeur SST, comité SST, direction des opérations, TI, terrain.

Tous les chiffres sont lus dans donnees/ au moment de la génération, pour que la présentation
ne prenne plus de retard sur le dossier : la version du 20 septembre en avait pris en une soirée.
Aucun nom de personne ; aucun verdict de conformité.
"""
import base64
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import (DONNEES, GABARITS, RACINE, SORTIE, ligne_version, lire_json,  # noqa: E402
                    nom_versionne, remplacer_jetons, table_des_noms)

ABSENTE = "ABSENTE DE L'INDEX"   # libellé renvoyé par verifier_citations.py
ONGLETS_GENERES = 2   # « Volumes et tendances » et « Recommandations au comité », ajoutés par generer_classeur.py


def e(t):
    return html.escape(str(t), quote=False)


def faits():
    """Tout ce que la présentation affiche, calculé à partir des données du dépôt."""
    sans_noms = table_des_noms(avec_prive=False)
    D = remplacer_jetons(lire_json(DONNEES / "registre_html.json"), sans_noms)
    P = remplacer_jetons(lire_json(DONNEES / "plan_action.json"), sans_noms)
    V = lire_json(DONNEES / "volumes.json")
    Rc = lire_json(DONNEES / "recommandations.json")
    ver = lire_json(DONNEES / "version.json")
    R = D["risques"]
    fiches = {s["fiche"] for r in R for s in r["sources"] if re.fullmatch(r"\d{8}", s["fiche"])}
    docs = [d for g in P["pages"][1]["documents"]["groupes"] for d in g["docs"]]
    etat_docs = Counter(c for c, _, _ in docs)

    try:
        import ordre_du_jour
        n_points = len(ordre_du_jour.construire_points())
    except Exception:  # noqa: BLE001
        n_points = None

    citations = None
    try:
        import os
        import verifier_citations as vc
        chemin = Path(os.environ.get("ANCRAGE_INDEX") or vc.INDEX_DEFAUT)
        if chemin.exists():
            citations = Counter(l[2] for l in vc.verifier(vc.index_procedures(chemin), R))
    except Exception:  # noqa: BLE001
        citations = None

    n_tests = sum(len(re.findall(r"^def test_", f.read_text(encoding="utf-8"), re.M))
                  for f in (RACINE / "tests").glob("test_*.py"))

    return {
        "ver": ver, "R": R, "n": len(R), "p1": sum(1 for r in R if r["prio"] == 1),
        "elements": sum(len(r["sources"]) for r in R), "visites": len(fiches), "incidents": len(D["incidents"]),
        "delais": Counter(r["bucket"] for r in R),
        "immediats": [r for r in R if r["bucket"] == "immediat"],
        "seance": [r for r in R if r["bucket"] == "seance"],
        "dossiers_seance": [i for i in D["initiatives"] if re.search(r"séance|immédiat|rencontre du comité", i.get("echeance", ""), re.I)],
        "decisions": D["comite"]["decisions"], "bloquantes": D["comite"]["bloquantes"],
        "echeances": D["comite"]["echeances"],
        "docs": (etat_docs.get("p3", 0), etat_docs.get("p2", 0), etat_docs.get("p1", 0), len(docs)),
        "sup": len(D["roles"]["superviseurs"]), "trav": len(D["roles"]["travailleurs"]),
        "reconnaissance": P["pages"][2]["reconnaissance"]["cartes"],
        "V": V, "delai_rec": Rc["delai_reponse"], "n_rec": len(Rc["recommandations"]),
        "points_odj": n_points, "citations": citations, "tests": n_tests,
        "onglets": len(lire_json(DONNEES / "classeur" / "_ordre.json")) + ONGLETS_GENERES,
        "incidents_rattaches": sum(1 for i in D["incidents"] if i.get("ref")),
    }


# ------------------------------------------------------------------ morceaux
def kpis(liste):
    return '<div class="kpis">' + "".join(f'<div class="kpi"><b>{e(n)}</b><span>{e(t)}</span></div>' for n, t in liste) + "</div>"


def carte(titre, texte, ton=""):
    return f'<div class="carte {ton}"><h4>{e(titre)}</h4><p>{texte}</p></div>'


def questions(qs):
    return '<div class="qs">' + "".join(f'<details><summary>{e(q)}</summary><p>{r}</p></details>' for q, r in qs) + "</div>"


def demandes(lignes):
    return ('<table class="dem"><tr><th>Ce qui vous est demandé</th><th>Pourquoi</th><th>Échéance</th></tr>'
            + "".join(f'<tr><td><b>{e(a)}</b></td><td>{b}</td><td class="ech">{e(c)}</td></tr>' for a, b, c in lignes) + "</table>")


def section(id_, titre, accroche, corps):
    return (f'<section class="acteur" id="a-{id_}" data-acteur="{id_}"><div class="oeil">{e(titre)}</div>'
            f'<h2>{e(accroche)}</h2>{corps}</section>')


# ------------------------------------------------------------------ sections
def commun(f):
    return (f'<section class="acteur commun" data-acteur="commun"><div class="oeil">Pour tous les auditoires</div>'
            '<h2>Tout est prêt pour que le comité reprenne ; ce qui manque, ce sont des décisions, pas des documents.</h2>'
            + kpis([(f["n"], "risques distincts"), (f["p1"], "de priorité 1"), (f["elements"], "éléments source"),
                    (f["visites"], "visites consolidées"), (f["incidents"], "incidents au dossier"), (f["tests"], "tests automatiques")])
            + '<div class="grille3">'
            + carte("Le point de départ", "Des visites SST consignées une à une dans eCompliance, sans être rapprochées. Un même écart pouvait revenir quatre fois sans que personne ne le voie. Aucun comité ne siège depuis le 18 décembre 2024.")
            + carte("Ce qui existe", f"Une seule source de données, d’où sortent tous les livrables : classeur de {f['onglets']} onglets, plan d’action PDF, tableau de bord de direction, page Comité avec mode séance, page Terrain, ordre du jour. Une correction se fait une fois et se répercute partout.")
            + carte("La règle du jeu", "Aucun verdict de conformité. Chaque risque cite sa source. Les erreurs trouvées sont inscrites et datées, pas effacées. Aucun nom de personne hors du dossier privé.")
            + "</div></section>")


def directeur(f):
    c = f["citations"]
    cit = (f"{c.get('confirme', 0)} confirmées, {c.get('partiel', 0)} partielles, {c.get('a_valider', 0)} à valider, "
           f"{c.get(ABSENTE, 0)} absentes") if c else "à confirmer — index ANCRAGE non accessible à la génération"
    corps = (demandes([
        ("Relancer le comité SST Infra", "Le programme de prévention s’élabore avec lui, et six procédures corporatives lui assignent un rôle qu’aucune instance n’assume depuis décembre 2024.", "Immédiat"),
        ("Faire trancher le découpage des établissements et le niveau des sites", "Ces deux réponses fixent le nombre de programmes de prévention, la fréquence des réunions et les échéances de formation.", "1er octobre"),
        ("Statuer sur la qualité de maître d’œuvre", "Elle commande l’article 2.9.5.2 du Code de sécurité pour les travaux de construction (décret 63-2025) : équipements de sauvetage et intervenant présent en tout temps. Voir R-39.", "Immédiat"),
        ("Ouvrir l’accès complet aux données eCompliance", f"Le tableau de bord compte {f['V']['comparaison'][0]['tableau']} inspections avant départ en 2026, l’export utilisé n’en montre que {f['V']['comparaison'][0]['export']}. Sans extraction complète, les volumes ne deviennent pas des taux.", "30 jours"),
        ("Désigner une seconde personne capable de faire tourner le dossier", "Aujourd’hui, une seule personne sait régénérer les livrables. Le mode d’emploi existe ; il manque quelqu’un pour s’en servir.", "À convenir"),
    ])
        + '<h3>Ce que la démarche a déjà trouvé</h3><div class="grille3">'
        + carte("Deux citations fausses, corrigées", "Une distance de repli en tension inconnue qui n’existe pas à l’annexe Québec de 1801, et une règle des cônes absente du §6.6.1 de 2000.", "rouge")
        + carte("Un constat reposait sur un export partiel", "R-15 annonçait trois inspections mensuelles ; le tableau de bord en compte 58 pour 2026. Le constat a été reformulé, et l’erreur inscrite.", "rouge")
        + carte(f"{f['V']['hauteur']['ouvertes']} évaluations en hauteur sur {f['V']['hauteur']['total']} jamais fermées", "Une fiche déclare 12 m de hauteur et répond « N/A » au plan de sauvetage.", "or")
        + carte(f"{f['V']['non_fermees']['total']} fiches d’inspection non fermées", "Sur 165 fiches datées. Une fiche en cours n’est pas un manquement ; c’est sa durée qui compte, et elle n’est pas encore mesurée.", "or")
        + carte("Les citations normatives sont vérifiées", f"Croisées avec l’index des procédures du système ANCRAGE : {cit}. L’index ne confirme jamais le contenu d’une section.", "")
        + carte("La chaîne est outillée", "Ingestion des exports, alertes d’échéances à 7 et 30 jours, rapport hebdomadaire, contrôles de confidentialité, de cohérence et de citations. Rien n’est inscrit au registre sans validation humaine.", "vert")
        + "</div>"
        + '<h3>Ce qu’il faut savoir du système</h3><ul class="pts">'
        + "<li><b>Une seule personne le fait tourner aujourd’hui.</b> C’est le principal risque, et la cinquième demande ci-dessus y répond.</li>"
        + "<li><b>La page Terrain est hébergée sur un compte Cloudflare ouvert à titre personnel pour les projets Telecon.</b> Elle ne contient aucune donnée nominative. À régulariser avec les TI.</li>"
        + "<li><b>Les données nominatives ne quittent pas les systèmes de Telecon</b> : dossier privé sur SharePoint, dépôts de code privés sous le compte de l’entreprise.</li></ul>"
        + questions([
            ("« Est-ce qu’on est conformes ? »", "Le dossier ne répond pas à cette question, et c’est voulu. Il constate, propose et trace ; la décision appartient au comité et à l’employeur."),
            ("« Pourquoi vos chiffres diffèrent-ils du tableau du 12 septembre ? »", f"Ni la même période ni le même périmètre : {f['incidents']} incidents rattachés au registre depuis juillet, 26 sur tout Infra Québec depuis février. Les deux sont justes."),
            ("« Combien de temps pour tenir le 1er octobre ? »", "L’identification des risques est faite et sourcée pour Falcon. Ce qui manque au programme de prévention — couverture de tout Infra Québec, risques psychosociaux, formation, sous-traitants — dépend du découpage des établissements et de la relance du comité."),
        ]))
    return section("directeur", "Directeur SST", "Cinq décisions, dont trois qui ne peuvent pas attendre le 1er octobre", corps)


def comite(f):
    d = f["delais"]
    tenus, gab, abs_, tot = f["docs"]
    delai = f["delai_rec"]
    corps = (kpis([(len(f["decisions"]) + len(f["seance"]) + len(f["dossiers_seance"]), "décisions à prendre"),
                   (f["points_odj"] if f["points_odj"] is not None else "à confirmer", "points à l’ordre du jour"),
                   (f"{tenus}/{tot}", "documents tenus"), (len(f["bloquantes"]), "questions bloquantes"),
                   (d.get("immediat", 0), "actions immédiates"), (f["n_rec"], "recommandations au registre")])
        + '<div class="grille3">'
        + carte("Un projet d’ordre du jour", "Produit à partir des données : dossiers dont le jalon tombe à la séance, risques à trancher, réserves, documents absents. Durées, date, lieu et composition restent à confirmer tant que la charte n’est pas adoptée.")
        + carte("Un mode séance", "Une page plein écran, projetable, sans navigation : les décisions à prendre, ce que la décision du comité déclenchera, les documents à produire, les échéances et les réserves.")
        + carte("Un registre des recommandations", f"Prêt à recevoir la première recommandation écrite. Délai de réponse : {'à confirmer — R-29 propose 21 jours, proposition non adoptée' if not delai.get('jours') else str(delai['jours']) + ' jours'}.")
        + "</div>"
        + '<h3>Ce que le comité tranche en premier</h3><div class="deux"><div><h4>Constitution du comité</h4><ol>'
        + "".join(f"<li>{e(x['d'])} <small>— {e(x['options'])}</small></li>" for x in f["decisions"])
        + '</ol></div><div><h4>Risques à trancher en séance</h4><ol>'
        + "".join(f"<li><b>{e(r['ref'])}</b> {e(r['titre'])}</li>" for r in f["seance"])
        + "</ol></div></div>"
        + f'<p class="encart">Les délais du registre — {d.get("immediat", 0)} immédiats, {d.get("j30", 0)} à 30 jours, {d.get("j60", 0)} à 60 jours, {d.get("j90", 0)} à 90 jours — courent <b>à compter de la décision du comité</b>. Tant qu’elle n’est pas prise, aucune action ne peut être dite en retard.</p>'
        + questions([
            ("« Le registre nous oblige-t-il à quelque chose ? »", "Non. Les priorités, porteurs et échéances sont proposés ; ils deviennent des décisions quand le comité les adopte."),
            ("« Pourquoi certaines références sont-elles marquées à valider ? »", "Parce que l’index des procédures ne les confirme pas encore, ou qu’elles n’ont pas été vérifiées au texte. Les réserves sont visibles plutôt qu’enfouies."),
        ]))
    return section("comite", "Comité SST", "Un ordre du jour, un mode séance et un registre des recommandations, prêts pour la reprise", corps)


def operations(f):
    corps = (f'<p class="intro">{len(f["immediats"])} risques portent un délai immédiat. Les porteurs sont proposés, par rôle ; la décision revient au comité et à l’employeur.</p>'
             + '<table class="dem"><tr><th>Risque</th><th>Porteur proposé</th></tr>'
             + "".join(f"<tr><td><b>{e(r['ref'])}</b> {e(r['titre'])}</td><td>{e(r['porteur'])}</td></tr>" for r in f["immediats"])
             + "</table>"
             + demandes([
                 ("Fournir les effectifs de parc", "Nombre de véhicules légers, de véhicules lourds et de pelles affectés à Infra Québec. Sans ce dénominateur, 581 inspections ne se comparent à rien.", "30 jours"),
                 ("Faire fermer les fiches en cours", f"{f['V']['non_fermees']['total']} fiches non fermées sur 165, dont {f['V']['non_fermees']['par_type'][0][1]} inspections avant départ, et {f['V']['hauteur']['ouvertes']} évaluations en hauteur.", "À convenir"),
                 ("Confirmer qui est maître d’œuvre sur les chantiers Falcon", "La réponse fixe qui porte les équipements de sauvetage et l’intervenant présent en tout temps.", "Immédiat"),
             ])
             + '<h3>Ce qui fonctionne déjà</h3><div class="grille3">'
             + "".join(carte(t, e(x)) for t, x, _ in f["reconnaissance"]) + "</div>"
             + questions([("« Ces écarts visent-ils des équipes ? »", "Non. La répétition relève du contrôle, pas des équipes : un même écart sur trois visites est un problème de système. Aucun nom n’apparaît.")]))
    return section("operations", "Direction des opérations", f"{len(f['immediats'])} actions immédiates, et trois informations qui manquent", corps)


def ti(f):
    corps = ('<table class="dem"><tr><th>Où</th><th>Quoi</th><th>Données personnelles</th></tr>'
             "<tr><td><b>GitHub, compte de l’entreprise, deux dépôts privés</b></td><td>Scripts, données du registre sans noms, index des procédures</td><td>Aucune — personnes remplacées par des jetons, contrôle automatique avant chaque dépôt</td></tr>"
             "<tr><td><b>SharePoint du comité</b></td><td>Dossier privé : noms, détail des incidents, photographies de chantier</td><td>Oui — reste dans le locataire Telecon</td></tr>"
             "<tr><td><b>Cloudflare Workers</b></td><td>Page Terrain seulement, protégée par mot de passe, non indexable, sans cache</td><td>Aucune</td></tr>"
             "<tr><td><b>Poste du partenaire d’affaires SST</b></td><td>Génération des livrables, exports eCompliance en transit</td><td>Oui, temporairement — dossiers exclus du dépôt</td></tr></table>"
             + demandes([
                 ("Régulariser l’hébergement de la page Terrain", "Le compte Cloudflare a été ouvert à titre personnel pour les projets Telecon. Options : compte d’entreprise, ou accès par Cloudflare Access relié à Entra ID.", "À convenir"),
                 ("Désigner un second administrateur", "Sur les deux dépôts et sur l’hébergement, pour qu’aucun accès ne dépende d’une seule personne.", "À convenir"),
                 ("Ouvrir une extraction eCompliance complète", "Liste des fiches avec dates et statuts, en lecture seule. L’export actuel ne montre que 165 fiches sur 1 837.", "30 jours"),
                 ("Valider l’approche au regard de la Loi 25", "Les renseignements personnels restent dans le locataire ; à confirmer par les TI.", "À convenir"),
             ])
             + questions([
                 ("« Qu’est-ce qui empêche un nom d’entrer dans le dépôt ? »", "Un contrôle automatique, lancé avant chaque dépôt, cherche tous les noms connus, les photographies et les exports. Il échoue au premier élément trouvé."),
                 ("« Le sélecteur de rôle de la page protège-t-il les données ? »", "Non, et c’est pourquoi la page Terrain est un fichier distinct qui ne contient que les consignes. La page Comité ne se diffuse qu’au comité."),
             ]))
    return section("ti", "TI et sécurité de l’information", "Où sont les données, et ce qui reste à régulariser", corps)


def terrain(f):
    corps = (kpis([(f["trav"], "consignes pour les travailleurs"), (f["sup"], "consignes pour les superviseurs"), (0, "nom de personne")])
             + '<div class="grille3">'
             + carte("Ce que c’est", "Des consignes tirées des visites de l’été et de l’automne. Chacune s’appuie sur une exigence écrite qui existe déjà.")
             + carte("Ce que ce n’est pas", "Ni une sanction ni une évaluation. Rien ne vise quelqu’un en particulier : les constats visent des unités et des pratiques, pas des personnes.")
             + carte("Comment y accéder", "Par un code QR affiché au dépôt et dans les fourgons. Le mot de passe se transmet de vive voix, jamais par écrit dans un courriel.")
             + "</div><h3>Ce qui a été vu de bien</h3><div class='grille3'>"
             + "".join(carte(t, e(x), "vert") for t, x, _ in f["reconnaissance"])
             + "</div><p class='encart'>Une question ou un doute sur le terrain : arrêter, en parler à son superviseur ou au partenaire d’affaires SST. Une équipe qui signale ce qui ne va pas est le meilleur indicateur d’un programme de santé et sécurité.</p>")
    return section("terrain", "Superviseurs et travailleurs", "Des consignes claires, sur téléphone, qui ne visent personne", corps)


CSS = """
:root{--band:#1F3864;--navy:#1F3864;--ink:#16202A;--paper:#fff;--card:#fff;--line:#D9DDE3;--soft:#EEF1F5;--muted:#5C6B7A;--p1:#B3261E;--p2:#9A6700;--p3:#2E6C4F;--wash:#F4F6F9}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--band:#16284A;--navy:#9FB6DC;--ink:#E9EDF3;--paper:#0C1218;--card:#141C24;--line:#2A3540;--soft:#1E2730;--muted:#9AA7B6;--p1:#F08A80;--p2:#DFB35A;--p3:#7BC5A3;--wash:#111922}}
:root[data-theme=dark]{--band:#16284A;--navy:#9FB6DC;--ink:#E9EDF3;--paper:#0C1218;--card:#141C24;--line:#2A3540;--soft:#1E2730;--muted:#9AA7B6;--p1:#F08A80;--p2:#DFB35A;--p3:#7BC5A3;--wash:#111922}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;font-size:16px;line-height:1.55}
header{background:var(--band);color:#fff;padding:26px 20px 18px}.dedans{max-width:1080px;margin:0 auto}
header img{height:26px}header h1{margin:10px 0 4px;font-size:28px}header p{margin:0;opacity:.9}
.choix{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.choix button{background:transparent;color:#fff;border:1px solid rgba(255,255,255,.5);border-radius:999px;padding:8px 14px;min-height:44px;font-size:14px;cursor:pointer}
.choix button[aria-pressed=true]{background:#fff;color:#1F3864;font-weight:700}
main{max-width:1080px;margin:0 auto;padding:0 20px 50px}
.acteur{margin-top:30px;padding-top:6px}.oeil{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--navy);font-weight:700}
h2{font-size:23px;margin:4px 0 14px;line-height:1.25}h3{font-size:17px;margin:22px 0 8px}h4{margin:0 0 4px;font-size:15.5px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:10px 0 14px}
.kpi{background:var(--wash);border:1px solid var(--line);border-radius:6px;padding:10px 12px}.kpi b{display:block;font-size:25px;color:var(--navy)}.kpi span{font-size:12.5px;color:var(--muted)}
.grille3{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}
.carte{border:1px solid var(--line);border-left:4px solid var(--navy);border-radius:5px;padding:12px 14px;background:var(--card)}.carte p{margin:0;font-size:14.5px;color:var(--muted)}
.carte.rouge{border-left-color:var(--p1)}.carte.or{border-left-color:var(--p2)}.carte.vert{border-left-color:var(--p3)}
table.dem{width:100%;border-collapse:collapse;margin:10px 0;font-size:14.5px}table.dem th{background:var(--band);color:#fff;text-align:left;padding:8px 10px;font-size:13px}
table.dem td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}td.ech{white-space:nowrap;text-align:right;font-weight:700}
.deux{display:grid;grid-template-columns:1fr 1fr;gap:16px}.deux ol{margin:4px 0;padding-left:20px}.deux small{color:var(--muted)}
.encart{border-left:4px solid var(--p2);background:var(--wash);padding:10px 14px;border-radius:5px;margin-top:14px}
ul.pts li{margin:6px 0}.intro{color:var(--muted)}
.qs details{border:1px solid var(--line);border-radius:5px;padding:9px 12px;margin:8px 0;background:var(--card)}.qs summary{font-weight:700;cursor:pointer}.qs p{margin:8px 0 0;color:var(--muted)}
body.filtre .acteur:not(.visible){display:none}
footer{max-width:1080px;margin:0 auto;padding:16px 20px 30px;font-size:12.5px;color:var(--muted);border-top:1px solid var(--line)}
@media (max-width:760px){header h1{font-size:22px}.deux{grid-template-columns:1fr}table.dem{display:block;overflow-x:auto}td.ech{white-space:normal}}
@media print{.choix{display:none}.acteur{page-break-before:always}.commun{page-break-before:auto}.qs details{display:block}.qs details p{display:block}body{font-size:11pt}
  header{-webkit-print-color-adjust:exact;print-color-adjust:exact}@page{size:letter;margin:14mm}}
"""

JS = """
const boutons=[...document.querySelectorAll('.choix button')];
function choisir(a){
  boutons.forEach(b=>b.setAttribute('aria-pressed', b.dataset.a===a));
  document.body.classList.toggle('filtre', a!=='tous');
  document.querySelectorAll('.acteur').forEach(s=>s.classList.toggle('visible', a==='tous'||s.dataset.acteur===a||s.dataset.acteur==='commun'));
  // l'aperçu de certains outils interdit de modifier l'adresse : on l'ignore sans bloquer la page
  try{ if(location.hash!=='#'+a) history.replaceState(null,'','#'+a); }catch(e){}
}
boutons.forEach(b=>b.addEventListener('click',()=>choisir(b.dataset.a)));
choisir((location.hash||'#tous').slice(1)||'tous');
"""


def construire():
    f = faits()
    logo = base64.b64encode((GABARITS / "assets" / "logo_telecon.png").read_bytes()).decode("ascii")
    acteurs = [("tous", "Tous"), ("directeur", "Directeur SST"), ("comite", "Comité SST"),
               ("operations", "Direction des opérations"), ("ti", "TI"), ("terrain", "Terrain")]
    choix = "".join(f'<button type="button" data-a="{a}" aria-pressed="false">{e(t)}</button>' for a, t in acteurs)
    corps = commun(f) + directeur(f) + comite(f) + operations(f) + ti(f) + terrain(f)
    v = f["ver"]
    return f, (f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
               f'<title>Registre des risques SST — Infra Québec · présentation par acteur</title><style>{CSS}</style></head><body>'
               f'<header><div class="dedans"><img src="data:image/png;base64,{logo}" alt="Telecon">'
               f'<h1>Registre des risques et plan d’action SST — Infra Québec</h1>'
               f'<p>Ce qui a été construit, ce qui est demandé à chacun, et les questions qu’on nous posera. Version {e(v["version"])}, {e(v["date_longue"])}.</p>'
               f'<div class="choix" role="group" aria-label="Choisir un auditoire">{choix}</div></div></header>'
               f'<main>{corps}</main><footer>{e(ligne_version("présentation par acteur — chiffres lus dans les données au moment de la génération ; aucun nom de personne"))}'
               f'<br><b>Validation humaine requise</b> avant toute diffusion : cette présentation propose, elle ne décide rien.</footer>'
               f'<script>{JS}</script></body></html>')


def generer():
    _, page = construire()
    base = SORTIE / nom_versionne("Presentation_par_acteur", "")
    base.parent.mkdir(parents=True, exist_ok=True)
    fichier = base.with_suffix(".html")
    fichier.write_text(page, encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page()
        pg.goto(fichier.resolve().as_uri() + "#tous")
        pg.evaluate("document.querySelectorAll('details').forEach(d=>d.open=true)")
        pg.pdf(path=str(base.with_suffix(".pdf")), format="Letter", print_background=True,
               margin={"top": "14mm", "bottom": "14mm", "left": "12mm", "right": "12mm"})
        nav.close()
    print(f"présentation → {fichier}\nprésentation → {base.with_suffix('.pdf')}")
    return fichier


if __name__ == "__main__":
    generer()
