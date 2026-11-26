"""Danh sách cho phép nguồn gửi AI (FR-AI-011, ADR-007): thuần, không cần site."""

import json
import pathlib
import unittest

from normcore.ai import guard

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _all_nc_doctypes():
	names = set()
	for p in ROOT.glob("nc_*/doctype/*/*.json"):
		try:
			d = json.loads(p.read_text(encoding="utf-8"))
		except ValueError:
			continue
		if d.get("doctype") == "DocType" and str(d.get("name", "")).startswith("NC "):
			names.add(d["name"])
	return names


class TestAIGuard(unittest.TestCase):
	def test_TC_AI_06_tu_choi_moi_doctype_ke_toan_tinh_gia(self):
		self.assertTrue(guard.FORBIDDEN_DOCTYPES)
		for dt in sorted(guard.FORBIDDEN_DOCTYPES):
			with self.subTest(doctype=dt):
				self.assertFalse(guard.is_allowed(dt))
				with self.assertRaises(guard.GuardError):
					guard.build_source(dt, {"name": "X"})

	def test_TC_AI_06_quet_moi_doctype_nc_ngoai_danh_sach_cho_phep(self):
		found = _all_nc_doctypes()
		self.assertIn("NC Item Price", found)
		for dt in sorted(found - set(guard.ALLOWED_SOURCES)):
			with self.subTest(doctype=dt):
				with self.assertRaises(guard.GuardError):
					guard.build_source(dt, {"name": "X"})

	def test_TC_AI_06_doctype_la_bi_tu_choi(self):
		with self.assertRaises(guard.GuardError):
			guard.build_source("ToDo", {"name": "x"})

	def test_TC_AI_06_hai_tap_roi_nhau(self):
		self.assertEqual(set(guard.ALLOWED_SOURCES) & guard.FORBIDDEN_DOCTYPES, set())
		self.assertEqual(
			set(guard.ALLOWED_SOURCES),
			{"NC Legal Section", "NC Technical Service", "NC Clinical Procedure", "NC Item", "NC Equipment"},
		)

	def test_TC_AI_06_doctype_duoc_phep_chi_tra_truong_cho_phep(self):
		rec = {
			"name": "EQ-1",
			"equipment_code": "EQ-1",
			"equipment_name": "Máy A",
			"original_cost": 5_000_000,
			"supplier_note": "x",
		}
		out = guard.build_source("NC Equipment", rec)
		self.assertEqual(out, {"equipment_code": "EQ-1", "equipment_name": "Máy A"})

	def test_TC_AI_06_truong_cam_trong_fields_bi_tu_choi(self):
		with self.assertRaises(guard.GuardError) as cm:
			guard.build_source(
				"NC Equipment", {"equipment_name": "A"}, fields=["equipment_name", "original_cost"]
			)
		self.assertIn("original_cost", str(cm.exception))
		with self.assertRaises(guard.GuardError):
			guard.build_source("NC Item", {}, fields=["price_history_html"])

	def test_TC_AI_06_fields_con_tap_cho_phep(self):
		out = guard.build_source(
			"NC Item", {"item_code": "I1", "item_name": "Găng", "uom": "Đôi"}, fields=["item_name"]
		)
		self.assertEqual(out, {"item_name": "Găng"})

	def test_TC_AI_06_bang_con_duoc_loc(self):
		rec = {
			"name": "P1",
			"overview": "ov",
			"internal_cost": 1,
			"steps": [{"step_id": "S1", "step_title": "t", "unit_price": 9}],
			"resources": [{"resource_text": "găng", "quantity": 2, "unit_price": 100}],
			"other_table": [{"a": 1}],
		}
		out = guard.build_source("NC Clinical Procedure", rec)
		self.assertNotIn("internal_cost", out)
		self.assertNotIn("other_table", out)
		self.assertEqual(out["steps"], [{"step_id": "S1", "step_title": "t"}])
		self.assertEqual(out["resources"], [{"resource_text": "găng", "quantity": 2}])

	def test_budget_exceeded_cac_bien(self):
		# FR-AI-013 "vượt": chỉ chặn khi lũy kế > hạn mức (Lead, ASM-023-04)
		self.assertFalse(guard.budget_exceeded(0, 1000))
		self.assertFalse(guard.budget_exceeded(999, 1000))
		self.assertFalse(guard.budget_exceeded(1000, 1000))
		self.assertTrue(guard.budget_exceeded(1001, 1000))
		self.assertTrue(guard.budget_exceeded(1200, 1000))
		self.assertFalse(guard.budget_exceeded(10**9, 0))

	def test_guard_khong_import_frappe(self):
		src = (ROOT / "ai" / "guard.py").read_text(encoding="utf-8")
		self.assertNotIn("import frappe", src)
