"""Tests du contrôle des citations. Lancer : pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from verifier_citations import citations, index_procedures, verifier  # noqa: E402

INDEX_FACTICE = """numero,titre,section,statut,page_manuel,niveau_confiance
SSE-1302,"Échelles et escabeaux",1300,actif,42,confirme
SSE-2000,"Sécurité routière",2000,actif,88,partiel
SSE-1303,"Poteaux et torons (en-têtes: HSE.TEL-PRO-403)",1300,actif,263,confirme
SSE-601-NOR,"Liste des EPI approuvés",600,absent_du_corpus,,a_valider
SSE-501.1,"À valider",à valider,absent_du_corpus,,a_valider
"""
ALIAS = {"403": "1303", "601": "601-NOR", "1309.1": "501.1"}


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
                              {"ref": "R-07", "norme": "SSE-2000 §6.8.1.2"}], {})
    assert [l[2] for l in lignes] == ["confirme", "partiel"]


def test_procedure_absente_signalee(tmp_path):
    index = ecrire_index(tmp_path)
    lignes = verifier(index, [{"ref": "R-04", "norme": "HSE.TEL-PRO-403 §9.1"}], {})
    assert lignes[0][2] == "ABSENTE DE L'INDEX"          # sans table de correspondances


def test_sous_numero_et_suffixe_conserves():
    assert citations("SSE-501.1 · HSE-1309.2") == ["501.1", "1309.2"]
    assert citations("SSE.TEL-NOR-601") == ["601-NOR"]
    assert citations("SSE-2001-F02 · SSE.TEL-FOR-1700-F01") == ["2001", "1700"]


def test_correspondances_entre_numeros(tmp_path):
    index = ecrire_index(tmp_path)
    lignes = verifier(index, [{"ref": "R-04", "norme": "HSE.TEL-PRO-403 §9.1"},
                              {"ref": "R-05", "norme": "HSE-601"},
                              {"ref": "R-06", "norme": "HSE-1309.1"}], ALIAS)
    assert [l[2] for l in lignes] == ["confirme", "a_valider", "a_valider"]
    assert lignes[0][1] == "SSE-1303 (cité 403)"


def test_reference_externe_non_comptee_comme_procedure(tmp_path):
    index = ecrire_index(tmp_path)
    lignes = verifier(index, [{"ref": "R-39", "norme": "CSTC art. 2.9.5.2, décret 63-2025"}], {})
    assert lignes[0][2] == "hors index"


def test_meme_document_sous_deux_numeros_compte_une_fois(tmp_path):
    index = ecrire_index(tmp_path)
    lignes = verifier(index, [{"ref": "R-06", "norme": "SSE-501.1 · HSE-1309.1"}], ALIAS)
    assert len(lignes) == 1
