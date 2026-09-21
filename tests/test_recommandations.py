"""Tests de l'onglet « Recommandations au comité ». Lancer : pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import generer_classeur as gc  # noqa: E402

SANS_DELAI = {"delai_reponse": {"jours": None, "jours_arret_de_travail": None}}


def test_registre_vide_au_depart():
    assert gc.lignes_recommandations({**SANS_DELAI, "recommandations": []}) == []


def test_sans_delai_adopte_aucune_echeance_calculee():
    rec = [{"date": "2026-10-06", "objet": "Adopter le délai de réponse", "risque": "R-29"}]
    l = gc.lignes_recommandations({**SANS_DELAI, "recommandations": rec})[0]
    assert l["echeance"] == "à confirmer"
    assert l["statut"] == "En attente de réponse"
    assert l["no"] == "REC-01"


def test_delai_adopte_applique_et_jours_ecoules_calcules():
    R = {"delai_reponse": {"jours": 21, "jours_arret_de_travail": 7},
         "recommandations": [
             {"date": "2026-10-06", "objet": "A", "risque": "R-06", "date_reponse": "2026-10-20", "reponse": "Accepté"},
             {"date": "2026-10-06", "objet": "B", "risque": "R-07", "arret_de_travail": True}]}
    a, b = gc.lignes_recommandations(R)
    assert a["echeance"] == "2026-10-27" and a["ecoule"] == 14 and a["statut"] == "Réponse écrite reçue"
    assert b["echeance"] == "2026-10-13" and b["ecoule"] == "—"


def test_date_illisible_marquee_a_confirmer():
    l = gc.lignes_recommandations({**SANS_DELAI, "recommandations": [{"date": "octobre", "objet": "C"}]})[0]
    assert l["date"] == "à confirmer" and l["echeance"] == "à confirmer"


def test_statut_ne_juge_pas_le_respect_du_delai():
    R = {"delai_reponse": {"jours": 21},
         "recommandations": [{"date": "2026-10-01", "objet": "D", "date_reponse": "2026-12-31", "reponse": "Refusé"}]}
    l = gc.lignes_recommandations(R)[0]
    assert l["statut"] == "Réponse écrite reçue"          # ni « en retard » ni « non conforme »
