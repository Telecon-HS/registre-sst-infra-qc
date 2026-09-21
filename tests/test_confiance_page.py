"""Tests du niveau de confiance affiché dans la fiche de chaque risque. Lancer : pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from commun import GABARITS  # noqa: E402
from generer_page import confiance_des_risques  # noqa: E402

INDEX = """numero,titre,section,statut,page_manuel,niveau_confiance
SSE-1303,"Poteaux et torons (en-têtes: HSE.TEL-PRO-403)",1300,actif,263,confirme
SSE-2000,"Sécurité routière",2000,actif,88,partiel
SSE-601-NOR,"Liste des EPI approuvés",600,absent_du_corpus,,a_valider
"""
RISQUES = [
    {"ref": "R-04", "norme": "HSE.TEL-PRO-403 §9.1 · SSE-1303 §8"},
    {"ref": "R-07", "norme": "SSE-2000 §6.8 · SSE-9999"},
    {"ref": "R-39", "norme": "CSTC art. 2.9.5.2, décret 63-2025"},
    {"ref": "R-10", "norme": "HSE-601"},
]


def index(tmp_path):
    f = tmp_path / "index.csv"
    f.write_text(INDEX, encoding="utf-8")
    return f


def test_index_inaccessible_donne_a_confirmer(tmp_path):
    c = confiance_des_risques(RISQUES, tmp_path / "absent.csv")
    assert all(v == {"disponible": False} for v in c.values())


def test_correspondance_et_meme_document_compte_une_fois(tmp_path):
    c = confiance_des_risques(RISQUES, index(tmp_path))
    assert [(p["numero"], p["niveau"]) for p in c["R-04"]["procedures"]] == [("SSE-1303", "confirme")]
    assert c["R-10"]["procedures"][0]["numero"] == "SSE-601-NOR"


def test_procedure_absente_de_l_index(tmp_path):
    c = confiance_des_risques(RISQUES, index(tmp_path))
    assert [p["niveau"] for p in c["R-07"]["procedures"]] == ["partiel", "absent"]


def test_reference_externe_signalee_sans_niveau(tmp_path):
    c = confiance_des_risques(RISQUES, index(tmp_path))
    assert c["R-39"]["procedures"] == [] and c["R-39"]["hors_index"] is True


def test_gabarit_rappelle_la_limite_de_l_index():
    g = (GABARITS / "page_registre.html").read_text(encoding="utf-8")
    assert "jamais le contenu d’une section" in g
    assert "Validation humaine requise" in g
    assert "À confirmer" in g
