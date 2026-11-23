"""Quyền theo data-model mục 4 cho 30 DocType: vai trò ngoài ma trận bị từ chối; NC Auditor chỉ đọc (FR-ACC-007, TC-ACC-04)."""

import json
from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.install import ROLES
from normcore.tests.utils import make_user

APP = Path(frappe.get_app_path("normcore"))
DOCTYPES = [
	json.loads(p.read_text(encoding="utf-8"))
	for p in sorted(APP.glob("nc_*/doctype/*/*.json"))
	if p.stem == p.parent.name
]
PARENTS = [d for d in DOCTYPES if not d.get("istable")]


class TestPermissions(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")

	def test_co_30_doctype_va_10_vai_tro(self):
		self.assertEqual(len(DOCTYPES), 30)
		for r in ROLES:
			self.assertTrue(frappe.db.exists("Role", r), r)

	def test_quyen_theo_vai_tro(self):
		users = {r: make_user(f"perm.{i}@normcore.test", r) for i, r in enumerate(ROLES)}
		for d in PARENTS:
			granted = {p["role"]: p for p in d["permissions"]}
			self.assertNotIn("All", granted, d["name"])
			for role, email in users.items():
				frappe.set_user(email)
				for ptype in ("read", "write", "create", "delete"):
					expected = bool(granted.get(role, {}).get(ptype))
					got = bool(frappe.has_permission(d["name"], ptype))
					self.assertEqual(got, expected, f"{d['name']} {role} {ptype}")

	def test_auditor_chi_doc_duoc(self):
		auditor = make_user("auditor.perm@normcore.test", "NC Auditor")
		frappe.set_user(auditor)
		for d in PARENTS:
			self.assertTrue(frappe.has_permission(d["name"], "read"), d["name"])
			for ptype in ("write", "create", "delete"):
				self.assertFalse(frappe.has_permission(d["name"], ptype), f"{d['name']} {ptype}")
