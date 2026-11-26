import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api import procedure as api
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document
from normcore.nc_library.doctype.nc_section_service_map.test_nc_section_service_map import make_section
from normcore.tests.utils import make_base, make_procedure, make_user, publish_procedure

STEP = {"phase": "Thực hiện", "step_title": "Bước mới", "description": "Mô tả bước mới"}


class TestProcedureAPI(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()
		self.proc = make_procedure(self.service, self.dept)
		self.clin = make_user("clin.api@normcore.test", "NC Clinician")
		access.assign_department(
			self.clin, self.dept
		)  # FEAT-001 (G5): người dùng phải được gán khoa; người duyệt đã chốt (a)
		self.auditor = make_user("auditor.api@normcore.test", "NC Auditor")
		self.finance = make_user("fin.api@normcore.test", "NC Finance")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_ham_duoc_whitelist(self):
		for fn in (api.get_procedure, api.add_step, api.list_procedures):
			self.assertIn(fn, frappe.whitelisted)

	def test_get_procedure_tra_cac_buoc(self):
		frappe.set_user(self.auditor)
		data = api.get_procedure(self.proc.name)
		self.assertEqual(data["name"], self.proc.name)
		self.assertEqual(data["steps"][0]["step_id"], "S001")
		self.assertEqual(data["workflow_state"], "Nháp")

	def test_nguoi_co_quyen_them_duoc_buoc(self):
		frappe.set_user(self.clin)
		out = api.add_step(self.proc.name, **STEP)
		self.assertEqual(out["step_id"], "S002")
		self.assertEqual(len(frappe.get_doc("NC Clinical Procedure", self.proc.name).steps), 2)

	def test_vai_tro_khong_quyen_va_auditor_bi_tu_choi(self):
		for user in (self.auditor, self.finance):
			frappe.set_user(user)
			self.assertRaises(frappe.PermissionError, api.add_step, self.proc.name, **STEP)
		frappe.set_user("Administrator")
		self.assertEqual(len(frappe.get_doc("NC Clinical Procedure", self.proc.name).steps), 1)

	def test_quy_trinh_da_ban_hanh_bi_chan(self):
		publish_procedure(self.proc, "QĐ-01", "2026-12-01")
		frappe.set_user(self.clin)
		self.assertRaises(frappe.ValidationError, api.add_step, self.proc.name, **STEP)

	def test_yeu_cau_giai_doan_ten_mo_ta(self):
		frappe.set_user(self.clin)
		for missing in ("phase", "step_title", "description"):
			args = {**STEP, missing: ""}
			self.assertRaises(frappe.ValidationError, api.add_step, self.proc.name, **args)


SECTIONS = ["Đại cương", "Chỉ định", "Chống chỉ định", "Thận trọng", "Chuẩn bị", "Các bước tiến hành"]


class TestProcedureEditorAPI(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()
		self.clin = make_user("clin.edit@normcore.test", "NC Clinician")
		self.auditor = make_user("auditor.edit@normcore.test", "NC Auditor")
		self.finance = make_user("fin.edit@normcore.test", "NC Finance")
		access.assign_department(self.clin, self.dept)  # FEAT-001: Clinician chỉ ghi được ở khoa được gán
		# NORM-65: legal_document, legal_section là Link; dùng bản ghi thật thay cho chuỗi tự do
		self.ld1 = make_legal_document("43/2013/TT-BYT")
		self.ls1 = {n: make_section(self.ld1, n).name for n in ("5", "6")}
		self.ld2 = make_legal_document("15/2023/QH15")
		self.ls2 = make_section(self.ld2, "7").name
		frappe.set_user(self.clin)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _draft(self):
		return api.create_procedure(self.service, self.dept)["name"]

	def _steps(self, name, n=3):
		for i in range(n):
			api.add_step(name, "Thực hiện", f"Bước {i + 1}", f"Mô tả {i + 1}")

	def _version_data(self, name):
		user = frappe.session.user
		frappe.set_user("Administrator")
		rows = frappe.get_all(
			"Version",
			filters={"ref_doctype": "NC Clinical Procedure", "docname": name},
			fields=["data", "owner", "creation"],
			order_by="creation",
		)
		frappe.set_user(user)
		return [(frappe.parse_json(r.data), r) for r in rows]

	def test_ham_moi_duoc_whitelist(self):
		for n in (
			"create_procedure find_existing save_sections update_step delete_step reorder_steps add_resource "
			"update_resource delete_resource suggest_catalog add_citation update_citation delete_citation "
			"copy_procedure"
		).split():
			self.assertIn(getattr(api, n), frappe.whitelisted, n)

	def test_TC_PROC_01_tao_ban_nhap(self):
		out = api.create_procedure(self.service, self.dept)
		self.assertEqual(out["version_no"], 1)
		data = api.get_procedure(out["name"])
		self.assertEqual(data["workflow_state"], "Nháp")
		self.assertEqual(data["version_no"], 1)
		self.assertEqual(len(data["sections"]), 8)
		self.assertEqual([s["label"] for s in data["sections"]][:6], SECTIONS)
		self.assertTrue(data["can_edit"])

	def test_TC_PROC_02_tao_lan_hai_bi_tu_choi_va_dan_toi_ban_co(self):
		name = self._draft()
		with self.assertRaises(api.ExistingProcedureError) as cm:
			api.create_procedure(self.service, self.dept)
		self.assertEqual(cm.exception.existing, name)
		self.assertIn(name, str(cm.exception))
		self.assertEqual(api.find_existing(self.service, self.dept), {"draft": name, "published": None})

	def test_Q3_tu_choi_tao_va_sao_chep_khi_da_ban_hanh(self):
		name = self._draft()
		frappe.set_user("Administrator")
		doc = frappe.get_doc("NC Clinical Procedure", name)
		publish_procedure(doc, "QĐ-01", "2026-12-01")
		frappe.set_user(self.clin)
		with self.assertRaises(api.ExistingProcedureError) as cm:
			api.create_procedure(self.service, self.dept)
		self.assertEqual(cm.exception.existing, name)
		self.assertIn("Dịch vụ đã có quy trình ban hành", str(cm.exception))
		self.assertRaises(api.ExistingProcedureError, api.copy_procedure, name, self.service, self.dept)
		self.assertEqual(api.find_existing(self.service, self.dept)["published"], name)

	def test_luu_phan(self):
		name = self._draft()
		out = api.save_sections(name, {"overview": "<p>Đại cương</p>", "indications": "<p>CĐ</p>"})
		self.assertEqual(out["overview"], "<p>Đại cương</p>")
		data = api.get_procedure(name)
		self.assertEqual(data["sections"][0]["value"], "<p>Đại cương</p>")
		self.assertRaises(frappe.ValidationError, api.save_sections, name, {"decision_no": "x"})

	def test_TC_PROC_03_tich_hop_sap_lai_xoa_them(self):
		name = self._draft()
		self._steps(name)
		api.reorder_steps(name, ["S003", "S002", "S001"])
		self.assertEqual([s["step_id"] for s in api.get_procedure(name)["steps"]], ["S003", "S002", "S001"])
		api.delete_step(name, "S002")
		new = api.add_step(name, "Kết thúc", "Mới", "Mô tả mới")
		self.assertEqual(new["step_id"], "S004")
		self.assertEqual([s["step_id"] for s in api.get_procedure(name)["steps"]], ["S003", "S001", "S004"])
		self.assertRaises(frappe.ValidationError, api.reorder_steps, name, ["S003", "S001"])

	def test_sua_buoc_tai_cho_va_xoa_buoc_con_nguon_luc(self):
		name = self._draft()
		self._steps(name, 2)
		api.update_step(name, "S001", "Chuẩn bị", "Tên mới", "Mô tả mới")
		s = api.get_procedure(name)["steps"][0]
		self.assertEqual((s["step_id"], s["phase"], s["step_title"]), ("S001", "Chuẩn bị", "Tên mới"))
		api.add_resource(name, "S001", "Vật tư", "Bơm tiêm", 2, "cái")
		self.assertRaises(frappe.ValidationError, api.delete_step, name, "S001")
		api.add_citation(name, target_step_id="S002")
		self.assertRaises(frappe.ValidationError, api.delete_step, name, "S002")

	def test_TC_PROC_04_nguon_luc_nhan_luc(self):
		name = self._draft()
		self._steps(name, 1)
		out = api.add_resource(name, "S001", "Nhân lực", "Điều dưỡng", 15, None, "NC Job Title", self.job, 2)
		self.assertEqual(out["resource_row_id"], "R001")
		r = api.get_procedure(name)["resources"][0]
		self.assertEqual(
			(r["step_id"], r["headcount"], r["linked_name"], r["uom"]), ("S001", 2, self.job, "phút")
		)
		api.update_resource(name, "R001", quantity=20)
		r = api.get_procedure(name)["resources"][0]
		self.assertEqual((r["resource_row_id"], r["quantity"]), ("R001", 20))
		api.delete_resource(name, "R001")
		out = api.add_resource(name, "S001", "Vật tư", "Găng", 1, "đôi")
		self.assertEqual(out["resource_row_id"], "R002")  # không tái dùng
		self.assertRaises(frappe.ValidationError, api.add_resource, name, "S009", "Vật tư", "x", 1, "cái")

	def test_FR_PROC_005_goi_y_va_de_trong_lien_ket(self):
		got = api.suggest_catalog("Nhân lực", "Điều")
		self.assertIn(self.job, [g["name"] for g in got])
		self.assertEqual(api.suggest_catalog("Thuốc", "Para"), [])
		name = self._draft()
		self._steps(name, 1)
		api.add_resource(name, "S001", "Nhân lực", "Bác sĩ chưa có trong danh mục", 10, "phút")
		self.assertFalse(api.get_procedure(name)["resources"][0]["linked_name"])
		self.assertRaises(
			frappe.ValidationError, api.add_resource, name, "S001", "Thuốc", "x", 1, "viên", "NC Item", "X"
		)

	def test_TC_PROC_08_lich_su_truoc_sau_nguoi_thoi_diem(self):
		name = self._draft()
		self._steps(name, 1)
		api.add_resource(name, "S001", "Vật tư", "Bơm tiêm", 2, "cái")
		api.update_step(name, "S001", "Thực hiện", "Bước 1", "Mô tả đã sửa")
		api.update_resource(name, "R001", quantity=5)
		seen = {}
		for data, row in self._version_data(name):
			for c in data.get("row_changed") or []:
				table, _idx, _rname, changes = c
				for field, before, after in changes:
					seen[(table, field)] = (before, after, row.owner, row.creation)
		before, after, owner, when = seen[("steps", "description")]
		self.assertEqual((before, after, owner), ("Mô tả 1", "Mô tả đã sửa", self.clin))
		self.assertIsNotNone(when)
		before, after, owner, when = seen[("resources", "quantity")]
		self.assertEqual((float(before), float(after), owner), (2.0, 5.0, self.clin))

	def test_TC_PROC_08_moc_thoi_gian_va_nguoi_cho_ca_hai_thay_doi(self):
		"""QA bổ sung: TC-PROC-08 đòi người và thời điểm cho cả bước lẫn dòng nguồn lực."""
		name = self._draft()
		self._steps(name, 1)
		api.add_resource(name, "S001", "Vật tư", "Bơm tiêm", 2, "cái")
		api.update_step(name, "S001", "Thực hiện", "Bước 1", "Mô tả đã sửa")
		api.update_resource(name, "R001", quantity=5)
		found = {}
		for data, row in self._version_data(name):
			for table, _idx, _rname, changes in data.get("row_changed") or []:
				for field, before, after in changes:
					found[(table, field)] = (before, after, row.owner, row.creation)
		expected = {
			("steps", "description"): ("Mô tả 1", "Mô tả đã sửa"),
			("resources", "quantity"): (2.0, 5.0),
		}
		for key, (before, after) in expected.items():
			b, a, owner, when = found[key]
			if key[0] == "resources":
				b, a = float(b), float(a)
			self.assertEqual((b, a), (before, after))
			self.assertEqual(owner, self.clin)
			self.assertIsNotNone(when)

	def test_TC_PROC_09_trich_dan(self):
		name = self._draft()
		self._steps(name, 2)
		a = api.add_citation(
			name,
			target_step_id="S001",
			relation="Theo hướng dẫn",
			legal_document=self.ld1.name,
			legal_section=self.ls1["5"],
			quote="đoạn trích",
		)
		b = api.add_citation(
			name,
			target_section="Chỉ định",
			relation="Khác biệt",
			legal_document=self.ld2.name,
			legal_section=self.ls2,
			quote="q",
			deviation_reason="Lý do",
		)
		c = api.add_citation(name, target_step_id="S002")
		cits = {x["name"]: x for x in api.get_procedure(name)["citations"]}
		self.assertEqual(cits[a["name"]]["relation"], "Theo hướng dẫn")
		self.assertEqual(cits[a["name"]]["quote"], "đoạn trích")
		self.assertEqual(cits[a["name"]]["legal_document"], self.ld1.name)
		self.assertEqual(cits[a["name"]]["legal_section"], self.ls1["5"])
		api.update_citation(name, a["name"], legal_section=self.ls1["6"])
		self.assertEqual(
			api.get_procedure(name, step_id="S001")["citations"][0]["legal_section"], self.ls1["6"]
		)
		self.assertEqual(
			api.get_procedure(name, step_id="S001")["citations"][0]["legal_document"],
			self.ld1.name,
		)
		self.assertEqual(cits[b["name"]]["deviation_reason"], "Lý do")
		self.assertEqual(cits[b["name"]]["relation"], "Khác biệt")
		self.assertEqual(cits[b["name"]]["legal_document"], self.ld2.name)
		self.assertEqual(cits[b["name"]]["legal_section"], self.ls2)
		self.assertEqual(cits[b["name"]]["quote"], "q")
		self.assertEqual(cits[c["name"]]["relation"], "Chưa có căn cứ")
		# lọc theo bước hoặc phần đang chọn
		self.assertEqual(
			[x["name"] for x in api.get_procedure(name, step_id="S001")["citations"]], [a["name"]]
		)
		self.assertEqual(
			[x["name"] for x in api.get_procedure(name, section="Chỉ định")["citations"]], [b["name"]]
		)
		api.update_citation(name, b["name"], relation="Chưa có căn cứ")
		self.assertEqual(
			api.get_procedure(name, section="Chỉ định")["citations"][0]["relation"], "Chưa có căn cứ"
		)
		api.delete_citation(name, a["name"])
		self.assertEqual(len(api.get_procedure(name)["citations"]), 2)
		self.assertRaises(
			frappe.ValidationError, api.add_citation, name, target_step_id="S001", target_section="Chỉ định"
		)

	def test_NORM_65_trich_dan_link_van_ban_muc(self):
		name = self._draft()
		self._steps(name, 1)
		# chọn mục: văn bản lấy từ mục
		a = api.add_citation(name, target_step_id="S001", legal_section=self.ls1["5"])
		self.assertEqual(a["legal_document"], self.ld1.name)
		# chỉ văn bản (trích dẫn cấp văn bản) vẫn được
		b = api.add_citation(name, target_step_id="S001", legal_document=self.ld2.name)
		self.assertEqual((b["legal_document"], b["legal_section"]), (self.ld2.name, None))
		# mục không thuộc văn bản đã chọn: từ chối
		self.assertRaises(
			frappe.ValidationError,
			api.add_citation,
			name,
			target_step_id="S001",
			legal_document=self.ld2.name,
			legal_section=self.ls1["5"],
		)
		# giá trị không phải tên bản ghi: từ chối
		self.assertRaises(
			frappe.LinkValidationError, api.add_citation, name, target_step_id="S001", legal_section="Điều 5"
		)
		self.assertRaises(
			frappe.LinkValidationError,
			api.add_citation,
			name,
			target_step_id="S001",
			legal_document="Thông tư 43/2013/TT-BYT",
		)
		self.assertTrue({self.ld1.name, self.ld2.name} <= {d["name"] for d in api.list_legal_documents()})
		self.assertEqual(
			sorted(s["name"] for s in api.list_legal_sections(self.ld1.name)), sorted(self.ls1.values())
		)

	def test_FR_PROC_013_sao_chep(self):
		src = self._draft()
		self._steps(src, 3)
		api.delete_step(src, "S002")
		api.add_resource(src, "S003", "Nhân lực", "Điều dưỡng", 10, "phút", "NC Job Title", self.job, 1)
		api.add_citation(
			src,
			target_step_id="S003",
			relation="Khác biệt",
			deviation_reason="x",
			legal_document=self.ld1.name,
			legal_section=self.ls1["5"],
		)
		api.save_sections(src, {"overview": "<p>Đại cương</p>"})
		frappe.set_user("Administrator")
		ensure_service = make_base("DV-TEST-B", self.dept)[0]
		frappe.set_user(self.clin)
		out = api.copy_procedure(src, ensure_service, self.dept)
		new = api.get_procedure(out["name"])
		self.assertEqual([s["step_id"] for s in new["steps"]], ["S001", "S002"])
		self.assertEqual(new["resources"][0]["step_id"], "S002")  # S003 cũ
		self.assertEqual(new["resources"][0]["resource_row_id"], "R001")
		self.assertEqual(new["citations"][0]["target_step_id"], "S002")
		self.assertEqual(new["citations"][0]["legal_document"], self.ld1.name)
		self.assertEqual(new["citations"][0]["legal_section"], self.ls1["5"])
		self.assertEqual(new["copied_from"], src)
		self.assertEqual(new["sections"][0]["value"], "<p>Đại cương</p>")
		self.assertEqual(new["workflow_state"], "Nháp")
		self.assertEqual(api.add_step(out["name"], "Thực hiện", "Thêm", "m")["step_id"], "S003")
		# đích đã có bản nháp: từ chối (FR-PROC-002)
		self.assertRaises(api.ExistingProcedureError, api.copy_procedure, src, ensure_service, self.dept)

	def test_quyen_vai_tro_chi_doc_va_auditor_bi_tu_choi(self):
		name = self._draft()
		self._steps(name, 1)
		api.add_resource(name, "S001", "Vật tư", "x", 1, "cái")
		cid = api.add_citation(name, target_step_id="S001")["name"]
		calls = [
			lambda: api.create_procedure(self.service, self.dept),
			lambda: api.save_sections(name, {"overview": "x"}),
			lambda: api.add_step(name, "Thực hiện", "a", "b"),
			lambda: api.update_step(name, "S001", "Thực hiện", "a", "b"),
			lambda: api.delete_step(name, "S001"),
			lambda: api.reorder_steps(name, ["S001"]),
			lambda: api.add_resource(name, "S001", "Vật tư", "y", 1, "cái"),
			lambda: api.update_resource(name, "R001", quantity=3),
			lambda: api.delete_resource(name, "R001"),
			lambda: api.add_citation(name, target_step_id="S001"),
			lambda: api.update_citation(name, cid, relation="Khác biệt"),
			lambda: api.delete_citation(name, cid),
			lambda: api.copy_procedure(name, "DV-TEST-A", self.dept),
		]
		for user in (self.finance, self.auditor):
			frappe.set_user(user)
			for i, call in enumerate(calls):
				with self.subTest(user=user, call=i), self.assertRaises(frappe.PermissionError):
					call()
			self.assertFalse(api.get_procedure(name)["can_edit"])
		frappe.set_user("Administrator")
		doc = frappe.get_doc("NC Clinical Procedure", name)
		self.assertEqual((len(doc.steps), len(doc.resources), len(doc.citations)), (1, 1, 1))

	def test_ban_khong_o_nhap_bi_tu_choi_o_moi_ham_ghi(self):
		name = self._draft()
		self._steps(name, 1)
		api.add_resource(name, "S001", "Vật tư", "x", 1, "cái")
		cid = api.add_citation(name, target_step_id="S001")["name"]
		frappe.set_user("Administrator")
		frappe.db.set_value("NC Clinical Procedure", name, "workflow_state", "Chờ trưởng khoa duyệt")
		frappe.set_user(self.clin)
		for call in (
			lambda: api.save_sections(name, {"overview": "x"}),
			lambda: api.add_step(name, "Thực hiện", "a", "b"),
			lambda: api.update_step(name, "S001", "Thực hiện", "a", "b"),
			lambda: api.delete_step(name, "S001"),
			lambda: api.reorder_steps(name, ["S001"]),
			lambda: api.add_resource(name, "S001", "Vật tư", "y", 1, "cái"),
			lambda: api.update_resource(name, "R001", quantity=3),
			lambda: api.delete_resource(name, "R001"),
			lambda: api.add_citation(name, target_step_id="S001"),
			lambda: api.update_citation(name, cid, relation="Khác biệt"),
			lambda: api.delete_citation(name, cid),
		):
			self.assertRaises(frappe.ValidationError, call)
		self.assertFalse(api.get_procedure(name)["can_edit"])
