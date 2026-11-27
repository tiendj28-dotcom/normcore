"""FEAT-027: giao diện trích bảng giá PDF (ui-design.md): kiểm tĩnh mã nguồn JS và bản dịch."""

import csv
import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = (ROOT / "public" / "js" / "benchmark_pdf_ai.js").read_text(encoding="utf-8")
FRAGMENT = ROOT / "translations" / "vi.d" / "FEAT-027.csv"
VI = {r[0]: r[1] for r in csv.reader(FRAGMENT.open(encoding="utf-8")) if len(r) > 1}


def strings(text):
	return {m.group(1).replace('\\"', '"') for m in re.finditer(r'__\(\s*"((?:[^"\\]|\\.)*)"', text)}


def merged_vi():
	out = {}
	for f in sorted((ROOT / "translations" / "vi.d").glob("*.csv")):
		out.update({r[0]: r[1] for r in csv.reader(f.open(encoding="utf-8")) if len(r) > 1})
	return out


class TestFeat027Ui(unittest.TestCase):
	def test_moi_chuoi_giao_dien_co_ban_dich(self):
		vi = merged_vi()
		self.assertEqual([s for s in strings(JS) if s not in vi], [])
		self.assertEqual(VI["Review rows"], "Rà soát các dòng")

	def test_chi_goi_api_benchmark_ai(self):
		self.assertIn('const API = "normcore.api.benchmark_ai."', JS)
		self.assertEqual(
			set(re.findall(r'call\(\s*"(\w+)"', JS)),
			{"start_price_list_extraction", "get_price_list_extraction_status"},
		)
		self.assertIn("normcore_price_list_ai", JS)

	def test_FR_AI_015_nut_theo_ai_bat_va_quyen(self):
		self.assertRegex(
			JS,
			r'normcore\.ai\.enabled\(\) && !frm\.is_new\(\) && frappe\.model\.can_create\("NC Benchmark Price"\)',
		)
		self.assertIn('frappe.ui.form.on("NC Benchmark Facility"', JS)

	def test_hook_registry_khai_bao_tep_js(self):
		reg = json.loads((ROOT / "hook_registry" / "FEAT-027.json").read_text(encoding="utf-8"))
		self.assertEqual(reg["app_include_js"], ["/assets/normcore/js/benchmark_pdf_ai.js"])

	def test_luong_loi_nhap_tay_hoac_excel(self):
		self.assertIn("nc_benchmark_price", JS)
		self.assertIn('frappe.new_doc("NC Benchmark Price"', JS)
		self.assertIn('"import-excel"', JS)

	def test_gia_tri_may_chu_duoc_escape(self):
		self.assertIn("frappe.utils.escape_html", JS)
		self.assertNotRegex(JS, r"#[0-9a-fA-F]{3,6}\b")

	def test_js_va_dich_feat_026_khong_doi(self):
		out = subprocess.run(
			[
				"git",
				"diff",
				"origin/develop",
				"--",
				"normcore/nc_benchmark/doctype/nc_benchmark_price/nc_benchmark_price_list.js",
				"normcore/nc_benchmark/doctype/nc_benchmark_price/nc_benchmark_price.js",
				"normcore/translations/vi.d/FEAT-026.csv",
			],
			cwd=ROOT.parent,
			capture_output=True,
			text=True,
		)
		self.assertEqual(out.stdout, "")
