# -*- coding: utf-8 -*-
"""Tests du contrôle des constats.

Chaque test correspond à une erreur réellement mesurée, ou à une règle de la
doctrine. Le cas témoin est la cage à bidons du dépôt Grenache, 9 septembre
2026 : l'agent avait conclu à l'absence de cadenas sur une seule photo, alors
que la cage était verrouillée.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from verifier_constats import verifier, BLOQUANT, AVERTISSEMENT  # noqa: E402


def photo(pid, **kw):
    base = {
        "id": pid,
        "empreinte": "0" * 64,
        "pris_le": "2026-09-09T09:30:13-04:00",
        "lieu": "INF-QC-ANJOU-COUR",
        "sequence": "S01",
        "visibilite_zone_critique": None,
        "renseignement_personnel": False,
        "sol_examine": True,
        "passage_examine": True,
    }
    base.update(kw)
    return base


def constat(**kw):
    base = {
        "id": "C-2026-09-09-04",
        "lieu": "INF-QC-ANJOU-COUR",
        "code_item": "LIQ-INFLAM",
        "enonce": "Cage à bidons non cadenassée, aucune rétention visible.",
        "statut": "non_conforme",
        "affirme_absence": True,
        "dispositif_absent": "cadenas",
        "photos": ["20260909_093013.jpg"],
        "source": ["photo"],
        "criticite_proposee": "critique",
    }
    base.update(kw)
    return base


def motifs(manquements, gravite=None):
    return [m for m in manquements if gravite is None or m["gravite"] == gravite]


# --- R1 : absence sans preuve ---------------------------------------------

def test_absence_sans_photo_de_la_zone_critique_est_retrogradee():
    """Le cas de la cage à bidons : c'est exactement ce qui doit être bloqué."""
    c = constat()
    p = [photo("20260909_093013.jpg", visibilite_zone_critique=None)]
    manquements = verifier([c], p)
    assert c["statut"] == "a_verifier"
    assert motifs(manquements, BLOQUANT)


def test_absence_avec_photo_de_la_zone_critique_est_acceptee():
    c = constat(photos=["a.jpg", "b.jpg"])
    p = [photo("a.jpg", visibilite_zone_critique=True), photo("b.jpg")]
    verifier([c], p)
    assert c["statut"] == "non_conforme"


def test_absence_detectee_dans_l_enonce_meme_sans_le_champ():
    """Filet : l'énoncé affirme une absence, le champ n'est pas posé."""
    c = constat(affirme_absence=False, dispositif_absent=None,
                enonce="Bouteilles debout, aucune sangle ni chaîne ne les retient.")
    verifier([c], [photo("20260909_093013.jpg")])
    assert c["affirme_absence"] is True
    assert c["statut"] == "a_verifier"


# --- R3 : mesure lue sur une photo ----------------------------------------

def test_mesure_tiree_d_une_photo_seule_est_retrogradee():
    c = constat(affirme_absence=False, dispositif_absent=None,
                enonce="Équipement entreposé sur un toit de conteneur à 2,6 m de haut.")
    manquements = verifier([c], [photo("20260909_093022.jpg")])
    assert c["statut"] == "a_verifier"
    assert any("2,6 m" in m["message"] for m in motifs(manquements, BLOQUANT))


def test_mesure_confirmee_par_entrevue_est_acceptee():
    c = constat(affirme_absence=False, dispositif_absent=None,
                source=["photo", "entrevue"],
                enonce="Équipement entreposé sur un toit de conteneur à 2,6 m de haut.")
    verifier([c], [photo("20260909_093022.jpg")])
    assert c["statut"] == "non_conforme"


# --- R4 : exposition -------------------------------------------------------

def test_frequence_affirmee_sur_photo_seule_est_retrogradee():
    c = constat(affirme_absence=False, dispositif_absent=None,
                enonce="Des travailleurs traversent la cour à pied chaque matin avant le jour.")
    verifier([c], [photo("20260909_093230.jpg")])
    assert c["statut"] == "a_verifier"


def test_frequence_appuyee_sur_note_vocale_est_acceptee():
    c = constat(affirme_absence=False, dispositif_absent=None,
                source=["photo", "note_vocale"],
                enonce="Des travailleurs traversent la cour à pied chaque matin avant le jour.")
    verifier([c], [photo("20260909_093230.jpg")])
    assert c["statut"] == "non_conforme"


# --- R5 : la machine ne déclare pas la conformité -------------------------

def test_conforme_sans_validation_humaine_est_retrograde():
    c = constat(statut="conforme", affirme_absence=False, dispositif_absent=None,
                enonce="Échelles rangées à la verticale contre le mur.")
    verifier([c], [photo("20260909_095156.jpg")])
    assert c["statut"] == "a_verifier"


def test_conforme_valide_par_un_humain_est_conserve():
    c = constat(statut="conforme", validation_humaine=True, valide_par="PASST",
                affirme_absence=False, dispositif_absent=None,
                enonce="Échelles rangées à la verticale contre le mur.")
    verifier([c], [photo("20260909_095156.jpg")])
    assert c["statut"] == "conforme"


# --- R2, R6, R7, R8 --------------------------------------------------------

def test_constat_sur_une_seule_photo_est_marque_fragile():
    c = constat(affirme_absence=False, dispositif_absent=None,
                enonce="Boyaux traversant la voie de circulation.")
    verifier([c], [photo("20260909_102013.jpg")])
    assert c["fragile"] is True


def test_constat_non_conforme_sans_aucune_source_est_bloquant():
    c = constat(affirme_absence=False, dispositif_absent=None, photos=[],
                enonce="Allées encombrées de boîtes.")
    manquements = verifier([c], [])
    assert motifs(manquements, BLOQUANT)


def test_photo_avec_renseignement_personnel_est_signalee():
    c = constat(affirme_absence=False, dispositif_absent=None, photos=["x.jpg", "y.jpg"],
                enonce="Affiche d'accès décolorée au portail.")
    p = [photo("x.jpg", renseignement_personnel=True), photo("y.jpg")]
    manquements = verifier([c], p)
    assert any("renseignement personnel" in m["message"].lower()
               for m in motifs(manquements, AVERTISSEMENT))


def test_angles_morts_non_examines_sont_signales():
    c = constat(affirme_absence=False, dispositif_absent=None, photos=["z.jpg", "w.jpg"],
                enonce="Palettier d'aplomb, charges retenues.")
    p = [photo("z.jpg", sol_examine=False, passage_examine=False),
         photo("w.jpg", sol_examine=False, passage_examine=False)]
    manquements = verifier([c], p)
    assert any("sol" in m["message"] for m in motifs(manquements, AVERTISSEMENT))


# --- journal ---------------------------------------------------------------

def test_chaque_retrogradation_est_inscrite_au_journal():
    """On inscrit et on date, on n'efface pas."""
    c = constat()
    verifier([c], [photo("20260909_093013.jpg")])
    assert c["journal"]
    assert any("2026" in ligne or "202" in ligne for ligne in c["journal"])
