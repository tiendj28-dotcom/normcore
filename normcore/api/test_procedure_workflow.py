"""Luồng duyệt ba cấp (FEAT-007; TC-PROC-05, 06, TC-WF-01, 02)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api import procedure_workflow as wf
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document
from normcore.tests.utils import make_base, make_procedure, make_user

DT = "NC Clinical Procedure"


def _state(name):
	return frappe.db.get_value(DT, name, "workflow_state")


def _notified(user, name):
	return frappe.get_all("Notification Log", {"for_user": user, "document_name": name}, pluck="subject")


class WorkflowBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_base()
		self.clin = make_user("clin.wf@normcore.test", "NC Clinician")
		self.head = make_user("head.wf@normcore.test", "NC Department Head")
		self.head2 = make_user("head2.wf@normcore.test", "NC Department Head")
		self.sec = make_user("sec.wf@normcore.test", "NC Council Member")
		self.member = make_user("mem.wf@normcore.test", "NC Council Member")
		self.director = make_user("dir.wf@normcore.test", "NC Director")
		self.auditor = make_user("aud.wf@normcore.test", "NC Auditor")
		self.finance = make_user("fin.wf@normcore.test", "NC Finance")
		access.assign_department(self.clin, self.dept)
		access.assign_department(self.head, self.dept)
		frappe.db.set_value("NC Department", self.dept, "head_user", self.head)
		settings = frappe.get_single("NC Settings")
		settings.council_secretary = self.sec
		settings.save(ignore_permissions=True)
		self.proc = make_procedure(self.service, self.dept)
		frappe.db.set_value(DT, self.proc.name, "owner", self.clin)
		self.name = self.proc.name

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def act(self, user, action, **kw):
		frappe.set_user(user)
		try:
			return wf.apply_action(self.name, action, **kw)
		finally:
			frappe.set_user("Administrator")

	def to_council(self):
		self.act(self.clin, "Gửi duyệt")
		self.act(self.head, "Đồng ý")


class TestApplyAction(WorkflowBase):
	def test_TC_WF_01_luong_bon_trang_thai_va_thong_bao(self):
		self.assertEqual(self.act(self.clin, "Gửi duyệt")["workflow_state"], "Chờ trưởng khoa duyệt")
		self.assertTrue(_notified(self.head, self.name))
		self.act(self.head, "Đồng ý")
		self.assertEqual(_state(self.name), "Chờ hội đồng thẩm định")
		self.assertTrue(_notified(self.sec, self.name))
		self.assertTrue(_notified(self.member, self.name))
		self.act(self.sec, "Thông qua")
		self.assertEqual(_state(self.name), "Chờ ban hành")
		self.assertTrue(_notified(self.director, self.name))
		self.act(self.director, "Ban hành", decision_no="123/QĐ-BV", effective_date="2026-01-01")
		self.assertEqual(_state(self.name), "Đã ban hành")
		self.assertEqual(frappe.db.get_value(DT, self.name, "decision_no"), "123/QĐ-BV")
		self.assertTrue(_notified(self.clin, self.name))
		events = frappe.get_all(
			"NC Audit Event",
			{"ref_name": self.name, "event_type": "Chuyển trạng thái"},
			["from_state", "to_state"],
			order_by="event_time asc, creation asc",
		)
		self.assertEqual(
			[(e.from_state, e.to_state) for e in events][-4:],
			[
				("Nháp", "Chờ trưởng khoa duyệt"),
				("Chờ trưởng khoa duyệt", "Chờ hội đồng thẩm định"),
				("Chờ hội đồng thẩm định", "Chờ ban hành"),
				("Chờ ban hành", "Đã ban hành"),
			],
		)

	def test_TC_WF_01_ca_am(self):
		self.act(self.clin, "Gửi duyệt")
		# trưởng khoa khoa khác
		frappe.db.delete("User Permission", {"user": self.head2})
		with self.assertRaises(frappe.PermissionError):
			self.act(self.head2, "Đồng ý")
		self.assertEqual(_state(self.name), "Chờ trưởng khoa duyệt")
		self.act(self.head, "Đồng ý")
		# thành viên hội đồng không phải thư ký
		with self.assertRaises(frappe.PermissionError):
			self.act(self.member, "Thông qua")
		self.act(self.sec, "Thông qua")
		# thiếu số quyết định
		with self.assertRaises(frappe.ValidationError):
			self.act(self.director, "Ban hành", effective_date="2026-01-01")
		with self.assertRaises(frappe.ValidationError):
			self.act(self.director, "Ban hành", decision_no="1/QĐ")
		self.assertEqual(_state(self.name), "Chờ ban hành")

	def test_hanh_dong_sai_trang_thai(self):
		with self.assertRaises(frappe.ValidationError):
			self.act(self.director, "Ban hành", decision_no="1", effective_date="2026-01-01")
		self.assertEqual(_state(self.name), "Nháp")

	def test_chua_cau_hinh_thu_ky(self):
		self.to_council()
		frappe.db.set_single_value("NC Settings", "council_secretary", None)
		with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
			self.act(self.sec, "Thông qua")
		self.assertEqual(_state(self.name), "Chờ hội đồng thẩm định")

	def test_quyen_auditor_va_finance(self):
		for user in (self.auditor, self.finance):
			with self.assertRaises(frappe.PermissionError):
				self.act(user, "Gửi duyệt")
		self.act(self.clin, "Gửi duyệt")
		for user in (self.auditor, self.finance):
			for action in ("Đồng ý", "Từ chối"):
				with self.assertRaises(frappe.PermissionError):
					self.act(user, action, reason="x")
		self.assertEqual(_state(self.name), "Chờ trưởng khoa duyệt")

	def test_TC_PROC_05_khac_biet_thieu_ly_do(self):
		doc = frappe.get_doc(DT, self.name)
		legal = make_legal_document("TT/NORM65").name  # NORM-65: legal_document là Link, cần bản ghi thật
		doc.append(
			"citations", {"target_section": "Chỉ định", "relation": "Khác biệt", "legal_document": legal}
		)
		doc.save(ignore_permissions=True)  # lưu nháp vẫn được
		with self.assertRaises(frappe.ValidationError) as cm:
			self.act(self.clin, "Gửi duyệt")
		self.assertIn("Trích dẫn dòng 1", str(cm.exception))
		self.assertIn("Chỉ định", str(cm.exception))
		self.assertEqual(_state(self.name), "Nháp")
		self.assertEqual(_notified(self.head, self.name), [])

	def test_TC_PROC_06_liet_ke_du_ba_loi(self):
		doc = frappe.get_doc(DT, self.name)
		doc.steps[0].phase = "Chuẩn bị"
		doc.append("steps", {"phase": "Chuẩn bị", "step_title": "B2", "description": ""})
		doc.append(
			"resources",
			{
				"step_id": doc.steps[0].step_id,
				"resource_type": "Vật tư",
				"resource_text": "Găng",
				"quantity": 1,
				"uom": "",
			},
		)
		doc.flags.ignore_mandatory = True  # dữ liệu cũ hoặc nhập qua đường khác có thể thiếu trường bắt buộc
		doc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError) as cm:
			self.act(self.clin, "Gửi duyệt")
		msg = str(cm.exception)
		self.assertIn("giai đoạn 'Thực hiện'", msg)
		self.assertIn("S002 thiếu mô tả", msg)
		self.assertIn("thiếu đơn vị", msg)
		self.assertEqual(_state(self.name), "Nháp")

	def test_TC_WF_02_tu_choi_o_ca_ba_cap(self):
		cases = (
			("Chờ trưởng khoa duyệt", lambda: None, self.head, "trưởng khoa"),
			("Chờ hội đồng thẩm định", lambda: self.act(self.head, "Đồng ý"), self.sec, "hội đồng"),
		)
		for target, prep, who, level in cases:
			with self.subTest(level=level):
				self.act(self.clin, "Gửi duyệt")
				prep()
				self.assertEqual(_state(self.name), target)
				with self.assertRaises(frappe.ValidationError):
					self.act(who, "Từ chối", reason="  ")
				self.assertEqual(_state(self.name), target)
				self.act(who, "Từ chối", reason="Thiếu căn cứ")
				self.assertEqual(_state(self.name), "Nháp")
				subjects = _notified(self.clin, self.name)
				self.assertTrue(any(level in s and "Thiếu căn cứ" in s for s in subjects))
				detail = frappe.get_all(
					"NC Audit Event",
					{"ref_name": self.name, "to_state": "Nháp", "from_state": target},
					pluck="detail",
				)
				self.assertEqual(detail, ["Thiếu căn cứ"])
		# cấp giám đốc
		self.to_council()
		self.act(self.sec, "Thông qua")
		with self.assertRaises(frappe.ValidationError):
			self.act(self.director, "Từ chối")
		self.act(self.director, "Từ chối", reason="Chưa đủ")
		self.assertEqual(_state(self.name), "Nháp")

	def test_get_review_hanh_dong_theo_nguoi(self):
		frappe.set_user(self.clin)
		self.assertEqual(wf.get_review(self.name)["actions"], ["Gửi duyệt"])
		frappe.set_user("Administrator")
		self.act(self.clin, "Gửi duyệt")
		frappe.set_user(self.head)
		self.assertEqual(wf.get_review(self.name)["actions"], ["Đồng ý", "Từ chối"])
		frappe.set_user(self.auditor)
		self.assertEqual(wf.get_review(self.name)["actions"], [])
		frappe.set_user(self.sec)
		self.assertTrue(wf.get_review(self.name)["is_secretary"])
