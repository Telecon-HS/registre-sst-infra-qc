"""Tests du rapport hebdomadaire. Lancer : pytest -q"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rapport_hebdo import comparer, concordance, etat_actuel, markdown  # noqa: E402

LIGNES = [
    {"id": "1", "titre": "Mensuelle", "statut": "Locked", "date": "2026-05-02", "signature": "X"},
    {"id": "2", "titre": "Mensuelle", "statut": "Submitted", "date": "2026-06-02", "signature": None},
]
RESUME = {"dépassé": 0, "7 jours": 1, "30 jours": 2, "sans_point_de_depart": True}


def test_premier_passage_ne_presente_rien_comme_nouveau():
    actuel = etat_actuel(LIGNES)
    assert comparer(None, actuel) is None
    t = markdown(date(2026, 9, 20), actuel, None, [], {}, RESUME, [])
    assert "aucun état précédent" in t
    assert "Photo de départ" in t


def test_fiche_fermee_depuis_la_semaine_precedente():
    precedent = {"total": 2, "par_type": {"Mensuelle": 2}, "non_fermees": {"Mensuelle": ["1", "3"]},
                 "identifiants": ["1", "2", "3"]}
    m0 = comparer(precedent, etat_actuel(LIGNES))
    assert m0["fermees_depuis"] == ["1"]        # « 1 » est présent et maintenant verrouillé
    precedent = {"total": 2, "par_type": {"Mensuelle": 2}, "non_fermees": {"Mensuelle": ["2", "3"]}}
    precedent["identifiants"] = ["1", "2", "3"]
    m = comparer(precedent, etat_actuel(LIGNES))
    assert m["fermees_depuis"] == []
    assert m["absentes_de_l_export"] == ["3"]
    assert m["nouvelles_non_fermees"] == []
    assert m["total"] == 0


def test_fiche_absente_de_l_export_n_est_pas_fermee():
    precedent = {"total": 3, "par_type": {"Mensuelle": 3}, "non_fermees": {"Mensuelle": ["2", "9"]},
                 "identifiants": ["1", "2", "9"]}
    m = comparer(precedent, etat_actuel(LIGNES))
    assert m["fermees_depuis"] == []            # « 9 » n'est pas dans l'export : statut inconnu
    assert m["absentes_de_l_export"] == ["9"]


def test_rapprochement_par_motif_explicite():
    volumes = {"comparaison": [{"type": "Inspection mensuelle du véhicule", "motif": "mensuelle",
                                "registre": 3, "export": 9, "tableau": 58}]}
    ecarts, _ = concordance(etat_actuel(LIGNES), volumes, [])
    assert ecarts[0]["ingestion"] == 2


def test_plusieurs_formulaires_pour_un_meme_type_sont_additionnes():
    lignes = LIGNES + [{"id": "3", "titre": "Rapport de visite de chantier", "statut": "Locked",
                        "date": "2026-06-10", "signature": "X"},
                       {"id": "4", "titre": "Rapport de visite de sites de travail", "statut": "Locked",
                        "date": "2026-06-11", "signature": "X"}]
    volumes = {"comparaison": [{"type": "Visite ou inspection SST de site", "motif": "visite de",
                                "registre": 6, "export": 14, "tableau": 418}]}
    ecarts, _ = concordance(etat_actuel(lignes), volumes, [])
    assert ecarts[0]["ingestion"] == 2


def test_nouvelle_fiche_non_fermee_signalee():
    precedent = {"total": 1, "par_type": {"Mensuelle": 1}, "non_fermees": {}}
    m = comparer(precedent, etat_actuel(LIGNES))
    assert m["nouvelles_non_fermees"] == ["2"]
    assert m["par_type"]["Mensuelle"] == 1


def test_ecarts_presentes_sans_seuil_ni_verdict():
    volumes = {"comparaison": [{"type": "Inspection mensuelle du véhicule", "court": "Mensuelle",
                                "registre": 3, "export": 9, "tableau": 58}]}
    ecarts, _ = concordance(etat_actuel(LIGNES), volumes, [])
    t = markdown(date(2026, 9, 20), etat_actuel(LIGNES), None, ecarts, {}, RESUME, [])
    assert "Aucun seuil n'est appliqué" in t
    assert "58" in t and "conformité" in t


def test_index_absent_marque_a_confirmer():
    t = markdown(date(2026, 9, 20), etat_actuel(LIGNES), None, [], {}, RESUME, [])
    assert "À confirmer" in t and "ANCRAGE" in t


def test_point_de_depart_absent_rappele_et_validation_humaine():
    t = markdown(date(2026, 9, 20), etat_actuel(LIGNES), None, [], {"confirme": 3}, RESUME, [])
    assert "décision du comité" in t
    assert "Validation humaine requise" in t
