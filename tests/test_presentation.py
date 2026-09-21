"""Tests de la présentation par acteur. Lancer : pytest -q"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import generer_presentation as gp  # noqa: E402
from commun import DONNEES, PRIVE  # noqa: E402

DATA = json.loads((DONNEES / "registre_html.json").read_text(encoding="utf-8"))


def test_chiffres_lus_dans_les_donnees():
    f = gp.faits()
    assert f["n"] == len(DATA["risques"])
    assert f["p1"] == sum(1 for r in DATA["risques"] if r["prio"] == 1)
    assert len(f["immediats"]) == sum(1 for r in DATA["risques"] if r["bucket"] == "immediat")
    assert f["tests"] > 0


def test_une_section_par_acteur():
    _, page = gp.construire()
    for a in ("commun", "directeur", "comite", "operations", "ti", "terrain"):
        assert f'data-acteur="{a}"' in page


def test_aucun_nom_ni_jeton():
    _, page = gp.construire()
    assert "⟦" not in page
    f = PRIVE / "noms.json"
    if f.exists():
        noms = [g for gs in json.loads(f.read_text(encoding="utf-8"))["variantes"].values() for g in gs]
        assert not [n for n in noms if n in page]


def test_delai_de_reponse_non_invente():
    _, page = gp.construire()
    assert "R-29 propose 21 jours, proposition non adoptée" in page


def test_doctrine_rappelee():
    _, page = gp.construire()
    assert "Aucun verdict de conformité" in page and "Validation humaine requise" in page
