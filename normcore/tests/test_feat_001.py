"""FEAT-001: vai trò, khoa, trung tâm chi phí, phạm vi theo khoa (FR-ACC-001..006, FR-ADM-004, FR-ADM-005)."""

import frappe
from frappe.exceptions import LinkExistsError, MandatoryError, PermissionError, ValidationError
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api.procedure import add_step
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import ensure, make_base, make_procedure, make_user

K01, K02 = "K01-F1", "K02-F1"


def _publish(proc):
	proc.workflow_state = "Đã ban hành"
	proc.decision_no = "QĐ-1"
	proc.effective_date = "2026-01-01"
	proc.flags.allow_publish = True
	proc.save(ignore_permissions=True)
	return proc


class FeatBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, _, self.job = make_base(department=K01)
		make_base(service="DV-TEST-B", department=K02)
		self.clin = make_user("clin.f1@normcore.test", "NC Clinician")
		self.head = make_user("head.f1@normcore.test", "NC Department Head")
		access.assign_department(self.clin, K01)
		access.assign_department(self.head, K01)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def draft(self, dept, service="DV-TEST-A", version=1):
		return make_procedure(service, dept, version=version)


class TestPhamViKhoa(FeatBase):
	def test_TC_ACC_01_phamvi_khoa_ghi_doc(self):
		draft_k02 = self.draft(K02, "DV-TEST-B")
		pub_k02 = _publish(self.draft(K02, "DV-TEST-B", version=2))
		ns_k02 = frappe.get_doc("NC Norm Set", make_norm_set(pub_k02.name))
		draft_k01 = self.draft(K01)
		for user in (self.clin, self.head):
			frappe.set_user(user)
			self.assertFalse(frappe.has_permission("NC Clinical Procedure", "write", doc=draft_k02))
			self.assertFalse(frappe.has_permission("NC Norm Set", "write", doc=ns_k02))
			with self.assertRaises(PermissionError):
				add_step(draft_k02.name, "Thực hiện", "Bước lạ", "Mô tả")
			with self.assertRaises(PermissionError):
				make_norm_set(pub_k02.name)
			new = frappe.get_doc(
				{"doctype": "NC Clinical Procedure", "technical_service": "DV-TEST-B", "department": K02, "version_no": 9}
			)
			self.assertFalse(frappe.has_permission("NC Clinical Procedure", "create", doc=new))
			with self.assertRaises(PermissionError):
				new.insert()
			# khoa của mình: ghi được
			self.assertTrue(frappe.has_permission("NC Clinical Procedure", "write", doc=draft_k01))
			add_step(draft_k01.name, "Thực hiện", "Bước mới", "Mô tả")
			# không đổi trường khoa để kéo bản ghi của khoa khác về khoa mình
			hijack = frappe.get_doc("NC Clinical Procedure", draft_k02.name)
			hijack.department = K01
			self.assertFalse(frappe.has_permission("NC Clinical Procedure", "write", doc=hijack))

	def test_TC_ACC_01_doc_theo_q3(self):
		draft_k02 = self.draft(K02, "DV-TEST-B")
		pub_k02 = _publish(self.draft(K02, "DV-TEST-B", version=2))
		ns_k02 = frappe.get_doc("NC Norm Set", make_norm_set(pub_k02.name))
		ns_k02.status = "Đã khóa"
		ns_k02.flags.allow_lock = True
		ns_k02.save(ignore_permissions=True)
		for user in (self.clin, self.head):
			frappe.set_user(user)
			names = frappe.get_list("NC Clinical Procedure", pluck="name")
			self.assertTrue(frappe.has_permission("NC Clinical Procedure", "read", doc=pub_k02))
			self.assertIn(pub_k02.name, names)
			self.assertFalse(frappe.has_permission("NC Clinical Procedure", "read", doc=draft_k02))
			self.assertNotIn(draft_k02.name, names)
			self.assertFalse(frappe.has_permission("NC Norm Set", "read", doc=ns_k02))
			self.assertNotIn(ns_k02.name, frappe.get_list("NC Norm Set", pluck="name"))
			with self.assertRaises(PermissionError):
				frappe.get_doc("NC Norm Set", ns_k02.name).check_permission("read")

	def test_TC_ACC_01_chua_gan_khoa_khong_ghi_duoc(self):  # G5
		draft_k01 = self.draft(K01)
		new_user = make_user("clin.chuagan@normcore.test", "NC Clinician")
		frappe.set_user(new_user)
		self.assertFalse(frappe.has_permission("NC Clinical Procedure", "write", doc=draft_k01))
		self.assertFalse(frappe.has_permission("NC Clinical Procedure", "read", doc=draft_k01))
		with self.assertRaises(PermissionError):
			add_step(draft_k01.name, "Thực hiện", "x", "y")

	def test_TC_ACC_01_vai_tro_khac_khong_bi_hep(self):  # G4
		draft_k02 = self.draft(K02, "DV-TEST-B")
		pub = _publish(self.draft(K02, "DV-TEST-B", version=2))
		ns = frappe.get_doc("NC Norm Set", make_norm_set(pub.name))
		both = make_user("clin.fin@normcore.test", "NC Clinician", "NC Finance")
		access.assign_department(both, K01)
		frappe.set_user(both)
		self.assertTrue(frappe.has_permission("NC Norm Set", "read", doc=ns))  # Finance đọc toàn viện
		self.assertIn(ns.name, frappe.get_list("NC Norm Set", pluck="name"))
		self.assertTrue(frappe.has_permission("NC Clinical Procedure", "read", doc=draft_k02))
		self.assertFalse(frappe.has_permission("NC Clinical Procedure", "write", doc=draft_k02))

	def test_TC_ACC_01_auditor_doc_moi_khoa_khong_ghi(self):
		draft_k02 = self.draft(K02, "DV-TEST-B")
		pub = _publish(self.draft(K02, "DV-TEST-B", version=2))
		ns = frappe.get_doc("NC Norm Set", make_norm_set(pub.name))
		auditor = make_user("auditor.f1@normcore.test", "NC Auditor")
		frappe.set_user(auditor)
		names = frappe.get_list("NC Clinical Procedure", pluck="name")
		self.assertIn(draft_k02.name, names)
		self.assertIn(ns.name, frappe.get_list("NC Norm Set", pluck="name"))
		self.assertFalse(frappe.has_permission("NC Clinical Procedure", "write", doc=draft_k02))
		self.assertFalse(frappe.has_permission("NC Norm Set", "write", doc=ns))
		with self.assertRaises(PermissionError):
			access.assign_department(self.clin, K02)
		with self.assertRaises(PermissionError):
			add_step(draft_k02.name, "Thực hiện", "x", "y")


