"""Tests des alertes d'échéances. Lancer : pytest -q"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from alertes import collecter, horizon, lire_date, markdown  # noqa: E402

DATA = {
    "comite": {"echeances": [{"date": "1er octobre 2026", "quoi": "Programmes de prévention", "portee": "5 sites"}]},
    "initiatives": [{"ref": "I-05", "titre": "Cale de roue", "jalon": "Remplacement avant le 1er décembre 2026"}],
    "risques": [{"ref": "R-01", "titre": "Porte-échelles", "bucket": "immediat", "echeance": "Immédiat"},
                {"ref": "R-15", "titre": "Inspection mensuelle", "bucket": "j60", "echeance": "60 jours"}],
    "documents": [{"doc": "Rapport annuel d’activités", "etat": "Non produit", "exigence": "À confirmer"},
                  {"doc": "Tableau de suivi", "etat": "Tenu par le présent classeur", "exigence": "Gabarit CNESST"}],
}


def test_lecture_des_dates_francaises():
    assert lire_date("1er octobre 2026") == date(2026, 10, 1)
    assert lire_date("2026-12-01") == date(2026, 12, 1)
    assert lire_date("prochaine séance") is None


def test_trois_horizons():
    j = date(2026, 9, 20)
    assert horizon(date(2026, 9, 18), j)[0] == "dépassé"
    assert horizon(date(2026, 9, 25), j)[0] == "7 jours"
    assert horizon(date(2026, 10, 15), j)[0] == "30 jours"
    assert horizon(date(2027, 1, 1), j)[0] == "plus tard"


def test_jalon_date_seulement_si_presente_comme_echeance():
    data = dict(DATA, initiatives=[
        {"ref": "I-05", "titre": "Cale de roue", "jalon": "Remplacement avant le 1er décembre 2026"},
        {"ref": "I-01", "titre": "Travail isolé", "jalon": "Triage des tâches",
         "etat": "Trousse version 1.0 du 15 septembre 2026"}])
    a = collecter(date(2026, 11, 20), data, {}, [])
    refs = [x["quoi"] for x in a if x["famille"] == "Dossier en cours"]
    assert refs == ["I-05 — Cale de roue"]          # la date de version n'est pas un jalon


def test_echeance_reglementaire_reperee():
    a = collecter(date(2026, 9, 20), DATA, {}, [])
    assert any(x["famille"] == "Réglementaire" and x["horizon"] == "30 jours" for x in a)


def test_sans_date_de_decision_aucune_date_inventee():
    t = markdown(date(2026, 9, 20), collecter(date(2026, 9, 20), DATA, {}, []), DATA, {}, False)
    assert "le point de départ est absent" in t
    assert "R-15 — Inspection mensuelle" not in t          # aucune date calculée pour les risques


def test_avec_date_de_decision_les_risques_apparaissent():
    config = {"date_decision_comite": "2026-09-22"}
    t = markdown(date(2026, 10, 20), collecter(date(2026, 10, 20), DATA, config, []), DATA, config, False)
    assert "R-01" in t and "2026-09-22" in t


def test_epi_absent_marque_a_confirmer():
    t = markdown(date(2026, 9, 20), [], DATA, {}, False)
    assert "À confirmer" in t and "HSE-601" in t
    assert "Validation humaine requise" in t
