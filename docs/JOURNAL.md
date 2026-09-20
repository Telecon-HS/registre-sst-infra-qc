# Journal

## 20 septembre 2026 — contrôle des citations, jonction avec ANCRAGE

`scripts/verifier_citations.py` croise les champs « norme » des 39 risques avec `corpus/index-procedures.csv` du dépôt Telecon-SST-Agents (ANCRAGE). Les préfixes SSE- et HSE- sont traités comme équivalents : seul le numéro compte. Cinq tests (`pytest -q`).

Premier passage, 67 citations : 33 confirmées, 19 partielles, 6 absentes de l'index, 1 hors index (CSTC et décret), 8 risques sans procédure Telecon citée.

Quatre procédures citées par le registre n'existent pas à l'index d'ANCRAGE : 403 (Poteaux et torons), 501 (lignes directrices de sauvetage), 601 (liste des EPI approuvés) et, indirectement, les formulaires F01. À remonter côté ANCRAGE.

Limite assumée : l'index ne descend pas au niveau des sections. Les § restent à vérifier au manuel, comme les 18 et 19 septembre 2026.

## 20 septembre 2026 — page Terrain en ligne

Page Terrain v8 déployée sur Cloudflare Workers, protégée par mot de passe (utilisateur `terrain`, secret `MOT_DE_PASSE`), sans cache et non indexable. Adresse : sst-terrain-infra-qc.mario-deshaies.workers.dev. Le projet de déploiement vit hors du dépôt. Règles et procédure de mise à jour : `DIFFUSION.md`.

## 20 septembre 2026 — volumes et tendances

Graphiques ajoutés à la vue Prévention de la page Comité : courbe de tendance mensuelle (six types les plus fréquents, février à septembre) et histogramme des trois relevés. SVG produit par la page, sans bibliothèque, adapté au téléphone et au mode sombre. Le classeur garde ses propres graphiques Excel.

`donnees/volumes.json` réunit les trois relevés du même volume d'activité : registre v7 (51 fiches verrouillées du 19 mai au 17 septembre), export daté « Public Inspections » (165 fiches, février à septembre 2026, tous statuts) et tableau de bord Safety Intelligence (1 837 fiches, année 2026, sans dates ni statuts).

- Nouvel onglet **« Volumes et tendances »** au classeur : volumes mensuels par type, courbe de tendance, comparaison des trois relevés en histogramme, lecture et réserve.
- La vue Prévention de la page Comité porte le tableau des trois relevés.
- Le PDF renvoie à l'onglet du classeur.

Point relevé au passage : sur l'export daté, l'inspection mensuelle du véhicule ne s'interrompt pas après le 16 juillet — une ou deux fiches par mois de mars à septembre. C'est un argument de plus pour la reformulation de R-15.

## 20 septembre 2026 — charpente du programme de prévention

`PROGRAMME_PREVENTION_STRUCTURE.md` : onze sections, avec pour chacune ce que le registre fournit déjà et ce qui manque. Trous principaux : couverture limitée à Falcon, risques psychosociaux absents, aucun volet de surveillance du milieu et de la santé, ni de gestion des sous-traitants, ni de formation structurée. Deux réserves commandent le reste : le découpage des établissements n'est pas tranché et le comité ne siège pas.

## 20 septembre 2026 — version 8 et règles de diffusion

- `donnees/version.json` devient la seule source de la version et de la date.
- Les quatre livrables portent une ligne de version en pied : version, date, rôle du support, pièce de référence, avis de péremption et adresse du dépôt.
- Les fichiers produits sont nommés avec leur version : `..._v8_2026-09-20`.
- `docs/DIFFUSION.md` fixe ce qui fait foi, qui reçoit quoi et ce qui se conserve.

## 20 septembre 2026 — corrections de contenu

