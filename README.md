# Registre des risques SST — Infra Québec (projet Falcon)

Ce dépôt sert à produire les livrables du comité SST d'Infra Québec à partir d'une seule source de données :

| Livrable | Script | Contenu |
|---|---|---|
| Classeur Excel, 15 onglets | `scripts/generer_classeur.py` | Registre de 39 risques, traçabilité, incidents, visites, inspections, initiatives, documents du comité, prévention, photos, dossier du comité, projets, CAPA, synthèse, lecture |
| Plan d'action PDF, 3 pages | `scripts/generer_plan_action.py` | Risques et calendrier · dossiers et documents du comité · prévention et reconnaissance |
| Page HTML **Comité** | `scripts/generer_page.py` | Sélecteur de rôle et neuf vues. Contient noms, photos et incidents : à partager **au comité seulement** |
| Tableau de bord **Direction**, PDF 4 pages | `scripts/generer_tableau_bord.py` | Priorités, familles, visites, incidents, trois relevés de volume, gouvernance. Graphiques SVG. Plus des tables CSV pour Power BI dans `sortie/powerbi/` |
| Page HTML **Terrain** | `scripts/generer_page.py` | Consignes Superviseurs et Travailleurs seulement. Aucun nom, aucune photo, aucun incident : peut être partagée sur le terrain |

**État actuel : version 7 du 19 septembre 2026, reconstruite le 20 septembre.** Des constats relevés depuis ne sont pas encore appliqués : voir [`docs/A_CORRIGER.md`](docs/A_CORRIGER.md).

Document préparatoire. Aucun verdict de conformité. Les références au manuel agrégé et aux textes réglementaires sont à revérifier avant tout usage réglementaire.

## Ce qui n'est pas dans ce dépôt

Le dépôt ne contient **aucun nom de personne, aucune photo et aucun détail d'incident**. Ces données vivent dans un **dossier privé**, conservé sur le SharePoint du comité :

```
prive/
  noms.json             jeton → nom (et graphies rencontrées)
  incidents.json        type, lieu, personnes et lecture de chaque incident
  classeur_prive.json   cellules privées de l'onglet Incidents
  photos/               44 photos, visages masqués
```

Dans les données du dépôt, une personne apparaît sous la forme d'un jeton : `⟦P01⟧`.

- **Avec** le dossier privé, les livrables sont complets.
- **Sans** lui, ils se génèrent quand même, avec « [nom retiré] », sans photos et sans détail d'incidents.

## Utilisation

```bash
pip install -r requirements.txt
playwright install chromium            # une seule fois, pour le PDF

# placer le dossier privé à côté du dépôt : ../prive
# (ou indiquer son chemin : export REGISTRE_PRIVE=/chemin/vers/prive)

python scripts/tout_generer.py                 # les cinq livrables → sortie/
python scripts/tout_generer.py --sans-prive    # version sans données privées
```

Les livrables sont écrits dans `sortie/`, qui n'est jamais versé au dépôt. Les formules du classeur se recalculent à l'ouverture dans Excel.

## Ingérer un export eCompliance

```bash
# déposer les .xlsx ou .csv dans ingest/ (ignoré par Git : ils contiennent des noms)
python scripts/ingerer_exports.py          # → rapports/rapport_ingestion_AAAA-MM-JJ.md
```

Le rapport donne les volumes par type et par mois, les fiches non fermées et les fiches sans signature. Il ne contient aucun nom, n'écrit jamais dans `donnees/` et ne porte aucun verdict : ce qu'il faut retenir s'inscrit au registre à la main, sourcé.

## Rapport hebdomadaire

```bash
python scripts/rapport_hebdo.py         # → rapports/rapport_hebdo_AAAA-MM-JJ.md
```

Un seul rapport : ce qui a bougé depuis la semaine dernière, ce qui est en retard, ce qui ne concorde pas entre les sources. Il assemble l'ingestion, les alertes et le contrôle des citations sans les remplacer. Pour le lancer chaque lundi : [`docs/TACHE_PLANIFIEE.md`](docs/TACHE_PLANIFIEE.md).

## Ordre du jour du comité

```bash
python scripts/ordre_du_jour.py         # → sortie/Ordre_du_jour_comite_SST_projet_v8_….md et .pdf
```

