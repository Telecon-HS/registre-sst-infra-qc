# REGARD — note de passation

**Registre · Écarts · Gestion · Actions · Risques · Décisions**

État au 23 septembre 2026. Dépôt `Telecon-HS/registre-sst-infra-qc`, branche `main`.
Commits de la journée : `7816e51` (installation), `344b2b4` (lieux et GPS).

Ce document dit ce qui existe, pourquoi c'est écrit ainsi, et ce qu'il reste à
faire. Il complète `docs/DOCTRINE_REGARD.md`, qui donne les règles, et
`docs/NOTE_TRANSFERT.md`, qui couvre le registre.

---

## 1. À quoi sert REGARD

Un agent lit les photos d'une visite et **propose** des constats, rattachés aux
items du formulaire, avec leurs actions préremplies. L'inspecteur tranche.
Rien n'entre au registre sans validation humaine et sans source.

REGARD est le volet amont du dépôt. Le registre, lui, était déjà là : REGARD
lui apporte de la matière première, il ne le remplace pas.

---

## 2. Ce qui est en place

| Fichier | Rôle |
|---|---|
| `scripts/ingerer_photos.py` | Lit un dossier de photos : EXIF, GPS, empreintes, séquences par journée, fichiers trop lourds. Écrit un rapport et un index. |
| `scripts/verifier_constats.py` | Contrôle les constats proposés par l'agent. Rétrograde ce qui affirme plus que la preuve ne permet. |
| `tests/test_verifier_constats.py` | 14 tests, un par règle, ancrés sur des erreurs réelles. |
| `donnees/schemas/photo.schema.json` | Contrat : ce qu'est une photo indexée. |
| `donnees/schemas/constat.schema.json` | Contrat : ce qu'est un constat proposé. |
| `donnees/lieux.json` | Registre des lieux, avec classe de risque, fréquence, responsable, vigilances. |
| `invites/lecture_photos_v1.md` | L'invite de production, versionnée. |
| `invites/auto_controle_v1.md` | L'invite de relecture, qui précède le script. |
| `docs/DOCTRINE_REGARD.md` | Les dix règles et leur origine. |

Aucune image n'entre dans le dépôt. Le `.gitignore` exclut `photos/`, les
formats d'image, les vidéos et `rapports/index_photos_*.json`.

---

## 3. La chaîne, de bout en bout

```
photos (hors dépôt, systèmes Telecon)
  └─ scripts/ingerer_photos.py    → rapports/rapport_photos_AAAA-MM-JJ.md
                                     rapports/index_photos_AAAA-MM-JJ.json
       └─ agent de lecture         → rapports/constats_AAAA-MM-JJ.json
            └─ scripts/verifier_constats.py
                                     → rapports/rapport_constats_AAAA-MM-JJ.md
                 └─ lecture et décision humaines
                      └─ inscription au registre, à la main, sourcée
```

Comme `ingerer_exports.py`, ces scripts **lisent et rapportent** : ils n'écrivent
jamais dans `donnees/` et ne portent aucun verdict. La dernière étape reste
manuelle, et c'est volontaire.

### Commandes

```powershell
cd C:\Dev\registre-sst-infra-qc

# 1. Ingestion
python scripts\ingerer_photos.py "CHEMIN\VERS\photos" --lieu INF-QC-ANJOU-COUR

#    avec allègement des fichiers de plus de 5 Mo, hors du dépôt
python scripts\ingerer_photos.py "CHEMIN\VERS\photos" --lieu INF-QC-ANJOU-COUR `
       --reduire "$HOME\Downloads\photos_allegees"

# 2. L'agent lit l'index et produit des constats (invites/lecture_photos_v1.md)

# 3. Contrôle
python scripts\verifier_constats.py rapports\constats_AAAA-MM-JJ.json `
       --photos rapports\index_photos_AAAA-MM-JJ.json
#    code de retour 1 si un manquement bloquant subsiste
```

---

## 4. Les règles, et pourquoi elles existent

Chacune vient d'une erreur mesurée, pas d'un principe général.

| Règle | Origine |
|---|---|
| R1 — jamais d'absence sans preuve | L'agent a déclaré une cage à bidons non cadenassée alors qu'elle l'était : le cadenas n'était pas dans le cadre |
| R2 — constat sur une seule photo signalé fragile | Constats bâtis sur une image isolée |
| R3 — une mesure ne se lit pas sur une photo | Hauteurs et distances tirées d'images |
| R4 — l'exposition ne se photographie pas | Le risque le plus grave du site n'apparaît sur aucune photo |
| R5 — la machine ne déclare jamais la conformité | Doctrine du dépôt |
| R8 — balayage obligatoire du sol et du passage | Ornières et timons de compresseurs jamais relevés |

Le détail complet est dans `docs/DOCTRINE_REGARD.md`.

---

## 5. Ce que le pilote a mesuré

Visite du dépôt de la rue Grenache, 9 septembre 2026, 100 photos. 62 lues par
l'agent, sans accès au dossier humain, puis confrontation zone par zone.

**Sur les dix éléments de la cour : 6 retrouvés, 1 partiel, 2 divergences,
2 manqués.**

- **Divergence 1** — le portail : jugé conforme par l'humain, non conforme par
  l'agent (affiche décolorée, texte rouge illisible). À trancher sur place.
- **Divergence 2** — la cage à bidons : **l'agent avait tort**. La cage était
  verrouillée, et il a manqué le vrai constat, la plaque d'identification
  vierge. C'est de là que vient la règle R1.
