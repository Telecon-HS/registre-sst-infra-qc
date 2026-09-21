# Journal

## 21 septembre 2026 — niveau de confiance dans chaque fiche

La fiche de chaque risque de la page Comité affiche maintenant le niveau de confiance de chaque procédure citée : confirmé, partiel, à valider, ou absent de l'index. Il est lu dans l'index ANCRAGE **au moment de la génération** (variable `ANCRAGE_INDEX`), avec les correspondances de `donnees/alias_procedures.json` ; un même document cité sous deux numéros ne compte qu'une fois. Une référence externe au manuel (CSTC, décret) est signalée comme hors index. Si l'index est inaccessible, la fiche affiche « à confirmer » plutôt qu'un niveau.

Chaque bloc rappelle que l'index confirme l'existence d'une procédure et son niveau de confiance, jamais le contenu d'une section. Aucune donnée de `donnees/` n'est modifiée : le niveau est ajouté à la page produite, pas au registre. Mode sombre, mode séance et affichage téléphone vérifiés. Cinq tests de plus (54 au total).

## 21 septembre 2026 — contrôle des citations corrigé, correspondances de numéros

**Erreur corrigée, inscrite ici.** Le contrôle du 20 septembre annonçait six citations « absentes de l'index ANCRAGE », dont 403 et 601. C'était en bonne partie un défaut du contrôle : il ramenait `SSE-501.1` à `501`, lisait mal `SSE-601-NOR`, et ignorait qu'un même document peut porter deux numéros. La vérification faite dans ANCRAGE l'a montré (constats 3 et 4).

- Le contrôle garde maintenant le sous-numéro (501.1) et le type NOR (601-NOR).
- `donnees/alias_procedures.json` porte les correspondances, chacune avec sa source : HSE.TEL-PRO-403 → SSE-1303 (constat 3), HSE-601 → SSE-601-NOR, HSE-1309.1 à .3 → SSE-501.1 à .3 (constat 4).
- Côté ANCRAGE, commit 8d39140 : ajout de SSE-501.1, 501.2 et 501.3 à l'index, en `a_valider`, et constat 7.

Nouveau passage, avec l'index à jour : 33 citations confirmées, 19 partielles, 5 à valider, 2 absentes — `SSE.TEL.FOR-103.2` et `HSE-300.1`, deux documents à sous-numéro que l'index ne connaît pas. Aucune n'est ramenée d'office à sa procédure parente. Quatre tests de plus (49 au total).

## 20 septembre 2026 — mode séance

Gabarit seulement, aucune donnée modifiée (vérifié : contenu de la page identique avant et après). Nouveau bouton « Mode séance » dans la lecture Comité, ou adresse terminée par `#seance` : une page plein écran, projetable, sans navigation, quittée par Échap.

- **Décisions à prendre** (18) : les six décisions de constitution du comité, les sept risques à trancher en séance, les cinq dossiers dont l'échéance tombe à la séance.
- **Actions en retard** : aucune ne peut l'être, les délais courant à compter de la décision du comité ; la page le dit et montre ce que cette décision déclenchera, par délai.
- **Documents du comité** : 3 tenus, 12 en gabarit ou à confirmer, 3 absents — même classement que le plan d'action et le tableau de bord. Le premier essai en comptait 4 absents : corrigé pour ne pas créer une nouvelle contradiction.
- **Échéances réglementaires**, avec le nombre de jours restants, et **réserves** visibles : les cinq questions bloquantes.

Testé en 1920 × 1080 et 1366 × 768, en mode clair et sombre ; sur téléphone, la vue passe en une colonne défilante. Aucun nom de personne.

## 20 septembre 2026 — registre des recommandations au comité

Nouvel onglet du classeur, « Recommandations au comité », alimenté par `donnees/recommandations.json` : date, objet, risque rattaché, procès-verbal, échéance de réponse, réponse de l'employeur, date de la réponse, jours écoulés, statut. Cinq tests de plus (46 au total). Les risques cités par une recommandation sont vérifiés par le contrôle de cohérence.

Le registre part vide : le comité ne siège pas depuis le 18 décembre 2024. Le délai de réponse reste **à confirmer** : la politique SSE-200-TEL-POL art. 4.3 h) ne le chiffre pas, aucun délai n'est prescrit au Québec selon le dossier (à confirmer), et les 21 jours de R-29 sont une proposition soumise au comité, non adoptée. Tant qu'aucun délai n'est inscrit, aucune échéance de réponse n'est calculée. Le statut dit seulement si une réponse écrite a été reçue ; il ne juge ni la réponse ni le respect d'un délai.

## 20 septembre 2026 — projet d'ordre du jour

`scripts/ordre_du_jour.py` produit un projet d'ordre du jour en markdown et en PDF : ouverture, dossiers dont le jalon tombe à la séance (5), risques à trancher en séance (7), réserves (4), documents du comité absents (3), clôture — 23 points. Cinq tests de plus (41 au total).

Aucune durée n'existe dans les données : chaque point et la durée totale restent « à confirmer » tant que `donnees/ordre_du_jour.json` ne fixe pas une durée par type de point. Même chose pour la date, le lieu et la composition, puisque la charte du comité n'est pas adoptée. Les porteurs sont désignés par leur rôle.

