"""FEAT-030: API phương án giá (FR-PRICE-001..010, FR-OUT-007)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import price_compare
from normcore.api import price_proposal as api
from normcore.benchmark import proposal as pr
from normcore.tests import proposal_fixtures as pf
from normcore.tests.utils import make_user

DT = "NC Price Proposal"


class ProposalCase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fin = make_user(pf.FIN_USER, "NC Finance")
		self.aud = make_user("aud.n84@normcore.test", "NC Auditor")
		self.dir = make_user("dir.n84@normcore.test", "NC Director")
		self.head = make_user("head.n84@normcore.test", "NC Department Head")
		self.cons = make_user("cons.n84@normcore.test", "NC Consultant")
		self.run, self.params, self.dept = pf.make_locked_golden_run(self.fin)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _create(self, **kw):
		frappe.set_user(self.fin)
		name = api.create_proposal(self.run.name, **kw)["name"]
		frappe.set_user("Administrator")
		return name

	def _item(self, name, service):
		return next(i for i in frappe.get_doc(DT, name).items if i.technical_service == service)


class TestProposalCreate(ProposalCase):
	def test_TC_PRICE_01_lap_tu_lan_tinh_khoa(self):
		name = self._create()
		frappe.set_user(self.fin)
		data = api.get_proposal(name)
		frappe.set_user("Administrator")
		items = {i["technical_service"]: i for i in data["items"]}
		self.assertEqual(len(items), 2)
		self.assertEqual(float(items["DV-TEST-A"]["proposed_price"]), 302100)
		self.assertEqual(float(items["DV-TEST-B"]["proposed_price"]), 92600)
		self.assertEqual(float(items["DV-TEST-A"]["full_cost"]), 287745.46)
		for i in items.values():
			self.assertEqual(float(i["proposed_price"]), float(i["rounded_price"]))
			self.assertEqual(i["below_cost"], 0)
		self.assertEqual(data["doc"]["workflow_state"], pr.DRAFT)
		self.assertEqual(data["approval_authority"], "Bệnh viện")
		# trung vị tham chiếu khớp thống kê của Bàn so sánh giá (FEAT-028)
		frappe.set_user(self.fin)
		cmp = {r["technical_service"]: r for r in price_compare.get_comparison(self.run.name)["rows"]}
		frappe.set_user("Administrator")
		for svc, i in items.items():
			self.assertEqual(i["benchmark_count"], cmp[svc]["count"])
			self.assertEqual(i["benchmark_median"] or None, cmp[svc]["median"])  # Currency rỗng lưu 0
		self.assertEqual(data["summary"], {"count": 2, "adjusted": 0, "below_cost": 0, "unacked": 0})

	def test_TC_PRICE_01_lan_tinh_chua_khoa_bi_tu_choi(self):
		frappe.db.set_value("NC Costing Run", self.run.name, "status", "Đã tính")
		frappe.set_user(self.fin)
		with self.assertRaises(frappe.ValidationError):
			api.create_proposal(self.run.name)

	def test_tao_phuong_an_can_quyen(self):
		for user in (self.aud, self.dir, self.cons, self.head):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.create_proposal(self.run.name)

	def test_get_proposal_can_quyen_doc(self):
		name = self._create()
		clin = make_user("clin.n84@normcore.test", "NC Clinician")
		frappe.set_user(clin)
		with self.assertRaises(frappe.PermissionError):
			api.get_proposal(name)
