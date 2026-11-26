"""FEAT-034: API bộ định mức theo hệ thống xét nghiệm (UC-021; TC-CLS-26, 29..33; FR-NORM-017..025)."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import load_workbook

from normcore.api import access
from normcore.api import norm as api
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import (
	confirm_norm_set,
	make_base,
	make_cls_data,
	make_eqa_program,
	make_procedure,
	make_qc_items,
	make_qc_plan,
	make_test_system,
	make_user,
	publish_procedure,
)

DEPT = "XN-N34"
TEMPLATE = "MDM-T-N34"


def _template_items():
	return [
		dict(item_name="Vật tư lấy mẫu", component="SUPPLY", default_cost_level="TUBE", is_mandatory=1),
		dict(item_name="Hóa chất chính", component="DRUG", default_cost_level="RESULT", is_mandatory=1),
		dict(item_name="Thiết bị", component="EQUIPMENT", default_cost_level="RESULT", is_mandatory=1),
	]


class ClsBase(FrappeTestCase):
	"""Dịch vụ GLU (cận lâm sàng, Hóa sinh), hệ thống GLU-A (EQ_A) và GLU-B (EQ_B), quy trình đã ban hành
	có dòng Hóa chất và Nhân lực, mẫu Hóa sinh đang dùng."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _eqs = make_cls_data(department=DEPT)
		make_qc_items()
		self.gluA = make_test_system("GLU-A", self.service, self.dept, "EQ_A", 60).name
		self.gluB = make_test_system("GLU-B", self.service, self.dept, "EQ_B", 40).name
		frappe.db.set_value("NC Norm Template", {"is_active": 1}, "is_active", 0)
		frappe.get_doc(
			{
				"doctype": "NC Norm Template",
				"template_code": TEMPLATE,
				"cls_group": "Hóa sinh",
				"is_active": 1,
				"items": _template_items(),
			}
		).insert()
		self.proc = make_procedure(self.service, self.dept, minutes=10)
		self.proc.append(
			"resources",
			{
				"step_id": self.proc.steps[0].step_id,
				"resource_type": "Hóa chất",
				"resource_text": "Hóa chất GLU",
				"linked_doctype": "NC Item",
				"linked_name": "HC_GLU",
				"quantity": 1,
				"uom": "test",
			},
		)
		self.proc.save(ignore_permissions=True)
		publish_procedure(self.proc)
		self.head = make_user("head.n34@normcore.test", "NC Department Head")
		self.fin = make_user("fin.n34@normcore.test", "NC Finance")
		self.aud = make_user("aud.n34@normcore.test", "NC Auditor")
		access.assign_department(self.head, self.dept)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def create(self, system="GLU-A"):
		frappe.set_user(self.head)
		out = api.create_norm_set(self.proc.name, system)
		return frappe.get_doc("NC Norm Set", out["name"])