class TestSoLieuTaiChinh(FeatBase):
	def _run(self):
		ps = frappe.get_doc(
			{"doctype": "NC Costing Run", "title": "Lần tính BImat-777", "fiscal_year": 2031,
			 "costing_date": "2031-03-01", "parameter_set": self._ps(), "status": "Nháp"}
		)
		ps.insert(ignore_permissions=True)
		return ps

	def _ps(self):
		from normcore.tests.utils import make_param_set

		return make_param_set(job=self.job).name

	def test_TC_ACC_02_clinician_khong_xem_so_lieu_tai_chinh(self):
		self._run()
		frappe.set_user(self.clin)
		for dt in ("NC Costing Run", "NC Service Cost"):
			with self.assertRaises(PermissionError):
				frappe.get_list(dt)
			with self.assertRaises(PermissionError):
				frappe.client.get_list(dt)

	def test_TC_ACC_03_mo_ban_ghi_ngoai_pham_vi_khong_lo_gia_tri(self):
		run = self._run()
		rm = make_user("rm.f1@normcore.test", "NC Resource Manager")
		frappe.set_user(rm)
		for call in (
			lambda: frappe.client.get("NC Costing Run", run.name),
			lambda: frappe.desk.form.load.getdoc("NC Costing Run", run.name),
		):
			frappe.response.clear()
			with self.assertRaises(PermissionError) as cm:
				call()
			text = str(cm.exception)
			self.assertNotIn("BImat-777", text)
			self.assertNotIn("2031", text)
			self.assertFalse(frappe.response.get("docs"))


