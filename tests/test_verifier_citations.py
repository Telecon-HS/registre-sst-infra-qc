"""Tests du contrôle des citations. Lancer : pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from verifier_citations import citations, index_procedures, verifier  # noqa: E402

INDEX_FACTICE = """numero,titre,section,statut,page_manuel,niveau_confiance
SSE-1302,"Échelles et escabeaux",1300,actif,42,confirme
SSE-2000,"Sécurité routière",2000,actif,88,partiel
"""


def ecrire_index(tmp_path):
    f = tmp_path / "index.csv"
    f.write_text(INDEX_FACTICE, encoding="utf-8")
    return index_procedures(f)


def test_prefixes_sse_et_hse_equivalents():
    assert citations("HSE-1302 §6.7") == ["1302"]
    assert citations("SSE-1302 §6.7") == ["1302"]
    assert citations("SSE.TEL-PRG-600 §6.3") == ["600"]


def test_pas_de_doublon_dans_une_meme_citation():
    assert citations("SSE-1302 §6.4 et §6.6 · HSE-1302 §6.3") == ["1302"]


def test_niveau_de_confiance_remonte(tmp_path):
    index = ecrire_index(tmp_path)
    lignes = verifier(index, [{"ref": "R-01", "norme": "HSE-1302 §6.7"},
                              {"ref": "R-07", "norme": "SSE-2000 §6.8.1.2"}])
    assert [l[2] for l in lignes] == ["confirme", "partiel"]


def test_procedure_absente_signalee(tmp_path):
    index = ecrire_index(tmp_path)
    lignes = verifier(index, [{"ref": "R-04", "norme": "HSE.TEL-PRO-403 §9.1"}])
    assert lignes[0][2] == "ABSENTE DE L'INDEX"


def test_reference_externe_non_comptee_comme_procedure(tmp_path):
    index = ecrire_index(tmp_path)
    lignes = verifier(index, [{"ref": "R-39", "norme": "CSTC art. 2.9.5.2, décret 63-2025"}])
    assert lignes[0][2] == "hors index"