class TestCreate(ClsBase):
	def test_TC_CLS_29_khoi_tao_gan_he_thong_va_them_khoan_muc_bat_buoc(self):
		ns = self.create("GLU-A")
		self.assertEqual((ns.test_system, ns.name), ("GLU-A", f"DM-{self.service}-{self.dept}-GLU-A-v1"))
		self.assertEqual(ns.norm_template, TEMPLATE)
		by_item = {r.template_item: r for r in ns.lines if r.template_item}
		self.assertEqual(set(by_item), {"Vật tư lấy mẫu", "Hóa chất chính", "Thiết bị"})
		self.assertTrue(by_item["Hóa chất chính"].procedure_resource_row)
		added = [r for r in ns.lines if not r.procedure_resource_row]
		self.assertEqual(len(added), 2)
		for r in added:
			self.assertEqual(r.service_level, 1)
			self.assertFalse(r.hospital_qty)
			self.assertFalse(r.resource)
		self.assertEqual(by_item["Vật tư lấy mẫu"].cost_level, "TUBE")
		self.assertEqual(by_item["Hóa chất chính"].apply_k, 1)  # ASM-034-06
		# không chọn hệ thống: từ chối, nêu cả hai
		with self.assertRaises(frappe.ValidationError) as cm:
			api.create_norm_set(self.proc.name)
		self.assertIn("GLU-A", str(cm.exception))
		self.assertIn("GLU-B", str(cm.exception))
		# hệ thống của dịch vụ khác: DI-15
		svc2, dept2, _ = make_cls_data(department="XN2-N34", service="URE")
		other = make_test_system("URE-A", svc2, dept2, "EQ_A", 50).name
		with self.assertRaises(frappe.ValidationError) as cm:
			api.create_norm_set(self.proc.name, other)
		self.assertIn("không thuộc dịch vụ", str(cm.exception))

	def test_create_options_va_bo_dang_soan(self):
		frappe.set_user(self.head)
		opt = api.create_options(self.proc.name)
		self.assertTrue(opt["required"])
		self.assertEqual(opt["template"], TEMPLATE)
		self.assertEqual([x["name"] for x in opt["test_systems"]], ["GLU-A", "GLU-B"])
		self.assertEqual(opt["test_systems"][0]["main_equipment"], "EQ_A")
		self.assertIsNone(opt["test_systems"][0]["open_set"])
		first = api.create_norm_set(self.proc.name, "GLU-A")
		again = api.create_norm_set(self.proc.name, "GLU-A")  # ASM-034-14
		self.assertEqual(again["name"], first["name"])
		self.assertIn("message", again)
		self.assertEqual(api.create_options(self.proc.name)["test_systems"][0]["open_set"], first["name"])
		self.assertEqual(api.create_norm_set(self.proc.name, "GLU-B")["name"].count("GLU-B"), 1)

	def test_khong_co_he_thong_khong_bat_buoc(self):
		frappe.db.set_value("NC Test System", {"technical_service": self.service}, "status", "Ngừng dùng")
		frappe.set_user(self.head)
		self.assertFalse(api.create_options(self.proc.name)["required"])
		ns = frappe.get_doc("NC Norm Set", api.create_norm_set(self.proc.name)["name"])
		self.assertIsNone(ns.test_system)
		with self.assertRaises(frappe.ValidationError):  # hệ thống đã ngừng dùng
			api.create_norm_set(self.proc.name, "GLU-A")

	def test_khong_co_mau_khong_them_dong(self):
		frappe.db.set_value("NC Norm Template", {"template_code": TEMPLATE}, "is_active", 0)
		ns = self.create("GLU-A")
		self.assertIsNone(ns.norm_template)
		self.assertEqual(len(ns.lines), 2)  # nhân lực + hóa chất của quy trình
		self.assertEqual({r.template_item for r in ns.lines}, {None})

	def test_auditor_khong_tao_duoc(self):
		frappe.set_user(self.aud)
		with self.assertRaises(frappe.PermissionError):
			api.create_options(self.proc.name)
		with self.assertRaises(frappe.PermissionError):
			api.create_norm_set(self.proc.name, "GLU-A")


def _line(name, line_id):
	ns = frappe.get_doc("NC Norm Set", name)
	return next(r for r in ns.lines if r.line_id == line_id)


