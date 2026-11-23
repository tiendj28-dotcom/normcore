import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import load_workbook

from normcore.api import importer as api
from normcore.tests.utils import make_user

KEY = "nc_job_title"
HEAD = ["Mã chức danh *", "Tên chức danh *", "Nhóm"]


def xlsx(rows):
	from openpyxl import Workbook

	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


class TestImporterAPI(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.finance = make_user("fin.imp@normcore.test", "NC Finance")
		self.rm = make_user("rm.imp@normcore.test", "NC Resource Manager")
		self.auditor = make_user("aud.imp@normcore.test", "NC Auditor")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_ham_duoc_whitelist(self):
		for fn in (api.list_import_sets, api.download_template, api.import_file):
			self.assertIn(fn, frappe.whitelisted)

	def test_TC_ADM_02_tai_mau_roi_nhap_lai_chinh_tep_do(self):
		frappe.set_user(self.finance)
		filename, content = api.build_template_file(KEY)
		self.assertIn(KEY, filename)
		rows = list(load_workbook(io.BytesIO(content)).active.iter_rows(values_only=True))
		self.assertEqual(list(rows[0]), ["Mã chức danh *", "Tên chức danh *", "Nhóm"])
		self.assertEqual(len(rows), 2)
		code = rows[1][0]
		before = frappe.db.count("NC Job Title")
		thu = api.run_import(KEY, content, "thu")
		self.assertEqual((thu["created"], thu["error_count"]), (1, 0))
		self.assertEqual(frappe.db.count("NC Job Title"), before)  # chế độ thử không ghi
		ghi = api.run_import(KEY, content, "ghi")
		self.assertEqual((ghi["created"], ghi["error_count"]), (1, 0))
		self.assertTrue(frappe.db.exists("NC Job Title", code))
		lai = api.run_import(KEY, content, "ghi")
		self.assertEqual((lai["created"], lai["updated"], lai["unchanged"], lai["error_count"]), (0, 0, 1, 0))
		self.assertEqual(frappe.db.count("NC Job Title"), before + 1)

	def test_cap_nhat_theo_ma_va_loi_kieu_cua_dong(self):
		frappe.set_user(self.finance)
		api.run_import(KEY, xlsx([HEAD, ["T-1", "Tên 1", "Khác"]]), "ghi")
		out = api.run_import(KEY, xlsx([HEAD, ["T-1", "Tên mới", None], ["T-2", "Tên 2", "Sai nhóm"]]), "ghi")
		self.assertEqual((out["created"], out["updated"], out["error_count"]), (0, 1, 1))
		self.assertEqual(frappe.db.get_value("NC Job Title", "T-1", "job_title_name"), "Tên mới")
		self.assertEqual(
			frappe.db.get_value("NC Job Title", "T-1", "job_group"), "Khác"
		)  # ô trống giữ nguyên
		self.assertIn("Nhóm", out["errors"][0]["text"])

	def test_vai_tro_chi_doc_va_auditor_bi_tu_choi(self):
		content = xlsx([HEAD, ["T-9", "Tên", "Khác"]])
		for user in (self.rm, self.auditor):
			frappe.set_user(user)
			for mode in ("thu", "ghi"):
				with self.assertRaises(frappe.PermissionError):
					api.run_import(KEY, content, mode)
			# FEAT-010 (ASM-084) và FEAT-009 (ASM-096, Lead duyệt): NC Resource Manager ghi được thiết bị, phòng theo ma trận mục 4; NC Auditor không có bộ nào
			expected = ["nc_equipment", "nc_room", "nc_item", "nc_item_price"] if user == self.rm else []
			self.assertEqual([s["key"] for s in api.list_import_sets()], expected)
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("NC Job Title", "T-9"))

	def test_tai_mau_can_quyen_doc(self):
		frappe.set_user(self.auditor)
		self.assertTrue(api.build_template_file(KEY)[1])  # chỉ đọc vẫn tải được mẫu (G6)
		frappe.set_user("Guest")
		with self.assertRaises(frappe.PermissionError):
			api.build_template_file(KEY)

	def test_finance_thay_bo_nhap_va_import_file_qua_file_rieng_tu(self):
		frappe.set_user(self.finance)
		self.assertEqual(
			[s["key"] for s in api.list_import_sets()],
			[
				KEY,
				"nc_equipment",
				"nc_room",
				"nc_item",
				"nc_item_price",
				"nc_account_mapping",
				"nc_service_volume",
				"nc_cost_center_driver",
			],
		)  # FEAT-010 (ASM-084), FEAT-009 (ASM-096), FEAT-016 (ASM-128, Lead duyệt trên NORM-28)
		f = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": "t.xlsx",
				"is_private": 1,
				"content": xlsx([HEAD, ["T-F", "Tên F", "Khác"]]),
			}
		).insert()
		out = api.import_file(KEY, f.file_url, "ghi")
		self.assertEqual(out["created"], 1)
		with self.assertRaises(frappe.ValidationError):
			api.import_file("khong_co", f.file_url, "thu")

	def test_FR_ADM_002_loi_validate_cua_frappe_o_mot_dong_khong_lam_hong_dong_khac(self):
		frappe.set_user(self.finance)
		frappe.local.message_log = []
		dai = "x" * 200  # vượt 140 ký tự: Frappe từ chối ở insert()
		out = api.run_import(
			KEY,
			xlsx([HEAD, ["PRB-1", "Tên 1", "Khác"], ["PRB-2", dai, "Khác"], ["PRB-3", "Tên 3", "Khác"]]),
			"ghi",
		)
		self.assertEqual((out["created"], out["error_count"]), (2, 1))
		self.assertEqual(out["errors"][0]["row"], 3)
		self.assertTrue(frappe.db.exists("NC Job Title", "PRB-1"))
		self.assertFalse(frappe.db.exists("NC Job Title", "PRB-2"))
		self.assertTrue(frappe.db.exists("NC Job Title", "PRB-3"))
		self.assertEqual(frappe.local.message_log, [])  # không đẩy hộp thoại msgprint lên Desk

	def test_FR_ADM_002_ma_chi_khac_hoa_thuong_la_khong_doi(self):
		frappe.set_user(self.finance)
		api.run_import(KEY, xlsx([HEAD, ["VD-HT", "Tên", "Khác"]]), "ghi")
		out = api.run_import(KEY, xlsx([HEAD, ["vd-ht", "Tên", "Khác"]]), "ghi")
		self.assertEqual((out["created"], out["updated"], out["unchanged"]), (0, 0, 1))
