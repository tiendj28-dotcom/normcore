import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import Workbook, load_workbook

from normcore.api import importer as api
from normcore.tests.utils import ensure, make_base, make_chain_data, make_user


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
		for email in users.values():
			frappe.set_user(email)
			doc = frappe.get_doc("NC Technical Service", "DV-S05")
			doc.append("departments", {"department": "K01"})
			self.assertRaises(frappe.PermissionError, doc.save)

	def test_TC_SVC_03_tinh_trang_chuoi(self):
		from normcore.api.service import get_chain_status

		service, dept, job = make_base(service="DV-S03", department="K-S03")
		data = make_chain_data(service, dept, job)
		frappe.set_user(make_user("fin.s03@normcore.test", "NC Finance"))
		res = get_chain_status(service)
		self.assertEqual([i["key"] for i in res["items"]], ["procedure", "norm_set", "cost", "price"])
		for item in res["items"]:
			self.assertTrue(item["links"], item["key"])
		self.assertIn(f"/app/nc-clinical-procedure/{data.procedure}", res["items"][0]["links"])
		self.assertIn(f"/app/nc-norm-set/{data.norm_set}", res["items"][1]["links"])
		self.assertIn(f"/app/nc-service-cost/{data.cost}", res["items"][2]["links"])
		self.assertEqual(res["items"][3]["links"], ["#nc-chain-price"])

	def test_SCR_DSK_005_loc_danh_sach(self):
		ensure("NC Specialty", "specialty_code", "CK-F1", specialty_name="CK lọc")
		_service(
			"DV-F1", specialty="CK-F1", departments=[{"department": "K01"}, {"department": "K02"}]
		).insert()
		_service("DV-F2", departments=[{"department": "K02"}]).insert()
		got = frappe.get_list(
			"NC Technical Service",
			filters=[["NC Service Department", "department", "=", "K01"]],
			pluck="name",
		)
		self.assertEqual(got, ["DV-F1"])
		both = frappe.get_list(
			"NC Technical Service",
			filters=[["NC Service Department", "department", "=", "K02"]],
			pluck="name",
		)
		self.assertEqual(sorted(both), ["DV-F1", "DV-F2"])
		self.assertEqual(
			frappe.get_list("NC Technical Service", filters={"specialty": "CK-F1"}, pluck="name"), ["DV-F1"]
		)

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

	# --- FEAT-031: khối cận lâm sàng ---

	def test_TC_CLS_20_danh_dau_can_lam_sang_yeu_cau_nhom_va_don_vi(self):
		svc = _service("GLU", is_paraclinical=1)
		with self.assertRaises(frappe.ValidationError) as ctx:
			svc.insert()
		self.assertIn("Nhóm chuyên ngành", str(ctx.exception))
		svc.cls_group = "Hóa sinh"
		with self.assertRaises(frappe.ValidationError) as ctx:
			svc.insert()
		self.assertIn("Đơn vị kết quả", str(ctx.exception))
		svc.result_unit = "Kết quả xét nghiệm"
		svc.insert()
		self.assertEqual(frappe.db.get_value("NC Technical Service", "GLU", "cls_group"), "Hóa sinh")

	def test_TC_CLS_20_khong_can_lam_sang_khong_bat_buoc(self):
		svc = _service("DV-KCLS").insert()
		self.assertEqual(svc.is_paraclinical, 0)
		self.assertFalse(svc.cls_group)

	def test_TC_CLS_21_ma_ngoai_gan_hai_dich_vu_bi_tu_choi(self):
		glu = _service("GLU", external_codes=[{"source_system": "LIS", "external_code": "L100"}]).insert()
		self.assertEqual(len(glu.external_codes), 1)
		other = _service("DV-OTHER", external_codes=[{"source_system": "LIS", "external_code": "L100"}])
		with self.assertRaises(frappe.ValidationError) as ctx:
			other.insert()
		self.assertIn("GLU", str(ctx.exception))
		self.assertIn("L100", str(ctx.exception))
		spaced = _service("DV-OTHER2", external_codes=[{"source_system": "LIS", "external_code": " l100 "}])
		with self.assertRaises(frappe.ValidationError):
			spaced.insert()
		_service("DV-OTHER3", external_codes=[{"source_system": "HIS", "external_code": "L100"}]).insert()

	def test_TC_CLS_21_lap_trong_cung_dich_vu(self):
		svc = _service(
			"DV-DUP",
			external_codes=[
				{"source_system": "LIS", "external_code": "L7"},
				{"source_system": "LIS", "external_code": "L7"},
			],
		)
		self.assertRaises(frappe.ValidationError, svc.insert)

	def test_TC_CLS_21_chi_muc_duy_nhat_o_co_so_du_lieu(self):
		_service("GLU", external_codes=[{"source_system": "LIS", "external_code": "L100"}]).insert()
		other = _service("DV-OTHER").insert()
		row = frappe.get_doc(
			{
				"doctype": "NC Service Code Map",
				"parent": other.name,
				"parenttype": "NC Technical Service",
				"parentfield": "external_codes",
				"source_system": "LIS",
				"external_code": "L100",
			}
		)
		with self.assertRaises(frappe.UniqueValidationError):
			row.insert(ignore_permissions=True)

	def test_FR_SVC_010_dich_vu_bo(self):
		svc = _service(
			"DV-BO", is_paraclinical=1, cls_group="Hóa sinh", result_unit="Kết quả xét nghiệm", is_panel=1
		)
		with self.assertRaises(frappe.ValidationError):
			svc.insert()
		svc.append("panel_components", {"parameter_code": "NA", "parameter_name": "Natri"})
		svc.append("panel_components", {"parameter_code": "K", "parameter_name": "Kali"})
		svc.insert()
		self.assertEqual(svc.panel_costing_mode, "Theo từng thông số")
		svc.append("panel_components", {"parameter_code": "na", "parameter_name": "Natri 2"})
		self.assertRaises(frappe.ValidationError, svc.save)

	def test_FR_SVC_011_gui_ngoai_can_gia(self):
		svc = _service(
			"DV-NGOAI",
			is_paraclinical=1,
			cls_group="Vi sinh",
			result_unit="Kết quả xét nghiệm",
			is_send_out=1,
		)
		self.assertRaises(frappe.ValidationError, svc.insert)
		svc.send_out_price = 150000
		svc.insert()
		self.assertEqual(svc.send_out_price, 150000)
