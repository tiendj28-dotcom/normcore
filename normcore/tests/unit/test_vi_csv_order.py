"""NORM-24: check_conventions báo lỗi khi vi.csv chưa sắp xếp hoặc trùng khóa; vi.csv thật đạt."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("check_conventions", ROOT / "scripts" / "check_conventions.py")
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)


def _root_with(tmp_path, text):
	f = tmp_path / "normcore" / "translations" / "vi.csv"
	f.parent.mkdir(parents=True)
	f.write_text(text, encoding="utf-8")
	return tmp_path


def test_vi_csv_da_sap_xep_khong_loi(tmp_path):
	assert cc.check_vi_csv(_root_with(tmp_path, "A,Một\nB,Hai\nB,Hai khác,Ngữ cảnh\n")) == []


def test_vi_csv_chua_sap_xep_bao_loi(tmp_path):
	errs = cc.check_vi_csv(_root_with(tmp_path, "B,Hai\nA,Một\n"))
	assert len(errs) == 1 and "NC-10" in errs[0]


def test_vi_csv_trung_khoa_bao_loi(tmp_path):
	errs = cc.check_vi_csv(_root_with(tmp_path, "A,Một\nA,Một nữa\n"))
	assert len(errs) == 1 and "NC-09" in errs[0]


def test_vi_csv_cung_khoa_khac_ngu_canh_khong_trung(tmp_path):
	assert cc.check_vi_csv(_root_with(tmp_path, "A,Một\nA,Một khác,Ngữ cảnh\n")) == []


def test_vi_csv_that_dat():
	assert cc.check_vi_csv(ROOT) == []
