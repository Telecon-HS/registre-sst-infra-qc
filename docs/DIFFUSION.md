# Diffusion, version et conservation

## Quelle forme fait foi

| Forme | Rôle | Diffusion |
|---|---|---|
| **PDF du plan d'action** | **Pièce de référence.** C'est elle qu'on cite en séance et qu'on joint au procès-verbal. | Membres du comité, direction |
| Page Comité (HTML) | Consultation : les neuf vues, les photographies, le détail des incidents | Comité seulement — contient des noms et des photographies |
| Page Terrain (HTML) | Consultation : consignes pour superviseurs et travailleurs | Peut circuler sur le terrain — aucune donnée nominative |
| Classeur (XLSX) | Source de travail, traçabilité ligne par ligne | Partenaire d'affaires SST, secrétariat du comité |

Rien ne se signe sur une page web. Les décisions se consignent au procès-verbal, PDF en pièce jointe.

## Version

`donnees/version.json` porte la version, la date et l'état. Les générateurs l'inscrivent dans les quatre livrables et l'ajoutent au nom des fichiers : `..._v8_2026-09-20`.

À chaque publication : monter la version dans `version.json`, régénérer, déposer, et inscrire une ligne dans `JOURNAL.md`.

## Ce qui se conserve, et où

- Le PDF de chaque version présentée en séance : SharePoint du comité, avec le procès-verbal qui le cite.
- Les données et les générateurs : le dépôt `Telecon-HS/registre-sst-infra-qc`, privé. L'historique des dépôts (commits) tient lieu d'historique des versions.
- Les noms, les photographies et le détail des incidents : dossier privé sur SharePoint, jamais dans le dépôt.
- Durée de conservation des procès-verbaux : à confirmer auprès de la CNESST. Voir `A_CORRIGER.md`.

## Points d'entrée

Pour le terrain, viser un lien stable — bibliothèque SharePoint, ou code QR affiché au dépôt — plutôt qu'un fichier envoyé par courriel : une copie enregistrée devient périmée sans prévenir. Chaque page porte l'avis correspondant en pied.
