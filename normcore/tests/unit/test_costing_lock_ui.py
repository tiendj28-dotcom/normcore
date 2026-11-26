"""FEAT-018 — SCR-DSK-022 bổ sung, report so sánh: JS chỉ gọi API costing, chuỗi có bản dịch, role=alert, không mã màu."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "nc_costing" / "report" / "nc_costing_run_comparison"
FORM = ROOT / "nc_costing" / "doctype" / "nc_costing_run" / "nc_costing_run.js"
JS = [FORM, REPORT / "nc_costing_run_comparison.js"]
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(")
API = (ROOT / "api" / "costing.py").read_text(encoding="utf-8")


def _t(p):
	return p.read_text(encoding="utf-8")


class TestCostingLockUI(unittest.TestCase):
	def test_tep_ton_tai(self):
		for f in (*JS, REPORT / "nc_costing_run_comparison.py", REPORT / "nc_costing_run_comparison.json"):
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
		used = set(
			re.findall(
				r"\b_\(\s*[\"']((?:[^\"'\\]|\\.)*)[\"']\s*\)", _t(REPORT / "nc_costing_run_comparison.py")
			)
		)
		self.assertEqual(sorted(used - vi), [])

	def test_chi_goi_api_costing(self):
		called = set(re.findall(r'"normcore\.api\.costing\.(\w+)"', _t(FORM)))
		for f in JS:
			self.assertNotRegex(_t(f), r'method:\s*"(?!normcore\.api\.costing\.)[a-z_.]+\.', f.name)
		self.assertTrue({"verify_snapshot", "duplicate_run", "lock_run"} <= called)
		self.assertIn("normcore.api.costing.lock_run", _t(FORM))
		for fn in called | {"lock_run", "compare_runs"}:
			self.assertRegex(API, rf"@frappe.whitelist\(\)\ndef {fn}\(")

	def test_form_nut_va_trang_thai(self):
		t = _t(FORM)
		for s in (
			'__("Duplicate")',
			'__("Check reproduction")',
			'__("Compare with another run")',
			"COMPARE_REPORT",
			"disable_form",
			"snapshot_hash",
		):
			self.assertIn(s, t)
		self.assertIn('role="alert"', t)
		self.assertIn("escape_html", t)

	def test_report_json_dung_bon_vai_tro(self):
		d = json.loads(_t(REPORT / "nc_costing_run_comparison.json"))
		self.assertEqual(
			sorted(r["role"] for r in d["roles"]), ["NC Admin", "NC Auditor", "NC Director", "NC Finance"]
		)
		self.assertEqual((d["ref_doctype"], d["report_type"]), ("NC Costing Run", "Script Report"))

	def test_TC_COST_18_doctype_cap_quyen_report(self):
		d = json.loads(_t(FORM.with_suffix(".json")))
		perms = {p["role"]: p for p in d["permissions"]}
		for role in ("NC Finance", "NC Director", "NC Admin", "NC Auditor"):
			self.assertEqual(perms[role].get("report"), 1, role)
		self.assertNotIn("NC Clinician", perms)

	def test_report_bo_loc_va_cay(self):
		t = _t(REPORT / "nc_costing_run_comparison.js")
		for f in ("base_run", "other_run", "only_changed", "technical_service"):
			self.assertIn(f'fieldname: "{f}"', t)
		self.assertIn("tree: true", t)
		self.assertIn("initial_depth: 0", t)

	def test_doctype_truong_anh_chup(self):
		d = json.loads(_t(ROOT / "nc_costing" / "doctype" / "nc_costing_run" / "nc_costing_run.json"))
		f = {x["fieldname"]: x for x in d["fields"]}
		for k in ("snapshot_file", "snapshot_hash"):
			self.assertEqual((f[k].get("read_only"), f[k].get("no_copy")), (1, 1), k)
		for k in ("progress", "allocation_warnings"):
			self.assertEqual(f[k].get("no_copy"), 1, k)
