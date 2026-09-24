"""Vérifie que les livrables disent la même chose, à partir des mêmes données.

    python scripts/verifier_coherence.py          # code de sortie 1 si un écart non connu est trouvé

Trois familles de contrôles :
  A. Compteurs — nombre de risques, de priorités 1, d'incidents, d'éléments source et de
     visites, tels qu'affichés par registre_html.json, plan_action.json et le classeur ;
     délais du calendrier du PDF contre ceux du registre ; plages des formules du classeur.
  B. Références — chaque R-xx cité quelque part existe au registre ; chaque jeton de
     personne cité dans donnees/ existe dans personnes.json, et chaque jeton de
     personnes.json est cité quelque part dans donnees/.
  C. Complétude — chaque risque a au moins une source, un porteur et une échéance.

Un écart déjà inscrit dans donnees/ecarts_connus.json, avec son renvoi à A_CORRIGER.md,
est affiché comme « connu, à trancher » et ne fait pas échouer le contrôle. Tout autre
écart le fait échouer. Aucun seuil de tolérance : deux chiffres concordent ou non.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import DONNEES, GABARITS, lire_json  # noqa: E402

CLASSEUR = DONNEES / "classeur"
REF = re.compile(r"\bR-(\d{2})\b")
JETON = re.compile(r"⟦(P\d{2})(?:~\d+)?⟧")
JETON_NU = re.compile(r"P\d{2}")          # forme sans crochets, seulement sous « responsable » (lieux.json)
NOMBRES = {"trente-huit": 38, "trente-neuf": 39, "quarante": 40, "trente-sept": 37, "quarante et un": 41,
           "dix": 10, "onze": 11, "douze": 12, "neuf": 9, "treize": 13}
BUCKET_CALENDRIER = {"IMMÉDIAT": "immediat", "30 JOURS": "j30", "60 JOURS": "j60", "90 JOURS": "j90",
                     "PROCHAINE SÉANCE": "seance"}
BUCKET_BADGE = {"Immédiat": "immediat", "30 j": "j30", "60 j": "j60", "90 j": "j90", "Séance": "seance"}


def cellules(nom):
    f = lire_json(CLASSEUR / nom)
    return {c[0]: c[1] for c in f["cellules"]}


def textes(obj):
    """Toutes les chaînes d'une structure JSON."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for x in obj:
            yield from textes(x)
    elif isinstance(obj, dict):
        for x in obj.values():
            yield from textes(x)


def jetons_cites(obj):
    """Jetons de personnes cités dans une structure JSON : ⟦Pnn⟧ dans le texte, ou un
    jeton nu (« P45 ») comme valeur d'une clé « responsable ». Ailleurs, « P45 » est
    une coordonnée de cellule du classeur, pas une personne."""
    trouves = {j for t in textes(obj) for j in JETON.findall(t)}
    pile = [obj]
    while pile:
        x = pile.pop()
        if isinstance(x, dict):
            v = x.get("responsable")
            if isinstance(v, str) and JETON_NU.fullmatch(v):
                trouves.add(v)
            pile.extend(x.values())
        elif isinstance(x, list):
            pile.extend(x)
    return trouves


def controle_jetons(declares, cites):
    """Compare les jetons déclarés dans personnes.json à ceux cités ailleurs dans donnees/."""
    inconnus = sorted(set(cites) - set(declares))
    orphelins = sorted(set(declares) - set(cites))
    res = [("jetons_inconnus", "ok" if not inconnus else "ecart",
            f"Jetons cités dans donnees/ : {len(set(cites))} distincts"
            + ("" if not inconnus else f" — absents de personnes.json : {', '.join(f'{j} ({cites[j]})' for j in inconnus)}"))]
    # un écart par jeton orphelin : un écart connu n'en couvre qu'un, un nouvel orphelin échoue
    res += [(f"jeton_orphelin_{j}", "ecart", f"Jeton {j} de personnes.json cité dans aucune donnée") for j in orphelins]
    if not orphelins:
        res.append(("jetons_orphelins", "ok", f"Les {len(declares)} jetons de personnes.json sont tous cités"))
    return res


