"""Lit les exports eCompliance déposés dans ingest/ et en tire un rapport daté.

    python scripts/ingerer_exports.py
    python scripts/ingerer_exports.py --ingest D:\\exports --sortie rapports

Ce que le script fait :
  - lit tous les .xlsx et .csv du dossier ingest/, dédoublonne par identifiant de fiche ;
  - compte les fiches par type de formulaire et par mois ;
  - relève les fiches non fermées (statut autre que verrouillé) et les fiches sans signature ;
  - écrit un rapport markdown daté dans rapports/.

Ce que le script ne fait pas :
  - il n'écrit jamais dans donnees/ : le registre ne se modifie qu'à la main ;
  - il ne compare à aucune cible et ne porte aucun verdict de conformité ;
  - il ne reproduit aucun nom de personne : seuls des décomptes et des numéros de fiche.

ingest/ et rapports/ sont ignorés par Git : les exports contiennent des noms.
"""
import argparse
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import openpyxl

RACINE = Path(__file__).resolve().parent.parent

# Noms de colonnes rencontrés dans les exports, ramenés à un rôle.
COLONNES = {
    "id": ["id", "identifiant", "form id", "no fiche"],
    "titre": ["title", "titre", "form title", "modele", "modèle"],
    "statut": ["status", "statut", "state"],
    "date": ["date performed", "date", "date realisee", "date réalisée", "performed on"],
    "signature": ["signed off by", "signe par", "signé par", "approved by"],
}
# Statuts qui valent « fiche fermée ». Tout autre statut est compté comme non fermée.
STATUTS_FERMES = {"locked", "verrouille", "verrouillé", "closed", "complete", "completed"}


