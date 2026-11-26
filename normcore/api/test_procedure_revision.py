"""Sửa đổi quy trình đã ban hành (FEAT-008; TC-WF-05, FR-WF-009)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api import procedure as api
from normcore.tests.utils import make_base, make_procedure, make_user, publish_procedure, to_state

DT = "NC Clinical Procedure"


def make_v1(service, dept, n_steps=4):
	"""Quy trình phiên bản 1 có `n_steps` bước S001.., mỗi bước một dòng nguồn lực, đã ban hành."""
	proc = make_procedure(service, dept)
	for i in range(2, n_steps + 1):
		proc.append("steps", {"phase": "Thực hiện", "step_title": f"Bước {i}", "description": f"Mô tả {i}"})
	proc.overview, proc.indications = "Đại cương v1", "Chỉ định v1"
	proc.save(ignore_permissions=True)
	for s in proc.steps[1:]:
		proc.append(
			"resources",
			{
				"step_id": s.step_id,
				"resource_type": "Nhân lực",
				"resource_text": "Điều dưỡng",
				"linked_doctype": "NC Job Title",
				"linked_name": "DD",
				"quantity": 5,
				"uom": "phút",
				"headcount": 1,
			},
		)
	proc.save(ignore_permissions=True)
	return publish_procedure(proc)


class RevisionBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_base()
		self.clin = make_user("clin.rev@normcore.test", "NC Clinician")
		self.head = make_user("head.rev@normcore.test", "NC Department Head")
		self.clin_other = make_user("clin2.rev@normcore.test", "NC Clinician")
		self.auditor = make_user("aud.rev@normcore.test", "NC Auditor")
		self.finance = make_user("fin.rev@normcore.test", "NC Finance")
		self.director = make_user("dir.rev@normcore.test", "NC Director")
		for u in (self.clin, self.head):
			access.assign_department(u, self.dept)
		other = make_base(department="KHOA-KHAC")[1]
		access.assign_department(self.clin_other, other)
		self.v1 = make_v1(self.service, self.dept)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def revise(self, user, name=None):
		frappe.set_user(user)
		try:
			return api.create_revision(name or self.v1.name)
		finally:
			frappe.set_user("Administrator")


class TestCreateRevision(RevisionBase):
	def test_TC_WF_05_sua_doi_giu_ma_buoc(self):
		self.assertEqual(len(self.v1.steps), 4)
		res = self.revise(self.clin)
		self.assertEqual((res["version_no"], res["existing"]), (2, 0))
		v2 = frappe.get_doc(DT, res["name"])
		self.assertEqual(v2.workflow_state, "Nháp")
		self.assertEqual(v2.previous_version, self.v1.name)
		self.assertEqual([s.step_id for s in v2.steps], [s.step_id for s in self.v1.steps])
		self.assertEqual([s.step_id for s in v2.steps], ["S001", "S002", "S003", "S004"])
		self.assertEqual(
			[r.resource_row_id for r in v2.resources], [r.resource_row_id for r in self.v1.resources]
		)
		self.assertEqual([r.step_id for r in v2.resources], [r.step_id for r in self.v1.resources])
		for f in ("overview", "indications", "contraindications", "cautions", "monitoring", "references"):
			self.assertEqual(v2.get(f), self.v1.get(f))
		self.assertEqual(v2.next_step_seq, self.v1.next_step_seq)
		self.assertEqual(v2.next_resource_seq, self.v1.next_resource_seq)
		self.assertFalse(v2.decision_no)
		self.assertFalse(v2.effective_date)
		# bước thêm mới không tái dùng mã
		v2.append("steps", {"phase": "Thực hiện", "step_title": "Mới", "description": "m"})
		v2.save(ignore_permissions=True)
		self.assertEqual(v2.steps[-1].step_id, "S005")

	def test_ma_khong_tai_dung_sau_khi_bo_buoc(self):
		v2 = frappe.get_doc(DT, self.revise(self.clin)["name"])
		v2.steps = [s for s in v2.steps if s.step_id != "S004"]
		v2.resources = [r for r in v2.resources if r.step_id != "S004"]
		v2.save(ignore_permissions=True)
		v2.append("steps", {"phase": "Thực hiện", "step_title": "Mới", "description": "m"})
		v2.save(ignore_permissions=True)
		self.assertEqual(v2.steps[-1].step_id, "S005")

	def test_truong_department_head_sua_doi_duoc(self):
		self.assertEqual(self.revise(self.head)["version_no"], 2)

	def test_sua_doi_da_co_ban_nhap_tra_ban_dang_co(self):
		first = self.revise(self.clin)
		count = frappe.db.count(DT, {"technical_service": self.service, "department": self.dept})
		again = self.revise(self.clin)
		self.assertEqual(again["name"], first["name"])
		self.assertEqual(again["existing"], 1)
		self.assertEqual(frappe.db.count(DT, {"technical_service": self.service, "department": self.dept}), count)

	def test_sua_doi_tu_choi_trang_thai_va_quyen(self):
		for role_user in (self.auditor, self.finance, self.director, self.clin_other):
			with self.assertRaises(frappe.PermissionError, msg=role_user):
				self.revise(role_user)
		for state in ("Đã thay thế", "Đã thu hồi"):
			to_state(self.v1, state)
			with self.assertRaises(frappe.ValidationError, msg=state):
				self.revise(self.clin)
		# bản Nháp (không phải bản ban hành)
		to_state(self.v1, "Nháp")
		draft_res = self.revise(self.clin)
		self.assertEqual(draft_res["existing"], 1)  # bản Nháp chính là bản đang soạn

	def test_sua_doi_tu_choi_ban_ban_hanh_cu_hon(self):
		v2 = frappe.get_doc(DT, self.revise(self.clin)["name"])
		publish_procedure(v2, "QĐ-2", "2027-01-01")
		with self.assertRaises(frappe.ValidationError):
			self.revise(self.clin, self.v1.name)
		self.assertEqual(self.revise(self.clin, v2.name)["version_no"], 3)

	def test_ghi_comment_va_lich_su(self):
		name = self.revise(self.clin)["name"]
		comments = frappe.get_all(
			"Comment", {"reference_doctype": DT, "reference_name": name, "comment_type": "Info"}, pluck="content"
		)
		self.assertTrue(any(self.v1.name in c for c in comments))


class TestListVersions(RevisionBase):
	def test_list_versions_moi_nhat_truoc(self):
		self.revise(self.clin)
		frappe.set_user(self.auditor)
		try:
			rows = api.list_versions(self.v1.name)
		finally:
			frappe.set_user("Administrator")
		self.assertEqual([r.version_no for r in rows], [2, 1])

	def test_list_versions_khoa_khac(self):
		# bản "Đã ban hành" đọc công khai; bản Nháp của khoa khác thì không
		v2 = self.revise(self.clin)["name"]
		frappe.set_user(self.clin_other)
		try:
			with self.assertRaises(frappe.PermissionError):
				api.list_versions(v2)
			self.assertEqual([r.name for r in api.list_versions(self.v1.name)], [self.v1.name])
		finally:
			frappe.set_user("Administrator")
