import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import Workbook, load_workbook

from normcore.api import importer
from normcore.api import item as api
from normcore.tests.utils import ensure, make_user

HEAD = ["Mã mặt hàng *", "Tên mặt hàng *", "Loại *", "Đơn vị tính *"]


def xlsx(rows):
	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


PHEAD = [
	"Mã đơn giá *",
	"Mặt hàng *",
	"Đơn giá (đã gồm thuế GTGT) *",
	"Nguồn giá *",
	"Số chứng từ *",
	"Ngày chứng từ *",
	"Hiệu lực từ *",
	"Hiệu lực đến",
]


def _item(code, **kw):
	values = {"item_name": "Mặt hàng thử", "item_type": "Thuốc", "uom": "viên"}
	values.update(kw)
	return ensure("NC Item", "item_code", code, **values)


def _price(item, source, valid_from, **kw):
	values = {
		"doctype": "NC Item Price",
		"item": item,
		"unit_price": 1000,
		"price_source": source,
		"document_no": "CT-1",
		"document_date": valid_from,
		"valid_from": valid_from,
	}
	values.update(kw)
	return frappe.get_doc(values).insert()


class TestItemAPI(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_ham_duoc_whitelist(self):
		for fn in (api.get_effective_price, api.verify_price, api.get_equivalent_items):
			self.assertIn(fn, frappe.whitelisted)

	def test_TC_CLS_45_chon_gia_theo_nguon_roi_ngay(self):
		_item("MH-A01")
		_price("MH-A01", "Trúng thầu", "2025-01-01", unit_price=900)
		_price("MH-A01", "Báo giá", "2026-06-01", unit_price=1200)
		out = api.get_effective_price("MH-A01", "2026-12-31")
		self.assertEqual(out["price"]["price_source"], "Trúng thầu")
		self.assertEqual(out["price"]["unit_price"], "900.0")

	def test_TC_CLS_45_gia_trung_thau_het_hieu_luc(self):
		_item("MH-A02")
		_price("MH-A02", "Trúng thầu", "2025-01-01", valid_to="2026-06-30")
		_price("MH-A02", "Báo giá", "2026-06-01", unit_price=1200)
		self.assertEqual(api.get_effective_price("MH-A02", "2026-12-31")["price"]["price_source"], "Báo giá")

	def test_TC_RES_01_ba_gia_cung_nguon(self):
		_item("MH-A03")
		for d in ("2026-01-01", "2026-06-01", "2027-01-01"):
			_price("MH-A03", "Hóa đơn", d, document_no=d)
		self.assertEqual(api.get_effective_price("MH-A03", "2026-12-31")["price"]["valid_from"], "2026-06-01")

	def test_TC_RES_02_chung_tu_cu_25_thang_canh_bao_van_tinh(self):
		_item("MH-A04")
		_price("MH-A04", "Hóa đơn", "2023-12-01", document_date="2023-11-30")
		out = api.get_effective_price("MH-A04", "2025-12-31")
		self.assertIn("Đơn giá quá hạn tham chiếu", out["warnings"])
		self.assertEqual(out["price"]["unit_price"], "1000.0")

	def test_TC_CLS_46_xac_minh_va_canh_bao_chua_xac_minh(self):
		_item("MH-A05")
		p = _price("MH-A05", "Hợp đồng", "2026-01-01", valid_to="2026-12-31")
		self.assertEqual(
			api.get_effective_price("MH-A05", "2026-06-01")["warnings"], ["Đơn giá chưa xác minh"]
		)
		with self.assertRaises(frappe.ValidationError):
			api.verify_price(p.name)
		frappe.db.set_value("NC Item Price", p.name, "attachment", "/files/hd.pdf")
		out = api.verify_price(p.name)
		self.assertEqual(out["verified_by"], "Administrator")
		now = api.get_effective_price("MH-A05", "2026-06-01")
		self.assertEqual(now["warnings"], [])
		self.assertTrue(now["price"]["verified"])

	def test_TC_CLS_47_don_gia_mot_don_vi_dinh_muc(self):
		_item("MH-A06", item_type="Hóa chất", uom="hộp", norm_uom="test", norm_units_per_purchase_unit=200)
		_price("MH-A06", "Hóa đơn", "2026-01-01", unit_price=6000000)
		out = api.get_effective_price("MH-A06", "2026-06-01")
		self.assertEqual(out["norm_unit_price"], "30000.0000")
		self.assertEqual(out["norm_uom"], "test")

	def test_FR_RES_004_khong_co_gia_hieu_luc_tra_none(self):
		_item("MH-A07")
		_price("MH-A07", "Hóa đơn", "2027-01-01")
		out = api.get_effective_price("MH-A07", "2026-06-01")
		self.assertIsNone(out["price"])
		self.assertEqual(out["warnings"], [])

	def test_FR_ACC_005_khong_co_quyen_bi_tu_choi(self):
		_item("MH-A08")
		user = make_user("itemapi.none@normcore.test", "NC Council Member")
		frappe.set_user(user)
		self.assertRaises(frappe.PermissionError, api.get_effective_price, "MH-A08")
		self.assertRaises(frappe.PermissionError, api.get_equivalent_items, "MH-A08")

	def test_FR_ACC_007_auditor_doc_duoc_nhung_khong_xac_minh(self):
		_item("MH-A09")
		p = _price("MH-A09", "Hóa đơn", "2026-01-01", attachment="/files/a.pdf")
		frappe.set_user(make_user("itemapi.aud@normcore.test", "NC Auditor"))
		self.assertIsNotNone(api.get_effective_price("MH-A09", "2026-06-01")["price"])
		self.assertRaises(frappe.PermissionError, api.verify_price, p.name)
		self.assertEqual(frappe.db.get_value("NC Item Price", p.name, "verification_status"), "Chưa xác minh")

	def test_FR_RES_013_nhom_tuong_duong(self):
		for code, group in (("MH-G1", "NHOM-1"), ("MH-G2", "NHOM-1"), ("MH-G3", "NHOM-2"), ("MH-G4", None)):
			_item(code, equivalent_group=group)
		self.assertEqual([r.name for r in api.get_equivalent_items("MH-G1")], ["MH-G2"])
		self.assertEqual(api.get_equivalent_items("MH-G4"), [])

	def test_TC_RES_08_nhap_tep_hai_dong_thieu_don_vi_tinh(self):
		frappe.set_user(make_user("itemapi.rm@normcore.test", "NC Resource Manager"))
		rows = [
			HEAD,
			["IM-01", "Gạc", "Vật tư tiêu hao", "cái"],
			["IM-02", "Kim", "Vật tư tiêu hao", None],
			["IM-03", "Bơm tiêm", "Vật tư tiêu hao", "cái"],
			["IM-04", "Chỉ", "Vật tư tiêu hao", None],
			["IM-05", "Ống", "Vật tư tiêu hao", "ống"],
		]
		out = importer.run_import("nc_item", xlsx(rows), "ghi")
		self.assertEqual((out["created"], out["error_count"]), (3, 2))
		self.assertEqual([e["row"] for e in out["errors"]], [3, 5])
		self.assertTrue(all("Đơn vị tính" in e["text"] for e in out["errors"]))
		for code, exists in (("IM-01", 1), ("IM-02", 0), ("IM-03", 1), ("IM-04", 0), ("IM-05", 1)):
			self.assertEqual(bool(frappe.db.exists("NC Item", code)), bool(exists), code)

	def test_TC_ADM_02_mat_hang_tai_mau_roi_nhap_lai(self):
		frappe.set_user(make_user("itemapi.fin@normcore.test", "NC Finance"))
		_, content = importer.build_template_file("nc_item")
		head = [c.value for c in next(load_workbook(io.BytesIO(content)).active.iter_rows())]
		self.assertEqual(head[:4], ["Mã mặt hàng *", "Tên mặt hàng *", "Loại *", "Đơn vị tính *"])
		ghi = importer.run_import("nc_item", content, "ghi")
		self.assertEqual((ghi["created"], ghi["error_count"]), (1, 0))
		self.assertTrue(frappe.db.exists("NC Item", "VD-MH01"))
		lai = importer.run_import("nc_item", content, "ghi")
		self.assertEqual((lai["created"], lai["updated"], lai["unchanged"], lai["error_count"]), (0, 0, 1, 0))

	# --- B2
	def test_FR_RES_018_hoa_chat_thieu_so_don_vi_khong_doan_la_1(self):
		_item("MH-B01", item_type="Hóa chất", uom="hộp", norm_units_per_purchase_unit=200)
		_price("MH-B01", "Hóa đơn", "2026-01-01", unit_price=6000000)
		frappe.db.set_value("NC Item", "MH-B01", "norm_units_per_purchase_unit", 0)  # dữ liệu cũ thiếu số
		out = api.get_effective_price("MH-B01", "2026-06-01")
		self.assertIsNone(out["norm_unit_price"])
		self.assertIsNotNone(out["price"])

	def test_FR_RES_018_loai_khac_thieu_so_don_vi_lui_ve_1(self):
		_item("MH-B02")
		_price("MH-B02", "Hóa đơn", "2026-01-01", unit_price=1234.5)
		frappe.db.set_value("NC Item", "MH-B02", "norm_units_per_purchase_unit", 0)
		self.assertEqual(api.get_effective_price("MH-B02", "2026-06-01")["norm_unit_price"], "1234.5000")

	# --- bộ nhập đơn giá (AMD-008)
	def _rm(self):
		frappe.set_user(make_user("itemapi.rm2@normcore.test", "NC Resource Manager"))

	def _row(self, code, item="MH-I01", price=1500, doc_no="HD-1", valid_to=None):
		return [code, item, price, "Hóa đơn", doc_no, "2026-01-10", "2026-01-10", valid_to]

	def test_FR_RES_012_don_gia_tao_cap_nhat_nhap_lai(self):
		_item("MH-I01")
		self._rm()
		out = importer.run_import("nc_item_price", xlsx([PHEAD, self._row("IP-1")]), "ghi")
		self.assertEqual((out["created"], out["error_count"]), (1, 0))
		name = frappe.db.get_value("NC Item Price", {"price_code": "IP-1"}, "name")
		self.assertEqual(frappe.db.get_value("NC Item Price", name, "unit_price"), 1500)
		again = importer.run_import("nc_item_price", xlsx([PHEAD, self._row("IP-1")]), "ghi")
		self.assertEqual((again["created"], again["updated"], again["unchanged"]), (0, 0, 1))
		upd = importer.run_import("nc_item_price", xlsx([PHEAD, self._row("IP-1", price=1700)]), "ghi")
		self.assertEqual((upd["created"], upd["updated"], upd["error_count"]), (0, 1, 0))
		self.assertEqual(frappe.db.get_value("NC Item Price", name, "unit_price"), 1700)
		self.assertEqual(frappe.db.count("NC Item Price", {"price_code": "IP-1"}), 1)

	def test_FR_RES_012_don_gia_cap_nhat_rieng_valid_to_khong_loi_kieu(self):
		_item("MH-I01")
		self._rm()
		importer.run_import("nc_item_price", xlsx([PHEAD, self._row("IP-2")]), "ghi")
		ok = importer.run_import(
			"nc_item_price", xlsx([PHEAD, self._row("IP-2", valid_to="2026-12-31")]), "ghi"
		)
		self.assertEqual((ok["updated"], ok["error_count"]), (1, 0))
		bad = importer.run_import(
			"nc_item_price", xlsx([PHEAD, self._row("IP-2", valid_to="2026-01-01")]), "ghi"
		)
		self.assertEqual(bad["error_count"], 1)
		self.assertIn("hết hiệu lực", bad["errors"][0]["text"])

	def test_FR_RES_012_don_gia_dong_loi_mat_hang_la_va_thieu_truong(self):
		_item("MH-I01")
		self._rm()
		rows = [
			PHEAD,
			self._row("IP-3"),
			self._row("IP-4", item="KHONG-CO"),
			["IP-5", "MH-I01", None, "Hóa đơn", "HD-5", "2026-01-10", "2026-01-10", None],
		]
		out = importer.run_import("nc_item_price", xlsx(rows), "ghi")
		self.assertEqual((out["created"], out["error_count"]), (1, 2))
		self.assertEqual([e["row"] for e in out["errors"]], [3, 4])
		self.assertIn("KHONG-CO", out["errors"][0]["text"])
		self.assertFalse(frappe.db.exists("NC Item Price", {"price_code": "IP-4"}))

	def test_FR_RES_012_hai_mat_hang_cung_so_chung_tu_khong_de_nhau(self):
		_item("MH-I01")
		_item("MH-I02")
		self._rm()
		rows = [
			PHEAD,
			self._row("IP-6", "MH-I01", 100, "HD-CHUNG"),
			self._row("IP-7", "MH-I02", 200, "HD-CHUNG"),
		]
		out = importer.run_import("nc_item_price", xlsx(rows), "ghi")
		self.assertEqual((out["created"], out["error_count"]), (2, 0))
		got = {
			r.price_code: (r.item, r.unit_price)
			for r in frappe.get_all(
				"NC Item Price", {"document_no": "HD-CHUNG"}, ["price_code", "item", "unit_price"]
			)
		}
		self.assertEqual(got, {"IP-6": ("MH-I01", 100), "IP-7": ("MH-I02", 200)})

	def test_FR_RES_012_don_gia_da_xac_minh_nhap_de_bi_tu_choi(self):
		_item("MH-I01")
		self._rm()
		importer.run_import("nc_item_price", xlsx([PHEAD, self._row("IP-8")]), "ghi")
		frappe.db.set_value(
			"NC Item Price",
			{"price_code": "IP-8"},
			{
				"attachment": "/files/a.pdf",
				"verification_status": "Đã xác minh",
				"verified_by": "Administrator",
			},
		)
		out = importer.run_import("nc_item_price", xlsx([PHEAD, self._row("IP-8", price=9999)]), "ghi")
		self.assertEqual((out["updated"], out["error_count"]), (0, 1))
		self.assertEqual(frappe.db.get_value("NC Item Price", {"price_code": "IP-8"}, "unit_price"), 1500)

	def test_FR_RES_012_don_gia_vai_tro_khong_quyen_va_auditor_bi_tu_choi(self):
		_item("MH-I01")
		content = xlsx([PHEAD, self._row("IP-9")])
		for i, role in enumerate(("NC Auditor", "NC Clinician", "NC Council Member")):
			frappe.set_user(make_user(f"itemapi.x{i}@normcore.test", role))
			for mode in ("thu", "ghi"):
				with self.assertRaises(frappe.PermissionError):
					importer.run_import("nc_item_price", content, mode)
			frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("NC Item Price", {"price_code": "IP-9"}))

	def test_FR_RES_012_don_gia_tai_mau_roi_nhap_lai(self):
		_item("VD-MH01")
		frappe.set_user(make_user("itemapi.fin2@normcore.test", "NC Finance"))
		_, content = importer.build_template_file("nc_item_price")
		ghi = importer.run_import("nc_item_price", content, "ghi")
		self.assertEqual((ghi["created"], ghi["error_count"]), (1, 0))
		lai = importer.run_import("nc_item_price", content, "ghi")
		self.assertEqual((lai["created"], lai["updated"], lai["unchanged"], lai["error_count"]), (0, 0, 1, 0))

	# --- nhập mặt hàng: hóa chất thiếu số đơn vị định mức
	def test_FR_RES_018_nhap_hoa_chat_thieu_so_don_vi_bao_loi_dong(self):
		self._rm()
		rows = [HEAD, ["HC-1", "Glucose", "Hóa chất", "hộp"], ["VT-1", "Gạc", "Vật tư tiêu hao", "cái"]]
		out = importer.run_import("nc_item", xlsx(rows), "ghi")
		self.assertEqual((out["created"], out["error_count"]), (1, 1))
		self.assertFalse(frappe.db.exists("NC Item", "HC-1"))
		self.assertEqual(frappe.db.get_value("NC Item", "VT-1", "norm_units_per_purchase_unit"), 1)
