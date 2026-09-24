"""Tests du projet d'ordre du jour. Lancer : pytest -q"""
import datetime as dt
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


JOUR = dt.date(2026, 9, 24)


def points_du_dossier():
    return [p for p in odj.construire_points(VIDE, JOUR) if p["dossier"] == "29384431"]


def test_cinq_points_a_trancher_pour_29384431():
    pts = points_du_dossier()
    assert len(pts) == 5 and all(p["type"] == "decision" and p["section"] == odj.SECTION_DOSSIERS for p in pts)
    titres = " ".join(p["titre"] for p in pts)
    for mot in ("SSE-900", "HSP-SS-001", "godets", "douleurs", "24 mois", "traduction"):
        assert mot in titres
    assert "6 jours" in pts[0]["decision"] and "15 jours ouvrables" in pts[0]["decision"]


def test_tableau_du_dossier():
    points = odj.construire_points(VIDE, JOUR)
    j, lignes = odj.tableau_dossiers(points, VIDE, JOUR)
    l = lignes[0]
    nums = [p["num"] for p in points if p["dossier"] == "29384431"]
    assert (l["dossier"], l["mesures"], l["en_retard"]) == ("29384431", 8, "4 (mesures 1, 6, 7, 8)")
    assert l["etat"].startswith("ouvert")
    assert "accuser réception" in l["a_decider"] and f"points {nums[0]} à {nums[-1]}" in l["a_decider"]


def test_retard_compte_a_la_date_de_seance_si_fixee():
    cfg = dict(VIDE, date_seance="2026-09-16")
    j, lignes = odj.tableau_dossiers(odj.construire_points(cfg), cfg)
    assert j == dt.date(2026, 9, 16) and lignes[0]["en_retard"] == "2 (mesures 1, 8)"


def test_section_dans_les_deux_formats_sans_modifier_l_etat():
    avant = (DONNEES / "dossiers_comite.json").read_text(encoding="utf-8")
    points = odj.construire_points(VIDE, JOUR)
    for t in (odj.markdown(points, VIDE), odj.page_html(points, VIDE)):
        assert "Dossiers transférés au comité" in t and "Ce que le comité doit décider" in t
        assert "l’état inscrit des mesures n’est pas modifié" in t.replace("'", "’")
    assert (DONNEES / "dossiers_comite.json").read_text(encoding="utf-8") == avant