- **Manqués** — l'état du sol, et les timons de compresseurs déployés à hauteur
  de tibia. L'agent regarde les objets, pas les trajets. D'où la règle R8.

Le classeur du pilote existe : `Pilote-photos-Grenache_2026-09-09.xlsx`,
27 constats, 25 actions, 11 risques, plus un onglet de recouvrement.
**Il n'est pas encore dans le dépôt** — voir §7.

---

## 6. Conventions à respecter

**Codes de lieu** — `DIVISION-REGION-SITE-ESPACE`, par exemple
`INF-QC-ANJOU-COUR`. Une fois inscrit, un code ne change plus : l'historique des
visites en dépend.

**Codes d'items** — stables et indépendants de l'ordre d'affichage du
formulaire. Sans eux, une révision du formulaire rompt l'historique.
`donnees/items.json` reste à créer.

**Jetons de personnes** — aucun nom dans `donnees/`. Les personnes y sont des
jetons `Pnn`, déclarés dans `donnees/personnes.json` avec un repli lisible.
La correspondance nominative vit dans `prive/noms.json`, hors du dépôt.

**Dossier privé** — `C:\Dev\prive`, à côté du dépôt et jamais dedans. La
variable d'environnement `REGISTRE_PRIVE` doit pointer dessus. Sans elle, les
contrôles s'exécutent en mode dégradé et le disent.

**Modification des JSON** — avec Python, jamais avec PowerShell.
`Set-Content -Encoding UTF8` ajoute un BOM que Python refuse de lire, et
`ConvertTo-Json` réécrit tout le fichier, ce qui rend les diffs illisibles.

---

## 7. Ce qu'il reste à faire

Par ordre d'utilité.

1. **`donnees/items.json`** — les codes d'items stables. Sans eux, ni comparaison
   entre visites, ni détection de récurrence. C'est le verrou principal, et il
   ne dépend que de Telecon.
2. **`etalons/grenache-2026-09-09/`** — verser le classeur du pilote comme
   étalon, avec `scripts/evaluer_agent.py`. C'est ce qui permettra de mesurer
   chaque nouvelle version de l'invite plutôt que de l'estimer.
3. **Canal des notes vocales** — dix secondes par zone. C'est le seul moyen
   d'atteindre l'exposition, donc les risques les plus graves. Les
   transcriptions nomment des personnes : elles vont dans `prive/`.
4. **`reference_gps` par lieu** — renseigner un point pour la cour et un pour
   l'entrepôt. L'ingestion proposera alors elle-même la répartition des photos
   entre les deux lieux ; le code est déjà écrit.
5. **Responsables des lieux** — `donnees/lieux.json` porte `P45` pour les deux
   lieux ; la correspondance nominative reste à ajouter dans `prive/noms.json`.
6. **Protocole de prise de vue** — une page pour les inspecteurs : photo de
   repère par zone, plan large puis détail, photo de l'endroit où un dispositif
   devrait être, vue au ras du sol, note vocale. C'est le levier le moins cher
   et le plus rentable.

---

## 8. Pièges connus

**Fichiers de plus de 5 Mo** — l'agent ne peut pas les lire. Trois photos sur
100 étaient concernées à Grenache. L'option `--reduire` écrit des copies
allégées hors du dépôt, sans toucher aux originaux.

**Vidéos** — ignorées par l'ingestion. Le dossier Grenache en contient une de
34 Mo, non exploitée. Elle mériterait un visionnement humain : la cour filmée
en mouvement porte ce que les photos ne montrent pas.

**Séquences ≠ zones** — une séquence de prise de vue est une présomption de
zone, pas une zone. Seule une photo de repère ou une note vocale la confirme.

**Une visite = une journée** — une photo prise la veille forme sa propre visite
et ne décale pas la numérotation.

**Renseignements personnels dans les photos** — visages, noms sur des affiches,
numéros de téléphone sur des étiquettes d'inspection. Quatre des 62 photos lues
en portaient. La photo est signalée, elle ne quitte pas les systèmes de Telecon,
et le dépôt n'en garde que l'empreinte. Cadrage Loi 25 à confirmer.

---

## 9. Vérifier que tout fonctionne encore

```powershell
cd C:\Dev\registre-sst-infra-qc
$env:REGISTRE_PRIVE                      # doit afficher C:\Dev\prive
pytest -q                                # 73 tests attendus
python scripts\verifier_confidentialite.py
python scripts\verifier_coherence.py
```

Au 23 septembre 2026 : 73 tests passés, 27 contrôles, 0 écart, 8 écarts connus
documentés dans `A_CORRIGER.md`.

---

## 10. Décisions en attente

- **Visibilité du dépôt.** Il est public. Le code n'y pose pas de difficulté ;
  les constats de terrain, c'est une autre question. À trancher avec le
  directeur SST et les TI.
- **Fréquences d'inspection.** Cour en risque élevé, entrepôt en risque moyen,
  mensuelles, avec une vérification des palettiers plus rapprochée : ce sont des
  propositions, à adopter par le comité SST.
- **Jetons orphelins** — P05, P09, P11, P16, P17, P23 et P26 sont déclarés mais
  cités nulle part, parce que ces personnes figurent en clair dans
  `prive/incidents.json`. Soit retirer ces jetons, soit tokeniser le fichier
  privé.

---

*Document préparatoire. Aucun verdict de conformité. Les références
réglementaires citées dans les constats sont à revérifier avant usage
réglementaire.*
