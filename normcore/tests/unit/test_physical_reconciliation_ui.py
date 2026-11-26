"""FEAT-037 — SCR-DSK-038, SCR-DSK-039, phần [1.1] của SCR-DSK-024 và SCR-DSK-022: JS chỉ gọi API costing,
chuỗi có bản dịch, role=alert ở dải chặn, không mã màu cứng, roles đúng thiết kế."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REP = ROOT / "nc_costing" / "report"
PHYS = REP / "nc_physical_reconciliation"
MISS = REP / "nc_missing_data"
DT = ROOT / "nc_costing" / "doctype"
JS = [
	PHYS / "nc_physical_reconciliation.js",
	MISS / "nc_missing_data.js",
	REP / "nc_reconciliation" / "nc_reconciliation.js",
	DT / "nc_costing_run" / "nc_costing_run.js",
	DT / "nc_reconciliation_line" / "nc_reconciliation_line.js",
	DT / "nc_reconciliation_line" / "nc_reconciliation_line_list.js",
]
PY = [PHYS / "nc_physical_reconciliation.py", MISS / "nc_missing_data.py"]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")
API = (ROOT / "api" / "costing.py").read_text(encoding="utf-8")


def _t(p):
	return p.read_text(encoding="utf-8")


class TestPhysicalReconciliationUI(unittest.TestCase):
	def test_tep_ton_tai(self):
		for f in [*JS, *PY, PHYS / "nc_physical_reconciliation.json", MISS / "nc_missing_data.json"]:
			self.assertTrue(f.is_file(), f.name)

	def test_khong_ma_mau_cung(self):
		for f in JS:
			self.assertIsNone(HEX.search(_t(f)), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as fh:
			vi = {row[0] for row in csv.reader(fh) if len(row) >= 2}
		for f in JS:
			used = set(re.findall(r"__\(\s*\"((?:[^\"\\]|\\.)*)\"", _t(f)))
			self.assertEqual(sorted(used - vi), [], f.name)
		for f in PY:
			used = set(re.findall(r"\b_\(\s*\"((?:[^\"\\]|\\.)*)\"", _t(f)))
			self.assertEqual(sorted(used - vi), [], f.name)

	def test_chi_goi_api_costing(self):
		called = set()
		for f in JS:
			called |= set(re.findall(r'API \+ "(\w+)"', _t(f)))
			self.assertNotRegex(_t(f), r'method:\s*"(?!normcore\.api\.costing\.)[a-z_.]+\.', f.name)
		self.assertTrue({"get_physical_reconciliation", "save_explanation", "lock_run"} <= called)
		for fn in called:
			self.assertRegex(API, rf"@frappe.whitelist\(\)\ndef {fn}\(")

	def test_role_alert_o_dai_chan_khoa(self):
		t = _t(PHYS / "nc_physical_reconciliation.js")
		self.assertIn('role="alert"', t)
		for color in ("danger", "warning", "success"):
			self.assertIn(color, t)
		self.assertIn('role="alert"', _t(DT / "nc_costing_run" / "nc_costing_run.js"))
		self.assertIn('role="alert"', _t(REP / "nc_reconciliation" / "nc_reconciliation.js"))

	def test_du_lieu_chen_html_qua_escape(self):
		for f in (JS[0], JS[3]):
			self.assertIn("escape_html", _t(f))

	def test_roles_hai_report_dung_thiet_ke(self):
		a = json.loads(_t(PHYS / "nc_physical_reconciliation.json"))
		self.assertEqual(sorted(r["role"] for r in a["roles"]), ["NC Admin", "NC Auditor", "NC Director", "NC Finance"])
		self.assertEqual((a["ref_doctype"], a["report_type"]), ("NC Reconciliation Line", "Script Report"))
		b = json.loads(_t(MISS / "nc_missing_data.json"))
		self.assertEqual(
			sorted(r["role"] for r in b["roles"]),
			["NC Admin", "NC Auditor", "NC Department Head", "NC Director", "NC Finance"],
		)
		self.assertEqual((b["ref_doctype"], b["report_type"]), ("NC Costing Run", "Script Report"))

	def test_bo_loc_va_nut(self):
		t = _t(JS[0])
		for f in ("costing_run", "table", "department", "only_attention"):
			self.assertIn(f'fieldname: "{f}"', t)
		self.assertIn("set_primary_action", t)
		self.assertIn("m.can_lock", t)
		m = _t(JS[1])
		for f in ("fiscal_year", "costing_date", "parameter_set", "price_category", "volume_scenario", "department", "technical_service", "kind"):
			self.assertIn(f'fieldname: "{f}"', m)
		for write in ("save_explanation", "lock_run", "frappe.call"):
			self.assertNotIn(write, m)  # báo cáo thiếu dữ liệu chỉ đọc

	def test_form_lan_tinh_co_nut_va_dai(self):
		t = _t(JS[3])
		for s in ('__("Material and volume reconciliation")', '__("Missing data report")', "physical_unreconciled", "open_physical", "open_missing"):
			self.assertIn(s, t)
