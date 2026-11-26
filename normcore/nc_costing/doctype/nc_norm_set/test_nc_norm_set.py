import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import (
	confirm_norm_set,
	ensure,
	make_base,
	make_param_set,
	make_procedure,
	make_user,
	publish_procedure,
)


def _published(service, dept, **kw):
	proc = make_procedure(service, dept, **kw)
	publish_procedure(proc, "QĐ-01", "2026-12-01")
	return proc


class TestNCNormSet(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_NORM_02_quy_trinh_nhap_tu_choi_khoi_tao(self):
		proc = make_procedure(self.service, self.dept)
		self.assertRaises(frappe.ValidationError, make_norm_set, proc.name)

	def test_khoi_tao_tu_quy_trinh_da_ban_hanh(self):
		proc = _published(self.service, self.dept, minutes=10)
		ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
		self.assertEqual(ns.status, "Nháp")
		self.assertEqual(len(ns.lines), 1)
		line = ns.lines[0]
		self.assertEqual(
			(line.line_id, line.component, line.step_id, line.procedure_resource_row),
			("L001", "LABOR", "S001", "R001"),
		)
		self.assertEqual(
			(line.resource_doctype, line.resource, line.hospital_qty, line.headcount),
			("NC Job Title", "DD", 10, 1),
		)
		self.assertEqual((line.basis, line.uom), ("Quy trình", "phút"))
		self.assertFalse(line.authority_qty)

	def test_khoa_chi_nc_finance_va_khong_sua_khong_xoa(self):
		proc = _published(self.service, self.dept)
		ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
		clin = make_user("clin.ns@normcore.test", "NC Clinician")
		fin = make_user("fin.ns@normcore.test", "NC Finance")
		frappe.set_user(clin)
		self.assertRaises(frappe.PermissionError, ns.lock)
		frappe.set_user(fin)
		confirm_norm_set(ns)
		ns.lock()
		ns.reload()
		self.assertEqual((ns.status, ns.locked_by), ("Đã khóa", fin))
		self.assertIsNotNone(ns.locked_on)
		ns.lines[0].hospital_qty = 99
		self.assertRaises(frappe.ValidationError, ns.save)
		frappe.set_user("Administrator")
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, "NC Norm Set", ns.name)

	def test_DI05_cau_phan_khop_loai_nguon_luc(self):
		proc = _published(self.service, self.dept)
		ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
		ns.lines[0].resource_doctype = "NC Item"
		self.assertRaises(frappe.ValidationError, ns.save)

	def test_DI04_ma_buoc_phai_ton_tai(self):
		proc = _published(self.service, self.dept)
		ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
		ns.lines[0].step_id = "S999"
		self.assertRaises(frappe.ValidationError, ns.save)

	def test_DI03_bo_khoa_moi_thay_the_bo_cu(self):
		p1 = _published(self.service, self.dept, version=1)
		ns1 = frappe.get_doc("NC Norm Set", make_norm_set(p1.name))
		confirm_norm_set(ns1)
		ns1.lock()
		p2 = _published(self.service, self.dept, version=2)
		ns2 = frappe.get_doc("NC Norm Set", make_norm_set(p2.name))
		confirm_norm_set(ns2)
		ns2.lock()
		self.assertEqual(frappe.db.get_value("NC Norm Set", ns1.name, "status"), "Đã thay thế")
		self.assertEqual(frappe.db.get_value("NC Norm Set", ns2.name, "status"), "Đã khóa")

	def test_TC_NORM_02_insert_truc_tiep_tu_quy_trinh_nhap_bi_tu_choi(self):
		proc = make_procedure(self.service, self.dept)  # còn Nháp
		ns = frappe.get_doc(
			{
				"doctype": "NC Norm Set",
				"technical_service": self.service,
				"department": self.dept,
				"procedure": proc.name,
				"version_no": 1,
			}
		)
		self.assertRaises(frappe.ValidationError, ns.insert)

	def test_nguon_luc_nhan_luc_chua_gan_chuc_danh_bi_tu_choi(self):
		proc = make_procedure(self.service, self.dept)
		proc.resources[0].linked_doctype = None
		proc.resources[0].linked_name = None
		proc.save()
		publish_procedure(proc, "QĐ-01", "2026-12-01")
		self.assertRaises(frappe.ValidationError, make_norm_set, proc.name)

	def test_phien_ban_dung_max_khong_dung_count(self):
		p1 = _published(self.service, self.dept, version=1)
		n1 = make_norm_set(p1.name)
		p2 = _published(self.service, self.dept, version=2)
		n2 = make_norm_set(p2.name)
		frappe.delete_doc("NC Norm Set", n1, force=True)  # xóa bản v1
		p3 = _published(self.service, self.dept, version=3)
		n3 = frappe.get_doc("NC Norm Set", make_norm_set(p3.name))
		self.assertEqual(n3.version_no, 3)
		self.assertNotEqual(n3.name, n2)