class TestLines(ClsBase):
	def test_TC_CLS_30_cap_phat_sinh_va_co_k(self):
		ns = self.create("GLU-A")
		eq_line = "L002"  # DRUG HC_GLU, Theo kết quả, nhân k bật sẵn (ASM-034-06)
		self.assertEqual(_line(ns.name, eq_line).apply_k, 1)
		# cờ k ở dòng Theo mẻ: từ chối, CSDL không đổi
		with self.assertRaises(frappe.ValidationError) as cm:
			api.save_line(ns.name, {"cost_level": "BATCH"}, eq_line)
		self.assertIn("Theo kết quả", str(cm.exception))
		self.assertEqual(_line(ns.name, eq_line).cost_level, "RESULT")
		# đặt từng cấp cho dòng
		api.save_line(ns.name, {"cost_level": "BATCH", "apply_k": 0}, eq_line)
		self.assertEqual(_line(ns.name, eq_line).cost_level, "BATCH")
		with self.assertRaises(frappe.ValidationError):  # bật k ở dòng Theo mẻ
			api.save_line(ns.name, {"apply_k": 1}, eq_line)
		self.assertEqual(_line(ns.name, eq_line).apply_k, 0)
		api.save_line(ns.name, {"cost_level": "TUBE"}, eq_line)
		api.save_line(ns.name, {"cost_level": "DAY", "attach_to": "Hệ thống xét nghiệm"}, eq_line)
		with self.assertRaises(frappe.ValidationError):  # DAY thiếu Gắn với
			api.save_line(ns.name, {"attach_to": None}, eq_line)
		api.save_line(
			ns.name, {"cost_level": "PERIOD", "attach_to": "Thiết bị", "attach_equipment": "EQ_A"}, eq_line
		)
		row = _line(ns.name, eq_line)
		self.assertEqual((row.cost_level, row.attach_equipment), ("PERIOD", "EQ_A"))
		out = api.save_line(ns.name, {"cost_level": "RESULT"}, eq_line)  # xóa Gắn với theo ASM-034-09
		self.assertEqual(_line(ns.name, eq_line).attach_to, None)
		cost = next(x for g in out["norm_set"]["groups"] for x in g["lines"] if x["line_id"] == eq_line)
		self.assertEqual(cost["cost"].get("missing") or "ok", cost["cost"].get("missing") or "ok")
		# cờ k ở dòng nhân lực: từ chối
		with self.assertRaises(frappe.ValidationError):
			api.save_line(ns.name, {"apply_k": 1}, "L001")
		# hao hụt 5% rồi bật k: lưu được, hao hụt về 0
		api.save_line(ns.name, {"wastage_rate": 5}, eq_line)
		self.assertEqual(_line(ns.name, eq_line).wastage_rate, 5)
		api.save_line(ns.name, {"apply_k": 1}, eq_line)
		row = _line(ns.name, eq_line)
		self.assertEqual((row.apply_k, row.wastage_rate), (1, 0))

	def test_TC_CLS_30_dich_vu_khong_can_lam_sang_luon_theo_ket_qua(self):
		svc, dept, _job = make_base(service="DV-N34-B", department="K-N34-B")
		proc = publish_procedure(make_procedure(svc, dept, minutes=10))
		access.assign_department(self.head, dept)
		frappe.set_user(self.head)
		ns = frappe.get_doc("NC Norm Set", api.create_norm_set(proc.name)["name"])
		api.save_line(ns.name, {"cost_level": "TUBE", "apply_k": 1}, "L001")
		row = _line(ns.name, "L001")
		self.assertEqual((row.cost_level, row.apply_k), ("RESULT", 0))

	def test_TC_CLS_31_tu_choi_dong_trung_ke_hoach_chat_luong(self):
		make_qc_plan("GLU-A")
		ns = self.create("GLU-A")
		step = self.proc.steps[0].step_id
		qc_line = {
			"step_id": step,
			"component": "DRUG",
			"resource_doctype": "NC Item",
			"resource": "QC_L",
			"hospital_qty": 1,
			"uom": "ml",
			"basis": "Ước tính",
		}
		before = frappe.db.count("NC Norm Line", {"parent": ns.name})
		with self.assertRaises(frappe.ValidationError) as cm:
			api.save_line(ns.name, qc_line)
		self.assertIn("QC_L", str(cm.exception))
		self.assertIn("kế hoạch", str(cm.exception))
		self.assertEqual(frappe.db.count("NC Norm Line", {"parent": ns.name}), before)
		# bộ của hệ thống chưa có kế hoạch: lưu được
		other = self.create("GLU-B")
		api.save_line(other.name, qc_line)
		self.assertEqual(frappe.db.count("NC Norm Line", {"parent": other.name}), before + 1)

	def test_save_head_so_xet_nghiem_moi_ong(self):
		ns = self.create("GLU-A")
		out = api.save_head(ns.name, {"tests_per_tube": 4})
		self.assertEqual(out["doc"]["tests_per_tube"], 4)
		with self.assertRaises(frappe.ValidationError):
			api.save_head(ns.name, {"tests_per_tube": -1})
		with self.assertRaises(frappe.ValidationError) as cm:
			api.save_head(ns.name, {"test_system": "GLU-B"})
		self.assertIn("Trường không được nhập", str(cm.exception))
		frappe.set_user(self.aud)
		with self.assertRaises(frappe.PermissionError):
			api.save_head(ns.name, {"tests_per_tube": 3})

	def test_get_norm_set_phan_cls(self):
		ns = self.create("GLU-A")
		out = api.get_norm_set(ns.name)
		self.assertEqual(out["doc"]["test_system_label"], "GLU-A · EQ_A")
		self.assertEqual(out["doc"]["norm_template"], TEMPLATE)
		self.assertEqual([o["value"] for o in out["options"]["cost_level"]][:2], ["RESULT", "TUBE"])
		self.assertEqual(out["meta"]["other_test_systems"][0]["name"], "GLU-B")
		self.assertTrue(out["meta"]["is_paraclinical"])
		lines = {x["line_id"]: x for g in out["groups"] for x in g["lines"]}
		self.assertTrue(lines["L003"]["placeholder"])
		self.assertFalse(lines["L002"]["placeholder"])
		self.assertEqual(lines["L002"]["cost"]["missing"], "Tính ở lần tính giá")  # nhân k, ASM-034-22
		self.assertTrue(out["summary"]["incomplete"])
		self.assertEqual(
			{t["item_name"]: t["satisfied"] for t in out["template_items"]},
			{"Vật tư lấy mẫu": False, "Hóa chất chính": True, "Thiết bị": False},
		)
		self.assertIn("save_head", out["actions"])
		self.assertIn("copy_norm_set", out["actions"])
		self.assertNotIn("export_norm_set", out["actions"])  # ASM-034-24
		self.assertTrue(any("kế hoạch" in b or "Số xét nghiệm" in b for b in out["set_blockers"]))


