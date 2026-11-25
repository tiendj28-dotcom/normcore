"""NORM-37: pr_sync_fix sắp lại vi.csv, bỏ dòng trùng hệt, sinh lại normcore.json."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import check_conventions as cc
import pr_sync_fix as fx


def _setup(tmp_path, vi, shortcuts):
	(tmp_path / "normcore/translations").mkdir(parents=True)
	(tmp_path / cc.VI_CSV).write_text(vi, encoding="utf-8")
	ws = tmp_path / "normcore/nc_core/workspace/normcore"
	ws.mkdir(parents=True)
	(ws / "shortcuts.txt").write_text(shortcuts, encoding="utf-8")
	return tmp_path


def test_sap_lai_bo_trung_va_sinh_workspace(tmp_path):
	root = _setup(tmp_path, "B,Hai\nA,Một\nB,Hai\n", "x-s|X|NC X|DocType|List\nx-s|X|NC X|DocType|List\n")
	changed = fx.fix(root)
	assert cc.VI_CSV in changed and any(c.endswith("normcore.json") for c in changed)
	assert (root / cc.VI_CSV).read_text(encoding="utf-8") == "A,Một\nB,Hai\n"
	assert cc.check_vi_csv(root) == [] and cc.check_workspace(root) == []
	assert fx.fix(root) == []  # chạy lại không đổi


def test_trung_khoa_khac_ban_dich_giu_nguyen_de_bao_loi(tmp_path):
	root = _setup(tmp_path, "A,Một\nA,Khác\n", "")
	fx.fix(root)
	assert any("NC-09" in e for e in cc.check_vi_csv(root))