Points tirés des données : dossiers dont le jalon tombe à la séance, risques à trancher en séance, réserves, documents absents. Date, lieu et durées restent « à confirmer » tant que `donnees/ordre_du_jour.json` ne les fixe pas.

## Alertes d'échéances

```bash
python scripts/alertes.py               # → rapports/alertes_AAAA-MM-JJ.md
python scripts/alertes.py --date 2026-10-05
```

Quatre familles : échéances réglementaires, jalons datés des dossiers, actions du registre et recertifications d'EPI. Trois horizons : dépassé, 7 jours, 30 jours.

Les délais du registre courent **à compter de la décision du comité**. Tant que `donnees/echeances.json` ne porte pas cette date, aucune échéance de risque n'est calculée : le rapport compte les actions par délai et le dit. La liste HSE-601 n'étant pas dans ce dépôt, la section EPI se remplit seulement si `prive/epi_recertification.json` existe.

## Modifier le registre

| Pour changer… | Éditer |
|---|---|
| un risque, un incident rattaché, un site, une vue de la page | `donnees/registre_html.json` |
| une cellule du classeur | `donnees/classeur/NN_Onglet.json` (coordonnée, valeur, style) |
| le texte du plan d'action PDF | `donnees/plan_action.json` |
| une recommandation écrite du comité, ou le délai de réponse adopté | `donnees/recommandations.json` (onglet « Recommandations au comité » du classeur) |
| la version et la date des livrables | `donnees/version.json` (elles apparaissent dans les quatre livrables et dans les noms de fichiers) |
| la priorité d'un risque dans le PDF | `donnees/registre_html.json` (le PDF la lit là) |
| l'apparence des pages HTML | `gabarits/page_registre.html` (son CSS sert aussi à la page Terrain) |
| la structure de la page Terrain | `gabarits/page_terrain.html` |

Une même information peut figurer dans plusieurs fichiers (par exemple un risque dans la page, le classeur et le PDF). **Une correction doit être faite partout où l'information apparaît**, dans un même dépôt daté.

**Avant chaque dépôt :**

```bash
python scripts/verifier_confidentialite.py
python scripts/verifier_citations.py    # citations normatives contre l'index ANCRAGE
python scripts/verifier_coherence.py    # les livrables disent-ils la même chose ?
pytest -q
```

Le contrôle des citations lit `corpus/index-procedures.csv` du dépôt **Telecon-SST-Agents (ANCRAGE)**. Donnez son chemin par la variable `ANCRAGE_INDEX`, ou placez les deux dépôts côte à côte. L'index confirme l'existence d'une procédure et son niveau de confiance ; il ne confirme jamais le contenu d'une section.

## Structure

```
donnees/        données du registre, sans noms (jetons ⟦Pnn⟧)
gabarits/       gabarit de la page HTML et logo
scripts/        générateurs, contrôles (confidentialité, citations)
tests/          tests des contrôles (pytest)
outils/         extraction ayant servi à reconstruire le dépôt le 20 septembre 2026
docs/           doctrine, note de transfert, journal, constats à appliquer
```

## Documents

- [`docs/DOCTRINE.md`](docs/DOCTRINE.md) — les règles qui rendent le dossier défendable, et les corrections à ne pas défaire
- [`docs/A_CORRIGER.md`](docs/A_CORRIGER.md) — constats du 20 septembre 2026, pas encore appliqués
- [`docs/PROGRAMME_PREVENTION_STRUCTURE.md`](docs/PROGRAMME_PREVENTION_STRUCTURE.md) — charpente du programme de prévention : ce qui existe, ce qui manque
- [`docs/TACHE_PLANIFIEE.md`](docs/TACHE_PLANIFIEE.md) — lancer le rapport hebdomadaire automatiquement
- [`docs/DIFFUSION.md`](docs/DIFFUSION.md) — quelle forme fait foi, qui reçoit quoi, ce qui se conserve
- [`docs/JOURNAL.md`](docs/JOURNAL.md) — historique et vérifications
- [`docs/NOTE_TRANSFERT_2026-09-19.md`](docs/NOTE_TRANSFERT_2026-09-19.md) — note de reprise du dossier
