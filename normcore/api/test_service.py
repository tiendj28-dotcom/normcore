import json

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api.service import get_chain_status
from normcore.install import ROLES
from normcore.tests.utils import ensure, make_base, make_chain_data, make_user

K, K2 = "K-CH1", "K-CH2"
MONEY_KEYS = ("direct_labor", "full_cost", "calculated_price", "rounded_price", "amount")
KEYS = ["procedure", "norm_set", "cost", "price"]


def _states(res):
	return [i["state"] for i in res["items"]]


class ChainBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, _, self.job = make_base(service="DV-CH1", department=K)
		make_base(service="DV-CH2", department=K2)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _assign(self, svc, *depts):
		frappe.db.set_value(
			"NC Technical Service",
			svc,
			"modified",
			frappe.db.get_value("NC Technical Service", svc, "modified"),
		)
		doc = frappe.get_doc("NC Technical Service", svc)
		for d in depts:
			doc.append("departments", {"department": d})
		doc.save()


class TestChainStatus(ChainBase):
	def test_FR_SVC_004_chua_co_gi(self):
		res = get_chain_status(self.service)
		self.assertEqual([i["key"] for i in res["items"]], KEYS)
		self.assertEqual(_states(res), ["empty"] * 4)

	def test_FR_SVC_004_theo_khoa(self):
		self._assign(self.service, K, K2)
		data = make_chain_data(self.service, K, self.job)
		# bộ định mức Nháp và quy trình Nháp của khoa K2 không được chọn
		from normcore.tests.utils import make_procedure

		make_procedure(self.service, K2, job=self.job)
		res = get_chain_status(self.service)
		proc, norm = res["items"][0], res["items"][1]
		self.assertEqual([r["department"] for r in proc["rows"]], [K, K2])
		self.assertEqual([r["state"] for r in proc["rows"]], ["ok", "empty"])
		self.assertEqual(proc["rows"][0]["name"], data.procedure)
		self.assertEqual(norm["rows"][0]["name"], data.norm_set)
		# khoa có dữ liệu ngoài `departments` vẫn được liệt kê
		other = make_base(service=self.service, department="K-CH3")[1]
		make_chain_data(self.service, other, self.job)
		depts = [r["department"] for r in get_chain_status(self.service)["items"][0]["rows"]]
		self.assertEqual(depts, [K, K2, other])

	def test_FR_SVC_004_quyen_theo_vai_tro(self):
		make_chain_data(self.service, K, self.job)
		self._assign(self.service, K)
		expected = {
			"NC Finance": ["ok", "ok", "ok", "empty"],
			"NC Director": ["ok", "ok", "ok", "empty"],
			"NC Admin": ["ok", "ok", "ok", "empty"],
			"NC Auditor": ["ok", "ok", "ok", "empty"],
			"NC Clinician": ["ok", "ok", "no_permission", "empty"],
			"NC Department Head": ["ok", "ok", "no_permission", "empty"],
			"NC Resource Manager": ["ok", "ok", "no_permission", "empty"],
			"NC Consultant": ["ok", "ok", "no_permission", "empty"],
			"NC Document Controller": ["ok", "no_permission", "no_permission", "empty"],
			"NC Council Member": ["ok", "no_permission", "no_permission", "empty"],
		}
		self.assertEqual(set(expected), set(ROLES))
		users = {r: make_user(f"chain.{i}@normcore.test", r) for i, r in enumerate(ROLES)}
		for role in ("NC Clinician", "NC Department Head"):
			access.assign_department(users[role], K)
		for role, email in users.items():
			frappe.set_user(email)
			self.assertEqual(_states(get_chain_status(self.service)), expected[role], role)

	def test_FR_ACC_005_khong_lo_thong_tin(self):
		self._assign(self.service, K)
		clin = make_user("chain.clin2@normcore.test", "NC Clinician")
		access.assign_department(clin, K2)
		frappe.set_user(clin)
		without = get_chain_status(self.service)["items"][1]
		frappe.set_user("Administrator")
		data = make_chain_data(self.service, K, self.job)
		frappe.set_user(clin)
		res = get_chain_status(self.service)
		self.assertEqual(res["items"][1], without)
		self.assertEqual(res["items"][1]["state"], "no_permission")
		self.assertEqual(res["items"][1]["rows"], [])
		dumped = json.dumps(res, ensure_ascii=False)
		self.assertNotIn(data.norm_set, dumped)
		self.assertNotIn(data.cost, dumped)
		self.assertNotIn(data.run, dumped)

	def test_FR_SVC_004_khong_hien_tien(self):
		make_chain_data(self.service, K, self.job)
		for role in ("NC Finance", "NC Director", "NC Auditor", "NC Clinician"):
			frappe.set_user("Administrator")
			frappe.set_user(make_user(f"chain.m.{role[3:6]}@normcore.test", role))
			text = json.dumps(get_chain_status(self.service))
			for k in MONEY_KEYS:
				self.assertNotIn(k, text)
		frappe.set_user("Administrator")
		frappe.set_user(make_user("chain.fin3@normcore.test", "NC Finance"))
		cost = get_chain_status(self.service)["items"][2]
		self.assertEqual(cost["badges"], [{"label": "Giả định — chờ xác nhận", "indicator": "yellow"}])

	def test_FR_ACC_005_tu_choi(self):
		self.assertRaises(frappe.DoesNotExistError, get_chain_status, "KHONG-CO-DV")
		frappe.set_user(make_user("chain.norole@normcore.test"))
		self.assertRaises(frappe.PermissionError, get_chain_status, self.service)
		self.assertRaises(frappe.PermissionError, get_chain_status, "KHONG-CO-DV")

	def test_FR_ACC_005_ham_duoc_whitelist_khong_guest(self):
		self.assertIn(get_chain_status, frappe.whitelisted)
		self.assertNotIn(get_chain_status, frappe.guest_methods)
