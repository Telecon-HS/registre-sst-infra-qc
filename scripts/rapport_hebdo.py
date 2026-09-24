"""Rapport hebdomadaire : ce qui a bougé, ce qui est en retard, ce qui ne concorde pas.

    python scripts/rapport_hebdo.py
    python scripts/rapport_hebdo.py --date 2026-09-27      # se placer à une date donnée

Il assemble les trois scripts existants, sans les remplacer :
  - `ingerer_exports.py` pour les fiches déposées dans ingest/ ;
  - `alertes.py` pour les échéances ;
  - `verifier_citations.py` pour les références normatives.

« Ce qui a bougé » se mesure contre l'état de la semaine précédente, conservé dans
rapports/etat.json. Au premier passage, il n'y a pas d'état précédent : le rapport le dit
plutôt que de présenter les 165 fiches comme des nouveautés.

Le script n'écrit jamais dans donnees/, ne recopie aucun nom et ne porte aucun verdict.
rapports/ est ignoré par Git.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import alertes as mod_alertes  # noqa: E402
import ingerer_exports as mod_ingestion  # noqa: E402
import verifier_citations as mod_citations  # noqa: E402
from commun import DONNEES, PRIVE, RACINE, lire_json  # noqa: E402


# ---------------------------------------------------------------- ce qui a bougé
def etat_actuel(lignes):
    """Photo des fiches : total, décompte par type, identifiants non fermés."""
    par_mois, _, non_fermees, _, _ = mod_ingestion.analyser(lignes)
    return {
        "total": len(lignes),
        "par_type": {t: sum(c.values()) for t, c in par_mois.items()},
        "non_fermees": {t: sorted(ids) for t, ids in non_fermees.items()},
        "identifiants": sorted({str(l.get("id") or "") for l in lignes} - {""}),
    }


def comparer(precedent, actuel):
    """Différences entre deux photos. precedent None → premier passage."""
    if not precedent:
        return None
    avant = {i for ids in precedent.get("non_fermees", {}).values() for i in ids}
    apres = {i for ids in actuel["non_fermees"].values() for i in ids}
    vues = set(actuel.get("identifiants", []))
    # une fiche absente de l'export de cette semaine n'est PAS une fiche fermée :
    # l'export peut simplement ne pas la contenir.
    types = set(precedent.get("par_type", {})) | set(actuel["par_type"])
    return {
        "total": actuel["total"] - precedent.get("total", 0),
        "fermees_depuis": sorted((avant - apres) & vues),
        "absentes_de_l_export": sorted(avant - vues),
        "nouvelles_non_fermees": sorted(apres - avant),
        "par_type": {t: actuel["par_type"].get(t, 0) - precedent.get("par_type", {}).get(t, 0) for t in types},
    }


# ---------------------------------------------------------------- ce qui ne concorde pas
def concordance(actuel, volumes, citations_lignes):
    """Écarts entre sources. Aucun seuil : les écarts sont présentés, pas jugés."""
    ecarts = []
    for ligne in volumes.get("comparaison", []):
        # rapprochement par motif explicite, inscrit dans donnees/volumes.json
        motif = str(ligne.get("motif", "")).lower()
        vu = None
        if motif:
            correspondants = [(t, n) for t, n in actuel["par_type"].items() if motif in t.lower()]
            if correspondants:
                vu = (" + ".join(t for t, _ in correspondants), sum(n for _, n in correspondants))
        ecarts.append({
            "type": ligne["type"],
            "registre": ligne.get("registre"),
            "export_conserve": ligne.get("export"),
            "tableau_de_bord": ligne.get("tableau"),
            "ingestion": vu[1] if vu else None,
        })
    citations = {}
    for _, _, etat, _ in citations_lignes:
        citations[etat] = citations.get(etat, 0) + 1
    return ecarts, citations


# ---------------------------------------------------------------- rapport
def markdown(jour, actuel, mouvement, ecarts, citations, resume_alertes, notes):
    t = [f"# Rapport hebdomadaire SST — Infra Québec, {jour.isoformat()}", "",
         "Assemblé automatiquement à partir des exports déposés, du registre et de l'index des procédures. "
         "Aucun verdict de conformité : ce sont des décomptes, des dates et des écarts.", ""]

    # 1 · ce qui a bougé
    t += ["## Ce qui a bougé", ""]
    if mouvement is None:
        t += ["Premier passage : aucun état précédent à comparer. "
              f"Photo de départ — **{actuel['total']} fiches**, "
              f"{sum(len(v) for v in actuel['non_fermees'].values())} non fermées. "
              "La semaine prochaine, les différences seront mesurées contre cette photo.", ""]
    else:
        t += [f"- Fiches au total : **{mouvement['total']:+d}**",
              f"- Fiches fermées depuis le dernier passage : **{len(mouvement['fermees_depuis'])}**"
              + (f" — {', '.join(mouvement['fermees_depuis'][:10])}" if mouvement["fermees_depuis"] else ""),
              f"- Nouvelles fiches non fermées : **{len(mouvement['nouvelles_non_fermees'])}**"
              + (f" — {', '.join(mouvement['nouvelles_non_fermees'][:10])}" if mouvement["nouvelles_non_fermees"] else ""),
              f"- Fiches suivies la semaine dernière et absentes de l'export de cette semaine : "
              f"**{len(mouvement['absentes_de_l_export'])}** — leur statut est inconnu, à confirmer",
              ""]
        bouges = {k: v for k, v in mouvement["par_type"].items() if v}
        if bouges:
            t += ["| Type de formulaire | Variation |", "|---|---|"]
            t += [f"| {k} | {v:+d} |" for k, v in sorted(bouges.items(), key=lambda x: -abs(x[1]))]
            t.append("")

    # 2 · ce qui est en retard
    t += ["## Ce qui est en retard", "",
          f"- Dépassé : **{resume_alertes['dépassé']}**",
          f"- Dans les 7 jours : **{resume_alertes['7 jours']}**",
          f"- Dans les 30 jours : **{resume_alertes['30 jours']}**",
          "",
          f"Le détail figure dans `alertes_{jour.isoformat()}.md`, produit en même temps.", ""]
    if resume_alertes.get("sans_point_de_depart"):
        t += ["> Les délais des risques ne sont pas convertis en dates : ils courent à compter de la décision "
              "du comité, absente de `donnees/echeances.json`.", ""]

    # 3 · ce qui ne concorde pas
    t += ["## Ce qui ne concorde pas", "", "### Volumes, selon la source", "",
          "| Type d'activité | Registre v7 | Export conservé | Tableau de bord 2026 | Ingestion de la semaine |",
          "|---|---|---|---|---|"]
    for e in ecarts:
        t.append(f"| {e['type']} | {e['registre'] or '—'} | {e['export_conserve'] or '—'} | "
                 f"{e['tableau_de_bord'] or '—'} | {e['ingestion'] if e['ingestion'] is not None else '—'} |")
    t += ["", "Aucun seuil n'est appliqué : les écarts sont présentés, pas jugés. "
          "Leur cause reste à confirmer auprès de l'administrateur eCompliance.", "",
          "### Citations normatives", ""]
    if citations:
        t += ["| État | Citations |", "|---|---|"]
        t += [f"| {k} | {v} |" for k, v in sorted(citations.items(), key=lambda x: -x[1])]
        t += ["", "Rappel : l'index confirme l'existence d'une procédure, jamais le contenu d'une section.", ""]
    else:
        t += ["**À confirmer.** L'index des procédures d'ANCRAGE n'était pas accessible : "
              "donner son chemin par la variable `ANCRAGE_INDEX`.", ""]

    if notes:
        t += ["## Notes de passage", ""] + [f"- {n}" for n in notes] + [""]

    t += ["---", "",
          "**Validation humaine requise.** Ce rapport n'inscrit rien au registre et ne ferme aucune action. "
          "Ce qui est retenu doit être vérifié, sourcé et inscrit à la main par le partenaire d'affaires SST."]
    return "\n".join(t) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date")
    p.add_argument("--ingest", default=RACINE / "ingest")
    p.add_argument("--sortie", default=RACINE / "rapports")
    p.add_argument("--index", help="index des procédures ANCRAGE")
    a = p.parse_args()

    jour = mod_alertes.lire_date(a.date) or date.today()
    sortie = Path(a.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    notes = []

    # 1 · exports
    dossier = Path(a.ingest)
    fichiers = sorted(f for f in dossier.iterdir() if f.suffix.lower() in {".xlsx", ".csv"}) if dossier.exists() else []
    lignes, vus = [], set()
    for f in fichiers:
        brutes, absentes = mod_ingestion.lire_fichier(f)
        if absentes:
            notes.append(f"`{f.name}` : colonnes absentes ({', '.join(absentes)}), décomptes à confirmer.")
        for l in brutes:
            ident = str(l.get("id") or "")
            if ident and ident in vus:
                continue
            vus.add(ident)
            lignes.append(l)
    if not fichiers:
        notes.append("Aucun export dans `ingest/` : la section « ce qui a bougé » reste sur l'état précédent.")
    actuel = etat_actuel(lignes)

    fichier_etat = sortie / "etat.json"
    precedent = json.loads(fichier_etat.read_text(encoding="utf-8")) if fichier_etat.exists() else None
    mouvement = comparer(precedent, actuel) if fichiers else None

    # 2 · alertes
    data = lire_json(DONNEES / "registre_html.json")
    config = lire_json(DONNEES / "echeances.json") if (DONNEES / "echeances.json").exists() else {}
    epi = lire_json(PRIVE / "epi_recertification.json").get("articles", []) if (PRIVE / "epi_recertification.json").exists() else []
    liste = mod_alertes.collecter(jour, data, config, epi, mod_alertes.lire_dossiers())
    (sortie / f"alertes_{jour.isoformat()}.md").write_text(
        mod_alertes.markdown(jour, liste, data, config, bool(epi)), encoding="utf-8")
    resume_alertes = {h: len([x for x in liste if x["horizon"] == h]) for h in ("dépassé", "7 jours", "30 jours")}
    resume_alertes["sans_point_de_depart"] = not config.get("date_decision_comite")

    # 3 · citations
    citations_lignes = []
    chemin_index = Path(a.index) if a.index else Path(mod_citations.INDEX_DEFAUT)
    if chemin_index.exists():
        citations_lignes = mod_citations.verifier(mod_citations.index_procedures(chemin_index), data["risques"])
    else:
        notes.append(f"Index des procédures introuvable ({chemin_index}) : citations non vérifiées cette semaine.")

    volumes = lire_json(DONNEES / "volumes.json") if (DONNEES / "volumes.json").exists() else {}
    ecarts, citations = concordance(actuel, volumes, citations_lignes)

    chemin = sortie / f"rapport_hebdo_{jour.isoformat()}.md"
    chemin.write_text(markdown(jour, actuel, mouvement, ecarts, citations, resume_alertes, notes), encoding="utf-8")
    if fichiers:
        fichier_etat.write_text(json.dumps(actuel, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"Rapport → {chemin}")
    print(f"Fiches lues : {actuel['total']} · dépassé : {resume_alertes['dépassé']} · "
          f"citations vérifiées : {len(citations_lignes)}")
    print("Validation humaine requise : rien n'est inscrit au registre automatiquement.")


if __name__ == "__main__":
    main()
