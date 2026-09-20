# Registre des risques SST — Infra Québec (projet Falcon)

Ce dépôt sert à produire les trois livrables du comité SST d'Infra Québec à partir d'une seule source de données :

| Livrable | Script | Contenu |
|---|---|---|
| Classeur Excel, 15 onglets | `scripts/generer_classeur.py` | Registre de 39 risques, traçabilité, incidents, visites, inspections, initiatives, documents du comité, prévention, photos, dossier du comité, projets, CAPA, synthèse, lecture |
| Plan d'action PDF, 3 pages | `scripts/generer_plan_action.py` | Risques et calendrier · dossiers et documents du comité · prévention et reconnaissance |
| Page HTML autonome | `scripts/generer_page.py` | Sélecteur de rôle (Comité, Direction, Superviseurs, Travailleurs) et neuf vues |

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

python scripts/tout_generer.py                 # les trois livrables → sortie/
python scripts/tout_generer.py --sans-prive    # version sans données privées
```

Les livrables sont écrits dans `sortie/`, qui n'est jamais versé au dépôt. Les formules du classeur se recalculent à l'ouverture dans Excel.

## Modifier le registre

| Pour changer… | Éditer |
|---|---|
| un risque, un incident rattaché, un site, une vue de la page | `donnees/registre_html.json` |
| une cellule du classeur | `donnees/classeur/NN_Onglet.json` (coordonnée, valeur, style) |
| le texte du plan d'action PDF | `donnees/plan_action.json` |
| la priorité d'un risque dans le PDF | `donnees/registre_html.json` (le PDF la lit là) |

Une même information peut figurer dans plusieurs fichiers (par exemple un risque dans la page, le classeur et le PDF). **Une correction doit être faite partout où l'information apparaît**, dans un même dépôt daté.

**Avant chaque dépôt :**

```bash
python scripts/verifier_confidentialite.py
```

## Structure

```
donnees/        données du registre, sans noms (jetons ⟦Pnn⟧)
gabarits/       gabarit de la page HTML et logo
scripts/        générateurs, contrôle de confidentialité
outils/         extraction ayant servi à reconstruire le dépôt le 20 septembre 2026
docs/           doctrine, note de transfert, journal, constats à appliquer
```

## Documents

- [`docs/DOCTRINE.md`](docs/DOCTRINE.md) — les règles qui rendent le dossier défendable, et les corrections à ne pas défaire
- [`docs/A_CORRIGER.md`](docs/A_CORRIGER.md) — constats du 20 septembre 2026, pas encore appliqués
- [`docs/JOURNAL.md`](docs/JOURNAL.md) — historique et vérifications
- [`docs/NOTE_TRANSFERT_2026-09-19.md`](docs/NOTE_TRANSFERT_2026-09-19.md) — note de reprise du dossier