def verifier():
    D = lire_json(DONNEES / "registre_html.json")
    P = lire_json(DONNEES / "plan_action.json")
    V = lire_json(DONNEES / "version.json")
    R = D["risques"]
    refs = {r["ref"] for r in R}
    n_p1 = sum(1 for r in R if r["prio"] == 1)
    n_el = sum(len(r["sources"]) for r in R)
    fiches = {s["fiche"] for r in R for s in r["sources"] if re.fullmatch(r"\d{8}", s["fiche"])}
    res = []

    def comparer(cle, libelle, attendu, affiche, ou):
        ok = str(attendu) == str(affiche)
        res.append((cle, "ok" if ok else "ecart", f"{libelle} : {affiche} affiché ({ou}), {attendu} au registre"))

    # ---------------------------------------------------------------- A · compteurs
    chiffres = {t.replace("<br>", " "): n for n, t in P["pages"][0]["chiffres"]}
    for motif, attendu, cle in [("risques distincts", len(R), "pdf_risques"),
                                ("priorité 1", n_p1, "pdf_p1"),
                                ("éléments", n_el, "pdf_elements"),
                                ("incidents", len(D["incidents"]), "pdf_incidents")]:
        affiche = next((n for t, n in chiffres.items() if motif in t), None)
        comparer(cle, f"PDF page 1, « {motif} »", attendu, affiche, "plan_action.json")
    visites_pdf = next((t for t in chiffres if "visites" in t), "")
    m = re.search(r"dont (\d+) consolidées", visites_pdf)
    comparer("pdf_visites_consolidees", "PDF page 1, visites consolidées", len(fiches),
             m.group(1) if m else "—", "plan_action.json")
    comparer("page_visites_consolidees", "Page Comité, visites marquées consolidées", len(fiches),
             sum(1 for v in D["visites"] if v["consolidee"]), "registre_html.json › visites")

    dirp1 = next((c["n"] for c in D["roles"]["dirchiffres"] if "priorité 1" in c["lab"]), None)
    comparer("direction_p1", "Vue Direction, priorités 1", n_p1, dirp1, "registre_html.json › roles")

    gabarit = (GABARITS / "page_registre.html").read_text(encoding="utf-8")
    for mot in re.findall(r"des ([a-z\- ]+?) risques consolidés", gabarit):
        comparer("direction_texte", "Vue Direction, texte d'introduction", len(R), NOMBRES.get(mot.strip(), mot), "gabarit")

    # calendrier du PDF contre les délais du registre
    for g in P["pages"][0]["calendrier"]["groupes"]:
        cle = BUCKET_CALENDRIER.get(g["titre"])
        attendus = sorted(r["ref"] for r in R if r["bucket"] == cle)
        ok = sorted(g["refs"]) == attendus
        res.append((f"calendrier_{cle}", "ok" if ok else "ecart",
                    f"Calendrier du PDF, {g['titre'].lower()} : {len(g['refs'])} risques"
                    + ("" if ok else f" — écart : {sorted(set(g['refs']) ^ set(attendus))}")))
    for col in P["pages"][0]["risques"]["colonnes"]:
        for k in col["risques"]:
            r = next((x for x in R if x["ref"] == k["ref"]), None)
            if r and BUCKET_BADGE.get(k["echeance"]) != r["bucket"]:
                res.append((f"badge_{k['ref']}", "ecart", f"PDF, pastille de {k['ref']} : « {k['echeance']} », délai « {r['bucket']} » au registre"))
    pdf_refs = sorted(k["ref"] for col in P["pages"][0]["risques"]["colonnes"] for k in col["risques"])
    comparer("pdf_colonnes", "PDF page 1, risques répartis dans les colonnes", len(R), len(set(pdf_refs)), "plan_action.json")

    # classeur
    reg = cellules("02_Registre.json")
    lignes_reg = sorted(v for k, v in reg.items() if re.fullmatch(r"A\d+", k) and isinstance(v, str) and REF.fullmatch(v))
    comparer("classeur_registre", "Classeur, lignes de l'onglet Registre", len(R), len(lignes_reg), "02_Registre.json")
    p1_classeur = sum(1 for k, v in reg.items() if re.fullmatch(r"D\d+", k) and str(v) == "1")
    comparer("classeur_p1", "Classeur, priorités 1 de l'onglet Registre", n_p1, p1_classeur, "02_Registre.json")
    synth = cellules("14_Synthese.json")
    formule = str(synth.get("B4", ""))
    m = re.search(r"\$D\$6:\$D\$(\d+)", formule)
    comparer("classeur_plage", "Classeur, plage des formules de la Synthèse", 5 + len(R), m.group(1) if m else "—", "14_Synthese.json")
    garde = cellules("01_Garde.json")
    for k, v in garde.items():
        m = re.search(r"version (\d+)", str(v))
        if m:
            comparer("classeur_version", f"Classeur, version inscrite en page de garde ({k})", V["version"], m.group(1), "01_Garde.json")

    # ---------------------------------------------------------------- B · références
    cites = set()
    sources_texte = [("registre_html.json", D), ("plan_action.json", P)]
    if (DONNEES / "recommandations.json").exists():
        sources_texte.append(("recommandations.json", lire_json(DONNEES / "recommandations.json")["recommandations"]))
    for nom in (CLASSEUR).glob("*.json"):
        if not nom.name.startswith("_"):
            sources_texte.append((nom.name, lire_json(nom)))
    for nom, obj in sources_texte:
        for t in textes(obj):
            for n in REF.findall(t):
                cites.add((f"R-{n}", nom))
    inconnues = sorted({(r, n) for r, n in cites if r not in refs})
    res.append(("references", "ok" if not inconnues else "ecart",
                f"Références R-xx citées : {len({r for r, _ in cites})} distinctes"
                + ("" if not inconnues else f" — inexistantes : {', '.join(f'{r} ({n})' for r, n in inconnues)}")))

    personnes = DONNEES / "personnes.json"
    cites_par = {}
    for f in sorted(DONNEES.rglob("*.json")):
        if f != personnes:
            for j in jetons_cites(lire_json(f)):
                cites_par.setdefault(j, f.relative_to(DONNEES).as_posix())
    res += controle_jetons(set(lire_json(personnes)["personnes"]), cites_par)

    # ---------------------------------------------------------------- C · complétude
    for r in R:
        manque = [c for c, ok in [("source", bool(r.get("sources"))), ("porteur", bool(str(r.get("porteur", "")).strip())),
                                  ("échéance", bool(str(r.get("echeance", "")).strip()))] if not ok]
        if manque:
            res.append((f"complet_{r['ref']}", "ecart", f"{r['ref']} sans {', '.join(manque)}"))
    if not any(c.startswith("complet_") for c, _, _ in res):
        res.append(("completude", "ok", f"Les {len(R)} risques ont une source, un porteur et une échéance"))
    return res


def appliquer_connus(res):
    f = DONNEES / "ecarts_connus.json"
    connus = {e["cle"]: e for e in lire_json(f)["ecarts"]} if f.exists() else {}
    sortie = []
    for cle, statut, detail in res:
        if statut == "ecart" and cle in connus:
            sortie.append((cle, "connu", f"{detail} — {connus[cle]['motif']} ({connus[cle]['renvoi']})"))
        else:
            sortie.append((cle, statut, detail))
    return sortie


def main():
    res = appliquer_connus(verifier())
    marque = {"ok": "  ok    ", "ecart": "  ÉCART ", "connu": "  connu "}
    for _, statut, detail in res:
        print(f"{marque[statut]} {detail}")
    ecarts = [r for r in res if r[1] == "ecart"]
    connus = [r for r in res if r[1] == "connu"]
    print(f"\n{len(res)} contrôles · {len(ecarts)} écarts · {len(connus)} écarts connus, à trancher")
    print("Validation humaine requise : un écart signale une contradiction entre livrables, "
          "pas un manquement. La correction se fait à la main, dans les données, puis se journalise.")
    sys.exit(1 if ecarts else 0)


if __name__ == "__main__":
    main()