class TestChuaDangNhap(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")

	def test_TC_ACC_05_guest_bi_tu_choi(self):
		frappe.set_user("Guest")
		with self.assertRaises(PermissionError):
			frappe.client.get_list("NC Technical Service")

	def test_TC_ACC_05_desk_chuyen_ve_trang_dang_nhap(self):
		from frappe.website.serve import get_response

		frappe.set_user("Guest")
		frappe.local.request = frappe._dict(path="/app", method="GET", args={}, headers={}, url="/app")
		response = get_response("app")
		self.assertIn(response.status_code, (301, 302, 303))
		self.assertIn("/login", response.headers.get("Location", ""))


class TestKhoaVaTrungTamChiPhi(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _dept(self, **kw):
		base = {"doctype": "NC Department", "department_code": "K03-F1", "department_name": "Khoa CLS",
		        "department_type": "Cận lâm sàng", "cost_center": "CC-F1"}
		return frappe.get_doc({**base, **kw})

	def setUp(self):
		frappe.set_user("Administrator")
		ensure("NC Cost Center", "cost_center_code", "CC-F1", cost_center_name="TT CLS", center_type="Lâm sàng")

	def test_TC_ADM_04_khoa_thieu_truong_bat_buoc_bi_tu_choi(self):
		for missing in ("department_code", "department_name", "department_type", "cost_center"):
			doc = self._dept()
			doc.set(missing, None)
			# mã khoa là tên bản ghi nên thiếu mã bị chặn ở bước đặt tên (ValidationError)
			with self.assertRaises(ValidationError, msg=missing):
				doc.insert()
		doc = self._dept()
		doc.department_type = None
		with self.assertRaises(MandatoryError):
			doc.insert()

	def test_TC_ADM_04_khoa_can_lam_sang_co_trung_tam_chi_phi(self):
		self._dept().insert()
		self.assertEqual(frappe.db.get_value("NC Department", "K03-F1", "cost_center"), "CC-F1")
		self.assertEqual(frappe.get_doc("NC Department", "K03-F1").cost_center, "CC-F1")

	def test_TC_ADM_04_trung_tam_chi_phi_thieu_truong_bi_tu_choi(self):
		doc = frappe.get_doc({"doctype": "NC Cost Center", "cost_center_code": "CC-X", "cost_center_name": "X"})
		with self.assertRaises(MandatoryError):
			doc.insert()

	def test_patch_cost_center_cho_khoa_co_san(self):
		from normcore.patches import add_cost_center_to_departments as patch

		frappe.db.sql("update `tabNC Department` set cost_center = null")
		frappe.db.set_value("NC Department", "K03-F1", "cost_center", None) if frappe.db.exists("NC Department", "K03-F1") else None
		for code, typ in (("KP-1", "Hỗ trợ"), ("KP-2", "Cận lâm sàng")):
			frappe.db.sql(
				"insert into `tabNC Department` (name, department_code, department_name, department_type, creation, modified, owner, modified_by) "
				"values (%s, %s, %s, %s, now(), now(), 'Administrator', 'Administrator')",
				(code, code, f"Khoa {code}", typ),
			)
		patch.execute()
		patch.execute()  # chạy lại không tạo trùng, không lỗi
		self.assertEqual(frappe.db.count("NC Department", {"cost_center": ["is", "not set"]}), 0)
		self.assertEqual(frappe.db.get_value("NC Cost Center", "KP-1", "center_type"), "Hỗ trợ")
		self.assertEqual(frappe.db.get_value("NC Cost Center", "KP-2", "center_type"), "Lâm sàng")
		self.assertEqual(frappe.db.count("NC Cost Center", {"name": "KP-1"}), 1)


class TestXoaDanhMuc(FeatBase):
	def _norm_set(self):
		pub = _publish(self.draft(K01))
		return make_norm_set(pub.name)

	def test_TC_ADM_05_xoa_danh_muc_dang_duoc_tham_chieu(self):
		ns = self._norm_set()
		admin = make_user("admin.f1@normcore.test", "NC Admin")
		frappe.set_user(admin)
		with self.assertRaises(LinkExistsError) as cm:
			frappe.delete_doc("NC Job Title", self.job)
		self.assertIn(ns, str(cm.exception))
		self.assertIn("NC Norm Set", str(cm.exception))
		self.assertTrue(frappe.db.exists("NC Job Title", self.job))

	def test_TC_ADM_05_admin_xoa_duoc_danh_muc_khong_ai_tham_chieu(self):
		ensure("NC Job Title", "job_title_code", "TRONG", job_title_name="Trống", job_group="Điều dưỡng")
		admin = make_user("admin.f1@normcore.test", "NC Admin")
		frappe.set_user(admin)
		frappe.delete_doc("NC Job Title", "TRONG")
		self.assertFalse(frappe.db.exists("NC Job Title", "TRONG"))

	def test_TC_ADM_05_vai_tro_khac_khong_xoa_duoc(self):
		ensure("NC Job Title", "job_title_code", "TRONG2", job_title_name="Trống", job_group="Điều dưỡng")
		fin = make_user("fin.f1@normcore.test", "NC Finance")
		frappe.set_user(fin)
		with self.assertRaises(PermissionError):
			frappe.delete_doc("NC Job Title", "TRONG2")


class TestGanKhoa(FeatBase):
	def test_FR_ACC_006_gan_va_bo_gan_co_hieu_luc_ngay(self):
		draft_k02 = self.draft(K02, "DV-TEST-B")
		admin = make_user("admin.f1@normcore.test", "NC Admin")  # không phải Administrator, không System Manager
		self.assertNotIn("System Manager", frappe.get_roles(admin))
		frappe.set_user(self.clin)
		self.assertFalse(frappe.has_permission("NC Clinical Procedure", "write", doc=draft_k02))
		frappe.set_user(admin)
		access.assign_department(self.clin, K02)
		self.assertIn(self.clin, access.list_department_users(K02))
		frappe.set_user(self.clin)  # không đăng nhập lại
		self.assertTrue(frappe.has_permission("NC Clinical Procedure", "write", doc=draft_k02))
		frappe.set_user(admin)
		access.unassign_department(self.clin, K02)
		frappe.set_user(self.clin)
		self.assertFalse(frappe.has_permission("NC Clinical Procedure", "write", doc=draft_k02))

	def test_FR_ACC_006_vai_tro_khac_gan_khoa_bi_tu_choi(self):
		for role in ("NC Clinician", "NC Department Head", "NC Finance", "NC Auditor"):
			frappe.set_user("Administrator")
			user = make_user(f"gan.{role[3:].lower().replace(' ', '')}@normcore.test", role)
			frappe.set_user(user)
			with self.assertRaises(PermissionError):
				access.assign_department(self.clin, K02)
			with self.assertRaises(PermissionError):
				access.unassign_department(self.clin, K01)

	def test_FR_ACC_006_nhieu_khoa_va_gan_lap_khong_trung(self):
		access.assign_department(self.clin, K02)
		self.assertFalse(access.assign_department(self.clin, K02))
		from normcore.core.permissions import get_user_departments

		self.assertEqual(get_user_departments(self.clin), {K01, K02})
