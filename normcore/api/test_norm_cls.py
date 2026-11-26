"""FEAT-034: API bộ định mức theo hệ thống xét nghiệm (UC-021; TC-CLS-26, 29..33; FR-NORM-017..025)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api import norm as api
from normcore.tests.utils import (
	make_cls_data,
	make_procedure,
	make_qc_items,
	make_qc_plan,
	make_test_system,
	make_user,
	publish_procedure,
)

DEPT = "XN-N34"
TEMPLATE = "MDM-T-N34"


def _template_items():
	return [
		dict(item_name="Vật tư lấy mẫu", component="SUPPLY", default_cost_level="TUBE", is_mandatory=1),
		dict(item_name="Hóa chất chính", component="DRUG", default_cost_level="RESULT", is_mandatory=1),
		dict(item_name="Thiết bị", component="EQUIPMENT", default_cost_level="RESULT", is_mandatory=1),
	]


class ClsBase(FrappeTestCase):
	"""Dịch vụ GLU (cận lâm sàng, Hóa sinh), hệ thống GLU-A (EQ_A) và GLU-B (EQ_B), quy trình đã ban hành
	có dòng Hóa chất và Nhân lực, mẫu Hóa sinh đang dùng."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _eqs = make_cls_data(department=DEPT)
		make_qc_items()
		self.gluA = make_test_system("GLU-A", self.service, self.dept, "EQ_A", 60).name
		self.gluB = make_test_system("GLU-B", self.service, self.dept, "EQ_B", 40).name
		frappe.db.set_value("NC Norm Template", {"is_active": 1}, "is_active", 0)
		frappe.get_doc(
			{
				"doctype": "NC Norm Template",
				"template_code": TEMPLATE,
				"cls_group": "Hóa sinh",
				"is_active": 1,
				"items": _template_items(),
			}
		).insert()
		self.proc = make_procedure(self.service, self.dept, minutes=10)
		self.proc.append(
			"resources",
			{
				"step_id": self.proc.steps[0].step_id,
				"resource_type": "Hóa chất",
				"resource_text": "Hóa chất GLU",
				"linked_doctype": "NC Item",
				"linked_name": "HC_GLU",
				"quantity": 1,
				"uom": "test",
			},
		)
		self.proc.save(ignore_permissions=True)
		publish_procedure(self.proc)
		self.head = make_user("head.n34@normcore.test", "NC Department Head")
		self.fin = make_user("fin.n34@normcore.test", "NC Finance")
		self.aud = make_user("aud.n34@normcore.test", "NC Auditor")
		access.assign_department(self.head, self.dept)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def create(self, system="GLU-A"):
		frappe.set_user(self.head)
		out = api.create_norm_set(self.proc.name, system)
		return frappe.get_doc("NC Norm Set", out["name"])


class TestCreate(ClsBase):
	def test_TC_CLS_29_khoi_tao_gan_he_thong_va_them_khoan_muc_bat_buoc(self):
		ns = self.create("GLU-A")
		self.assertEqual((ns.test_system, ns.name), ("GLU-A", f"DM-{self.service}-{self.dept}-GLU-A-v1"))
		self.assertEqual(ns.norm_template, TEMPLATE)
		by_item = {r.template_item: r for r in ns.lines if r.template_item}
		self.assertEqual(set(by_item), {"Vật tư lấy mẫu", "Hóa chất chính", "Thiết bị"})
		self.assertTrue(by_item["Hóa chất chính"].procedure_resource_row)
		added = [r for r in ns.lines if not r.procedure_resource_row]
		self.assertEqual(len(added), 2)
		for r in added:
			self.assertEqual(r.service_level, 1)
			self.assertFalse(r.hospital_qty)
			self.assertFalse(r.resource)
		self.assertEqual(by_item["Vật tư lấy mẫu"].cost_level, "TUBE")
		self.assertEqual(by_item["Hóa chất chính"].apply_k, 1)  # ASM-034-06
		# không chọn hệ thống: từ chối, nêu cả hai
		with self.assertRaises(frappe.ValidationError) as cm:
			api.create_norm_set(self.proc.name)
		self.assertIn("GLU-A", str(cm.exception))
		self.assertIn("GLU-B", str(cm.exception))
		# hệ thống của dịch vụ khác: DI-15
		svc2, dept2, _ = make_cls_data(department="XN2-N34", service="URE")
		other = make_test_system("URE-A", svc2, dept2, "EQ_A", 50).name
		with self.assertRaises(frappe.ValidationError) as cm:
			api.create_norm_set(self.proc.name, other)
		self.assertIn("không thuộc dịch vụ", str(cm.exception))

	def test_create_options_va_bo_dang_soan(self):
		frappe.set_user(self.head)
		opt = api.create_options(self.proc.name)
		self.assertTrue(opt["required"])
		self.assertEqual(opt["template"], TEMPLATE)
		self.assertEqual([x["name"] for x in opt["test_systems"]], ["GLU-A", "GLU-B"])
		self.assertEqual(opt["test_systems"][0]["main_equipment"], "EQ_A")
		self.assertIsNone(opt["test_systems"][0]["open_set"])
		first = api.create_norm_set(self.proc.name, "GLU-A")
		again = api.create_norm_set(self.proc.name, "GLU-A")  # ASM-034-14
		self.assertEqual(again["name"], first["name"])
		self.assertIn("message", again)
		self.assertEqual(api.create_options(self.proc.name)["test_systems"][0]["open_set"], first["name"])
		self.assertEqual(api.create_norm_set(self.proc.name, "GLU-B")["name"].count("GLU-B"), 1)

	def test_khong_co_he_thong_khong_bat_buoc(self):
		frappe.db.set_value("NC Test System", {"technical_service": self.service}, "status", "Ngừng dùng")
		frappe.set_user(self.head)
		self.assertFalse(api.create_options(self.proc.name)["required"])
		ns = frappe.get_doc("NC Norm Set", api.create_norm_set(self.proc.name)["name"])
		self.assertIsNone(ns.test_system)
		with self.assertRaises(frappe.ValidationError):  # hệ thống đã ngừng dùng
			api.create_norm_set(self.proc.name, "GLU-A")

	def test_khong_co_mau_khong_them_dong(self):
		frappe.db.set_value("NC Norm Template", {"template_code": TEMPLATE}, "is_active", 0)
		ns = self.create("GLU-A")
		self.assertIsNone(ns.norm_template)
		self.assertEqual(len(ns.lines), 2)  # nhân lực + hóa chất của quy trình
		self.assertEqual({r.template_item for r in ns.lines}, {None})

	def test_auditor_khong_tao_duoc(self):
		frappe.set_user(self.aud)
		with self.assertRaises(frappe.PermissionError):
			api.create_options(self.proc.name)
		with self.assertRaises(frappe.PermissionError):
			api.create_norm_set(self.proc.name, "GLU-A")
