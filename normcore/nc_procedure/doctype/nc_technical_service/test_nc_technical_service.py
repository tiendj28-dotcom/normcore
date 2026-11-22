import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import ensure, make_user


def _dept(code):
	ensure("NC Cost Center", "cost_center_code", code, cost_center_name=f"TT {code}", center_type="Lâm sàng")
	return ensure(
		"NC Department",
		"department_code",
		code,
		department_name=f"Khoa {code}",
		department_type="Lâm sàng",
		cost_center=code,
	).name


def _service(code="DV-S05", **kw):
	return frappe.get_doc(
		{"doctype": "NC Technical Service", "service_code": code, "service_name": "Dịch vụ thử", **kw}
	)


class TestNCTechnicalService(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.k01, self.k02 = _dept("K01"), _dept("K02")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_SVC_04_nhieu_khoa(self):
		svc = _service().insert()
		svc.append("departments", {"department": "K01"})
		svc.save()
		svc.append("departments", {"department": "K02"})
		svc.save()
		rows = frappe.get_all(
			"NC Service Department",
			{"parent": svc.name, "parenttype": "NC Technical Service"},
			pluck="department",
			order_by="idx",
		)
		self.assertEqual(rows, ["K01", "K02"])
		self.assertEqual(
			[d.department for d in frappe.get_doc("NC Technical Service", svc.name).departments],
			["K01", "K02"],
		)

	def test_FR_SVC_003_trung_khoa_bi_tu_choi(self):
		svc = _service(departments=[{"department": "K01"}, {"department": "K01"}])
		with self.assertRaises(frappe.ValidationError) as ctx:
			svc.insert()
		self.assertIn("K01", str(ctx.exception))

	def test_FR_SVC_003_vai_tro_chi_doc_khong_sua(self):
		_service().insert()
		users = {
			r: make_user(f"svc.ro{i}@normcore.test", r) for i, r in enumerate(("NC Finance", "NC Auditor"))
		}
		for role, email in users.items():
			frappe.set_user(email)
			doc = frappe.get_doc("NC Technical Service", "DV-S05")
			doc.append("departments", {"department": "K01"})
			self.assertRaises(frappe.PermissionError, doc.save)

	def test_FR_SVC_001_gan_chuyen_khoa(self):
		ensure("NC Specialty", "specialty_code", "CK-S05", specialty_name="CK thử")
		svc = _service(specialty="CK-S05").insert()
		self.assertEqual(frappe.db.get_value("NC Technical Service", svc.name, "specialty"), "CK-S05")
