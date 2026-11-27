"""FEAT-028 T03: NC Adjustment Suggestion (FR-ADJ-005, 008; FR-ACC-003, 007)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import costing as api
from normcore.core import permissions
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_base, make_user

DOCTYPE = "NC Adjustment Suggestion"
COST = "NC Service Cost"


def suggestion_values(service_cost, **kw):
	base = {
		"doctype": DOCTYPE,
		"service_cost": service_cost,
		"rule_code": "BR-ADJ-001",
		"direction": "Giảm",
		"component": "EQUIPMENT",
		"target_ref": "EQ1",
		"current_value": "0,4",
		"suggested_value": "0,5",
		"estimated_impact": -15411.93,
	}
	base.update(kw)
	return base


class TestNCAdjustmentSuggestion(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fin = make_user("fin.n81@normcore.test", "NC Finance")
		self.aud = make_user("aud.n81@normcore.test", "NC Auditor")
		self.dir = make_user("dir.n81@normcore.test", "NC Director")
		self.head = make_user("head.n81@normcore.test", "NC Department Head")
		self.clin = make_user("clin.n81@normcore.test", "NC Clinician")
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.run = cf.make_golden_run(self.params)
		frappe.set_user(self.fin)
		api.start_costing(self.run.name)
		frappe.set_user("Administrator")
		self.cost = frappe.get_value(COST, {"costing_run": self.run.name, "technical_service": "DV-TEST-A"})

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _make(self, **kw):
		doc = frappe.get_doc(suggestion_values(self.cost, **kw))
		doc.flags.adj_system = True
		return doc.insert(ignore_permissions=True)

	def test_quyen_clinician_khong_doc(self):
		doc = self._make()
		permissions.assign_department(self.clin, self.dept)
		frappe.set_user(self.clin)
		self.assertFalse(frappe.has_permission(DOCTYPE, "read", doc=doc))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(DOCTYPE, doc.name).check_permission("read")

	def test_quyen_auditor_chi_doc(self):
		doc = self._make()
		frappe.set_user(self.aud)
		self.assertTrue(frappe.has_permission(DOCTYPE, "read", doc=doc))
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission(DOCTYPE, ptype), ptype)
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(suggestion_values(self.cost)).insert()
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.current_value = "x"
		with self.assertRaises(frappe.PermissionError):
			d.save()

	def test_quyen_truong_khoa_theo_khoa(self):
		doc = self._make()
		make_base("DV-N81-X", "KHOA-N81-X")
		permissions.assign_department(self.head, "KHOA-N81-X")
		frappe.set_user(self.head)
		self.assertFalse(frappe.has_permission(DOCTYPE, "read", doc=doc))
		self.assertEqual(frappe.get_list(DOCTYPE, pluck="name"), [])
		frappe.set_user("Administrator")
		permissions.assign_department(self.head, self.dept)
		frappe.set_user(self.head)
		self.assertTrue(frappe.has_permission(DOCTYPE, "read", doc=doc))
		self.assertEqual(frappe.get_list(DOCTYPE, pluck="name"), [doc.name])
		self.assertFalse(frappe.has_permission(DOCTYPE, "write", doc=doc))
		self.assertFalse(frappe.has_permission(DOCTYPE, "delete", doc=doc))

	def test_quyen_theo_ma_tran(self):
		doc = self._make()
		readers = {"NC Finance", "NC Director", "NC Consultant", "NC Admin", "NC Auditor"}
		from normcore.install import ROLES

		users = {r: make_user(f"n81.perm{i}@normcore.test", r) for i, r in enumerate(ROLES)}
		for role, user in users.items():
			if role in ("NC Clinician", "NC Department Head"):
				continue
			frappe.set_user(user)
			self.assertEqual(bool(frappe.has_permission(DOCTYPE, "read", doc=doc)), role in readers, role)
			self.assertEqual(bool(frappe.has_permission(DOCTYPE, "create")), role == "NC Finance", role)
			self.assertFalse(frappe.has_permission(DOCTYPE, "delete"), role)

	def test_quyen_finance_tao(self):
		frappe.set_user(self.fin)
		doc = frappe.get_doc(suggestion_values(self.cost)).insert()
		self.assertEqual(doc.status, "Mới")
		# Finance không tự đặt trạng thái đã quyết khi tạo: luôn là "Mới"
		d = frappe.get_doc(suggestion_values(self.cost, status="Chấp nhận", target_ref="EQ2")).insert()
		self.assertEqual(d.status, "Mới")

	def test_FR_ADJ_008_validate_tu_choi_can_ly_do(self):
		doc = self._make()
		doc.flags.adj_decision = True
		doc.status = "Từ chối"
		doc.decision_reason = "   "
		with self.assertRaises(frappe.ValidationError) as ctx:
			doc.save(ignore_permissions=True)
		self.assertIn("nêu lý do", str(ctx.exception))
		doc = frappe.get_doc(DOCTYPE, doc.name)
		doc.flags.adj_decision = True
		doc.status = "Từ chối"
		doc.decision_reason = "Không khả thi"
		doc.save(ignore_permissions=True)
		self.assertEqual(frappe.db.get_value(DOCTYPE, doc.name, "status"), "Từ chối")

	def test_sua_ngoai_api_bi_chan(self):
		doc = self._make()
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.status = "Chấp nhận"
		with self.assertRaises(frappe.ValidationError):
			d.save(ignore_permissions=True)
		# đã quyết thì không sửa được nữa, kể cả có cờ
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.flags.adj_decision = True
		d.status = "Chấp nhận"
		d.save(ignore_permissions=True)
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.flags.adj_decision = True
		d.status = "Từ chối"
		d.decision_reason = "đổi ý"
		with self.assertRaises(frappe.ValidationError):
			d.save(ignore_permissions=True)

	def test_quy_tac_khong_hop_le(self):
		with self.assertRaises(frappe.ValidationError):
			self._make(rule_code="BR-ADJ-009")
