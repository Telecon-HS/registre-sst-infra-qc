"""Liste ce qui arrive à échéance, en markdown, prêt à coller dans un courriel.

    python scripts/alertes.py
    python scripts/alertes.py --date 2026-10-05        # se placer à une date donnée
    python scripts/alertes.py --sortie rapports

Quatre familles :
  1. Échéances réglementaires — dates fixes, lues au dossier du comité.
  2. Jalons des dossiers en cours — seulement ceux qui portent une date réelle.
  3. Actions du registre — leurs délais courent **à compter de la décision du comité**.
     Tant que cette date est absente de donnees/echeances.json, aucune date n'est
     calculée : le script le dit et compte les actions par délai, sans inventer un départ.
  4. Recertifications d'EPI — la liste HSE-601 n'est pas dans ce dépôt. Si le fichier
     prive/epi_recertification.json existe, il est lu ; sinon la section est marquée
     « à confirmer ».

Le script ne porte aucun verdict et n'écrit jamais dans donnees/.
"""
import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commun import DONNEES, PRIVE, RACINE, lire_json  # noqa: E402

MOIS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}
# états de document qui valent « le document n'est pas tenu »
ETATS_A_FAIRE = ("absent", "non produit", "non versé", "à créer", "à produire", "à planifier",
                 "à confirmer", "gabarit", "partiel")


def lire_date(texte):
    """« 1er octobre 2026 » ou « 2026-10-01 » → date. None si illisible."""
    if not texte:
        return None
    t = str(texte).strip().lower()
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r"(\d{1,2})\s*(?:er)?\s+([a-zéû]+)\s+(\d{4})", t)
    if m and m.group(2) in MOIS:
        return date(int(m.group(3)), MOIS[m.group(2)], int(m.group(1)))
    return None


def horizon(echeance, aujourdhui):
    """dépassé / 7 jours / 30 jours / plus tard"""
    jours = (echeance - aujourdhui).days
    if jours < 0:
        return "dépassé", jours
    if jours <= 7:
        return "7 jours", jours
    if jours <= 30:
        return "30 jours", jours
    return "plus tard", jours


def collecter(aujourdhui, data, config, epi):
    """Renvoie la liste des éléments datés, avec leur horizon."""
    items = []
    for e in data["comite"]["echeances"]:
        d = lire_date(e["date"])
        if d:
            items.append((d, "Réglementaire", e["quoi"], e.get("portee", "")))
    for i in data.get("initiatives", []):
        # seulement le jalon, et seulement quand la date est présentée comme une échéance :
        # une date de version dans le champ « état » n'est pas un jalon.
        m = re.search(r"(?:avant le|d.ici|au plus tard le|échéance du)\s+(\d{1,2}\s*(?:er)?\s+[a-zéû]+\s+\d{4}|\d{4}-\d{2}-\d{2})",
                      str(i.get("jalon", "")), re.I)
        d = lire_date(m.group(1)) if m else None
        if d:
            items.append((d, "Dossier en cours", f"{i['ref']} — {i['titre']}", "jalon"))
    for e in config.get("echeances_ajoutees", []):
        d = lire_date(e.get("date"))
        if d:
            items.append((d, e.get("famille", "Ajoutée"), e.get("quoi", ""), e.get("source", "")))
    for a in epi:
        d = lire_date(a.get("echeance"))
        if d:
            items.append((d, "EPI — recertification", a.get("article", "article à confirmer"), a.get("unite", "")))

    sortie = []
    for d, famille, quoi, detail in items:
        h, jours = horizon(d, aujourdhui)
        if h != "plus tard":
            sortie.append({"date": d, "famille": famille, "quoi": quoi, "detail": detail, "horizon": h, "jours": jours})
    return sorted(sortie, key=lambda x: x["date"])


