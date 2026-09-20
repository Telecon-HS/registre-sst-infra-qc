# Journal

## 20 septembre 2026 — reconstruction du dépôt

Les modules de données et les générateurs d'origine avaient été perdus. Le dépôt a été reconstitué à partir des livrables du 19 septembre 2026 (version 7) avec `outils/extraire_depuis_livrables.py`. **Aucune donnée n'a été modifiée.**

Vérifications faites le jour même :

- **Page HTML** : régénérée avec le dossier privé, identique octet pour octet à la page publiée.
- **Classeur** : 15 onglets, 4 085 cellules comparées (valeurs et mise en forme) sans écart ; 151 formules recalculées sans erreur, mêmes résultats que l'original.
- **Plan d'action PDF** : reconstitué à partir du texte et des images du v7 ; très proche visuellement, pas identique au pixel. Format lettre paysage.
- **Confidentialité** : 27 personnes remplacées par des jetons ; 44 photos et le détail de 9 incidents sortis vers le dossier privé ; contrôle `verifier_confidentialite.py` sans problème ; livrables produits sans dossier privé vérifiés sans aucun nom.

Constats du jour, non appliqués : voir `A_CORRIGER.md`.
