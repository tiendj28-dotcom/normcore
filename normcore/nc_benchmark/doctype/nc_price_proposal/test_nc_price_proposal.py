"""FEAT-030 T03: NC Price Proposal (FR-PRICE-001, FR-ACC-003, 007; DI-07; ADR-011)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.benchmark import proposal as pr
from normcore.benchmark import proposal_setup
from normcore.core import permissions
from normcore.tests import proposal_fixtures as pf
from normcore.tests.utils import make_base, make_user

DOCTYPE = "NC Price Proposal"


class TestNCPriceProposal(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fin = make_user(pf.FIN_USER, "NC Finance")
		self.aud = make_user("aud.n84@normcore.test", "NC Auditor")
		self.dir = make_user("dir.n84@normcore.test", "NC Director")
		self.head = make_user("head.n84@normcore.test", "NC Department Head")
		self.clin = make_user("clin.n84@normcore.test", "NC Clinician")
		self.cons = make_user("cons.n84@normcore.test", "NC Consultant")
		self.run, self.params, self.dept = pf.make_locked_golden_run(self.fin)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _values(self, **kw):
		cost = frappe.get_all(
			"NC Service Cost",
			{"costing_run": self.run.name},
			["technical_service", "department", "full_cost", "calculated_price", "rounded_price"],
			order_by="technical_service",
		)
		items = [
			{**{k: c[k] for k in c}, "proposed_price": c.rounded_price} for c in cost
		]
		base = {"doctype": DOCTYPE, "title": "Phương án thử", "costing_run": self.run.name, "items": items}
		base.update(kw)
		return base

	def _make(self):
		return frappe.get_doc(self._values()).insert(ignore_permissions=True)

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
			frappe.get_doc(self._values()).insert()
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.title = "x"
		with self.assertRaises(frappe.PermissionError):
			d.save()

	def test_quyen_truong_khoa_theo_khoa(self):
		doc = self._make()
		make_base("DV-N84-X", "KHOA-N84-X")
		permissions.assign_department(self.head, "KHOA-N84-X")
		frappe.set_user(self.head)
		self.assertFalse(frappe.has_permission(DOCTYPE, "read", doc=doc))
		self.assertNotIn(doc.name, frappe.get_list(DOCTYPE, pluck="name"))
		frappe.set_user("Administrator")
		permissions.assign_department(self.head, self.dept)
		frappe.set_user(self.head)
		self.assertTrue(frappe.has_permission(DOCTYPE, "read", doc=doc))
		self.assertIn(doc.name, frappe.get_list(DOCTYPE, pluck="name"))
		self.assertFalse(frappe.has_permission(DOCTYPE, "write", doc=doc))

	def test_quyen_consultant_chi_doc(self):
		doc = self._make()
		frappe.set_user(self.cons)
		self.assertTrue(frappe.has_permission(DOCTYPE, "read", doc=doc))
		for ptype in ("write", "create", "delete"):
			self.assertFalse(frappe.has_permission(DOCTYPE, ptype), ptype)

	def test_quyen_finance_tao_xoa_nhap(self):
		frappe.set_user(self.fin)
		doc = frappe.get_doc(self._values()).insert()
		self.assertEqual(doc.workflow_state, pr.DRAFT)
		self.assertEqual(doc.price_category, "PC-GOLD")
		self.assertEqual(len(doc.items), 2)
		self.assertFalse(frappe.has_permission(DOCTYPE, "delete", doc=doc))  # ASM-030-17: không DocPerm xóa

	def test_sua_ngoai_api_bi_chan(self):
		doc = self._make()
		frappe.set_user(self.fin)
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.workflow_state = pr.WAIT_DIRECTOR
		with self.assertRaises(frappe.ValidationError):
			d.save()
		# ngoài "Nháp": sửa nội dung bị chặn, trừ khi do API
		frappe.db.set_value(DOCTYPE, doc.name, "workflow_state", pr.WAIT_DEPT)
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.items[0].proposed_price = 1
		with self.assertRaises(frappe.ValidationError):
			d.save()
		frappe.set_user("Administrator")
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc(DOCTYPE, doc.name)
		frappe.set_user(self.fin)
		d = frappe.get_doc(DOCTYPE, doc.name)
		d.flags.proposal_action = "Gửi duyệt"
		d.items[0].proposed_price = 1
		d.save()

	def test_workflow_khop_transitions(self):
		proposal_setup.ensure_workflow()
		proposal_setup.ensure_workflow()  # idempotent
		wf = frappe.get_doc("Workflow", "NC Price Proposal")
		got = {(t.state, t.action, t.next_state, t.allowed) for t in wf.transitions}
		self.assertEqual(got, set(pr.TRANSITIONS))
		self.assertEqual({s.state for s in wf.states}, set(pr.STATES))
		self.assertEqual(wf.document_type, DOCTYPE)

	def test_auditor_khong_co_transition(self):
		proposal_setup.ensure_workflow()
		self.assertEqual(permissions.read_only_violations(), [])

	def test_lan_tinh_chua_khoa_bi_tu_choi(self):
		frappe.db.set_value("NC Costing Run", self.run.name, "status", "Hoàn tất")
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(self._values()).insert(ignore_permissions=True)

	def test_dong_duoi_gia_thanh_duoc_danh_dau(self):
		vals = self._values()
		vals["items"][0]["proposed_price"] = 280000
		doc = frappe.get_doc(vals).insert(ignore_permissions=True)
		flags = {r.technical_service: r.below_cost for r in doc.items}
		self.assertEqual(flags, {"DV-TEST-A": 1, "DV-TEST-B": 0})
