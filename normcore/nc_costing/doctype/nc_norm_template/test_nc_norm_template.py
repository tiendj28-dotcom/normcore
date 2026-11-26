"""FEAT-034: NC Norm Template (FR-NORM-021, FR-ACC-002, FR-ACC-007; ASM-034-03, 18, 20, 21)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.install import ROLES, ensure_norm_templates
from normcore.norm.templates import DEFAULT_TEMPLATES
from normcore.tests.utils import make_user

ITEMS = [
	dict(item_name="Vật tư lấy mẫu", component="SUPPLY", default_cost_level="TUBE", is_mandatory=1),
	dict(item_name="Thiết bị", component="EQUIPMENT", default_cost_level="RESULT", is_mandatory=1),
]
READERS = {
	"NC Clinician",
	"NC Department Head",
	"NC Finance",
	"NC Resource Manager",
	"NC Director",
	"NC Consultant",
	"NC Admin",
	"NC Auditor",
}
WRITERS = {"NC Finance", "NC Admin"}


def values(code="MDM-T1", **kw):
	v = {"doctype": "NC Norm Template", "template_code": code, "cls_group": "Hóa sinh", "items": ITEMS}
	v.update(kw)
	return v


class TestNCNormTemplate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		# mẫu cài sẵn có thể đã bật ở site test; tắt trong giao dịch của test
		frappe.db.set_value("NC Norm Template", {"is_active": 1}, "is_active", 0)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_FR_NORM_021_luu_duoc(self):
		doc = frappe.get_doc(values(is_active=1)).insert()
		self.assertEqual((doc.name, len(doc.items)), ("MDM-T1", 2))

	def test_FR_NORM_021_hai_mau_dang_dung_cung_nhom_bi_tu_choi(self):
		frappe.get_doc(values(is_active=1)).insert()
		with self.assertRaises(frappe.ValidationError) as cm:
			frappe.get_doc(values("MDM-T2", is_active=1)).insert()
		self.assertIn("MDM-T1", str(cm.exception))
		frappe.get_doc(values("MDM-T2", is_active=0)).insert()  # chưa bật thì được
		frappe.get_doc(values("MDM-T3", cls_group="Miễn dịch", is_active=1)).insert()  # nhóm khác được

	def test_FR_NORM_021_trung_ten_khoan_muc(self):
		items = ITEMS + [dict(ITEMS[0], item_name=" thiết bị ")]
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(values(items=items)).insert()

	def test_FR_NORM_021_mau_dang_dung_khong_khoan_muc(self):
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(values(items=[], is_active=1)).insert()

	def test_FR_NORM_021_sua_mau_dang_dung_van_luu_duoc(self):
		doc = frappe.get_doc(values(is_active=1)).insert()
		doc.items[0].is_mandatory = 0
		doc.save()  # không tự trùng với chính nó

	def test_quyen_norm_template_theo_ma_tran(self):
		frappe.get_doc(values()).insert()
		users = {role: make_user(f"tpl.perm{i}@normcore.test", role) for i, role in enumerate(ROLES)}
		for role, user in users.items():
			frappe.set_user(user)
			self.assertEqual(bool(frappe.has_permission("NC Norm Template", "read")), role in READERS, role)
			self.assertEqual(bool(frappe.has_permission("NC Norm Template", "write")), role in WRITERS, role)
			self.assertEqual(bool(frappe.has_permission("NC Norm Template", "create")), role in WRITERS, role)
			self.assertFalse(frappe.has_permission("NC Norm Template", "delete"), role)

	def test_quyen_norm_template_council_member_bi_tu_choi(self):
		frappe.get_doc(values()).insert()
		frappe.set_user(make_user("tpl.council@normcore.test", "NC Council Member"))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("NC Norm Template", "MDM-T1").check_permission("read")
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc("NC Norm Template", "MDM-T1").check_permission("write")

	def test_quyen_norm_template_auditor_chi_doc(self):
		frappe.get_doc(values()).insert()
		frappe.set_user(make_user("tpl.auditor@normcore.test", "NC Auditor"))
		doc = frappe.get_doc("NC Norm Template", "MDM-T1")
		doc.check_permission("read")
		doc.is_active = 1
		with self.assertRaises(frappe.PermissionError):
			doc.save()
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(values("MDM-T9")).insert()

	def test_quyen_norm_template_clinician_khong_tao_duoc(self):
		frappe.set_user(make_user("tpl.clin@normcore.test", "NC Clinician"))
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(values()).insert()

	def test_quyen_norm_template_finance_tao_duoc(self):
		frappe.set_user(make_user("tpl.fin@normcore.test", "NC Finance"))
		self.assertEqual(frappe.get_doc(values()).insert().name, "MDM-T1")


class TestDefaultTemplates(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_mau_cai_san_hoa_sinh_va_mien_dich_chua_bat(self):
		ensure_norm_templates()
		for tpl in DEFAULT_TEMPLATES:
			doc = frappe.get_doc("NC Norm Template", tpl["template_code"])
			self.assertEqual((doc.cls_group, doc.is_active, len(doc.items)), (tpl["cls_group"], 0, 8))
		self.assertGreaterEqual(frappe.db.count("NC Norm Template"), 2)

	def test_chay_hai_lan_khong_nhan_ban_va_khong_ghi_de(self):
		ensure_norm_templates()
		before = frappe.db.count("NC Norm Template")
		doc = frappe.get_doc("NC Norm Template", "MDM-HOA-SINH")
		doc.items[0].is_mandatory = 0
		doc.is_active = 1
		doc.save()
		ensure_norm_templates()
		self.assertEqual(frappe.db.count("NC Norm Template"), before)
		doc.reload()
		self.assertEqual((doc.is_active, doc.items[0].is_mandatory), (1, 0))
