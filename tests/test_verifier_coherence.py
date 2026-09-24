"""Tests du contrôle de cohérence. Lancer : pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import verifier_coherence as vc  # noqa: E402


def test_les_donnees_actuelles_ne_laissent_aucun_ecart_non_connu():
    res = vc.appliquer_connus(vc.verifier())
    assert [d for _, s, d in res if s == "ecart"] == []


def test_ecart_connu_reste_visible():
    res = vc.appliquer_connus(vc.verifier())
    connus = [d for _, s, d in res if s == "connu"]
    assert all("A_CORRIGER" in d for d in connus)


def test_un_ecart_non_inscrit_fait_echouer(monkeypatch):
    monkeypatch.setattr(vc, "verifier", lambda: [("pdf_p1", "ecart", "PDF : 11 affiché, 12 au registre")])
    res = vc.appliquer_connus(vc.verifier())
    assert res[0][1] == "ecart"


def test_references_inexistantes_detectees(monkeypatch):
    donnees = {"risques": [{"ref": "R-01"}]}
    trouvees = {f"R-{n}" for t in vc.textes({"a": "voir R-01 et R-99", "b": ["R-45"]}) for n in vc.REF.findall(t)}
    assert trouvees - {r["ref"] for r in donnees["risques"]} == {"R-99", "R-45"}


def test_nombres_en_lettres():
    assert vc.NOMBRES["trente-huit"] == 38 and vc.NOMBRES["trente-neuf"] == 39


def test_jetons_cites_sous_les_deux_formes():
    obj = {"a": "par ⟦P06⟧ et ⟦P13~1⟧", "lieux": [{"responsable": "P45"}], "b": ["voir P99 plus haut"],
           "cellules": [["P10", "texte", 3]]}              # coordonnée de cellule, pas une personne
    assert vc.jetons_cites(obj) == {"P06", "P13", "P45"}


def test_jeton_cite_mais_non_declare():
    res = dict((c, s) for c, s, _ in vc.controle_jetons({"P01"}, {"P01": "a.json", "P46": "b.json"}))
    assert res == {"jetons_inconnus": "ecart", "jetons_orphelins": "ok"}


def test_jeton_declare_mais_jamais_cite():
    res = dict((c, s) for c, s, _ in vc.controle_jetons({"P01", "P46"}, {"P01": "a.json"}, {}))
    assert res == {"jetons_inconnus": "ok", "jeton_orphelin_P46": "ecart"}


def test_un_jeton_utilise_seulement_dans_prive_n_est_pas_orphelin():
    res = {c: s for c, s, _ in vc.controle_jetons({"P01", "P05"}, {"P01": "a.json"}, {"P05": "prive/incidents.json"})}
    assert "jeton_orphelin_P05" not in res and res["jetons_orphelins"] == "ok"


def test_orphelin_partout_echoue_avec_le_dossier_prive():
    res = {c: s for c, s, _ in vc.controle_jetons({"P01", "P99"}, {"P01": "a.json"}, {})}
    assert res["jeton_orphelin_P99"] == "ecart"


def test_sans_dossier_prive_l_orphelin_est_a_verifier_sans_echec():
    res = vc.appliquer_connus(vc.controle_jetons({"P01", "P05"}, {"P01": "a.json"}, None))
    assert {c: s for c, s, _ in res}["jeton_orphelin_P05"] == "a_verifier"
    assert not [r for r in res if r[1] == "ecart"]


def test_jetons_prives_lit_prive_sauf_noms(tmp_path, monkeypatch):
    (tmp_path / "noms.json").write_text('{"variantes": {"P77": ["X"]}}', encoding="utf-8")
    (tmp_path / "incidents.json").write_text('{"1": {"personnes": "⟦P05⟧"}}', encoding="utf-8")
    monkeypatch.setattr(vc, "PRIVE", tmp_path)
    monkeypatch.setattr(vc, "prive_disponible", lambda: True)
    assert vc.jetons_prives() == {"P05": "prive/incidents.json"}
    monkeypatch.setattr(vc, "prive_disponible", lambda: False)
    assert vc.jetons_prives() is None
