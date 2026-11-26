"""NORM-60: tệp scripts/conventions/perm_matrix/*.json và kiểm NC-08/09/10/11 trên bố cục mảnh."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
import check_conventions as cc

CODES = "R R - W R - R R W R"


def _perm(root: Path, name: str, data):
	d = root / cc.PERM_MATRIX_DIR
	d.mkdir(parents=True, exist_ok=True)
	(d / f"{name}.json").write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")


@pytest.fixture(autouse=True)
def _restore_dicts():
	m, r, d = dict(cc.MATRIX), dict(cc.DOCTYPE_ROW), {k: set(v) for k, v in cc.DELETE_ALLOWED.items()}
	yield
	cc.MATRIX.clear()
	cc.MATRIX.update(m)
	cc.DOCTYPE_ROW.clear()
	cc.DOCTYPE_ROW.update(r)
	cc.DELETE_ALLOWED.clear()
	cc.DELETE_ALLOWED.update(d)


class TestPermMatrixFiles:
	def test_nap_vao_ba_dict(self, tmp_path):
		_perm(
			tmp_path,
			"nc_x_thu",
			{"doctype": "NC X Thu", "row": "Dòng thử", "codes": CODES, "delete": ["NC Admin"]},
		)
		assert cc.load_perm_matrix(tmp_path) == []
		assert cc.DOCTYPE_ROW["NC X Thu"] == "Dòng thử"
		assert cc.MATRIX["Dòng thử"] == CODES
		assert "NC X Thu" in cc.DELETE_ALLOWED["NC Admin"]

	def test_nap_hai_lan_khong_loi(self, tmp_path):
		_perm(tmp_path, "nc_x_thu", {"doctype": "NC X Thu", "row": "Dòng thử", "codes": CODES})
		assert cc.load_perm_matrix(tmp_path) == []
		assert cc.load_perm_matrix(tmp_path) == []

	def test_nc08_tep_hong(self, tmp_path):
		_perm(tmp_path, "nc_x_thu", "{khong phai json")
		errs = cc.load_perm_matrix(tmp_path)
		assert len(errs) == 1 and "NC-08" in errs[0]

	def test_nc08_doctype_khong_khop_ten_tep(self, tmp_path):
		_perm(tmp_path, "nc_khac", {"doctype": "NC X Thu", "row": "Dòng thử", "codes": CODES})
		assert "không khớp tên tệp" in cc.load_perm_matrix(tmp_path)[0]

	def test_nc08_codes_lech_dong_da_co(self, tmp_path):
		row = "Quy trình"
		_perm(tmp_path, "nc_x_thu", {"doctype": "NC X Thu", "row": row, "codes": CODES})
		assert "codes khác ma trận" in cc.load_perm_matrix(tmp_path)[0]
		assert "NC X Thu" not in cc.DOCTYPE_ROW

	def test_nc08_codes_sai_dinh_dang(self, tmp_path):
		_perm(tmp_path, "nc_x_thu", {"doctype": "NC X Thu", "row": "Dòng thử", "codes": "R R"})
		assert "codes cần" in cc.load_perm_matrix(tmp_path)[0]

	def test_nc08_khai_trung_voi_bang_literal(self, tmp_path):
		_perm(
			tmp_path,
			"nc_item",
			{
				"doctype": "NC Item",
				"row": "Mặt hàng, đơn giá, thiết bị, phòng",
				"codes": cc.MATRIX["Mặt hàng, đơn giá, thiết bị, phòng"],
			},
		)
		assert "đã khai trong bảng literal" in cc.load_perm_matrix(tmp_path)[0]

	def test_thu_muc_that_nap_sach(self):
		assert cc.load_perm_matrix(REPO) == []


def _frag_root(tmp_path: Path) -> Path:
	(tmp_path / cc.VI_DIR).mkdir(parents=True)
	(tmp_path / cc.VI_DIR / "A.csv").write_text("B,b\nA,a\n", encoding="utf-8")
	return tmp_path


class TestConventionsOnFragments:
	def test_ghep_sach(self, tmp_path):
		assert cc.check_vi_csv(_frag_root(tmp_path)) == []

	def test_nc09_trung_khoa_giua_hai_manh(self, tmp_path):
		root = _frag_root(tmp_path)
		(root / cc.VI_DIR / "B.csv").write_text("A,khac\n", encoding="utf-8")
		errs = cc.check_vi_csv(root)
		assert errs and "NC-09" in errs[0] and "A.csv" in errs[0] and "B.csv" in errs[0]

	def test_nc10_vi_csv_tren_dia_cu(self, tmp_path):
		root = _frag_root(tmp_path)
		(root / cc.VI_CSV).write_text("A,cu\n", encoding="utf-8")
		errs = cc.check_vi_csv(root)
		assert errs and "NC-10" in errs[0] and "build_generated" in errs[0]

	def test_vi_csv_dung_khop_ghep_thi_sach(self, tmp_path):
		root = _frag_root(tmp_path)
		(root / cc.VI_CSV).write_text("A,a\nB,b\n", encoding="utf-8")
		assert cc.check_vi_csv(root) == []

	def test_nc10_vi_csv_dang_duoc_git_theo_doi(self, tmp_path):
		root = _frag_root(tmp_path)
		(root / cc.VI_CSV).write_text("A,a\nB,b\n", encoding="utf-8")
		subprocess.run(["git", "init", "-q", str(root)], check=True)
		subprocess.run(["git", "-C", str(root), "add", "-f", cc.VI_CSV], check=True)
		assert any("git theo dõi" in e for e in cc.check_vi_csv(root))

	def test_nc11_id_trung_khac_noi_dung_giua_hai_manh(self, tmp_path):
		import build_workspace as bw

		d = tmp_path / bw.REL / "shortcuts.d"
		d.mkdir(parents=True)
		(d / "A.txt").write_text("a1|Một|NC Item|DocType|List\n", encoding="utf-8")
		(d / "B.txt").write_text("a1|Khác|NC Item|DocType|List\n", encoding="utf-8")
		errs = cc.check_workspace(tmp_path)
		assert errs and "NC-11" in errs[0]

	def test_nc11_con_shortcuts_txt_canh_shortcuts_d(self, tmp_path):
		import build_workspace as bw

		d = tmp_path / bw.REL / "shortcuts.d"
		d.mkdir(parents=True)
		(d / "A.txt").write_text("a1|Một|NC Item|DocType|List\n", encoding="utf-8")
		(tmp_path / bw.REL / "shortcuts.txt").write_text("a2|Hai|NC Room|DocType|List\n", encoding="utf-8")
		assert any("shortcuts.txt" in e for e in cc.check_workspace(tmp_path))
