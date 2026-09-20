# Journal

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
