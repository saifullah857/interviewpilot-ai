"""Rebuilds data/questions/*.json from the qb_*.py authoring files. Run: python scripts/build_question_bank.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qb_10pearls, qb_afiniti, qb_arbisoft, qb_confiz, qb_conrad, qb_contour, qb_cubix, qb_curemd, qb_devsinc, qb_folio3, qb_kualitatem, qb_mindstorm, qb_netsol, qb_nextbridge, qb_northbay, qb_purelogics, qb_systems, qb_techlogix, qb_tkxel, qb_vteams, qb_xeven  # noqa: E401

for m in (qb_10pearls, qb_afiniti, qb_arbisoft, qb_confiz, qb_conrad, qb_contour, qb_cubix, qb_curemd, qb_devsinc, qb_folio3, qb_kualitatem, qb_mindstorm, qb_netsol, qb_nextbridge, qb_northbay, qb_purelogics, qb_systems, qb_techlogix, qb_tkxel, qb_vteams, qb_xeven):
    print(len(m.build()), "questions written by", m.__name__)
