"""Tests des alertes d'échéances. Lancer : pytest -q"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from alertes import collecter, horizon, lire_date, lire_dossiers, markdown  # noqa: E402

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


DOSSIERS = {"dossiers": [{"numero": "29384431", "mesures": [
    {"numero": 1, "libelle": "Collecte de preuves", "responsable": "⟦P06⟧", "date_visee": "2026-09-15", "etat": "à confirmer"},
    {"numero": 2, "libelle": "Seuil de charge", "responsable": "⟦P18⟧", "date_visee": "2026-09-30", "etat": "en cours"},
    {"numero": 4, "libelle": "Moyen mécanique", "responsable": "à désigner", "responsable_role": "Gestionnaire des équipements",
     "date_visee": "2026-10-20", "etat": "à confirmer"},
    {"numero": 5, "libelle": "Support de changement", "responsable": "à désigner", "date_visee": "2026-12-31", "etat": "à confirmer"},
    {"numero": 8, "libelle": "Classification", "responsable": "⟦P18⟧", "date_visee": "2026-09-15", "etat": "réalisée"},
]}]}


def mesures(jour):
    return {x["quoi"].split(" — ")[0]: x for x in collecter(jour, DATA, {}, [], DOSSIERS) if x["famille"] == "Mesure corrective"}


def test_mesure_passee_non_realisee_est_depassee():
    m = mesures(date(2026, 9, 24))
    assert m["Dossier 29384431 · mesure 1"]["horizon"] == "dépassé"


def test_mesures_futures_suivent_les_horizons():
    m = mesures(date(2026, 9, 24))
    assert m["Dossier 29384431 · mesure 2"]["horizon"] == "7 jours"
    assert m["Dossier 29384431 · mesure 4"]["horizon"] == "30 jours"
    assert "Dossier 29384431 · mesure 5" not in m              # plus tard


def test_mesure_realisee_n_apparait_pas_meme_date_passee():
    assert "Dossier 29384431 · mesure 8" not in mesures(date(2026, 9, 24))


def test_le_retard_ne_modifie_pas_l_etat():
    etats = [m["etat"] for m in DOSSIERS["dossiers"][0]["mesures"]]
    mesures(date(2027, 1, 1))
    assert [m["etat"] for m in DOSSIERS["dossiers"][0]["mesures"]] == etats
    assert "état inscrit : à confirmer" in mesures(date(2027, 1, 1))["Dossier 29384431 · mesure 1"]["detail"]


def test_dossier_et_responsable_par_jeton():
    m = mesures(date(2026, 9, 24))
    assert m["Dossier 29384431 · mesure 1"]["detail"].startswith("Responsable : ⟦P06⟧")
    assert "à désigner (Gestionnaire des équipements)" in m["Dossier 29384431 · mesure 4"]["detail"]
    t = markdown(date(2026, 9, 24), collecter(date(2026, 9, 24), DATA, {}, [], DOSSIERS), DATA, {}, False)
    assert "Dossier 29384431 · mesure 1" in t and "⟦P06⟧" in t


def test_donnees_reelles_au_24_septembre():
    m = {x["quoi"].split(" — ")[0]: x["horizon"]
         for x in collecter(date(2026, 9, 24), DATA, {}, [], lire_dossiers()) if x["famille"] == "Mesure corrective"}
    assert sorted(k for k, h in m.items() if h == "dépassé") == [
        f"Dossier 29384431 · mesure {n}" for n in (1, 6, 7, 8)]
    assert sorted(k for k, h in m.items() if h == "7 jours") == [
        f"Dossier 29384431 · mesure {n}" for n in (2, 3, 4)]
