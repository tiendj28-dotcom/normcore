"""FEAT-038: NC AI Norm Suggestion (FR-AI-005, FR-AI-017; AMD-038-01; data-model mục 4)."""

import json
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.cls_norm_ai_fixtures import (
	QUOTE_A,
	make_glu_a,
	make_manufacturer_doc,
	make_suggestion,
	suggestion_values,
)

ROOT = Path(__file__).resolve().parents[4]


class TestNCAINormSuggestion(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_glu_a()
		self.doc, self.sec = make_manufacturer_doc("HG-GLU-1.0", [("NC Item", "HC_GLU")])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _cited(self, **kw):
		return suggestion_values(
			relation="Theo hướng dẫn", legal_section=self.sec.name, quote=QUOTE_A, **kw
		)

	def test_FR_AI_005_trich_dan_de_xuat_nguyen_van(self):
		doc = frappe.get_doc(self._cited()).insert(ignore_permissions=True)
		self.assertTrue(doc.name.startswith("AINS-"))
		self.assertEqual(doc.status, "Đề xuất")
		self.assertTrue(doc.department)
		bad = self._cited()
		bad["quote"] = "Đoạn này không có trong tài liệu"
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(bad).insert(ignore_permissions=True)
		# "Theo hướng dẫn" thiếu mục hoặc đoạn trích
		for drop in ("legal_section", "quote"):
			v = self._cited()
			v.pop(drop)
			with self.assertRaises(frappe.ValidationError, msg=drop):
				frappe.get_doc(v).insert(ignore_permissions=True)
		# Chưa có căn cứ: không cần mục
		self.assertEqual(make_suggestion().relation, "Chưa có căn cứ")

	def test_FR_AI_005_trang_thai_khong_quay_lai(self):
		doc = make_suggestion()
		doc.status = "Đã chấp nhận"
		doc.save(ignore_permissions=True)
		doc.status = "Đề xuất"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		doc.reload()
		doc.status = "Đã bỏ"
		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError):
			make_suggestion(status="Đã chấp nhận")

	def test_FR_AI_018_co_resource_tat_not_in_catalog(self):
		doc = make_suggestion(not_in_catalog=1)
		self.assertEqual(doc.not_in_catalog, 0)
		doc = make_suggestion(resource_doctype=None, resource=None, not_in_catalog=1, resource_text="X")
		self.assertEqual(doc.not_in_catalog, 1)

	def test_quyen_nc_ai_norm_suggestion_doctype(self):
		meta = json.loads(
			(ROOT / "normcore/nc_costing/doctype/nc_ai_norm_suggestion/nc_ai_norm_suggestion.json").read_text()
		)
		perms = {p["role"]: p for p in meta["permissions"]}
		self.assertNotIn("NC Council Member", perms)
		self.assertNotIn("NC Document Controller", perms)
		for role in ("NC Clinician", "NC Department Head"):
			self.assertTrue(perms[role].get("write") and perms[role].get("create"))
		for role in ("NC Finance", "NC Resource Manager", "NC Director", "NC Consultant", "NC Admin", "NC Auditor"):
			self.assertEqual(perms[role].get("read"), 1, role)
			self.assertFalse(perms[role].get("write") or perms[role].get("create"), role)
		self.assertFalse(any(p.get("delete") for p in meta["permissions"]))
		scope = json.loads((ROOT / "normcore/core/scope_rules/nc_ai_norm_suggestion.json").read_text())
		self.assertEqual(scope["department_field"], "department")
		self.assertEqual(scope["public_read"], {})
		self.assertNotIn("via", scope)
