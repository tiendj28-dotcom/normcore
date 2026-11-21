import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import procedure as api
from normcore.tests.utils import make_base, make_procedure, make_user

STEP = {"phase": "Thực hiện", "step_title": "Bước mới", "description": "Mô tả bước mới"}


class TestProcedureAPI(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()
		self.proc = make_procedure(self.service, self.dept)
		self.clin = make_user("clin.api@normcore.test", "NC Clinician")
		self.auditor = make_user("auditor.api@normcore.test", "NC Auditor")
		self.finance = make_user("fin.api@normcore.test", "NC Finance")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_ham_duoc_whitelist(self):
		for fn in (api.get_procedure, api.add_step, api.list_procedures):
			self.assertIn(fn, frappe.whitelisted)

	def test_get_procedure_tra_cac_buoc(self):
		frappe.set_user(self.auditor)
		data = api.get_procedure(self.proc.name)
		self.assertEqual(data["name"], self.proc.name)
		self.assertEqual(data["steps"][0]["step_id"], "S001")
		self.assertEqual(data["workflow_state"], "Nháp")

	def test_nguoi_co_quyen_them_duoc_buoc(self):
		frappe.set_user(self.clin)
		out = api.add_step(self.proc.name, **STEP)
		self.assertEqual(out["step_id"], "S002")
		self.assertEqual(len(frappe.get_doc("NC Clinical Procedure", self.proc.name).steps), 2)

	def test_vai_tro_khong_quyen_va_auditor_bi_tu_choi(self):
		for user in (self.auditor, self.finance):
			frappe.set_user(user)
			self.assertRaises(frappe.PermissionError, api.add_step, self.proc.name, **STEP)
		frappe.set_user("Administrator")
		self.assertEqual(len(frappe.get_doc("NC Clinical Procedure", self.proc.name).steps), 1)

	def test_quy_trinh_da_ban_hanh_bi_chan(self):
		self.proc.decision_no, self.proc.effective_date = "QĐ-01", "2026-12-01"
		self.proc.publish()
		frappe.set_user(self.clin)
		self.assertRaises(frappe.ValidationError, api.add_step, self.proc.name, **STEP)

	def test_yeu_cau_giai_doan_ten_mo_ta(self):
		frappe.set_user(self.clin)
		for missing in ("phase", "step_title", "description"):
			args = {**STEP, missing: ""}
			self.assertRaises(frappe.ValidationError, api.add_step, self.proc.name, **args)
