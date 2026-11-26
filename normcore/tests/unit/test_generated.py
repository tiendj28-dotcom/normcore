"""NORM-60: ghép mảnh theo FEAT thành vi.csv và normcore.json (normcore/generated.py), pure Python."""

import csv
import json
import subprocess
import sys
from pathlib import Path

from normcore import generated as g
from normcore.tests.unit.tmpcase import TmpCase as _Base

REPO = Path(__file__).resolve().parents[3]


def _write(path: Path, text: str):
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(text, encoding="utf-8")


def _tree(tmp_path: Path, frag: dict, shortcuts: dict) -> Path:
	for name, text in frag.items():
		_write(tmp_path / "normcore/translations/vi.d" / name, text)
	for name, text in shortcuts.items():
		_write(tmp_path / g.REL / "shortcuts.d" / name, text)
	return tmp_path


class TestTranslations(_Base):
	def test_ghep_nhieu_manh_va_sap_xep(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"FEAT-002.csv": "Zeta,Z\nAlpha,A\n", "00-base.csv": "Mid,M\n"}, {})
		rows, errors = g.merge_translations(root)
		assert errors == []
		assert [r[0] for r in rows] == ["Alpha", "Mid", "Zeta"]

	def test_bo_dong_trung_het(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"A.csv": "Same,S\n", "B.csv": "Same,S\n"}, {})
		rows, errors = g.merge_translations(root)
		assert errors == [] and rows == [["Same", "S"]]

	def test_nc09_trung_khoa_giua_hai_manh_neu_ca_hai_tep(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"A.csv": "Same,S1\n", "B.csv": "Same,S2\n"}, {})
		_rows, errors = g.merge_translations(root)
		assert len(errors) == 1
		assert "NC-09" in errors[0] and "A.csv" in errors[0] and "B.csv" in errors[0]

	def test_ngu_canh_khac_khong_phai_trung(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"A.csv": "Same,S1,ctx1\n", "B.csv": "Same,S2,ctx2\n"}, {})
		_rows, errors = g.merge_translations(root)
		assert errors == []

	def test_write_translations_loi_khong_ghi_tep(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"A.csv": "Same,S1\n", "B.csv": "Same,S2\n"}, {})
		with self.assertRaisesRegex(ValueError, "NC-09"):
			g.write_translations(root)
		assert not (root / "normcore/translations/vi.csv").exists()

	def test_write_translations_idempotent(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"A.csv": "B,b\nA,a\n"}, {})
		assert g.write_translations(root) is True
		assert g.write_translations(root) is False
		with open(root / "normcore/translations/vi.csv", encoding="utf-8", newline="") as fh:
			assert [r[0] for r in csv.reader(fh)] == ["A", "B"]

	def test_thu_tu_00_base_roi_theo_ten(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"FEAT-010.csv": "X,1\n", "00-base.csv": "X,1\n", "FEAT-002.csv": "Y,2\n"}, {})
		assert [p.name for p in g.fragment_files(root / "normcore/translations/vi.d", "*.csv")] == [
			"00-base.csv",
			"FEAT-002.csv",
			"FEAT-010.csv",
		]


class TestWorkspace(_Base):
	ROW1 = "a1|Một|NC Item|DocType|List\n"
	ROW2 = "a2|Hai|NC Room|DocType|List\n"

	def test_doc_nhieu_manh_theo_thu_tu(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {}, {"FEAT-002.txt": self.ROW2, "00-base.txt": self.ROW1})
		rows = g.read_sources(root)
		assert [r[0] for r in rows] == ["a1", "a2"]

	def test_dong_trung_het_bi_bo(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {}, {"A.txt": self.ROW1, "B.txt": self.ROW1})
		assert len(g.read_sources(root)) == 1

	def test_id_trung_khac_noi_dung_bao_loi_nc11(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {}, {"A.txt": self.ROW1, "B.txt": "a1|Khác|NC Room|DocType|List\n"})
		with self.assertRaisesRegex(ValueError, "NC-11"):
			g.read_sources(root)

	def test_modified_mac_dinh_la_hang_so_cu(self):
		rows = [r.split("|") for r in (self.ROW1 + self.ROW2).splitlines()]
		doc = json.loads(g.render(rows))
		assert doc["modified"] == "2026-11-26 10:00:00.000000"
		assert json.loads(g.render(rows, modified="2030-01-01 00:00:00.000000"))["modified"].startswith(
			"2030"
		)

	def test_bo_cuc_cu_shortcuts_txt_van_dung_nhu_truoc(self):
		tmp_path = self.tmp_path
		_write(tmp_path / g.REL / "shortcuts.txt", "# c\n" + self.ROW1)
		assert g.read_sources(tmp_path) == [["a1", "Một", "NC Item", "DocType", "List"]]

	def test_write_workspace_dung_manh(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {}, {"00-base.txt": self.ROW1, "FEAT-9.txt": self.ROW2})
		g.write_workspace(root)
		doc = json.loads((root / g.REL / "normcore.json").read_text(encoding="utf-8"))
		assert [s["label"] for s in doc["shortcuts"]] == ["Một", "Hai"]


class TestModulo(_Base):
	def test_build_all_ghi_ca_hai(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"A.csv": "A,a\n"}, {"A.txt": "a1|Một|NC Item|DocType|List\n"})
		written = g.build_all(root)
		assert sorted(Path(w).name for w in written) == ["normcore.json", "vi.csv"]
		assert g.build_all(root) == []

	def test_generated_khong_import_frappe_o_muc_module(self):
		src = (REPO / "normcore/generated.py").read_text(encoding="utf-8")
		assert not [ln for ln in src.splitlines() if ln.startswith(("import frappe", "from frappe"))]

	def test_cli_build_workspace_van_dung_ten_cu(self):
		sys.path.insert(0, str(REPO / "scripts"))
		import build_workspace as bw

		assert bw.REL == g.REL and bw.render is g.render and bw.read_shortcuts is g.read_shortcuts

	def test_cli_build_generated_chay_duoc(self):
		tmp_path = self.tmp_path
		root = _tree(tmp_path, {"A.csv": "A,a\n"}, {"A.txt": "a1|Một|NC Item|DocType|List\n"})
		r = subprocess.run(
			[sys.executable, str(REPO / "scripts/build_generated.py"), str(root)],
			capture_output=True,
			text=True,
		)
		assert r.returncode == 0, r.stderr
		assert (root / "normcore/translations/vi.csv").exists()

	def test_write_workspace_sinh_ca_shortcuts_txt_tong_hop(self):
		tmp_path = self.tmp_path
		"""ASM-NORM60-09: test cũ đọc thẳng shortcuts.txt vẫn thấy dòng của mọi mảnh."""
		root = _tree(
			tmp_path,
			{},
			{"00-base.txt": "a1|Một|NC Item|DocType|List\n", "FEAT-9.txt": "a2|Hai|NC Room|DocType|List\n"},
		)
		g.write_workspace(root)
		text = (root / g.REL / "shortcuts.txt").read_text(encoding="utf-8")
		assert "a1|Một|NC Item|DocType|List" in text and "a2|Hai|NC Room|DocType|List" in text
		assert g.read_shortcuts(root / g.REL / "shortcuts.txt") == g.read_sources(root)
