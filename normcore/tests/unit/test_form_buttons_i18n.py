"""Nút tạm trên form (NORM-10): tệp JS có đủ, chuỗi qua __() có bản dịch vi.csv, không mã màu cứng."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORM_JS = [
	ROOT / "nc_procedure" / "doctype" / "nc_clinical_procedure" / "nc_clinical_procedure.js",
	ROOT / "nc_costing" / "doctype" / "nc_norm_set" / "nc_norm_set.js",
	ROOT / "nc_costing" / "doctype" / "nc_costing_run" / "nc_costing_run.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
I18N = re.compile(r"__\(\s*(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')")
LABELS = {
	"Publish": "Ban hành",
	"Create norm set": "Khởi tạo bộ định mức",
	"Lock": "Khóa",
	"Run costing": "Chạy tính giá",
	"Open editor": "Mở trình soạn",
	"View costing results": "Xem kết quả tính giá",
}


def _vi():
	with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
		return {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}


def _strings(path):
	return {
		m[1:-1].replace("\\'", "'").replace('\\"', '"')
		for m in I18N.findall(path.read_text(encoding="utf-8"))
	}


class TestFormButtonsI18n(unittest.TestCase):
	def test_ba_tep_js_ton_tai(self):
		for p in FORM_JS:
			self.assertTrue(p.is_file(), p.name)

	def test_chuoi_co_ban_dich(self):
		vi = _vi()
		used = set()
		for p in FORM_JS:
			used |= _strings(p)
		self.assertTrue(used)
		self.assertEqual(sorted(used - set(vi)), [])

	def test_nhan_tieng_viet_dung(self):
		vi = _vi()
		used = set()
		for p in FORM_JS:
			used |= _strings(p)
		for src, label in LABELS.items():
			self.assertIn(src, used)
			self.assertEqual(vi[src], label)

	def test_khong_ma_mau_cung(self):
		for p in FORM_JS:
			self.assertIsNone(HEX.search(p.read_text(encoding="utf-8")), p.name)