class TestNCNormSetFeat012(FrappeTestCase):
	"""FEAT-012: kiểm dòng ở controller (mọi đường ghi), khóa nội dung, chuyển trạng thái."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()
		ensure(
			"NC Item",
			"item_code",
			"VT-NS01",
			item_name="Gạc",
			item_type="Vật tư tiêu hao",
			uom="cái",
			norm_units_per_purchase_unit=1,
		)
		proc = _published(self.service, self.dept)
		self.ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
		self.ns.append(
			"lines",
			{
				"step_id": "S001",
				"component": "SUPPLY",
				"resource_doctype": "NC Item",
				"resource": "VT-NS01",
				"hospital_qty": 2,
				"uom": "cái",
				"basis": "Quy trình",
			},
		)
		self.ns.save()
		self.labor, self.supply = self.ns.lines[0], self.ns.lines[1]

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _fails(self, text):
		with self.assertRaises(frappe.ValidationError) as cm:
			self.ns.save()
		self.assertIn(text, str(cm.exception))
		self.ns.reload()

	def test_TC_NORM_10_thieu_don_vi_thieu_so_phut_tu_choi(self):
		self.supply.uom = ""
		self._fails("Đơn vị")
		self.ns.lines[0].hospital_qty = 0
		self._fails("Số phút")
		self.assertEqual(frappe.db.get_value("NC Norm Line", self.supply.name, "uom"), "cái")

	def test_TC_NORM_07_loai_tru_can_ly_do_trong_danh_sach(self):
		self.supply.is_excluded = 1
		self._fails("Lý do loại trừ")
		self.ns.lines[1].is_excluded = 1
		self.ns.lines[1].exclude_reason = "Tùy ý"
		with self.assertRaises(frappe.ValidationError):
			self.ns.save()
		self.ns.reload()
		self.ns.lines[1].is_excluded = 1
		self.ns.lines[1].exclude_reason = "Thanh toán riêng"
		self.ns.save()

	def test_TC_NORM_04_vuot_tran_hao_hut_can_ly_do(self):
		make_param_set().db_set("wastage_cap", 5)
		self.supply.wastage_rate = 8
		self._fails("Lý do vượt trần")
		self.ns.lines[1].wastage_rate = 8
		self.ns.lines[1].wastage_reason = "Hao hụt khi cắt"
		self.ns.save()

	def test_sua_dong_xoa_xac_nhan_cua_dong_do(self):
		for ln in self.ns.lines:
			ln.db_set("confirmed_by", "Administrator")
		self.ns.reload()
		self.ns.lines[1].hospital_qty = 3
		self.ns.save()
		self.ns.reload()
		self.assertIsNone(self.ns.lines[1].confirmed_by)
		self.assertEqual(self.ns.lines[0].confirmed_by, "Administrator")

	def test_doi_trang_thai_khong_qua_nut_bi_tu_choi(self):
		self.ns.status = "Đã xác nhận chuyên môn"
		self._fails("nút trên lưới")

	def test_da_xac_nhan_chuyen_mon_khoa_noi_dung(self):
		confirm_norm_set(self.ns)
		self.ns.reload()
		self.ns.lines[1].hospital_qty = 9
		self._fails("đã xác nhận chuyên môn")

	def test_khoa_tu_nhap_bi_tu_choi_va_bo_khoa_khong_sua_qua_client(self):
		fin = make_user("fin.ns12@normcore.test", "NC Finance")
		frappe.set_user(fin)
		self.assertRaises(frappe.ValidationError, self.ns.lock)  # Nháp
		confirm_norm_set(self.ns)
		self.ns.lock()
		frappe.set_user("Administrator")
		self.assertRaises(
			frappe.ValidationError,
			frappe.client.set_value,
			"NC Norm Set",
			self.ns.name,
			"step_change_note",
			"x",
		)
		self.assertRaises(
			frappe.ValidationError, frappe.client.set_value, "NC Norm Set", self.ns.name, "status", "Nháp"
		)
		self.assertEqual(frappe.db.get_value("NC Norm Set", self.ns.name, "status"), "Đã khóa")

	def test_nhan_luc_chua_gan_chuc_danh_van_tu_choi_con_loai_khac_cho_chua_lien_ket(self):
		proc = make_procedure(self.service, self.dept, version=7)
		proc.append(
			"resources",
			{
				"step_id": "S001",
				"resource_type": "Vật tư",
				"resource_text": "Bơm tiêm",
				"quantity": 1,
				"uom": "cái",
			},
		)
		proc.save()
		publish_procedure(proc, "QĐ-07", "2026-12-01")
		ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
		unlinked = [r for r in ns.lines if r.component == "SUPPLY"]
		self.assertEqual(len(unlinked), 1)
		self.assertFalse(unlinked[0].resource)
		self.assertEqual(unlinked[0].resource_doctype, "NC Item")