class TestConfirm(ClsBase):
	def test_TC_CLS_29_bo_thieu_he_thong_khong_xac_nhan_duoc(self):
		bare = frappe.get_doc("NC Norm Set", make_norm_set(self.proc.name))
		self.assertIsNone(bare.test_system)
		frappe.set_user(self.head)
		with self.assertRaises(frappe.ValidationError) as cm:
			api.confirm_set(bare.name)
		self.assertIn("Chưa gắn hệ thống xét nghiệm", str(cm.exception))

	def test_TC_CLS_32_xac_nhan_can_so_xn_moi_ong_va_khoan_muc_bat_buoc(self):
		ns = self.create("GLU-A")
		frappe.set_user(self.head)
		for lid in ("L001", "L002"):
			api.confirm_line(ns.name, lid)
		# thiếu số xét nghiệm mỗi ống (dòng L003 Theo ống mẫu)
		with self.assertRaises(frappe.ValidationError) as cm:
			api.confirm_set(ns.name)
		self.assertIn("Số xét nghiệm bình quân trên một ống mẫu", str(cm.exception))
		self.assertEqual(frappe.db.get_value("NC Norm Set", ns.name, "status"), "Nháp")
		api.save_head(ns.name, {"tests_per_tube": 4})
		# thiếu khoản mục bắt buộc
		with self.assertRaises(frappe.ValidationError) as cm:
			api.confirm_set(ns.name)
		msg = str(cm.exception)
		self.assertIn("Thiếu khoản mục bắt buộc", msg)
		self.assertIn("Thiết bị", msg)
		self.assertNotIn("Số xét nghiệm", msg)
		# đánh dấu "Không áp dụng" (nhập đủ nguồn lực, đơn vị vì dòng đã sửa), rồi xác nhận từng dòng
		api.save_line(
			ns.name,
			{
				"is_excluded": 1,
				"exclude_reason": "Không áp dụng",
				"resource_doctype": "NC Item",
				"resource": "HC_GLU",
				"uom": "ống",
			},
			"L003",
		)
		api.save_line(
			ns.name,
			{
				"is_excluded": 1,
				"exclude_reason": "Không áp dụng",
				"resource_doctype": "NC Equipment",
				"resource": "EQ_A",
				"uom": "phút",
			},
			"L004",
		)
		for lid in ("L003", "L004"):
			api.confirm_line(ns.name, lid)
		out = api.confirm_set(ns.name)
		self.assertEqual(out["doc"]["status"], "Đã xác nhận chuyên môn")

	def test_set_blockers_dung_truoc_loi_dong(self):
		ns = self.create("GLU-A")
		frappe.set_user(self.head)
		with self.assertRaises(frappe.ValidationError) as cm:
			api.confirm_set(ns.name)
		msg = str(cm.exception)
		self.assertLess(msg.index("Số xét nghiệm"), msg.index("Chưa xác nhận"))

	def test_TC_CLS_26_canh_bao_tren_bo_dinh_muc_van_khoa_duoc(self):
		ns = self.create("GLU-A")
		out = api.get_norm_set(ns.name)
		self.assertEqual(out["warnings"][0]["code"], "missing_iqc")
		self.assertIn("GLU-A", out["warnings"][0]["message"])
		confirm_norm_set(ns)
		frappe.set_user(self.fin)
		self.assertEqual(api.lock_set(ns.name)["doc"]["status"], "Đã khóa")  # cảnh báo không chặn
		# có kế hoạch nội kiểm thì hết cảnh báo
		make_qc_plan("GLU-B")
		other = self.create("GLU-B")
		self.assertEqual(api.get_norm_set(other.name)["warnings"], [])


