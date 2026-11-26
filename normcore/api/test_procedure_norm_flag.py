"""Ban hành phiên bản mới gắn cờ "Cần cập nhật" cho bộ định mức (FEAT-008; TC-WF-06, FR-WF-011)."""

import frappe

from normcore.api import procedure_workflow as wf
from normcore.api.test_procedure_revision import RevisionBase
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set

DT = "NC Clinical Procedure"
NS = "NC Norm Set"


class TestNormFlag(RevisionBase):
	def setUp(self):
		super().setUp()
		from normcore.tests.utils import make_user

		self.sec = make_user("sec.nf@normcore.test", "NC Council Member")
		frappe.db.set_single_value("NC Settings", "council_secretary", self.sec)
		frappe.db.set_value("NC Department", self.dept, "head_user", self.head)
		self.ns_draft = make_norm_set(self.v1.name)
		self.ns_locked = make_norm_set(self.v1.name)
		ns = frappe.get_doc(NS, self.ns_locked)
		ns.status = "Đã khóa"
		ns.flags.allow_lock = True
		ns.save(ignore_permissions=True)
		self.ns_replaced = make_norm_set(self.v1.name)
		frappe.db.set_value(NS, self.ns_replaced, "status", "Đã thay thế")

	def edit_v2(self):
		v2 = frappe.get_doc(DT, self.revise(self.clin)["name"])
		v2.steps = [s for s in v2.steps if s.step_id != "S002"]
		v2.resources = [r for r in v2.resources if r.step_id != "S002"]
		v2.append("steps", {"phase": "Thực hiện", "step_title": "Mới", "description": "m"})
		for r in v2.resources:
			if r.step_id == "S003":
				r.quantity = 9
		v2.save(ignore_permissions=True)
		return v2

	def act(self, user, name, action, **kw):
		frappe.set_user(user)
		try:
			return wf.apply_action(name, action, **kw)
		finally:
			frappe.set_user("Administrator")

	def publish_v2(self, v2):
		self.act(self.clin, v2.name, "Gửi duyệt")
		self.act(self.head, v2.name, "Đồng ý")
		self.act(self.sec, v2.name, "Thông qua")
		self.act(self.director, v2.name, "Ban hành", decision_no="2/QĐ", effective_date="2026-01-01")

	def flags(self, name):
		return frappe.db.get_value(NS, name, ["needs_update", "step_change_note"], as_dict=True)

	def test_TC_WF_06_ban_hanh_gan_co_bo_dinh_muc(self):
		v2 = self.edit_v2()
		self.assertEqual(self.flags(self.ns_draft).needs_update, 0)
		self.publish_v2(v2)
		self.assertEqual(frappe.db.get_value(DT, v2.name, "workflow_state"), "Đã ban hành")
		for name in (self.ns_draft, self.ns_locked):
			f = self.flags(name)
			self.assertEqual(f.needs_update, 1, name)
			self.assertEqual(f.step_change_note, "thêm S005; bỏ S002; đổi S003")
		self.assertEqual(self.flags(self.ns_replaced).needs_update, 0)
		# bộ dựa trên v2 (tạo sau khi v2 ban hành) không bị gắn
		ns_v2 = make_norm_set(v2.name)
		self.assertEqual(self.flags(ns_v2).needs_update, 0)
		self.assertTrue(
			frappe.get_all(
				"Comment",
				{"reference_doctype": NS, "reference_name": self.ns_draft, "content": ["like", "%S005%"]},
			)
		)

	def test_ban_hanh_khong_co_bo_dinh_muc_khong_loi(self):
		frappe.db.delete(NS, {"procedure": self.v1.name})
		self.publish_v2(self.edit_v2())

	def test_truong_co_chi_doc_va_auditor_khong_sua(self):
		meta = frappe.get_meta(NS)
		for f in ("needs_update", "step_change_note"):
			self.assertEqual(meta.get_field(f).read_only, 1)
		frappe.set_user(self.auditor)
		try:
			self.assertFalse(frappe.has_permission(NS, "write", doc=self.ns_draft))
		finally:
			frappe.set_user("Administrator")
