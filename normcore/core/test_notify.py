"""core/notify: thông báo, email, nguồn việc chờ (FEAT-002; FR-NOTI-001..003)."""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api import procedure_workflow as wf
from normcore.core import notify
from normcore.tests.utils import make_base, make_procedure, make_user

DT = "NC Clinical Procedure"


def _logs(user, name, subject=None):
	f = {"for_user": user, "document_type": DT, "document_name": name}
	if subject:
		f["subject"] = subject
	return frappe.get_all("Notification Log", f, ["subject", "type", "from_user"])


class NotifyBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_base()
		self.proc = make_procedure(self.service, self.dept)
		self.name = self.proc.name
		self.u1 = make_user("n1.noti@normcore.test", "NC Clinician")
		self.u2 = make_user("n2.noti@normcore.test", "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()


class TestNotify(NotifyBase):
	def test_FR_NOTI_001_notify_bo_administrator_guest_va_user_tat(self):
		frappe.db.set_value("User", self.u2, "enabled", 0)
		n = notify.notify(["Administrator", "Guest", "", None, self.u2, self.u1], "Tiêu đề", DT, self.name)
		self.assertEqual(n, 1)
		self.assertEqual(len(_logs(self.u1, self.name)), 1)
		self.assertEqual(_logs(self.u2, self.name), [])
		self.assertEqual(_logs("Administrator", self.name), [])

	def test_FR_NOTI_001_notify_gop_trung_va_goi_lai_khong_tao_them(self):
		self.assertEqual(notify.notify([self.u1, self.u1], "Tiêu đề", DT, self.name), 1)
		self.assertEqual(notify.notify([self.u1], "Tiêu đề", DT, self.name), 0)
		self.assertEqual(notify.notify([self.u1], "Tiêu đề khác", DT, self.name), 1)
		self.assertEqual(len(_logs(self.u1, self.name)), 2)

	def test_FR_NOTI_001_notify_co_lien_ket_ban_ghi(self):
		notify.notify([self.u1], "Tiêu đề", DT, self.name, from_user=self.u2)
		row = _logs(self.u1, self.name)[0]
		self.assertEqual((row.type, row.from_user), ("Alert", self.u2))

	def test_FR_NOTI_002_email_khi_co_may_chu(self):
		with patch("frappe.sendmail") as sendmail:
			notify.notify([self.u1], "Email thử", DT, self.name)
		sendmail.assert_called_once()
		kwargs = sendmail.call_args.kwargs
		self.assertEqual(kwargs["recipients"], self.u1)
		self.assertIn("/app/nc-clinical-procedure/", kwargs["args"]["doc_link"])
		self.assertTrue(kwargs["args"]["doc_link"].endswith(self.name))

	def test_FR_NOTI_002_khong_may_chu_van_thong_bao(self):
		with patch("frappe.sendmail", side_effect=frappe.OutgoingEmailError("không có máy chủ")):
			n = notify.notify([self.u1], "Không email", DT, self.name)
		self.assertEqual(n, 1)
		self.assertEqual(len(_logs(self.u1, self.name, "Không email")), 1)


class TestPendingSources(NotifyBase):
	def test_FR_NOTI_003_nguon_loi_duong_dan_bi_bo(self):
		hooks = ["normcore.api.procedure_workflow.pending_for", "normcore.khong_co.module.ham"]
		with patch("frappe.get_hooks", return_value=hooks), patch("frappe.log_error") as log:
			sources = notify.register_pending_sources()
		self.assertEqual([s.__name__ for s in sources], ["pending_for"])
		log.assert_called_once()

	def test_FR_NOTI_003_nguon_nem_loi_khong_lam_hong_nguon_khac(self):
		def boom(user):
			raise RuntimeError("hỏng")

		def good(user):
			return [{"name": "A", "since": "2026-01-02"}]

		with (
			patch("normcore.core.notify.register_pending_sources", return_value=[boom, good]),
			patch("frappe.log_error"),
		):
			self.assertEqual(notify.pending_for(self.u1), [{"name": "A", "since": "2026-01-02"}])

	def test_FR_NOTI_003_sap_theo_since_tang_dan(self):
		items = [{"name": "B", "since": "2026-03-01"}, {"name": "A", "since": "2026-01-01"}]
		with patch("normcore.core.notify.register_pending_sources", return_value=[lambda u: items]):
			self.assertEqual([i["name"] for i in notify.pending_for(self.u1)], ["A", "B"])

	def test_FR_NOTI_003_nguon_quy_trinh_cho_dung_truong_khoa(self):
		head = make_user("head.noti@normcore.test", "NC Department Head")
		other = make_user("head2.noti@normcore.test", "NC Department Head")
		access.assign_department(head, self.dept)
		frappe.db.set_value(DT, self.name, "workflow_state", "Chờ trưởng khoa duyệt")
		got = wf.pending_for(head)
		self.assertEqual([i["name"] for i in got], [self.name])
		self.assertEqual(got[0]["task"], "Duyệt cấp trưởng khoa")
		self.assertEqual(got[0]["route"], f"/app/procedure-editor/{self.name}")
		self.assertEqual(wf.pending_for(other), [])
		self.assertEqual(wf.pending_for("Guest"), [])
