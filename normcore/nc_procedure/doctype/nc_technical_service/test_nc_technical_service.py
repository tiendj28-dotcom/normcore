import io

import frappe
from openpyxl import Workbook, load_workbook
from frappe.tests.utils import FrappeTestCase

from normcore.api import importer as api
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


KEY = "nc_technical_service"
HEAD = ["Mã dịch vụ *", "Tên dịch vụ *", "Chuyên khoa"]


def _xlsx(rows):
	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


class TestServiceImport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.dc = make_user("dc.svc@normcore.test", "NC Document Controller")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _file10(self):
		rows = [HEAD] + [[f"SVC0{i}", f"Dịch vụ {i}", None] for i in range(1, 8)]
		rows += [["SVC08", None, None], ["SVC01", "Lặp 1", None], ["SVC02", "Lặp 2", None]]
		return _xlsx(rows)

	def test_TC_SVC_01_nhap_danh_muc(self):
		frappe.set_user(self.dc)
		before = frappe.db.count("NC Technical Service")
		thu = api.run_import(KEY, self._file10(), "thu")
		self.assertEqual(thu["created"], 7)
		self.assertEqual(frappe.db.count("NC Technical Service"), before)
		ghi = api.run_import(KEY, self._file10(), "ghi")
		self.assertEqual((ghi["created"], ghi["updated"]), (7, 0))
		self.assertEqual(frappe.db.count("NC Technical Service"), before + 7)
		self.assertEqual(frappe.db.get_value("NC Technical Service", "SVC01", "service_name"), "Dịch vụ 1")
		self.assertEqual(frappe.db.get_value("NC Technical Service", "SVC02", "service_name"), "Dịch vụ 2")
		self.assertEqual(
			[e["text"] for e in ghi["errors"]],
			[
				'Dòng 9, cột "Tên dịch vụ": ô bắt buộc đang để trống',
				'Dòng 10, cột "Mã dịch vụ": trùng khóa "SVC01" với dòng 2 trong cùng tệp',
				'Dòng 11, cột "Mã dịch vụ": trùng khóa "SVC02" với dòng 3 trong cùng tệp',
			],
		)

	def test_FR_SVC_001_tai_mau_nhap_lai(self):
		frappe.set_user(self.dc)
		_, content = api.build_template_file(KEY)
		rows = list(load_workbook(io.BytesIO(content)).active.iter_rows(values_only=True))
		self.assertEqual(list(rows[0]), HEAD)
		first = api.run_import(KEY, content, "ghi")
		self.assertEqual((first["created"], first["error_count"]), (1, 0))
		again = api.run_import(KEY, content, "ghi")
		self.assertEqual((again["unchanged"], again["created"], again["error_count"]), (1, 0, 0))

	def test_FR_SVC_001_cap_nhat_theo_ma(self):
		ensure("NC Specialty", "specialty_code", "CK-I1", specialty_name="CK 1")
		_dept("K01")
		_service("SVC-U1", departments=[{"department": "K01"}], is_active=0).insert()
		frappe.set_user(self.dc)
		res = api.run_import(KEY, _xlsx([HEAD, ["SVC-U1", "Tên mới", "CK-I1"]]), "ghi")
		self.assertEqual((res["updated"], res["created"], res["error_count"]), (1, 0, 0))
		doc = frappe.get_doc("NC Technical Service", "SVC-U1")
		self.assertEqual((doc.service_name, doc.specialty), ("Tên mới", "CK-I1"))
		self.assertEqual([d.department for d in doc.departments], ["K01"])
		self.assertEqual(doc.is_active, 0)

	def test_FR_SVC_001_chuyen_khoa_la(self):
		frappe.set_user(self.dc)
		res = api.run_import(KEY, _xlsx([HEAD, ["SVC-L1", "A", "CK-LA"], ["SVC-L2", "B", None]]), "ghi")
		self.assertEqual(res["created"], 1)
		self.assertEqual(
			res["errors"][0]["text"], 'Dòng 2, cột "Chuyên khoa": "CK-LA" không tồn tại trong NC Specialty'
		)
		self.assertFalse(frappe.db.exists("NC Specialty", "CK-LA"))
		self.assertTrue(frappe.db.exists("NC Technical Service", "SVC-L2"))

	def test_FR_SVC_002_thieu_ma(self):
		frappe.set_user(self.dc)
		res = api.run_import(KEY, _xlsx([HEAD, [None, "Không mã", None], ["SVC-M1", "Có mã", None]]), "ghi")
		self.assertEqual(res["created"], 1)
		self.assertEqual(res["errors"][0]["text"], 'Dòng 2, cột "Mã dịch vụ": ô bắt buộc đang để trống')

	def test_FR_SVC_001_vai_tro_chi_doc_bi_tu_choi(self):
		users = [
			make_user("fin.svc@normcore.test", "NC Finance"),
			make_user("aud.svc@normcore.test", "NC Auditor"),
		]
		for u in users:
			frappe.set_user(u)
			self.assertRaises(
				frappe.PermissionError, api.run_import, KEY, _xlsx([HEAD, ["X1", "X", None]]), "ghi"
			)
