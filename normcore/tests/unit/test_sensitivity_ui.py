"""SCR-DSK-040 (FEAT-037): kiểm tĩnh trang `sensitivity` — chỉ gọi API đọc, dải "Kết quả thử, không lưu", không mã màu cứng,
chuỗi qua __() có bản dịch, lỗi role=alert, roles đúng thiết kế."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "public" / "js" / "sensitivity"
PAGE_DIR = ROOT / "nc_costing" / "page" / "sensitivity"
SERVICE_COST_JS = ROOT / "nc_costing" / "doctype" / "nc_service_cost" / "nc_service_cost.js"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
I18N = re.compile(r"""__\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')""")
VUE = (UI_DIR / "Sensitivity.vue").read_text(encoding="utf-8")
API = (ROOT / "api" / "costing.py").read_text(encoding="utf-8")
COMP_LABEL = ("Labor", "Drug and chemical", "Supply", "Equipment", "Infrastructure", "Utility")


def _sources():
	return [*UI_DIR.glob("*"), *PAGE_DIR.glob("*.js")]


class TestSensitivityUI(unittest.TestCase):
	def test_tep_ton_tai(self):
		self.assertTrue((UI_DIR / "Sensitivity.vue").is_file())
		self.assertTrue((UI_DIR / "sensitivity.bundle.js").is_file())
		for n in ("sensitivity.js", "sensitivity.json", "__init__.py"):
			self.assertTrue((PAGE_DIR / n).is_file(), n)

	def test_khong_ma_mau_cung(self):
		for p in _sources():
			self.assertIsNone(HEX.search(p.read_text(encoding="utf-8")), p.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0] for row in csv.reader(f) if len(row) >= 2}
		used = set(COMP_LABEL)
		for p in [*_sources(), SERVICE_COST_JS]:
			for a, b in I18N.findall(p.read_text(encoding="utf-8")):
				used.add(a or b)
		self.assertEqual(sorted(used - vi), [])

	def test_chi_goi_api_doc_khong_goi_api_ghi(self):
		called = set(re.findall(r'API \+ "(\w+)"', VUE))
		self.assertEqual(called, {"get_sensitivity_base", "run_sensitivity"})
		self.assertIn('const API = "normcore.api.costing.";', VUE)
		for fn in called:
			self.assertRegex(API, rf"@frappe.whitelist\(\)\ndef {fn}\(")
		for p in _sources():
			t = p.read_text(encoding="utf-8")
			for write in ("save_explanation", "lock_run", "frappe.client", "set_value", "insert", "db.set"):
				self.assertNotIn(write, t.replace("serverMessage", ""), (p.name, write))
		self.assertNotRegex(VUE, r'method:\s*"(?!"?\s*\+)')

	def test_dai_co_dinh_ket_qua_thu_khong_luu(self):
		self.assertIn('__("Trial result, not saved")', VUE)
		self.assertIn("position: sticky", VUE)
		self.assertIn('class="nc-sens__banner"', VUE)

	def test_loi_role_alert_va_kiem_tra_phia_may_khach(self):
		self.assertIn('class="nc-sens__error" role="alert"', VUE)
		self.assertIn('role="alert"', VUE)
		for msg in ("Assumed volume must be greater than 0", "Assumed price must not be negative", "Enter the annual contract cost"):
			self.assertIn(msg, VUE)
		self.assertIn("Ctrl", VUE)

	def test_page_roles_dung_thiet_ke(self):
		d = json.loads((PAGE_DIR / "sensitivity.json").read_text(encoding="utf-8"))
		self.assertEqual(
			sorted(r["role"] for r in d["roles"]),
			["NC Admin", "NC Auditor", "NC Department Head", "NC Director", "NC Finance"],
		)
		self.assertEqual((d["name"], d["page_name"], d["module"]), ("sensitivity", "sensitivity", "NC Costing"))

	def test_loi_vao_tu_nc_service_cost(self):
		t = SERVICE_COST_JS.read_text(encoding="utf-8")
		self.assertIn('__("Sensitivity analysis")', t)
		self.assertIn('frappe.set_route("sensitivity"', t)
