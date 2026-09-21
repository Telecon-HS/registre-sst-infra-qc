"""Tests du tableau de bord de direction. Lancer : pytest -q"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import generer_tableau_bord as tb  # noqa: E402
from commun import DONNEES, PRIVE  # noqa: E402

DATA = json.loads((DONNEES / "registre_html.json").read_text(encoding="utf-8"))


def test_chiffres_calcules_et_non_saisis():
    x = tb.calculer(avec_prive=False)
    assert len(x["R"]) == len(DATA["risques"])
    assert x["prio"][1] == sum(1 for r in DATA["risques"] if r["prio"] == 1)
    assert x["elements"] == sum(len(r["sources"]) for r in DATA["risques"])
    assert len(x["visites"]) == 10            # fiches d'inspection citées comme sources


def test_sans_dossier_prive_les_categories_restent_a_confirmer():
    x = tb.calculer(avec_prive=False)
    assert {i["stky"] for i in x["incidents"]} == {"À confirmer"}


def test_normalisation_stky_bilingue():
    assert tb.normaliser("Road Safety—Driving for Work", tb.STKY) == "Conduite au travail"
    assert tb.normaliser("Sécurité routière – Conduire pour le travail", tb.STKY) == "Conduite au travail"
    assert tb.normaliser("Not Applicable", tb.STKY) == "Sans objet"
    assert tb.normaliser("", tb.STKY) == "Non renseignée"


def test_aucun_nom_dans_le_tableau_de_bord():
    _, page = tb.construire(avec_prive=True)
    noms_fichier = PRIVE / "noms.json"
    if noms_fichier.exists():
        noms = [g for gs in json.loads(noms_fichier.read_text(encoding="utf-8"))["variantes"].values() for g in gs]
        assert not [n for n in noms if n in page]
    assert "⟦" not in page
    assert "aucun verdict de conformité" in page


def test_tables_powerbi_sans_nom(tmp_path):
    x = tb.calculer(avec_prive=False)
    fichiers = tb.tables_powerbi(x, tmp_path)
    assert "risques.csv" in fichiers and "incidents.csv" in fichiers
    texte = "".join((tmp_path / f).read_text(encoding="utf-8-sig") for f in fichiers)
    assert "⟦" not in texte