def sans_accent(texte):
    t = unicodedata.normalize("NFKD", str(texte or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().lower()


def role_des_colonnes(entetes):
    """En-tête de l'export → rôle connu. Les colonnes inconnues sont ignorées."""
    roles = {}
    for i, e in enumerate(entetes):
        cle = sans_accent(e)
        for role, alias in COLONNES.items():
            if role not in roles and cle in [sans_accent(a) for a in alias]:
                roles[role] = i
    return roles


def lire_fichier(chemin):
    """Renvoie (lignes, colonnes manquantes). Une ligne = dict des rôles trouvés."""
    if chemin.suffix.lower() == ".csv":
        import csv
        with open(chemin, encoding="utf-8-sig", newline="") as f:
            table = list(csv.reader(f))
    else:
        ws = openpyxl.load_workbook(chemin, read_only=True, data_only=True).worksheets[0]
        table = [list(r) for r in ws.iter_rows(values_only=True)]
    if not table:
        return [], sorted(COLONNES)

    roles = role_des_colonnes(table[0])
    manquantes = sorted(set(COLONNES) - set(roles))
    lignes = []
    for brute in table[1:]:
        if all(c is None or str(c).strip() == "" for c in brute):
            continue
        lignes.append({r: brute[i] if i < len(brute) else None for r, i in roles.items()})
    return lignes, manquantes


def mois_de(valeur):
    """AAAA-MM, ou None si la date est absente ou illisible."""
    if valeur is None:
        return None
    if hasattr(valeur, "year"):
        return f"{valeur.year:04d}-{valeur.month:02d}"
    m = re.search(r"(\d{4})[-/](\d{2})", str(valeur))
    return f"{m.group(1)}-{m.group(2)}" if m else None


def analyser(lignes):
    par_mois = defaultdict(Counter)      # titre → mois → n
    statuts = Counter()
    non_fermees = defaultdict(list)      # titre → identifiants
    sans_signature = defaultdict(list)
    sans_date = Counter()
    for l in lignes:
        titre = str(l.get("titre") or "titre absent").strip()
        statut = str(l.get("statut") or "").strip()
        statuts[statut or "statut absent"] += 1
        mois = mois_de(l.get("date"))
        if mois:
            par_mois[titre][mois] += 1
        else:
            sans_date[titre] += 1
        ident = str(l.get("id") or "sans identifiant")
        if sans_accent(statut) not in STATUTS_FERMES:
            non_fermees[titre].append(ident)
        if not str(l.get("signature") or "").strip():
            sans_signature[titre].append(ident)
    return par_mois, statuts, non_fermees, sans_signature, sans_date


def tableau_mensuel(par_mois):
    mois = sorted({m for c in par_mois.values() for m in c})
    lignes = [f"| Type de formulaire | {' | '.join(m[5:] + '/' + m[2:4] for m in mois)} | Total |",
              f"|---|{'---|' * (len(mois) + 1)}"]
    for titre in sorted(par_mois, key=lambda t: -sum(par_mois[t].values())):
        c = par_mois[titre]
        lignes.append(f"| {titre} | {' | '.join(str(c.get(m, '—')) for m in mois)} | **{sum(c.values())}** |")
    return "\n".join(lignes), mois


def rapport(fichiers, lignes, doublons, manquantes, sortie):
    par_mois, statuts, non_fermees, sans_signature, sans_date = analyser(lignes)
    table, mois = tableau_mensuel(par_mois)
    jour = date.today().isoformat()
    total = len(lignes)

    t = [f"# Rapport d'ingestion — {jour}", "",
         "Relevé produit automatiquement à partir des exports déposés. "
         "Aucun verdict de conformité : ce sont des décomptes, pas des constats.", "",
         "## Sources lues", ""]
    for f, n in fichiers:
        t.append(f"- `{f}` — {n} lignes")
    t += ["", f"**{total} fiches** après dédoublonnage par identifiant"
          + (f" ({doublons} doublons écartés)" if doublons else "") + ".", ""]
    if mois:
        t.append(f"Période couverte : {mois[0]} à {mois[-1]}.")
    if manquantes:
        t.append("")
        t.append(f"> **Colonnes absentes des exports : {', '.join(manquantes)}.** "
                 "Les décomptes qui en dépendent sont à confirmer.")

    t += ["", "## Volumes par type et par mois", "", table, ""]
    if sum(sans_date.values()):
        t.append(f"{sum(sans_date.values())} fiches sans date exploitable ne figurent pas au tableau.")

    t += ["", "## Fiches non fermées", "",
          "Statut autre que verrouillé au moment de l'export. "
          "Ce qui suit est un relevé, pas un manquement : une fiche peut être en cours normalement.", ""]
    if non_fermees:
        t.append("| Type de formulaire | Non fermées | Identifiants |")
        t.append("|---|---|---|")
        for titre in sorted(non_fermees, key=lambda x: -len(non_fermees[x])):
            ids = non_fermees[titre]
            apercu = ", ".join(ids[:12]) + (f" … et {len(ids) - 12} autres" if len(ids) > 12 else "")
            t.append(f"| {titre} | **{len(ids)}** | {apercu} |")
    else:
        t.append("Aucune.")

    t += ["", "## Fiches sans signature", ""]
    if sans_signature:
        t.append("| Type de formulaire | Sans signature |")
        t.append("|---|---|")
        for titre in sorted(sans_signature, key=lambda x: -len(sans_signature[x])):
            t.append(f"| {titre} | **{len(sans_signature[titre])}** |")
    else:
        t.append("Aucune.")

    t += ["", "## Statuts rencontrés", "",
          " · ".join(f"{s} : {n}" for s, n in statuts.most_common()), "",
          "## Réserves", "",
          "- Les exports ne couvrent que ce que le compte utilisé peut voir. Un écart avec le tableau de bord reste possible ; il est à confirmer auprès de l'administrateur eCompliance.",
          "- « Fermée » signifie ici un statut verrouillé. La correspondance exacte avec le vocabulaire d'eCompliance est à confirmer.",
          "- Aucun nom de personne ne figure dans ce rapport. Les exports d'origine en contiennent : ils restent dans `ingest/`, hors du dépôt.",
          "",
          "---", "",
          "**Validation humaine requise.** Ce rapport n'entre pas au registre tel quel : chaque élément retenu doit être vérifié, sourcé et inscrit à la main par le partenaire d'affaires SST."]

    sortie.mkdir(parents=True, exist_ok=True)
    chemin = sortie / f"rapport_ingestion_{jour}.md"
    chemin.write_text("\n".join(t) + "\n", encoding="utf-8")
    return chemin, total, sum(len(v) for v in non_fermees.values())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ingest", default=RACINE / "ingest")
    p.add_argument("--sortie", default=RACINE / "rapports")
    a = p.parse_args()

    dossier = Path(a.ingest)
    if not dossier.exists():
        sys.exit(f"Dossier introuvable : {dossier}\nDéposez-y les exports eCompliance (.xlsx ou .csv).")
    fichiers = sorted(f for f in dossier.iterdir() if f.suffix.lower() in {".xlsx", ".csv"})
    if not fichiers:
        sys.exit(f"Aucun export dans {dossier}.")

    lignes, resume, manquantes, vus = [], [], set(), set()
    doublons = 0
    for f in fichiers:
        brutes, absentes = lire_fichier(f)
        manquantes |= set(absentes)
        resume.append((f.name, len(brutes)))
        for l in brutes:
            ident = str(l.get("id") or "")
            if ident and ident in vus:
                doublons += 1
                continue
            if ident:
                vus.add(ident)
            lignes.append(l)

    chemin, total, ouvertes = rapport(resume, lignes, doublons, sorted(manquantes), Path(a.sortie))
    print(f"{len(fichiers)} fichiers lus, {total} fiches, {ouvertes} non fermées.")
    print(f"Rapport → {chemin}")
    print("Validation humaine requise : rien n'est inscrit au registre automatiquement.")


if __name__ == "__main__":
    main()