def markdown(aujourdhui, alertes, data, config, epi_disponible):
    t = [f"# Alertes SST — Infra Québec, au {aujourdhui.isoformat()}", "",
         "Relevé automatique. Aucun verdict de conformité : ce sont des dates, pas des constats.", ""]

    for titre, cle in [("Dépassé", "dépassé"), ("Dans les 7 jours", "7 jours"), ("Dans les 30 jours", "30 jours")]:
        lot = [a for a in alertes if a["horizon"] == cle]
        t += [f"## {titre} — {len(lot)}", ""]
        if lot:
            t += ["| Date | Famille | Quoi | Détail |", "|---|---|---|---|"]
            t += [f"| {a['date'].isoformat()} | {a['famille']} | {a['quoi']} | {a['detail']} |" for a in lot]
        else:
            t.append("Rien.")
        t.append("")

    # 3 · actions du registre
    depart = lire_date(config.get("date_decision_comite"))
    risques = data["risques"]
    t += ["## Actions du registre", ""]
    if depart is None:
        familles = {}
        for r in risques:
            familles[r["bucket"]] = familles.get(r["bucket"], 0) + 1
        t += ["**Aucune date calculée : le point de départ est absent.** Les délais du registre courent "
              "à compter de la décision du comité, qui n'a pas eu lieu. Inscrire la date dans "
              "`donnees/echeances.json`, champ `date_decision_comite`, pour que les échéances deviennent des dates.", "",
              "| Délai proposé | Risques |", "|---|---|"]
        libelle = {"immediat": "Immédiat", "j30": "30 jours", "j60": "60 jours", "j90": "90 jours", "seance": "Prochaine séance"}
        for cle, nb in sorted(familles.items(), key=lambda x: -x[1]):
            t.append(f"| {libelle.get(cle, cle)} | {nb} |")
    else:
        t += [f"Point de départ : décision du comité du {depart.isoformat()}.", "",
              "| Échéance | Risque | Délai inscrit au registre |", "|---|---|---|"]
        jours = {"immediat": 0, "j30": 30, "j60": 60, "j90": 90}
        for r in risques:
            if r["bucket"] in jours:
                d = depart + timedelta(days=jours[r["bucket"]])
                h, _ = horizon(d, aujourdhui)
                if h != "plus tard":
                    t.append(f"| {d.isoformat()} ({h}) | {r['ref']} — {r['titre']} | {r['echeance']} |")
    t.append("")

    # 4 · documents du comité
    manquants = [d for d in data.get("documents", [])
                 if any(m in str(d.get("etat", "")).lower() for m in ETATS_A_FAIRE)]
    t += [f"## Documents du comité à produire — {len(manquants)}", "",
          "Relevé indicatif, à confirmer auprès de la CNESST : ce n'est pas un avis juridique.", ""]
    if manquants:
        t += ["| Document | État | Exigence citée |", "|---|---|---|"]
        t += [f"| {d['doc']} | {d.get('etat', '')} | {str(d.get('exigence', ''))[:80]} |" for d in manquants]
    else:
        t.append("Aucun.")
    t.append("")

    # 5 · EPI
    t += ["## Recertifications d'EPI", ""]
    if not epi_disponible:
        t += ["**À confirmer.** La liste HSE-601 et les dates de mise en service ne sont pas dans ce dépôt : "
              "elles vivent sur SharePoint. Déposer `prive/epi_recertification.json` "
              "(articles, unités, dates d'échéance) pour que cette section se remplisse.", ""]
    else:
        lot = [a for a in alertes if a["famille"].startswith("EPI")]
        t.append(f"{len(lot)} articles à échéance dans les 30 jours ou déjà dépassés." if lot else "Aucun dans les 30 jours.")
        t.append("")

    t += ["---", "",
          "**Validation humaine requise.** Ces alertes ne ferment ni n'ouvrent aucune action : "
          "elles signalent des dates. La décision appartient au comité et à l'employeur."]
    return "\n".join(t) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--date", help="se placer à cette date, format AAAA-MM-JJ")
    p.add_argument("--sortie", default=RACINE / "rapports")
    a = p.parse_args()

    aujourdhui = lire_date(a.date) or date.today()
    data = lire_json(DONNEES / "registre_html.json")
    fichier_config = DONNEES / "echeances.json"
    config = lire_json(fichier_config) if fichier_config.exists() else {}
    fichier_epi = PRIVE / "epi_recertification.json"
    epi = lire_json(fichier_epi).get("articles", []) if fichier_epi.exists() else []

    alertes = collecter(aujourdhui, data, config, epi)
    texte = markdown(aujourdhui, alertes, data, config, bool(epi))

    sortie = Path(a.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    chemin = sortie / f"alertes_{aujourdhui.isoformat()}.md"
    chemin.write_text(texte, encoding="utf-8")

    compte = {h: len([x for x in alertes if x["horizon"] == h]) for h in ("dépassé", "7 jours", "30 jours")}
    print(f"Dépassé : {compte['dépassé']} · 7 jours : {compte['7 jours']} · 30 jours : {compte['30 jours']}")
    print(f"Alertes → {chemin}")
    print("Validation humaine requise : ces alertes ne ferment aucune action.")


if __name__ == "__main__":
    main()
