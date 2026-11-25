"""Tác vụ ngày của luồng duyệt (FR-WF-006, FR-WF-013; TC-WF-04)."""

import frappe
from frappe.utils import add_days, nowdate

from normcore.api import procedure_workflow as wf
from normcore.api.test_procedure_workflow import DT, WorkflowBase, _notified, _state
from normcore.tests.utils import make_procedure


class TestJobs(WorkflowBase):
	def full_flow(self, name, effective_date):
		self.name = name
		self.act(self.clin, "Gửi duyệt")
		self.act(self.head, "Đồng ý")
		self.act(self.sec, "Thông qua")
		self.act(self.director, "Ban hành", decision_no=f"QĐ-{name}", effective_date=effective_date)

	def test_TC_WF_04_phien_ban_cu_thay_the_dung_ngay_hieu_luc(self):
		self.full_flow(self.proc.name, "2020-01-01")
		self.assertEqual(_state(self.proc.name), "Đã ban hành")
		v2 = make_procedure(self.service, self.dept, version=2)
		day = add_days(nowdate(), 30)
		self.full_flow(v2.name, day)
		self.assertEqual(_state(v2.name), "Đã ban hành")
		# trước ngày: v1 còn hiệu lực
		self.assertEqual(wf.supersede_due(today=add_days(day, -1)), 0)
		self.assertEqual(_state(self.proc.name), "Đã ban hành")
		# đến ngày
		self.assertEqual(wf.supersede_due(today=day), 1)
		self.assertEqual(_state(self.proc.name), "Đã thay thế")
		self.assertEqual(_state(v2.name), "Đã ban hành")
		self.assertEqual(wf.supersede_due(today=day), 0)  # chạy lại không đổi
		events = frappe.get_all(
			"NC Audit Event",
			{"ref_name": self.proc.name, "to_state": "Đã thay thế"},
			pluck="from_state",
		)
		self.assertEqual(events, ["Đã ban hành"])

	def test_TC_WF_04_ngay_hieu_luc_hom_nay_thay_ngay_khi_ban_hanh(self):
		self.full_flow(self.proc.name, "2020-01-01")
		v2 = make_procedure(self.service, self.dept, version=2)
		self.full_flow(v2.name, nowdate())
		self.assertEqual(_state(self.proc.name), "Đã thay thế")

	def test_FR_WF_013_nhac_khi_qua_han(self):
		self.act(self.clin, "Gửi duyệt")
		today = frappe.utils.getdate(nowdate())
		self.assertEqual(wf.send_approval_reminders(today=add_days(today, 6)), 0)  # 6 ngày < 7
		self.assertEqual(wf.send_approval_reminders(today=add_days(today, 7)), 1)
		self.assertEqual(wf.send_approval_reminders(today=add_days(today, 8)), 0)  # đã nhắc
		self.assertTrue(any(s.startswith("Nhắc duyệt") for s in _notified(self.head, self.proc.name)))

	def test_FR_WF_013_theo_cau_hinh_so_ngay(self):
		frappe.db.set_single_value("NC Settings", "approval_reminder_days", 2)
		self.to_council()
		today = frappe.utils.getdate(nowdate())
		self.assertEqual(wf.send_approval_reminders(today=add_days(today, 1)), 0)
		created = wf.send_approval_reminders(today=add_days(today, 2))
		self.assertEqual(created, 2)  # thư ký và thành viên hội đồng
		self.assertTrue(any(s.startswith("Nhắc duyệt") for s in _notified(self.member, self.proc.name)))

	def test_daily_job_khai_o_hooks(self):
		self.assertIn("normcore.api.procedure_workflow.daily_job", frappe.get_hooks("scheduler_events")["daily"])
		wf.daily_job()
