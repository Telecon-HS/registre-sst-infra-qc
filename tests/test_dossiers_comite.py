"""Tests de l'onglet « Dossiers transférés au comité ». Lancer : pytest -q"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import generer_classeur as gc  # noqa: E402
from commun import DONNEES, PRIVE  # noqa: E402

D = json.loads((DONNEES / "dossiers_comite.json").read_text(encoding="utf-8"))


def test_le_dossier_verse_est_decrit():
    d = next(x for x in D["dossiers"] if x["numero"] == "29384431")
    assert d["date_evenement"] == "2026-08-19"
    assert d["etat"] in D["etats"]
    assert d["etat"].startswith("ouvert")          # l'enquête n'est pas terminée


def test_compte_des_pieces():
    l = gc.lignes_dossiers(D)[0]
    assert l["pieces"] == "3 sur 7" and l["a_obtenir"] == 4


def test_valeurs_inconnues_marquees_a_confirmer():
    l = gc.lignes_dossiers(D)[0]
    assert l["accuse"] == "à confirmer" and l["date_accuse"] == "à confirmer"
    assert l["risque"] == "à confirmer"


def test_aucun_nom_ni_donnee_medicale():
    texte = json.dumps(D, ensure_ascii=False)
    f = PRIVE / "noms.json"
    if f.exists():
        noms = [g for gs in json.loads(f.read_text(encoding="utf-8"))["variantes"].values() for g in gs]
        assert not [n for n in noms if n in texte]
    for mot in ("diagnostic médical", "physiothérapie", "chiropraxie", "médecin traitant"):
        assert mot not in texte
    assert "⟦P01⟧" in texte                         # les personnes passent par des jetons


def test_ce_qui_ne_se_transfere_pas_est_liste_sans_son_contenu():
    d = D["dossiers"][0]
    elements = [x["element"] for x in d["ne_se_transfere_pas"]]
    assert "Pièces médicales, diagnostic, suivi thérapeutique" in elements
    assert all("motif" in x and "responsable" in x for x in d["ne_se_transfere_pas"])
