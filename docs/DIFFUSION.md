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

## Page Terrain en ligne — Cloudflare

**Adresse** : https://sst-terrain-infra-qc.mario-deshaies.workers.dev
**Accès** : mot de passe, utilisateur `terrain`. Le mot de passe se transmet de vive voix ou par un canal interne. **Jamais dans ce dépôt.**
**Mise en ligne le** : 20 septembre 2026, version 8.

### Ce qui peut y aller, et ce qui n'y va jamais

Seule la page Terrain est hébergée là. Le compte Cloudflare est un compte personnel ouvert pour les projets Telecon : **la page Comité, le classeur et les PDF n'y vont jamais**, parce qu'ils contiennent des noms, des blessures et des photographies. Les y déposer reviendrait à sortir des renseignements personnels du locataire Telecon.

### Mettre la page à jour

Dans `C:\Dev\terrain-site`, hors du dépôt Git :

```
copier la nouvelle page dans public\index.html
npx.cmd wrangler deploy
```

Changer le mot de passe : `npx.cmd wrangler secret put MOT_DE_PASSE`

### Points de vigilance

- Le projet Cloudflare (`worker.js`, `wrangler.jsonc`) vit **hors du dépôt**, pour éviter que la page publiée y soit versée par mégarde.
- Le compte est au nom d'une seule personne : ajouter un second administrateur, ou prévenir les TI de l'existence du site.
- L'adresse reste stable ; seul le contenu change. Un code QR affiché au dépôt et dans les fourgons suffit à la diffusion.
- La page est servie sans mise en cache et avec `noindex` : elle n'est pas indexée par les moteurs de recherche.

