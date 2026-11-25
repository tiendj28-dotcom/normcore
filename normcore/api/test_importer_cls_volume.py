"""FEAT-035, FR-ACCT-012..015: bộ nhập sản lượng cận lâm sàng, phút khai thác, xuất kho (TC-CLS-34, 35, 36)."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import Workbook, load_workbook

from normcore.api import importer as api
from normcore.core.importer import get_import_set, header_label
from normcore.tests.utils import ensure, make_base, make_cls_data, make_test_system, make_user

TSV, EU, SIA = "nc_test_system_volume", "nc_equipment_usage", "nc_stock_issue_actual"
SETS = (TSV, EU, SIA)
AUX = ("iqc_tests", "calibration_tests", "rerun_tests", "eqa_tests")


def xlsx(rows):
	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def head(key):
	return [header_label(c) for c in get_import_set(key).columns]


def row(key, **vals):
	return [vals.get(c.fieldname) for c in get_import_set(key).columns]


GLU_A = dict(
	fiscal_year=2026,
	scenario="Thực tế 12 tháng",
	test_system="GLU-A",
	source_system="LIS",
	service_code="LIS-GLU",
	department="HS-CLS",
	patient_results=12000,
	iqc_tests=600,
	calibration_tests=48,
	rerun_tests=240,
	eqa_tests=12,
	wastage_rate=3,
	avg_batch_size=40,
	run_days=300,
)
GLU_B = {**GLU_A, "test_system": "GLU-B", "patient_results": 4000} | dict.fromkeys(AUX)
GLU_B.update(wastage_rate=None, avg_batch_size=None, run_days=None)


class TestClsVolumeImport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.service, self.dept, _ = make_cls_data()
		make_test_system("GLU-A", self.service, self.dept, "EQ_A", 75)
		make_test_system("GLU-B", self.service, self.dept, "EQ_B", 25)
		svc = frappe.get_doc("NC Technical Service", self.service)
		svc.append("external_codes", {"source_system": "LIS", "external_code": "LIS-GLU"})
		svc.save()
		make_base(department="XN")
		ensure(
			"NC Item",
			"item_code",
			"HC_GLU",
			item_name="Hóa chất glucose",
			item_type="Hóa chất",
			uom="Hộp",
			norm_uom="Test",
			norm_units_per_purchase_unit=200,
			nominal_tests=200,
		)
		self.fin = make_user("fin.imp.cv@normcore.test", "NC Finance")
		self.auditor = make_user("aud.imp.cv@normcore.test", "NC Auditor")
		self.director = make_user("dir.imp.cv@normcore.test", "NC Director")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _vols(self, **filters):
		return frappe.get_all("NC Test System Volume", filters=filters, fields=["*"], order_by="test_system")

	def test_TC_CLS_34_ma_lis_doi_sang_ma_dich_vu_cot_trong_duoc_chap_nhan(self):
		frappe.set_user(self.fin)
		content = xlsx([head(TSV), row(TSV, **GLU_A), row(TSV, **GLU_B)])
		dry = api.run_import(TSV, content, "thu")
		self.assertEqual((dry["created"], dry["error_count"]), (2, 0), dry["errors"])
		self.assertEqual(self._vols(), [])
		res = api.run_import(TSV, content, "ghi")
		self.assertEqual((res["created"], res["error_count"]), (2, 0), res["errors"])
		a, b = self._vols(fiscal_year=2026, scenario="Thực tế 12 tháng")
		self.assertEqual((a.test_system, b.test_system), ("GLU-A", "GLU-B"))
		for v in (a, b):
			self.assertEqual(v.technical_service, self.service)  # mã LIS đã đổi sang mã dịch vụ
			self.assertEqual(v.department, self.dept)
		self.assertEqual(
			(a.patient_results, a.iqc_tests, a.calibration_tests, a.rerun_tests, a.eqa_tests),
			(12000, 600, 48, 240, 12),
		)
		self.assertEqual((a.wastage_rate, a.avg_batch_size, a.run_days), (3, 40, 300))
		self.assertEqual(b.patient_results, 4000)
		for f in (*AUX, "wastage_rate", "avg_batch_size", "run_days"):
			self.assertIsNone(b[f], f)  # trống = NULL, không phải 0
		again = api.run_import(TSV, content, "ghi")
		self.assertEqual((again["created"], again["unchanged"], again["error_count"]), (0, 2, 0))
		self.assertEqual(len(self._vols()), 2)
		plan = xlsx(
			[
				head(TSV),
				row(TSV, **{**GLU_A, "scenario": "Kế hoạch"}),
				row(TSV, **{**GLU_B, "scenario": "Kế hoạch"}),
			]
		)
		self.assertEqual(api.run_import(TSV, plan, "ghi")["created"], 2)
		self.assertEqual(len(self._vols()), 4)
		self.assertEqual(len(self._vols(scenario="Kế hoạch")), 2)

	def test_nguon_ma_trong_dung_ma_noi_bo(self):
		frappe.set_user(self.fin)
		r = {**GLU_A, "source_system": None, "service_code": self.service}
		res = api.run_import(TSV, xlsx([head(TSV), row(TSV, **r)]), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (1, 0), res["errors"])

	def test_TC_CLS_35_ma_he_thong_la_va_so_am_bao_loi_dong_dung_van_luu(self):
		frappe.set_user(self.fin)
		bad_system = {**GLU_A, "test_system": "GLU-X"}
		negative = {**GLU_B, "scenario": "Kế hoạch", "patient_results": -5}
		content = xlsx(
			[head(TSV), row(TSV, **GLU_A), row(TSV, **bad_system), row(TSV, **negative), row(TSV, **GLU_B)]
		)
		for mode in ("thu", "ghi"):
			res = api.run_import(TSV, content, mode)
			self.assertEqual(res["error_count"], 2, (mode, res["errors"]))
			self.assertEqual(res["created"], 2, mode)
			by_row = {e["row"]: e for e in res["errors"]}
			self.assertEqual(sorted(by_row), [3, 4])
			self.assertEqual(by_row[3]["column"], "Mã hệ thống xét nghiệm")
			self.assertIn("GLU-X", by_row[3]["message"])
			self.assertEqual(by_row[4]["column"], "Số kết quả trả")
			self.assertIn("không được âm", by_row[4]["message"])
		self.assertEqual([v.test_system for v in self._vols()], ["GLU-A", "GLU-B"])
		self.assertEqual(self._vols(test_system="GLU-B")[0].patient_results, 4000)

	def test_TC_CLS_35_ma_dich_vu_ma_khoa_khong_khop_va_so_phu_sai(self):
		frappe.set_user(self.fin)
		cases = {
			"Mã dịch vụ": {**GLU_A, "service_code": "LIS-XXX"},
			"Mã khoa": {**GLU_A, "department": "KHOA-LA"},
			"Số test chạy lại": {**GLU_A, "rerun_tests": -1},
			"Tỷ lệ hao hụt (%)": {**GLU_A, "wastage_rate": 120},
		}
		for column, r in cases.items():
			res = api.run_import(TSV, xlsx([head(TSV), row(TSV, **r)]), "ghi")
			self.assertEqual((res["created"], res["error_count"]), (0, 1), (column, res["errors"]))
			self.assertEqual(res["errors"][0]["column"], column)
		# khoa có thật nhưng khác khoa của hệ thống
		res = api.run_import(TSV, xlsx([head(TSV), row(TSV, **{**GLU_A, "department": "XN"})]), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (0, 1), res["errors"])
		self.assertEqual(res["errors"][0]["column"], "Mã khoa")
		self.assertEqual(self._vols(), [])

	def test_cap_nhat_giu_o_trong(self):
		frappe.set_user(self.fin)
		api.run_import(TSV, xlsx([head(TSV), row(TSV, **GLU_A)]), "ghi")
		res = api.run_import(TSV, xlsx([head(TSV), row(TSV, **{**GLU_A, "patient_results": 13000})]), "ghi")
		self.assertEqual((res["updated"], res["error_count"]), (1, 0), res["errors"])
		self.assertEqual(self._vols()[0].patient_results, 13000)

	def test_TC_CLS_36_xuat_kho_theo_mat_hang_khoa_nam(self):
		frappe.set_user(self.fin)
		r = dict(fiscal_year=2026, department="XN", item="HC_GLU", issued_qty=94)
		res = api.run_import(SIA, xlsx([head(SIA), row(SIA, **r)]), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (1, 0), res["errors"])
		rec = frappe.get_all("NC Stock Issue Actual", fields=["*"])
		self.assertEqual(len(rec), 1)
		self.assertEqual(
			(rec[0].fiscal_year, rec[0].department, rec[0].item, rec[0].issued_qty),
			(2026, "XN", "HC_GLU", 94),
		)
		same = api.run_import(SIA, xlsx([head(SIA), row(SIA, **r)]), "ghi")
		self.assertEqual((same["created"], same["unchanged"]), (0, 1))
		upd = api.run_import(SIA, xlsx([head(SIA), row(SIA, **{**r, "issued_qty": 100})]), "ghi")
		self.assertEqual(upd["updated"], 1)
		self.assertEqual(frappe.db.count("NC Stock Issue Actual"), 1)
		self.assertEqual(frappe.db.get_value("NC Stock Issue Actual", rec[0].name, "issued_qty"), 100)
		neg = api.run_import(
			SIA, xlsx([head(SIA), row(SIA, **{**r, "department": "XN", "issued_qty": -1})]), "ghi"
		)
		self.assertEqual((neg["updated"], neg["error_count"]), (0, 1))
		self.assertEqual(neg["errors"][0]["column"], "Lượng xuất (đơn vị mua)")

	def test_phut_khai_thac(self):
		frappe.set_user("Administrator")
		frappe.db.set_value("NC Equipment", "EQ_A", "allocation_basis", "Phút chiếm máy")
		frappe.set_user(self.fin)
		ok = dict(
			fiscal_year=2026,
			scenario="Thực tế 12 tháng",
			equipment="EQ_A",
			department="HS-CLS",
			total_minutes=120000,
		)
		rows = [
			head(EU),
			row(EU, **ok),
			row(EU, **{**ok, "equipment": "EQ_X"}),
			row(EU, **{**ok, "equipment": "EQ_B"}),  # chia theo Số kết quả
			row(EU, **{**ok, "equipment": "EQ_A", "department": "XN", "total_minutes": -5}),
		]
		res = api.run_import(EU, xlsx(rows), "ghi")
		self.assertEqual((res["created"], res["error_count"]), (1, 3), res["errors"])
		self.assertEqual(frappe.db.count("NC Equipment Usage"), 1)
		self.assertEqual(
			frappe.db.get_value("NC Equipment Usage", {"equipment": "EQ_A"}, "total_minutes"), 120000
		)

	def test_quyen_auditor_director_va_tep_mau(self):
		for user in (self.auditor, self.director):
			frappe.set_user(user)
			keys = [s["key"] for s in api.list_import_sets()]
			for key in SETS:
				self.assertNotIn(key, keys)
				content = xlsx([head(key)])
				for mode in ("thu", "ghi"):
					self.assertRaises(frappe.PermissionError, api.run_import, key, content, mode)
		frappe.set_user(self.fin)
		self.assertTrue(set(SETS) <= {s["key"] for s in api.list_import_sets()})
		for key in SETS:
			_, content = api.build_template_file(key)
			ws = load_workbook(io.BytesIO(content)).active
			self.assertEqual([c.value for c in ws[1]], head(key))
