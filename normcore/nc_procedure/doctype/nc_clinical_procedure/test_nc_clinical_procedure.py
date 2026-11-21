import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.tests.utils import make_base, make_procedure, make_user


def _step(title, phase="Thực hiện"):
	return {"phase": phase, "step_title": title, "description": f"Mô tả {title}"}


class TestNCClinicalProcedure(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _new(self, **kw):
		doc = frappe.get_doc(
			{
				"doctype": "NC Clinical Procedure",
				"technical_service": self.service,
				"department": self.dept,
				"version_no": 1,
				**kw,
			}
		)
		return doc

	def test_TC_PROC_03_ma_buoc_bat_bien(self):
		proc = self._new(steps=[_step("A"), _step("B"), _step("C")])
		proc.insert()
		self.assertEqual([s.step_id for s in proc.steps], ["S001", "S002", "S003"])
		# đổi thứ tự bước 1 và 3 (idx), xóa bước 2, thêm bước mới
		s1, s2, s3 = proc.steps
		s1.idx, s3.idx = 3, 1
		proc.steps = [s3, s2, s1]
		proc.steps.remove(s2)
		proc.append("steps", _step("D"))
		proc.save()
		ids = {s.step_title: s.step_id for s in proc.steps}
		self.assertEqual(ids["A"], "S001")
		self.assertEqual(ids["C"], "S003")
		self.assertEqual(ids["D"], "S004")  # không tái dùng S002
		self.assertNotIn("S002", ids.values())

	def test_TC_PROC_03_khong_doi_ma_buoc(self):
		proc = self._new(steps=[_step("A")])
		proc.insert()
		proc.steps[0].step_id = "S009"
		self.assertRaises(frappe.ValidationError, proc.save)

	def test_TC_PROC_04_nguon_luc_nhan_luc_co_ma_dong_bat_bien(self):
		proc = make_procedure(self.service, self.dept, minutes=15)
		res = proc.resources[0]
		self.assertEqual(res.resource_row_id, "R001")
		self.assertEqual(res.step_id, "S001")
		self.assertEqual(res.headcount, 1)
		proc.append("resources", {**res.as_dict(), "name": None, "resource_row_id": None, "idx": None})
		proc.save()
		self.assertEqual([r.resource_row_id for r in proc.resources], ["R001", "R002"])
		proc.resources[0].resource_row_id = "R009"
		self.assertRaises(frappe.ValidationError, proc.save)

	def test_buoc_cua_nguon_luc_phai_ton_tai(self):
		proc = make_procedure(self.service, self.dept)
		proc.resources[0].step_id = "S999"
		self.assertRaises(frappe.ValidationError, proc.save)

	def test_nhan_luc_phai_tinh_bang_phut(self):
		proc = make_procedure(self.service, self.dept)
		proc.resources[0].uom = "giờ"
		self.assertRaises(frappe.ValidationError, proc.save)

	def test_ban_hanh_chi_nc_director_va_can_so_quyet_dinh(self):
		proc = make_procedure(self.service, self.dept)
		clin = make_user("clin.proc@normcore.test", "NC Clinician")
		director = make_user("dir.proc@normcore.test", "NC Director")
		frappe.set_user(clin)
		self.assertRaises(frappe.PermissionError, proc.publish)
		frappe.set_user(director)
		self.assertRaises(frappe.ValidationError, proc.publish)  # thiếu decision_no, effective_date
		proc.decision_no, proc.effective_date = "QĐ-01", "2026-12-01"
		proc.publish()
		self.assertEqual(
			frappe.db.get_value("NC Clinical Procedure", proc.name, "workflow_state"), "Đã ban hành"
		)

	def test_quy_trinh_da_ban_hanh_khong_sua_khong_xoa(self):
		proc = make_procedure(self.service, self.dept)
		proc.decision_no, proc.effective_date = "QĐ-01", "2026-12-01"
		proc.publish()
		proc = frappe.get_doc("NC Clinical Procedure", proc.name)
		proc.decision_no = "QĐ-02"
		self.assertRaises(frappe.ValidationError, proc.save)
		self.assertRaises(frappe.ValidationError, frappe.delete_doc, "NC Clinical Procedure", proc.name)

	def test_khong_tu_dat_trang_thai_da_ban_hanh(self):
		proc = self._new(workflow_state="Đã ban hành")
		self.assertRaises(frappe.ValidationError, proc.insert)