## 20 septembre 2026 — contrôle de cohérence

`scripts/verifier_coherence.py` vérifie que les livrables disent la même chose : nombre de risques, de priorités 1, d'incidents, d'éléments source et de visites entre `registre_html.json`, `plan_action.json` et le classeur ; calendrier et pastilles du PDF contre les délais du registre ; plages des formules du classeur ; existence de chaque R-xx cité ; source, porteur et échéance pour chaque risque. Code de sortie 1 au premier écart non connu. Aucun seuil de tolérance. Cinq tests de plus (36 au total).

Premier passage, deux écarts trouvés :
- **Corrigé** — la page de garde du classeur affichait encore « version 3 ». Elle lit maintenant `donnees/version.json`, comme les autres livrables.
- **Inscrit comme écart connu** (`donnees/ecarts_connus.json`, renvoi `A_CORRIGER.md` §7) — la page Comité compte 9 visites consolidées, le registre 10 : la visite 29632342 du dépôt Grenache est consolidée mais absente de la liste des visites. Son statut eCompliance est à confirmer avant de l'ajouter.

## 20 septembre 2026 — tableau de bord de direction

Cinquième livrable, `scripts/generer_tableau_bord.py` : quatre pages en lettre paysage, inspirées du tableau de bord opérationnel du 12 septembre, mais calculées à partir des données du registre v8 — aucun chiffre n'est saisi dans le script.

1. Niveau de risque : priorités, familles, délais, éléments par visite, matrice familles × visites.
2. Incidents : les neuf incidents au dossier, catégories STKY normalisées (français et anglais), rattachement aux risques.
3. Prévention : les trois relevés de volume, la tendance mensuelle, les 51 fiches non fermées, les 44 évaluations en hauteur ouvertes.
4. Gouvernance : dossiers en cours, documents du comité, échéances réglementaires.

Tables CSV pour Power BI dans `sortie/powerbi/`, sans aucun nom. Cinq tests de plus (31 au total).

Ce qui n'a pas été repris du tableau du 12 septembre, faute de source dans le dépôt : les huit contrôles critiques et leur état par situation, la sévérité de chaque écart, les 26 incidents de tout Infra QC, l'avancement en pourcentage des chantiers et le diagramme de déploiement. La page 2 explique l'écart de périmètre (9 incidents au registre, 26 sur tout Infra QC). Décomptes agrégés ajoutés à `donnees/volumes.json` : fiches non fermées par type, évaluations en hauteur, question de l'AST.

## 20 septembre 2026 — rapport hebdomadaire

`scripts/rapport_hebdo.py` assemble l'ingestion, les alertes et le contrôle des citations en un seul rapport : ce qui a bougé, ce qui est en retard, ce qui ne concorde pas. L'état de la semaine est conservé dans `rapports/etat.json`. Huit tests de plus (25 au total). `docs/TACHE_PLANIFIEE.md` documente la tâche Windows du lundi matin.

Deux pièges relevés en écrivant le script, corrigés et couverts par des tests :
- une fiche absente de l'export de la semaine n'est **pas** une fiche fermée ; elle est comptée à part, statut inconnu, à confirmer ;
- le rapprochement entre un type d'activité du registre et un titre de formulaire passe par un motif explicite inscrit dans `donnees/volumes.json`, et non par un mot deviné : le premier essai confondait « inspection avant départ » et « inspection quotidienne avant utilisation ».

Aucun seuil d'écart n'est appliqué : les volumes des quatre sources sont présentés côte à côte, sans jugement.

## 20 septembre 2026 — alertes d'échéances

`scripts/alertes.py` produit `rapports/alertes_AAAA-MM-JJ.md` : échéances réglementaires, jalons datés des dossiers, actions du registre, documents du comité à produire, recertifications d'EPI. Trois horizons : dépassé, 7 jours, 30 jours. Sept tests de plus (17 au total).

Deux refus d'inventer, inscrits dans le code et couverts par des tests :
- les délais des risques ne sont pas convertis en dates tant que `donnees/echeances.json` ne porte pas la date de décision du comité ; le rapport compte alors les actions par délai et explique pourquoi ;
- une date de version trouvée dans le champ « état » d'un dossier n'est pas traitée comme un jalon.

Au 20 septembre : rien de dépassé, rien sous 7 jours, deux échéances réglementaires au 1er octobre, 15 documents du comité à produire, section EPI marquée « à confirmer » faute de la liste HSE-601.

## 20 septembre 2026 — ingestion des exports

`scripts/ingerer_exports.py` lit les exports déposés dans `ingest/`, dédoublonne par identifiant de fiche et écrit un rapport daté dans `rapports/` : volumes par type et par mois, fiches non fermées, fiches sans signature, statuts rencontrés, réserves. Cinq tests de plus (`pytest -q` : 10 au total).

Le script n'écrit jamais dans `donnees/` et ne recopie aucun nom. `ingest/` et `rapports/` sont ignorés par Git, parce que les exports contiennent des noms de personnes.

Premier passage sur les deux exports du 20 septembre : 165 fiches de février à septembre 2026, dont 51 non fermées — 27 inspections avant départ, 7 camion-nacelle, 4 visites SST du partenaire d'affaires.

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
