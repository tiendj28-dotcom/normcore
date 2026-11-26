"""FEAT-013: phiên bản bộ định mức theo quy trình mới (FR-NORM-015, TC-NORM-08 sau TC-WF-06)."""

import frappe

from normcore.api import norm as api
from normcore.api import test_procedure_norm_flag as flagmod
from normcore.api.test_procedure_norm_flag import NS
from normcore.api.test_procedure_revision import RevisionBase

LINE = "NC Norm Line"


class TestNormVersion(RevisionBase):
	"""Dùng lại dữ liệu TC-WF-06: v1 S001..S004; v2 bỏ S002, thêm S005, đổi S003."""

	# dựng v2 như TC-WF-06: dùng lại hàm của TestNormFlag, không chép số liệu
	edit_v2 = flagmod.TestNormFlag.edit_v2
	act = flagmod.TestNormFlag.act
	publish_v2 = flagmod.TestNormFlag.publish_v2

	def setUp(self):
		super().setUp()
		from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
		from normcore.tests.utils import make_user

		self.sec = make_user("sec.nv@normcore.test", "NC Council Member")
		frappe.db.set_single_value("NC Settings", "council_secretary", self.sec)
		frappe.db.set_value("NC Department", self.dept, "head_user", self.head)
		self.ns_draft = make_norm_set(self.v1.name)
		self.lock(self.ns_draft)
		self.src = self.ns_draft
		self.v2 = self.edit_v2()
		self.publish_v2(self.v2)

	def lock(self, name):
		ns = frappe.get_doc(NS, name)
		ns.status = "Đã khóa"
		ns.flags.allow_lock = True
		ns.save(ignore_permissions=True)

	def as_user(self, user, fn, *a, **kw):
		frappe.set_user(user)
		try:
			return fn(*a, **kw)
		finally:
			frappe.set_user("Administrator")

	def steps_of(self, name, removed=None):
		ns = frappe.get_doc(NS, name)
		return {
			r.step_id: r.step_removed for r in ns.lines if removed is None or bool(r.step_removed) == removed
		}

	def test_TC_NORM_08_phien_ban_theo_quy_trinh_moi(self):
		prior = max(
			frappe.get_all(
				NS, {"technical_service": self.service, "department": self.dept}, pluck="version_no"
			)
		)
		res = self.as_user(self.clin, api.new_version, self.src)
		new = frappe.get_doc(NS, res["name"])
		self.assertEqual(new.status, "Nháp")
		self.assertEqual(new.procedure, self.v2.name)
		self.assertEqual(new.previous_version, self.src)
		self.assertEqual(new.version_no, prior + 1)
		flags = {r.step_id: int(r.step_removed) for r in new.lines}
		self.assertEqual(flags, {"S001": 0, "S002": 1, "S003": 0, "S004": 0})
		src_ids = {r.step_id: r.line_id for r in frappe.get_doc(NS, self.src).lines}
		self.assertEqual({r.step_id: r.line_id for r in new.lines}, src_ids)  # giữ line_id
		self.assertEqual(res["steps_without_lines"], ["S005"])
		self.assertEqual(res["removed_steps"], ["S002"])
		self.assertEqual(len(res["carried"]), 3)
		self.assertTrue(all(not r.confirmed_by for r in new.lines))
		got = self.as_user(self.clin, api.get_norm_set, new.name)
		self.assertEqual([m["step_id"] for m in got["steps_without_lines"]], ["S005"])
		titles = [g["title"] for g in got["groups"]]
		self.assertIn("Bước đã bỏ", titles)
		self.assertLess(titles.index("Bước đã bỏ"), titles.index("Chung cho cả dịch vụ"))
		self.assertEqual(got["doc"]["newer_procedure"], None)
		self.assertTrue(
			frappe.get_all(
				"Comment",
				{"reference_doctype": NS, "reference_name": new.name, "content": ["like", "%S005%"]},
			)
		)
		# bộ nguồn không đổi
		self.assertEqual(frappe.db.get_value(NS, self.src, "status"), "Đã khóa")

	def test_FR_NORM_015_dong_buoc_bo_chan_xac_nhan(self):
		name = self.as_user(self.clin, api.new_version, self.src)["name"]
		got = self.as_user(self.head, api.get_norm_set, name)
		self.assertTrue(any("Thuộc bước đã bỏ" in b["reasons"] for b in got["blockers"]))
		with self.assertRaises(frappe.ValidationError):
			self.as_user(self.head, api.confirm_set, name)
		lid = next(r.line_id for r in frappe.get_doc(NS, name).lines if r.step_removed)
		with self.assertRaises(frappe.ValidationError):
			self.as_user(self.head, api.confirm_line, name, lid)

	def test_FR_NORM_015_xu_ly_dong_buoc_bo(self):
		name = self.as_user(self.clin, api.new_version, self.src)["name"]
		ns = frappe.get_doc(NS, name)
		gone = next(r.line_id for r in ns.lines if r.step_removed)
		kept = next(r.line_id for r in ns.lines if r.step_id == "S003")
		# gán bước hợp lệ → cờ gỡ
		self.as_user(self.clin, api.save_line, name, {"step_id": "S003"}, gone, 1)
		row = next(r for r in frappe.get_doc(NS, name).lines if r.line_id == gone)
		self.assertEqual((row.step_id, int(row.step_removed)), ("S003", 0))
		# xóa dòng có cờ được; dòng từ quy trình không cờ vẫn không xóa được
		name2 = self.as_user(self.clin, api.new_version, self.src)
		self.assertEqual(name2["existing"], 1)
		with self.assertRaises(frappe.ValidationError):
			self.as_user(self.clin, api.delete_line, name, kept)

	def test_FR_NORM_015_xoa_dong_co_co(self):
		name = self.as_user(self.clin, api.new_version, self.src)["name"]
		gone = next(r.line_id for r in frappe.get_doc(NS, name).lines if r.step_removed)
		self.as_user(self.clin, api.delete_line, name, gone)
		self.assertNotIn(gone, [r.line_id for r in frappe.get_doc(NS, name).lines])

	def test_FR_NORM_015_co_buoc_bo_khong_ghi_tu_client(self):
		name = self.as_user(self.clin, api.new_version, self.src)["name"]
		ns = frappe.get_doc(NS, name)
		for r in ns.lines:
			if r.step_id == "S001":
				r.step_removed = 1
		ns.save(ignore_permissions=True)
		self.assertEqual(self.steps_of(name)["S001"], 0)
		for r in ns.lines:
			if r.step_id == "S001":
				r.step_id = "S777"
				r.step_removed = 1
		with self.assertRaises(frappe.ValidationError):
			ns.save(ignore_permissions=True)

	def test_FR_NORM_015_tu_bo_nhap_va_khong_tao_trung(self):
		frappe.db.set_value(NS, self.src, "status", "Nháp")
		res = self.as_user(self.clin, api.new_version, self.src)
		self.assertEqual(res["existing"], 0)
		self.assertEqual(frappe.db.get_value(NS, self.src, "status"), "Nháp")
		again = self.as_user(self.clin, api.new_version, self.src)
		self.assertEqual((again["existing"], again["name"]), (1, res["name"]))

	def test_FR_NORM_015_khong_co_quy_trinh_moi_giu_hanh_vi_cu(self):
		ns = frappe.get_doc(NS, make_ns_on_v2(self))
		with self.assertRaises(frappe.ValidationError):
			self.as_user(self.clin, api.new_version, ns.name)  # Nháp, không có quy trình mới hơn
		self.lock(ns.name)
		res = self.as_user(self.clin, api.new_version, ns.name)
		self.assertEqual(frappe.db.get_value(NS, res["name"], "procedure"), self.v2.name)

	def test_FR_NORM_015_bo_da_thay_the_tu_choi(self):
		frappe.db.set_value(NS, self.src, "status", "Đã thay thế")
		with self.assertRaises(frappe.ValidationError):
			self.as_user(self.clin, api.new_version, self.src)

	def test_quyen_new_version_auditor_finance_khoa_khac(self):
		for user in (self.auditor, self.finance, self.clin_other):
			with self.assertRaises(frappe.PermissionError, msg=user):
				self.as_user(user, api.new_version, self.src)
		got = self.as_user(self.auditor, api.get_norm_set, self.src)
		self.assertNotIn("new_version", got["actions"])
		self.assertIn("new_version", self.as_user(self.clin, api.get_norm_set, self.src)["actions"])


def make_ns_on_v2(case):
	from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set

	return make_norm_set(case.v2.name)
