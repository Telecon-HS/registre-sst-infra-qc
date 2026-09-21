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
