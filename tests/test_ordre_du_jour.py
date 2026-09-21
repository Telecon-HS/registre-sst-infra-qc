"""Tests du projet d'ordre du jour. Lancer : pytest -q"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import ordre_du_jour as odj  # noqa: E402
from commun import DONNEES, PRIVE  # noqa: E402

DATA = json.loads((DONNEES / "registre_html.json").read_text(encoding="utf-8"))
VIDE = {"date_seance": None, "lieu": None, "durees": {"ouverture": None, "decision": None, "information": None}}


def test_tous_les_risques_de_seance_sont_a_l_ordre_du_jour():
    titres = " ".join(p["titre"] for p in odj.construire_points(VIDE))
    for r in DATA["risques"]:
        if r["bucket"] == "seance":
            assert r["ref"] in titres


def test_aucune_duree_inventee():
    points = odj.construire_points(VIDE)
    assert all(p["duree"] is None for p in points)
    assert odj.total(points) is None
    t = odj.markdown(points, VIDE)
    assert "**Durée totale** : à confirmer" in t and "**Date** : à confirmer" in t


def test_durees_appliquees_quand_fixees():
    cfg = {"durees": {"ouverture": 5, "decision": 10, "information": 3}}
    points = odj.construire_points(cfg)
    attendu = sum({"ouverture": 5, "decision": 10, "information": 3}[p["type"]] for p in points)
    assert odj.total(points) == attendu


def test_seuls_les_dossiers_dont_le_jalon_tombe_a_la_seance():
    titres = [p["titre"] for p in odj.construire_points(VIDE) if p["section"] == "Dossiers en cours"]
    assert any(t.startswith("I-01") for t in titres)
    assert not any(t.startswith("I-05") for t in titres)      # jalon au 1er décembre


def test_aucun_nom_ni_jeton_et_validation_humaine():
    points = odj.construire_points(VIDE)
    t = odj.markdown(points, VIDE) + odj.page_html(points, VIDE)
    assert "⟦" not in t and "[nom retiré]" not in t
    noms = PRIVE / "noms.json"
    if noms.exists():
        for gs in json.loads(noms.read_text(encoding="utf-8"))["variantes"].values():
            assert not [g for g in gs if g in t]
    assert "Validation humaine requise" in t
    assert "Aucun verdict de conformité" in t
