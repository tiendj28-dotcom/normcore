"""Trang chủ: việc chờ, thông báo, tình trạng chuỗi (FEAT-002; TC-NOTI-01, FR-NOTI-003, FR-OUT-010)."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access, home
from normcore.api import procedure_workflow as wf
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import (
	make_base,
	make_chain_data,
	make_procedure,
	make_user,
	publish_procedure,
)

DT = "NC Clinical Procedure"
K, K2 = "K-HOME1", "K-HOME2"


def _as(user, fn, *args, **kw):
	frappe.set_user(user)
	try:
		return fn(*args, **kw)
	finally:
		frappe.set_user("Administrator")


def _counts(res):
	return {s["stage"]: s["count"] for s in res["stages"]}


class HomeBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base(service="DV-HOME0", department=K)
		self.dept2 = make_base(service="DV-HOME-X", department=K2)[1]
		self.clin = make_user("clin.home@normcore.test", "NC Clinician")
		self.head = make_user("head.home@normcore.test", "NC Department Head")
		self.head2 = make_user("head2.home@normcore.test", "NC Department Head")
		self.sec = make_user("sec.home@normcore.test", "NC Council Member")
		self.member = make_user("mem.home@normcore.test", "NC Council Member")
		self.finance = make_user("fin.home@normcore.test", "NC Finance")
		self.auditor = make_user("aud.home@normcore.test", "NC Auditor")
		access.assign_department(self.clin, K)
		access.assign_department(self.head, K)
		access.assign_department(self.head2, K2)
		frappe.db.set_value("NC Department", K, "head_user", self.head)
		settings = frappe.get_single("NC Settings")
		settings.council_secretary = self.sec
		settings.save(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _assign(self, svc, *depts):
		doc = frappe.get_doc("NC Technical Service", svc)
		for d in depts:
			doc.append("departments", {"department": d})
		doc.save()


class TestHomePending(HomeBase):
	def setUp(self):
		super().setUp()
		self.proc = make_procedure(self.service, K)
		frappe.db.set_value(DT, self.proc.name, "owner", self.clin)
		self.name = self.proc.name

	def test_TC_NOTI_01_gui_duyet_thong_bao_va_trang_chu_truong_khoa(self):
		_as(self.clin, wf.apply_action, self.name, "Gửi duyệt")
		logs = frappe.get_all(
			"Notification Log",
			{"for_user": self.head, "document_type": DT, "document_name": self.name},
			["subject"],
		)
		self.assertEqual(len(logs), 1)
		pending = _as(self.head, home.get_home)["pending"]
		self.assertEqual([p["name"] for p in pending], [self.name])
		self.assertEqual(pending[0]["task"], "Duyệt cấp trưởng khoa")
		self.assertEqual(pending[0]["route"], f"/app/procedure-editor/{self.name}")

	def test_TC_NOTI_01_viec_cho_dung_nguoi(self):
		_as(self.clin, wf.apply_action, self.name, "Gửi duyệt")
		for user in (self.head2, self.finance, self.clin):
			self.assertEqual(_as(user, home.get_home)["pending"], [], user)
		_as(self.head, wf.apply_action, self.name, "Đồng ý")
		self.assertEqual(_as(self.head, home.get_home)["pending"], [])
		sec = _as(self.sec, home.get_home)["pending"]
		self.assertEqual([p["task"] for p in sec], ["Thẩm định cấp hội đồng"])
		self.assertEqual(_as(self.member, home.get_home)["pending"], [])

	def test_quyen_get_home_guest(self):
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				home.get_home()
		finally:
			frappe.set_user("Administrator")

	def test_TC_NOTI_01_auditor_khong_co_viec(self):
		_as(self.clin, wf.apply_action, self.name, "Gửi duyệt")
		self.assertEqual(_as(self.auditor, home.get_home)["pending"], [])


class TestStages(HomeBase):
	def setUp(self):
		super().setUp()
		self.s = {}
		for i, code in enumerate(("DV-HOME1", "DV-HOME2", "DV-HOME3", "DV-HOME4", "DV-HOME5")):
			make_base(service=code, department=K)
			self.s[i] = code
		for code in self.s.values():
			self._assign(code, K)
		# DV-HOME1 không có gì; DV-HOME2 có quy trình; DV-HOME3 có định mức khóa; DV-HOME4 đã tính;
		# DV-HOME5 đã tính nhưng ngừng hoạt động (không được đếm)
		publish_procedure(make_procedure(self.s[1], K, job=self.job), "QĐ-H", "2026-01-01")
		p = publish_procedure(make_procedure(self.s[2], K, job=self.job), "QĐ-H", "2026-01-01")
		ns = frappe.get_doc("NC Norm Set", make_norm_set(p.name))
		ns.status = "Đã khóa"
		ns.flags.allow_lock = True
		ns.save(ignore_permissions=True)
		make_chain_data(self.s[3], K, self.job)
		make_chain_data(self.s[4], K, self.job)
		frappe.db.set_value("NC Technical Service", self.s[4], "is_active", 0)
		# dữ liệu của các dịch vụ khác trong DB thử được đếm chung: lấy mức cơ sở
		self.base = None

	def _expect(self, res, delta):
		got = _counts(res)
		for stage, n in delta.items():
			self.assertGreaterEqual(got[stage], n, stage)

	def test_FR_OUT_010_dem_theo_tinh_trang_chuoi(self):
		res = home.get_home()
		counts = _counts(res)
		by_service = home._stage_by_service()
		self.assertEqual(by_service[self.s[0]], "no_procedure")
		self.assertEqual(by_service[self.s[1]], "procedure")
		self.assertEqual(by_service[self.s[2]], "norm_locked")
		self.assertEqual(by_service[self.s[3]], "costed")
		self.assertNotIn(self.s[4], by_service)
		self.assertEqual(sum(v for v in counts.values() if v is not None), len(by_service))
		self.assertEqual(counts["price_approved"], 0)
		self.assertEqual([s["stage"] for s in res["stages"]], list(home.chain.STAGES))
		self.assertTrue(res["stages"][-1]["assumption"])

	def test_FR_OUT_010_loc_khoa_va_pham_vi(self):
		self._assign("DV-HOME-X", K2)
		res_k = home.get_home(department=K)
		self.assertEqual(res_k["department"], K)
		stages_k = home._stage_by_service(K)
		self.assertIn(self.s[3], stages_k)
		self.assertNotIn("DV-HOME-X", stages_k)
		self.assertIn("DV-HOME-X", home._stage_by_service(K2))
		# Clinician khoa K: chỉ dịch vụ của K; mục "Đã tính giá" không có quyền
		res = _as(self.clin, home.get_home)
		by = {s["stage"]: s for s in res["stages"]}
		self.assertTrue(by["costed"]["no_permission"] and by["costed"]["count"] is None)
		self.assertEqual({d["name"] for d in res["departments"]}, {K})
		self.assertNotIn("DV-HOME-X", _as(self.clin, home._stage_by_service))
		with self.assertRaises(frappe.PermissionError):
			_as(self.clin, home.get_home, department=K2)
		with self.assertRaises(frappe.DoesNotExistError):
			home.get_home(department="KHONG-CO-KHOA")

	def test_FR_OUT_010_bo_loc_danh_sach_dich_vu(self):
		self.assertIn(self.s[2], home.services_in_stage("norm_locked"))
		self.assertNotIn(self.s[3], home.services_in_stage("norm_locked"))
		self.assertIn(self.s[0], home.services_in_stage("no_procedure"))
		self.assertEqual(home.services_in_stage("price_approved"), [])
		with self.assertRaises(frappe.ValidationError):
			home.services_in_stage("khong_co")
		self.assertEqual(_as(self.clin, home.services_in_stage, "costed"), [])
		got = home.get_service_stages(json.dumps([self.s[1], self.s[4], "KHONG-CO"]))
		self.assertEqual(list(got), [self.s[1]])
		self.assertEqual(got[self.s[1]]["stage"], "procedure")
		self.assertEqual(
			[(d["key"], d["state"]) for d in got[self.s[1]]["dots"]],
			[("procedure", "ok"), ("norm_set", "empty"), ("cost", "empty"), ("price", "empty")],
		)
		clin = _as(self.clin, home.get_service_stages, json.dumps([self.s[1]]))
		self.assertEqual(clin[self.s[1]]["dots"][2]["state"], "no_permission")
		with self.assertRaises(frappe.ValidationError):
			home.get_service_stages(json.dumps([f"S{i}" for i in range(501)]))

	def test_FR_OUT_010_so_truy_van_get_home(self):
		queries = []
		original = frappe.db.sql

		def counting(query, *a, **kw):
			queries.append(str(query))
			return original(query, *a, **kw)

		frappe.db.sql = counting
		try:
			home.get_home()
		finally:
			frappe.db.sql = original
		# bỏ truy vấn siêu dữ liệu của Frappe (is_virtual, information_schema), chỉ đếm truy vấn dữ liệu
		data = [q for q in queries if "is_virtual" not in q and "information_schema" not in q]
		print(f"\n[FEAT-002] get_home: {len(data)} truy vấn dữ liệu ({len(queries)} gồm siêu dữ liệu)")
		self.assertEqual(
			len(data), 10
		)  # ASM-002-16: 9 + 1 nguồn việc chờ của FEAT-030 (ASM-030-18), không phụ thuộc số dịch vụ
