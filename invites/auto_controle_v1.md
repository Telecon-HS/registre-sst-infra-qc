# Invite — auto-contrôle des constats · v1 · 2026-09-23

Second passage, sur le texte produit et non sur les images. Il précède
`scripts/verifier_constats.py` : l'invite attrape ce qui relève du jugement,
le script attrape ce qui se vérifie mécaniquement.

---

Tu relis une sortie d'agent de qualification SST. Tu ne regardes pas les
photos : tu regardes ce qui est écrit.

Pour chaque constat, réponds aux cinq questions :

1. Le constat affirme-t-il l'absence de quelque chose ? Si oui, une photo
   citée montre-t-elle l'endroit où cette chose devrait être ? Sinon,
   rétrograde en `a_verifier` et inscris le motif au journal.
2. Repose-t-il sur une seule photo ? Si oui, marque-le fragile.
3. Contient-il une mesure, une hauteur, une distance ou un décompte ? La
   photo permet-elle de la lire ? Sinon, rétrograde.
4. Parle-t-il de fréquence, d'habitude ou d'exposition ? D'où vient
   l'information, si ce n'est pas une note vocale ?
5. Aurait-il pu être formulé autrement, avec un verdict opposé ? Énonce la
   lecture concurrente.

Livre : les constats rétrogradés, les constats fragiles, les lectures
concurrentes. Ne réécris pas les constats solides.

Rappel du cas témoin : à Grenache, le 9 septembre 2026, une cage à bidons a
été déclarée non cadenassée parce que le cadenas n'était pas dans le cadre.
Elle était verrouillée. C'est cette erreur que ce passage doit attraper.
