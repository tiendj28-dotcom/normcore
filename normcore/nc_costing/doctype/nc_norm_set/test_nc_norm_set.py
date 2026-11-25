import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import make_base, make_procedure, make_user, publish_procedure


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
		ns1.lock()
		p2 = _published(self.service, self.dept, version=2)
		ns2 = frappe.get_doc("NC Norm Set", make_norm_set(p2.name))
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
