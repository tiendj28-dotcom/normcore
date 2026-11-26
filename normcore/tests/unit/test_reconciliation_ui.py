"""FEAT-017 — SCR-DSK-024, SCR-DSK-022 bổ sung: JS chỉ gọi API costing, chuỗi có bản dịch, role=alert, không mã màu cứng."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "nc_costing" / "report" / "nc_reconciliation"
DT = ROOT / "nc_costing" / "doctype"
FILES = [
	REPORT / "nc_reconciliation.js",
	DT / "nc_reconciliation_line" / "nc_reconciliation_line.js",
	DT / "nc_reconciliation_line" / "nc_reconciliation_line_list.js",
	DT / "nc_costing_run" / "nc_costing_run.js",
]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")
API = (ROOT / "api" / "costing.py").read_text(encoding="utf-8")


def _t(p):
	return p.read_text(encoding="utf-8")


class TestReconciliationUI(unittest.TestCase):
	def test_tep_ton_tai(self):
		for f in [*FILES, REPORT / "nc_reconciliation.py", REPORT / "nc_reconciliation.json"]:
			self.assertTrue(f.is_file(), f.name)

	def test_khong_ma_mau_cung(self):
		for f in FILES:
			self.assertIsNone(HEX.search(_t(f)), f.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as fh:
			vi = {row[0] for row in csv.reader(fh) if len(row) >= 2}
		for f in FILES:
			used = set(re.findall(r"__\(\s*\"((?:[^\"\\]|\\.)*)\"", _t(f)))
			self.assertEqual(sorted(used - vi), [], f.name)
		used = set(re.findall(r"\b_\(\s*\"((?:[^\"\\]|\\.)*)\"", _t(REPORT / "nc_reconciliation.py")))
		self.assertEqual(sorted(used - vi), [])

	def test_chi_goi_api_costing(self):
		called = set()
		for f in FILES:
			called |= set(re.findall(r'API \+ "(\w+)"', _t(f)))
			self.assertNotRegex(_t(f), r'method:\s*"(?!normcore\.api\.costing\.)[a-z_.]+\.', f.name)
		self.assertTrue({"get_reconciliation", "save_explanation", "lock_run"} <= called)
		self.assertIn("normcore.api.costing.lock_run", _t(FILES[3]))
		for fn in called | {"lock_run"}:
			self.assertRegex(API, rf"@frappe.whitelist\(\)\ndef {fn}\(")

	def test_role_alert_o_dai_chan_khoa_va_canh_bao(self):
		t = _t(FILES[0])
		self.assertIn('role="alert"', t)
		self.assertIn("danger", t)
		self.assertIn("warning", t)
		self.assertIn('role="alert"', _t(FILES[3]))

	def test_du_lieu_chen_html_qua_escape(self):
		for f in (FILES[0], FILES[3]):
			self.assertIn("escape_html", _t(f))

	def test_report_json_dung_bon_vai_tro(self):
		d = json.loads(_t(REPORT / "nc_reconciliation.json"))
		self.assertEqual(
			sorted(r["role"] for r in d["roles"]), ["NC Admin", "NC Auditor", "NC Director", "NC Finance"]
		)
		self.assertEqual((d["ref_doctype"], d["report_type"]), ("NC Reconciliation Line", "Script Report"))

	def test_bo_loc_va_nut_khoa(self):
		t = _t(FILES[0])
		for f in ("costing_run", "cost_center", "only_over"):
			self.assertIn(f'fieldname: "{f}"', t)
		self.assertIn("set_primary_action", t)
		self.assertIn("m.can_lock", t)

	def test_form_lan_tinh_co_nut_khoa_va_doi_soat(self):
		t = _t(FILES[3])
		for s in ('__("Lock")', '__("Reconciliation table")', "allocation_warnings", "recon_blocked"):
			self.assertIn(s, t)
