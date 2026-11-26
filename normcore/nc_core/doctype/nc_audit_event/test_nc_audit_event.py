"""FEAT-003: sổ sự kiện, tính bất biến, tra cứu (TC-AUD-01..03, FR-AUD-001..004)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import audit as audit_api
from normcore.core import audit
from normcore.tests.utils import confirm_norm_set, make_base, make_procedure, make_user, publish_procedure


def _publish(proc):
	publish_procedure(proc, "QĐ-01", "2026-12-01")


class TestNCAuditEvent(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()
		self.admin = make_user("admin.aud@normcore.test", "NC Admin")
		self.director = make_user("dir.aud@normcore.test", "NC Director")
		self.auditor = make_user("auditor.aud@normcore.test", "NC Auditor")
		self.clin = make_user("clin.aud@normcore.test", "NC Clinician")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _event(self):
		return audit.log_event("Xuất tệp", "NC Department", self.dept, detail="x")

	def _events_of(self, doctype, name):
		return frappe.get_all(
			"NC Audit Event",
			{"ref_doctype": doctype, "ref_name": name},
			["name", "event_type", "from_state", "to_state", "user"],
			order_by="event_time asc, creation asc",
		)

	def test_TC_AUD_01_lich_su_va_su_kien(self):
		# lịch sử theo trường: sửa một danh mục (NC Item Price chưa có, ASM-068)
		jt = frappe.get_doc("NC Job Title", self.job)
		old = jt.job_title_name
		jt.job_title_name = "Điều dưỡng chính"
		jt.save(ignore_version=False)
		ver = frappe.get_all("Version", {"ref_doctype": "NC Job Title", "docname": self.job}, pluck="data")
		self.assertTrue(ver)
		changed = frappe.parse_json(ver[0])["changed"]
		self.assertIn(["job_title_name", old, "Điều dưỡng chính"], changed)
		# sự kiện chuyển trạng thái khi ban hành quy trình
		proc = make_procedure(self.service, self.dept)
		frappe.set_user(self.director)
		_publish(frappe.get_doc("NC Clinical Procedure", proc.name))
		events = self._events_of("NC Clinical Procedure", proc.name)
		self.assertEqual(
			[(e.from_state, e.to_state) for e in events], [("", "Nháp"), ("Nháp", "Đã ban hành")]
		)
		self.assertEqual(events[-1].event_type, "Chuyển trạng thái")
		self.assertEqual(events[-1].user, self.director)

	def test_FR_AUD_001_khoa_bo_dinh_muc(self):
		from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set

		proc = make_procedure(self.service, self.dept)
		_publish(proc)
		ns = frappe.get_doc("NC Norm Set", make_norm_set(proc.name))
		fin = make_user("fin.aud@normcore.test", "NC Finance")
		frappe.set_user(fin)
		confirm_norm_set(ns)
		ns.lock()
		events = self._events_of("NC Norm Set", ns.name)
		self.assertEqual(events[-1].event_type, "Khóa")
		self.assertEqual((events[-1].from_state, events[-1].to_state), ("Đã xác nhận chuyên môn", "Đã khóa"))
		self.assertEqual(events[-1].user, fin)

	def test_FR_AUD_001_xoa_ban_ghi_nguon_khong_bi_chan(self):
		frappe.get_doc(
			{"doctype": "NC Specialty", "specialty_code": "CK-AUD", "specialty_name": "CK"}
		).insert()
		audit.log_event("Đổi cấu hình", "NC Specialty", "CK-AUD", detail="thử")
		frappe.delete_doc("NC Specialty", "CK-AUD")
		self.assertFalse(frappe.db.exists("NC Specialty", "CK-AUD"))

	def test_TC_AUD_02_ban_ghi_bat_bien(self):
		name = self._event().name
		log = frappe.get_doc(
			{"doctype": "NC AI Log", "purpose": "DRAFT_PROCEDURE", "status": "Thành công"}
		).insert(ignore_permissions=True)
		for dt, n in (("NC Audit Event", name), ("NC AI Log", log.name)):
			for who in (self.admin, "Administrator"):
				frappe.set_user(who)
				# giao diện / API: kiểm quyền
				self.assertFalse(frappe.has_permission(dt, "write", n) and who != "Administrator", (dt, who))
				self.assertFalse(frappe.has_permission(dt, "delete", n) and who != "Administrator", (dt, who))
				with self.assertRaises(frappe.PermissionError):
					frappe.client.set_value(dt, n, "detail" if dt == "NC Audit Event" else "response", "sửa")
				with self.assertRaises(frappe.PermissionError):
					frappe.client.delete(dt, n)
				doc = frappe.get_doc(dt, n)
				doc.flags.ignore_permissions = True
				with self.assertRaises(frappe.PermissionError):
					doc.save()
				with self.assertRaises(frappe.PermissionError):
					doc.delete()
				self.assertTrue(frappe.db.exists(dt, n))
		frappe.set_user("Administrator")

	def test_FR_AUD_002_khong_tao_ngoai_ma_may_chu(self):
		for who in (self.admin, self.auditor, self.clin, "Administrator"):
			frappe.set_user(who)
			self.assertFalse(frappe.has_permission("NC Audit Event", "create") and who != "Administrator")
			with self.assertRaises(frappe.PermissionError):
				frappe.get_doc(
					{"doctype": "NC Audit Event", "event_type": "Xuất tệp", "event_time": frappe.utils.now()}
				).insert(ignore_permissions=who == "Administrator")
		frappe.set_user("Administrator")

	def test_TC_AUD_03_loc_theo_quy_trinh(self):
		p1 = make_procedure(self.service, self.dept)
		p2 = make_procedure(self.service, self.dept, version=2)
		_publish(p1)
		frappe.set_user(self.director)
		rows = audit_api.get_events(ref_doctype="NC Clinical Procedure", ref_name=p1.name)
		self.assertEqual([r["to_state"] for r in rows], ["Nháp", "Đã ban hành"])
		self.assertEqual({r["ref_name"] for r in rows}, {p1.name})
		times = [r["event_time"] for r in rows]
		self.assertEqual(times, sorted(times))
		other = audit_api.get_events(ref_doctype="NC Clinical Procedure", ref_name=p2.name)
		self.assertEqual(len(other), 1)

	def test_FR_AUD_003_loc_nguoi_thoi_gian_va_quyen(self):
		p = make_procedure(self.service, self.dept)
		frappe.set_user(self.director)
		_publish(frappe.get_doc("NC Clinical Procedure", p.name))
		for who in (self.auditor, self.admin):
			frappe.set_user(who)
			rows = audit_api.get_events(user=self.director, ref_name=p.name)
			self.assertEqual([r["to_state"] for r in rows], ["Đã ban hành"])
		rows = audit_api.get_events(ref_name=p.name, from_time="2000-01-01", to_time="2000-01-02")
		self.assertEqual(rows, [])
		rows = audit_api.get_events(ref_name=p.name, from_time="2000-01-01")
		self.assertEqual(len(rows), 2)
		frappe.set_user(self.clin)
		with self.assertRaises(frappe.PermissionError):
			audit_api.get_events()

	def test_FR_AUD_004_ghi_xuat_tep(self):
		frappe.set_user(self.director)
		ev = audit.log_export("xlsx", "NC Department", self.dept, "gia-thanh.xlsx")
		doc = frappe.get_doc("NC Audit Event", ev.name)
		self.assertEqual(doc.event_type, "Xuất tệp")
		self.assertEqual(doc.user, self.director)
		self.assertEqual((doc.ref_doctype, doc.ref_name), ("NC Department", self.dept))
		self.assertIn("xlsx", doc.detail)
		self.assertIn("gia-thanh.xlsx", doc.detail)

	# --- Sửa theo Reviewer (NORM-21): NC Costing Run, xóa, to_time ---

	def _run(self):
		from normcore.tests.utils import make_param_set

		params = make_param_set()
		run = frappe.get_doc(
			{
				"doctype": "NC Costing Run",
				"title": "Lần tính thử",
				"fiscal_year": 2026,
				"costing_date": "2026-12-31",
				"parameter_set": params.name,
			}
		)
		run.insert(ignore_permissions=True)
		return run

	def test_FR_AUD_001_lan_tinh_gia_thanh_cong_mot_su_kien_moi_lan_chuyen(self):
		run = self._run()
		run.run_costing()
		events = self._events_of("NC Costing Run", run.name)
		self.assertEqual([(e.from_state, e.to_state) for e in events], [("", "Nháp"), ("Nháp", "Đã tính")])

	def test_FR_AUD_001_lan_tinh_gia_loi_roi_tinh_lai(self):
		from unittest import mock

		from normcore.nc_costing.doctype.nc_costing_run.nc_costing_run import NCCostingRun

		run = self._run()
		with mock.patch.object(NCCostingRun, "_run", side_effect=RuntimeError("boom")):
			run.run_costing()
		self.assertEqual(run.status, "Tính lỗi")
		run.run_costing()  # cùng đối tượng, hai lần db_set liên tiếp
		events = self._events_of("NC Costing Run", run.name)
		self.assertEqual(
			[(e.from_state, e.to_state) for e in events],
			[("", "Nháp"), ("Nháp", "Tính lỗi"), ("Tính lỗi", "Đã tính")],
		)

	def test_FR_AUD_001_luu_nhieu_lan_khong_ghi_trung(self):
		proc = make_procedure(self.service, self.dept)
		for _i in range(3):
			doc = frappe.get_doc("NC Clinical Procedure", proc.name)
			doc.save(ignore_permissions=True)
		self.assertEqual(len(self._events_of("NC Clinical Procedure", proc.name)), 1)

	def test_FR_AUD_001_xoa_de_lai_su_kien_va_gia_tri_truoc(self):
		jt = frappe.get_doc("NC Job Title", self.job)
		jt.job_title_name = "Điều dưỡng chính"
		jt.save(ignore_version=False)
		frappe.set_user(self.admin)
		frappe.delete_doc("NC Job Title", self.job)
		frappe.set_user("Administrator")
		self.assertFalse(frappe.db.exists("Version", {"ref_doctype": "NC Job Title", "docname": self.job}))
		events = frappe.get_all(
			"NC Audit Event",
			{"ref_doctype": "NC Job Title", "ref_name": self.job, "event_type": "Xóa"},
			["user", "event_time", "before_value"],
		)
		self.assertEqual(len(events), 1)
		self.assertEqual(events[0].user, self.admin)
		self.assertTrue(events[0].event_time)
		before = frappe.parse_json(events[0].before_value)
		self.assertEqual(before["doc"]["job_title_name"], "Điều dưỡng chính")
		self.assertEqual(len(before["versions"]), 1)
		self.assertIn("job_title_name", before["versions"][0]["data"])
		self.assertTrue(before["owner"] and before["creation"])

	def test_FR_AUD_001_xoa_bi_chan_thi_khong_co_su_kien(self):
		spec = frappe.get_doc(
			{"doctype": "NC Specialty", "specialty_code": "CK-X", "specialty_name": "CK"}
		).insert()
		svc = frappe.get_doc("NC Technical Service", self.service)
		svc.specialty = spec.name
		svc.save()
		with self.assertRaises(frappe.LinkExistsError):
			frappe.delete_doc("NC Specialty", spec.name)
		self.assertFalse(frappe.db.exists("NC Audit Event", {"ref_name": spec.name, "event_type": "Xóa"}))

	def test_FR_AUD_001_gia_tri_truoc_bo_truong_password(self):
		user = frappe.get_doc("User", self.admin)
		snap = frappe.parse_json(audit.snapshot(user))
		self.assertNotIn("new_password", snap["doc"])

	def test_FR_AUD_003_to_time_chi_co_ngay_lay_tron_ngay(self):
		today = frappe.utils.today()
		ev = audit.log_event("Xuất tệp", "NC Department", self.dept, detail="x")
		for to_time in (today, frappe.utils.now_datetime() + frappe.utils.datetime.timedelta(minutes=1)):
			rows = audit_api.get_events(ref_name=self.dept, to_time=str(to_time))
			self.assertIn(ev.name, [r["name"] for r in rows], to_time)
		yesterday = frappe.utils.add_days(today, -1)
		rows = audit_api.get_events(ref_name=self.dept, to_time=yesterday)
		self.assertNotIn(ev.name, [r["name"] for r in rows])
		rows = audit_api.get_events(ref_name=self.dept, from_time=today, to_time=today)
		self.assertIn(ev.name, [r["name"] for r in rows])
