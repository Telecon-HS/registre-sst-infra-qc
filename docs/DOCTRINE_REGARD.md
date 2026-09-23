# REGARD — doctrine du volet photos

**Registre · Écarts · Gestion · Actions · Risques · Décisions**

Ce document complète `docs/DOCTRINE.md`. Il ne le remplace pas : toutes les
règles du dépôt s'appliquent aux constats issus de photos, en plus de
celles-ci.

REGARD lit des photos de visite et propose des constats. Il ne constate rien
lui-même : il prépare le travail de l'inspecteur, qui tranche.

---

## Ce qui a motivé ces règles

Un pilote a été conduit sur le dépôt de la rue Grenache, visite du 9 septembre
2026 : 62 photos lues sur 99, sans accès au dossier humain, puis confrontation
zone par zone avec l'analyse du partenaire SST.

Résultat sur les dix éléments de la cour : **6 retrouvés, 1 partiel,
2 divergences, 2 manqués.**

Les règles ci-dessous viennent de ces écarts. Elles ne sont pas des principes
généraux : chacune répond à une erreur qui a réellement eu lieu.

| Erreur mesurée | Règle |
|---|---|
| Cage à bidons déclarée non cadenassée alors qu'elle l'était : le cadenas n'était pas dans le cadre | R1 — jamais d'absence sans preuve |
| Constat bâti sur une seule photo | R2 — constat fragile signalé |
| Hauteurs et distances tirées d'images | R3 — une mesure ne se lit pas sur une photo |
| Risque d'exposition coté trop bas faute de savoir qui circule | R4 — l'exposition ne se photographie pas |
| Sol et obstacles au passage jamais relevés | R8 — balayage obligatoire du sol et du passage |

---

## Les règles

**R1. Ne jamais conclure à l'absence d'un dispositif qu'on ne voit pas.**
Cadenas, sangle, chaîne, plaque, garde-corps, extincteur, protecteur : si
l'élément n'apparaît pas, le statut est « à vérifier », jamais « absent ».
Un constat d'absence exige au moins une photo dont `visibilite_zone_critique`
est vrai, c'est-à-dire une photo qui montre, dégagée et nette, la place où le
dispositif devrait être.

**R2. Un constat sur une seule photo est fragile.** Il n'est pas faux ; il est
à confirmer sur place. Le contrôle le marque, il ne le bloque pas.

**R3. Une mesure ne se lit pas sur une photo.** Hauteur, jeu, distance,
nombre de niveaux : « à vérifier », sauf si une entrevue ou un document
l'appuie.

**R4. L'exposition ne se photographie pas.** Qui circule, à quelle heure,
combien, avec quel éclairage : ces informations viennent des notes vocales ou
des entrevues. Une photo ne les porte pas. Un constat de fréquence appuyé sur
une image seule est rétrogradé.

**R5. La machine ne déclare jamais la conformité.** Le statut « conforme »
exige `validation_humaine`. C'est la règle du dépôt, appliquée aux constats.

**R6. Un constat non conforme cite sa source.** Photo ou note vocale, sans
exception.

**R7. Les renseignements personnels relèvent du dossier privé.** Visages,
noms sur des affiches, numéros de téléphone sur des étiquettes d'inspection,
plaques d'immatriculation : la photo est signalée, elle ne quitte pas les
systèmes de Telecon, et le dépôt n'en garde que l'empreinte.

**R8. Le sol et le passage sont les deux angles morts.** Chaque photo doit
déclarer si l'agent les a examinés : ornières, flaques, glace, taches d'un
côté ; timons, béquilles, boyaux, câbles, barres qui dépassent de l'autre.
Le modèle regarde spontanément les objets, pas les trajets.

**R9. On inscrit et on date, on n'efface pas.** Chaque rétrogradation est
écrite au journal du constat, comme les erreurs du registre.

**R10. Relever aussi ce qui va bien.** Rangement, EPI portés, protecteurs en
place, étiquettes à jour. Un rapport composé uniquement d'écarts se lit comme
un réquisitoire, et le document du 10 septembre l'avait déjà compris : *rien
ici ne vise le travail de qui que ce soit.*

---

## Ce que le dépôt ne contient pas

**Aucune image, jamais.** Les photos vivent dans les systèmes de Telecon. Le
dépôt ne garde que l'empreinte SHA-256, l'horodatage, la séquence et la
lecture. C'est le même cloisonnement que pour les noms, avec les jetons
`⟦Pnn⟧`.

**Aucune note vocale.** Sa transcription nomme des personnes : elle va dans le
dossier privé.

---

## La chaîne

```
photos (hors dépôt)
  └─ scripts/ingerer_photos.py      → rapports/index_photos_AAAA-MM-JJ.json
       └─ agent de lecture           → rapports/constats_AAAA-MM-JJ.json
            └─ scripts/verifier_constats.py
                 └─ lecture et décision humaines
                      └─ inscription au registre, à la main, sourcée
```

Comme pour l'ingestion des exports eCompliance, **rien n'est écrit dans
`donnees/` par un script**. La dernière étape reste manuelle, et c'est
volontaire : c'est elle qui rend le dossier défendable.

---

## Ce que le contrôle ne mesure pas

`verifier_constats.py` vérifie qu'un constat n'affirme pas plus que sa preuve
ne permet. Il ne dit pas si le constat est juste, ni si quelque chose a été
manqué. Seule la confrontation à un étalon le mesure : voir
`etalons/grenache-2026-09-09/`.

Et l'étalon lui-même a ses limites : il ne contient que ce que l'humain a vu.
Les deux manqués du pilote — l'état du sol et les timons de compresseurs — ont
été trouvés par l'humain seul. Rien ne garantit qu'il n'ait pas, lui aussi,
son angle mort.

---

*Document préparatoire. Aucun verdict de conformité. Les références au manuel
agrégé et aux textes réglementaires sont à revérifier avant tout usage
réglementaire.*
