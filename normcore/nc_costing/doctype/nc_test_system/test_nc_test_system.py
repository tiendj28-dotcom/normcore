"""FEAT-031: NC Test System (FR-CLS-001, 002, 005, 006; FR-ACC-008; TC-CLS-20, TC-CLS-22)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.tests.utils import ensure, make_base, make_cls_data, make_test_system, make_user

SYS = dict(est_rerun_rate=2, est_wastage_rate=3)


class TestNCTestSystem(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _ = make_cls_data()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _two(self):
		a = make_test_system("GLU-A", self.service, self.dept, "EQ_A", 75, **SYS)
		b = make_test_system("GLU-B", self.service, self.dept, "EQ_B", 25, **SYS)
		return a, b

	def test_TC_CLS_20_hai_he_thong_cung_ton_tai(self):
		a, b = self._two()
		got = frappe.get_all(
			"NC Test System",
			{"technical_service": self.service, "department": self.dept},
			pluck="name",
			order_by="name",
		)
		self.assertEqual(got, ["GLU-A", "GLU-B"])
		self.assertEqual(a.est_rerun_rate, 2)
		self.assertEqual(a.est_wastage_rate, 3)
		self.assertEqual(b.status, "Đang dùng")

	def test_TC_CLS_20_thieu_truong_bat_buoc_bi_tu_choi(self):
		base = dict(
			doctype="NC Test System",
			test_system_code="GLU-X",
			technical_service=self.service,
			department=self.dept,
			main_equipment="EQ_A",
			volume_share_pct=50,
		)
		for f in (
			"test_system_code",
			"technical_service",
			"department",
			"main_equipment",
			"volume_share_pct",
		):
			bad = {k: v for k, v in base.items() if k != f}
			with self.assertRaises(frappe.ValidationError, msg=f):
				frappe.get_doc(bad).insert()

	def test_TC_CLS_20_dich_vu_phai_can_lam_sang(self):
		ensure("NC Technical Service", "service_code", "KHONG-CLS", service_name="Không cận lâm sàng")
		with self.assertRaises(frappe.ValidationError) as ctx:
			make_test_system("X-1", "KHONG-CLS", self.dept, "EQ_A", 100)
		self.assertIn("cận lâm sàng", str(ctx.exception))

	def test_ty_trong_va_ty_le_ngoai_mien(self):
		for kw in (
			{"volume_share_pct": 0},
			{"volume_share_pct": 101},
			{"est_rerun_rate": -1},
			{"est_wastage_rate": 100},
		):
			args = dict(share=50, **{k: v for k, v in kw.items() if k != "volume_share_pct"})
			if "volume_share_pct" in kw:
				args["share"] = kw["volume_share_pct"]
			with self.assertRaises(frappe.ValidationError, msg=str(kw)):
				make_test_system("GLU-Y", self.service, self.dept, "EQ_A", **args)

	def test_FR_CLS_005_phut_chiem_may(self):
		frappe.db.set_value("NC Equipment", "EQ_A", "allocation_basis", "Phút chiếm máy")
		with self.assertRaises(frappe.ValidationError) as ctx:
			make_test_system("GLU-P", self.service, self.dept, "EQ_A", 50)
		self.assertIn("Phút chiếm máy", str(ctx.exception))
		doc = make_test_system("GLU-P", self.service, self.dept, "EQ_A", 50, machine_minutes_per_case=15)
		self.assertEqual(doc.machine_minutes_per_case, 15)

	def test_TC_CLS_22_clinician_khoa_khac_khong_sua_duoc(self):
		self._two()
		make_base(department="VS-CLS")
		ensure(
			"NC Department",
			"department_code",
			"VS-CLS",
			department_name="Vi sinh",
			department_type="Lâm sàng",
			cost_center="VS-CLS",
		)
		clin_vs = make_user("clin.vs@normcore.test", "NC Clinician")
		clin_hs = make_user("clin.hs@normcore.test", "NC Clinician")
		access.assign_department(clin_vs, "VS-CLS")
		access.assign_department(clin_hs, self.dept)
		frappe.set_user(clin_vs)
		doc = frappe.get_doc("NC Test System", "GLU-A")
		self.assertFalse(frappe.has_permission("NC Test System", "write", doc=doc))
		doc.est_rerun_rate = 5
		with self.assertRaises(frappe.PermissionError):
			doc.save()
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(
				dict(
					doctype="NC Test System",
					test_system_code="GLU-Z",
					technical_service=self.service,
					department=self.dept,
					main_equipment="EQ_A",
					volume_share_pct=10,
				)
			).insert()
		self.assertNotIn("GLU-A", frappe.get_list("NC Test System", pluck="name"))
		frappe.set_user(clin_hs)
		doc = frappe.get_doc("NC Test System", "GLU-A")
		doc.est_rerun_rate = 4
		doc.save()
		self.assertEqual(frappe.db.get_value("NC Test System", "GLU-A", "est_rerun_rate"), 4)
		doc.department = "VS-CLS"
		with self.assertRaises(frappe.PermissionError):
			doc.save()

	def test_quyen_theo_ma_tran_va_auditor(self):
		self._two()
		expected_read = {
			"NC Clinician",
			"NC Department Head",
			"NC Finance",
			"NC Resource Manager",
			"NC Director",
			"NC Consultant",
			"NC Admin",
			"NC Auditor",
		}
		from normcore.install import ROLES

		users = {role: make_user(f"ts.perm{i}@normcore.test", role) for i, role in enumerate(ROLES)}
		for role, user in users.items():
			frappe.set_user(user)
			if role in ("NC Clinician", "NC Department Head"):
				continue  # phạm vi khoa: kiểm riêng
			self.assertEqual(
				bool(frappe.has_permission("NC Test System", "read")), role in expected_read, role
			)
			for ptype in ("write", "create", "delete"):
				self.assertFalse(frappe.has_permission("NC Test System", ptype), f"{role} {ptype}")
		frappe.set_user("Administrator")
		auditor = make_user("ts.auditor@normcore.test", "NC Auditor")
		frappe.set_user(auditor)
		doc = frappe.get_doc("NC Test System", "GLU-A")
		self.assertTrue(frappe.has_permission("NC Test System", "read", doc=doc))
		doc.est_rerun_rate = 9
		with self.assertRaises(frappe.PermissionError):
			doc.save()
		with self.assertRaises(frappe.PermissionError):
			frappe.get_doc(
				dict(
					doctype="NC Test System",
					test_system_code="GLU-Q",
					technical_service=self.service,
					department=self.dept,
					main_equipment="EQ_A",
					volume_share_pct=1,
				)
			).insert()

	def test_vai_tro_khong_co_quyen_bi_tu_choi(self):
		self._two()
		users = {
			r: make_user(f"ts.none{i}@normcore.test", r)
			for i, r in enumerate(("NC Document Controller", "NC Council Member"))
		}
		for role, user in users.items():
			frappe.set_user(user)
			self.assertFalse(frappe.has_permission("NC Test System", "read"), role)
			with self.assertRaises(frappe.PermissionError):
				frappe.get_doc("NC Test System", "GLU-A").check_permission("read")

	def test_FR_SVC_008_bo_co_can_lam_sang_khi_con_he_thong_bi_tu_choi(self):
		self._two()
		svc = frappe.get_doc("NC Technical Service", self.service)
		svc.is_paraclinical = 0
		with self.assertRaises(frappe.ValidationError) as ctx:
			svc.save()
		self.assertIn("GLU-A", str(ctx.exception))

	def test_FR_ADM_005_xoa_thiet_bi_dang_duoc_he_thong_tham_chieu(self):
		self._two()
		frappe.set_user(make_user("ts.admin@normcore.test", "NC Admin"))
		with self.assertRaises(frappe.LinkExistsError) as ctx:
			frappe.delete_doc("NC Equipment", "EQ_A")
		self.assertIn("GLU-A", str(ctx.exception))

	def _locked_run(self):
		"""Một lần tính "Đã tính" có NC Service Cost, dùng để kiểm lần đã có không bị đụng tới."""
		from normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run import _published_norm_set, _run
		from normcore.tests.utils import make_param_set

		make_param_set()
		ns = _published_norm_set(self.service, self.dept)
		ns.lock()
		run = _run(frappe.get_doc("NC Costing Parameter Set", {"title": "Bộ tham số vàng"}))
		run.run_costing()
		return run

	def test_TC_CLS_23_ngung_dung_khong_vao_lan_tinh_moi_lan_da_khoa_giu_nguyen(self):
		self._two()
		old = self._locked_run()
		old.db_set("status", "Đã khóa")
		snapshot = _snapshot(old.name)
		self.assertEqual(len(snapshot["costs"]), 1)
		frappe.db.set_value("NC Test System", "GLU-B", "status", "Ngừng dùng")
		new = frappe.get_doc(
			{
				"doctype": "NC Costing Run",
				"title": "Lần tính mới",
				"fiscal_year": 2026,
				"costing_date": "2026-12-31",
				"parameter_set": old.parameter_set,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(new.test_systems_in_scope(), ["GLU-A"])
		new.run_costing()
		new.reload()
		self.assertEqual(new.status, "Đã tính")
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": new.name}), 1)
		self.assertEqual(_snapshot(old.name), snapshot)
		self.assertEqual(snapshot["run"][1], "Đã khóa")
		# Dùng lại: hệ thống trở lại phạm vi
		frappe.db.set_value("NC Test System", "GLU-B", "status", "Đang dùng")
		self.assertEqual(new.test_systems_in_scope(), ["GLU-A", "GLU-B"])

	def test_FR_SVC_011_dich_vu_gui_ngoai_khong_tinh_tu_dinh_muc(self):
		from normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run import _published_norm_set, _run
		from normcore.tests.utils import make_param_set

		params = make_param_set()
		ns = _published_norm_set(self.service, self.dept)
		ns.lock()
		frappe.db.set_value("NC Technical Service", self.service, {"is_send_out": 1, "send_out_price": 90000})
		run = _run(params)
		run.run_costing()
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), 0)
		frappe.db.set_value("NC Technical Service", self.service, "is_send_out", 0)
		run2 = _run(params)
		run2.run_costing()
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run2.name}), 1)

	def test_FR_SVC_011_co_gui_ngoai_cu_khi_da_bo_can_lam_sang_van_tinh(self):
		"""ASM-109: bỏ cờ cận lâm sàng giữ giá trị cũ; `is_send_out` bị ẩn không được loại dịch vụ khỏi lần tính."""
		from normcore.nc_costing.doctype.nc_costing_run.test_nc_costing_run import _published_norm_set, _run
		from normcore.tests.utils import make_param_set

		params = make_param_set()
		ns = _published_norm_set(self.service, self.dept)
		ns.lock()
		frappe.db.set_value(
			"NC Technical Service",
			self.service,
			{"is_send_out": 1, "send_out_price": 90000, "is_paraclinical": 0},
		)
		run = _run(params)
		run.run_costing()
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), 1)


def _snapshot(run):
	return {
		"run": tuple(frappe.db.get_value("NC Costing Run", run, ["modified", "status"])),
		"costs": [
			tuple(d.values())
			for d in frappe.get_all(
				"NC Service Cost",
				{"costing_run": run},
				["name", "modified", "direct_labor"],
				order_by="name",
			)
		],
	}