- **R-15 reformulé.** Le constat n'est plus « plus aucune inspection depuis le 16 juillet », mais l'écart entre deux sources : trois fiches à l'export « Public Inspections », 58 au tableau de bord pour 2026, plus deux fiches d'août et de septembre restées non verrouillées (29444070, 29719434). La décision demandée comprend maintenant la question à poser à l'administrateur eCompliance.
- **Page 3 et vue Prévention refaites.** Les volumes sont présentés comme un relevé partiel, avec une réserve visible : 165 fiches à l'export contre 1 837 au tableau de bord, écart non expliqué. Chaque ligne porte le chiffre du tableau de bord en regard. Les indicateurs du haut passent aux chiffres 2026 : 1 837 fiches, 113 personnes, 409 rapports de visite de chantier, 165 fiches à l'export.
- **Chiffres rendus cohérents** : trente-neuf risques et douze priorités 1 dans la lecture Direction.

Le tableau mois par mois ne peut pas être refait pour l'instant : le tableau de bord ne donne ni dates ni statuts.

## 20 septembre 2026 — audit UX/UI, points 6 à 17

Interface seulement ; aucune donnée modifiée.

- **6** Les chiffres du comité ne s'affichent plus hors de la lecture Comité.
- **7** Le nom de l'auteur disparaît des lectures Superviseurs et Travailleurs.
- **8** « 11 / 9 » devient « 11 visites SST au dossier, dont 9 consolidées ».
- **9** Le numéro et le titre ne sont plus collés dans le calendrier.
- **10** La priorité est écrite (P1, P2, P3) à côté de la pastille de couleur.
- **11** Cibles tactiles d'au moins 44 px sur téléphone.
- **12** Plus aucun texte sous 12 px sur téléphone ; plus rien à 10 px ailleurs.
- **13** Photographies repliées par site et bouton « retour en haut » sur téléphone.
- **14** Mise en page d'impression : lettre paysage, sans navigation.
- **15** Repli de police complété pour la lecture hors ligne.
- **16** Bouton clair / sombre, mémorisé quand le navigateur le permet.
- **17** Visionneuse plein écran pour les photographies, fermeture par Échap.

La page Terrain reçoit les mêmes corrections : elle partage le CSS de la page Comité.

## 20 septembre 2026 — page Terrain séparée et corrections d'affichage

Décision : l'audit UX/UI a montré qu'un travailleur pouvait cliquer sur « Comité » et lire les noms et le détail des incidents. Le sélecteur de rôle n'est pas une protection.

- **Page Terrain** (`gabarits/page_terrain.html`) : nouveau fichier distinct, consignes Superviseurs et Travailleurs seulement. Ne reçoit jamais de nom, de photo ni d'incident ; le générateur refuse de l'écrire s'il en détecte.
- **Mode sombre** : le bandeau garde un fond foncé. Contraste du titre : environ 2:1 avant, 14,6:1 après. Règle CSS mal formée supprimée.
- **Onglets sur téléphone** : ils défilent au lieu d'élargir la page. Largeur de la page : 814 px avant, 390 px après, sur les neuf vues.
- **Premier écran sur téléphone** : texte d'introduction replié derrière « À propos de ce document », chiffres sur une ligne défilante. Début du contenu : environ 680 px avant, 276 px après.
- **Liste → fiche sur téléphone** : toucher un risque amène à sa fiche, avec un bouton « Retour à la liste des risques ».

Données : inchangées (contenu de la page Comité identique à la v7, vérifié). La page Comité n'est plus identique octet pour octet à la v7 : c'est voulu.

## 20 septembre 2026 — reconstruction du dépôt

Les modules de données et les générateurs d'origine avaient été perdus. Le dépôt a été reconstitué à partir des livrables du 19 septembre 2026 (version 7) avec `outils/extraire_depuis_livrables.py`. **Aucune donnée n'a été modifiée.**

Vérifications faites le jour même :

- **Page HTML** : régénérée avec le dossier privé, identique octet pour octet à la page publiée.
- **Classeur** : 15 onglets, 4 085 cellules comparées (valeurs et mise en forme) sans écart ; 151 formules recalculées sans erreur, mêmes résultats que l'original.
- **Plan d'action PDF** : reconstitué à partir du texte et des images du v7 ; très proche visuellement, pas identique au pixel. Format lettre paysage.
- **Confidentialité** : 27 personnes remplacées par des jetons ; 44 photos et le détail de 9 incidents sortis vers le dossier privé ; contrôle `verifier_confidentialite.py` sans problème ; livrables produits sans dossier privé vérifiés sans aucun nom.

Constats du jour, non appliqués : voir `A_CORRIGER.md`.
