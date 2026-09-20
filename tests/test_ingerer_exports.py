"""Tests de l'ingestion des exports. Lancer : pytest -q"""
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from ingerer_exports import analyser, lire_fichier, mois_de, rapport, role_des_colonnes  # noqa: E402


def export(tmp_path, lignes, entetes=("Id", "Title", "Status", "Date Performed", "Signed off by")):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(list(entetes))
    for l in lignes:
        ws.append(list(l))
    f = tmp_path / "export.xlsx"
    wb.save(f)
    return f


def test_colonnes_reconnues_malgre_accents_et_casse():
    roles = role_des_colonnes(["ID", "Modèle", "STATUT", "Date réalisée", "Signé par"])
    assert set(roles) == {"id", "titre", "statut", "date", "signature"}


def test_mois_accepte_date_et_texte():
    assert mois_de(datetime(2026, 7, 3)) == "2026-07"
    assert mois_de("2026-07-03") == "2026-07"
    assert mois_de(None) is None


def test_non_fermees_et_sans_signature(tmp_path):
    f = export(tmp_path, [
        (1, "Mensuelle", "Locked", datetime(2026, 5, 2), "X"),
        (2, "Mensuelle", "Submitted", datetime(2026, 6, 2), None),
        (3, "Mensuelle", "In Progress", datetime(2026, 6, 9), None),
    ])
    lignes, manquantes = lire_fichier(f)
    assert manquantes == []
    par_mois, statuts, non_fermees, sans_signature, _ = analyser(lignes)
    assert par_mois["Mensuelle"] == {"2026-05": 1, "2026-06": 2}
    assert len(non_fermees["Mensuelle"]) == 2
    assert len(sans_signature["Mensuelle"]) == 2


def test_colonne_absente_signalee(tmp_path):
    f = export(tmp_path, [(1, "Mensuelle", "Locked")], entetes=("Id", "Title", "Status"))
    _, manquantes = lire_fichier(f)
    assert manquantes == ["date", "signature"]


def test_rapport_sans_nom_et_avec_validation_humaine(tmp_path):
    f = export(tmp_path, [(1, "Mensuelle", "Submitted", datetime(2026, 5, 2), "Untel Quelqu'un")])
    lignes, _ = lire_fichier(f)
    chemin, total, ouvertes = rapport([("export.xlsx", 1)], lignes, 0, [], tmp_path / "rapports")
    texte = chemin.read_text(encoding="utf-8")
    assert total == 1 and ouvertes == 1
    assert "Untel" not in texte                      # aucun nom recopié
    assert "Validation humaine requise" in texte
    assert "verdict de conformité" in texte