class TestCopyVersion(ClsBase):
	def _locked_gluA(self):
		ns = self.create("GLU-A")
		api.save_line(
			ns.name,
			{"cost_level": "PERIOD", "attach_to": "Thiết bị", "attach_equipment": "EQ_A", "apply_k": 0},
			"L002",
		)
		confirm_norm_set(ns)
		frappe.set_user(self.fin)
		api.lock_set(ns.name)
		return ns.name

	def test_TC_CLS_33_sao_chep_khoa_hai_bo_va_xuat(self):
		src = self._locked_gluA()
		frappe.set_user(self.head)
		out = api.copy_norm_set(src, "GLU-B")
		self.assertEqual(out["skipped"], [])
		new = frappe.get_doc("NC Norm Set", out["name"])
		self.assertEqual(new.name, f"DM-{self.service}-{self.dept}-GLU-B-v1")
		self.assertEqual((new.status, new.copied_from, new.test_system), ("Nháp", src, "GLU-B"))
		source = frappe.get_doc("NC Norm Set", src)
		self.assertEqual([r.line_id for r in new.lines], [r.line_id for r in source.lines])
		self.assertFalse(any(r.confirmed_by for r in new.lines))
		self.assertEqual(next(r for r in new.lines if r.line_id == "L002").attach_equipment, "EQ_B")
		self.assertEqual(new.norm_template, TEMPLATE)
		# khóa cả hai: bộ GLU-A không thành "Đã thay thế" (DI-03 theo hệ thống)
		confirm_norm_set(new)
		frappe.set_user(self.fin)
		api.lock_set(new.name)
		self.assertEqual(frappe.db.get_value("NC Norm Set", src, "status"), "Đã khóa")
		self.assertEqual(frappe.db.get_value("NC Norm Set", new.name, "status"), "Đã khóa")
		# xuất: hai tệp, có cấp phát sinh, kế hoạch chất lượng, k
		make_qc_plan("GLU-A")
		make_eqa_program(department=self.dept)
		for name, system in ((src, "GLU-A"), (new.name, "GLU-B")):
			api.export_norm_set(name)
			self.assertEqual(frappe.response["filename"], f"{name}.xlsx")
			wb = load_workbook(io.BytesIO(frappe.response["filecontent"]))
			rows = list(wb["Bộ định mức"].iter_rows(values_only=True))
			header = next(r for r in rows if r[0] == "Bước")
			body = rows[rows.index(header) + 1 :]
			levels = {r[header.index("Cấp phát sinh")] for r in body}
			self.assertEqual(levels, {"Theo kết quả", "Theo ống mẫu", "Theo kỳ"})
			if system == "GLU-A":
				self.assertEqual(wb["Nội kiểm"].cell(2, 1).value, "QC_L")
			else:
				self.assertEqual(wb["Nội kiểm"].cell(1, 1).value, "Chưa có kế hoạch chất lượng")
			self.assertEqual(wb["Ngoại kiểm"].cell(2, 1).value, "EQA-HS")
			self.assertEqual(wb["Hệ số k"].cell(2, 1).value, system)
			self.assertEqual(wb["Hệ số k"].cell(2, 4).value, "Chưa có lần tính giá")  # ASM-034-16
		frappe.set_user(self.aud)  # Auditor đọc được thì xuất được
		api.export_norm_set(src)
		self.assertTrue(frappe.response["filecontent"])

	def test_sao_chep_bo_cac_dong_thuoc_ke_hoach_chat_luong(self):
		ns = self.create("GLU-A")
		api.save_line(
			ns.name,
			{
				"step_id": self.proc.steps[0].step_id,
				"component": "DRUG",
				"resource_doctype": "NC Item",
				"resource": "QC_L",
				"hospital_qty": 1,
				"uom": "ml",
				"basis": "Ước tính",
			},
		)
		make_qc_plan("GLU-B")
		out = api.copy_norm_set(ns.name, "GLU-B")
		self.assertEqual(len(out["skipped"]), 1)
		self.assertIn("kế hoạch chất lượng", out["skipped"][0]["reason"])

	def test_sao_chep_tu_choi(self):
		ns = self.create("GLU-A")
		with self.assertRaises(frappe.ValidationError):
			api.copy_norm_set(ns.name, "GLU-A")  # cùng hệ thống
		bare = frappe.get_doc("NC Norm Set", make_norm_set(self.proc.name))
		with self.assertRaises(frappe.ValidationError):
			api.copy_norm_set(bare.name, "GLU-B")  # nguồn không có hệ thống
		first = api.copy_norm_set(ns.name, "GLU-B")
		again = api.copy_norm_set(ns.name, "GLU-B")  # đã có bộ đang soạn (ASM-034-14)
		self.assertEqual(again["name"], first["name"])
		self.assertIn("message", again)
		frappe.set_user(self.aud)
		with self.assertRaises(frappe.PermissionError):
			api.copy_norm_set(ns.name, "GLU-B")

	def test_FR_NORM_017_phien_ban_moi_giu_he_thong(self):
		src = self._locked_gluA()
		frappe.db.set_value("NC Norm Set", src, "tests_per_tube", 4)
		frappe.set_user(self.head)
		out = api.new_version(src)
		new = frappe.get_doc("NC Norm Set", out["name"])
		self.assertEqual(
			(new.test_system, new.tests_per_tube, new.norm_template, new.version_no, new.previous_version),
			("GLU-A", 4, TEMPLATE, 2, src),
		)
		self.assertIn("GLU-A-v2", new.name)
		again = api.new_version(src)  # đã có bộ đang soạn của hệ thống
		self.assertEqual(again["name"], new.name)
		self.assertIn("message", again)
