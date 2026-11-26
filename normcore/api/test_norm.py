"""FEAT-012: API bộ định mức (UC-009). Mỗi TC có test cùng mã; quyền: Council không có quyền, Auditor chỉ đọc."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import access
from normcore.api import norm as api
from normcore.tests.utils import (
	ensure,
	make_base,
	make_equipment,
	make_param_set,
	make_procedure,
	make_user,
	publish_procedure,
)

DEPT, OTHER = "K01-N12", "K02-N12"


class NormBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, _d, self.job = make_base(department=DEPT)
		make_base(service="DV-TEST-B", department=OTHER)
		ensure("NC Job Title", "job_title_code", "BS", job_title_name="Bác sĩ", job_group="Bác sĩ")
		self.items = {
			c: ensure(
				"NC Item", "item_code", c, item_name=c, item_type=t, uom="cái", norm_units_per_purchase_unit=1
			)
			for c, t in (("VT-N12", "Vật tư tiêu hao"), ("TH-N12", "Thuốc"), ("DIEN-N12", "Tiện ích"))
		}
		self.equipment = make_equipment("TB-N12", department=DEPT)
		self.room = ensure(
			"NC Room",
			"room_code",
			"P-N12",
			room_name="Phòng",
			department=DEPT,
			annual_infrastructure_cost=52800000,
			available_hours_per_year=2112,
		)
		self.clin = make_user("clin.n12@normcore.test", "NC Clinician")
		self.clin2 = make_user("clin2.n12@normcore.test", "NC Clinician")
		self.head = make_user("head.n12@normcore.test", "NC Department Head")
		self.fin = make_user("fin.n12@normcore.test", "NC Finance")
		self.aud = make_user("aud.n12@normcore.test", "NC Auditor")
		self.council = make_user("council.n12@normcore.test", "NC Council Member")
		for u in (self.clin, self.head):
			access.assign_department(u, DEPT)
		access.assign_department(self.clin2, OTHER)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def procedure6(self):
		"""Quy trình ban hành có 6 dòng nguồn lực: 2 Nhân lực, Thuốc, Vật tư, Thiết bị, Phòng."""
		proc = make_procedure(self.service, DEPT, minutes=10)
		step = proc.steps[0].step_id
		for rtype, doctype, name, qty, uom, hc in (
			("Nhân lực", "NC Job Title", "BS", 20, "phút", 1),
			("Thuốc", None, None, 1, "ống", None),
			("Vật tư", "NC Item", "VT-N12", 2, "cái", None),
			("Thiết bị", None, None, 20, "phút", None),
			("Phòng", None, None, 30, "phút", None),
		):
			proc.append(
				"resources",
				{
					"step_id": step,
					"resource_type": rtype,
					"resource_text": rtype,
					"linked_doctype": doctype,
					"linked_name": name,
					"quantity": qty,
					"uom": uom,
					"headcount": hc,
				},
			)
		proc.save(ignore_permissions=True)
		return publish_procedure(proc)

	def make_set(self):
		frappe.set_user(self.clin)
		self.proc = self.procedure6()
		return api.create_norm_set(self.proc.name)["name"]

	def link_all(self, name, skip=()):
		"""Dựng dữ liệu: gắn nguồn lực cho mọi dòng chưa liên kết (trừ `skip`)."""
		target = {
			"DRUG": ("NC Item", "TH-N12"),
			"EQUIPMENT": ("NC Equipment", "TB-N12"),
			"INFRA": ("NC Room", "P-N12"),
		}
		for r in frappe.get_doc("NC Norm Set", name).lines:
			if not r.resource and r.line_id not in skip and r.component in target:
				frappe.db.set_value("NC Norm Line", r.name, "resource", target[r.component][1])

	def confirm_all(self, name, skip=()):
		frappe.set_user(self.clin)
		for r in frappe.get_doc("NC Norm Set", name).lines:
			if r.line_id not in skip:
				api.confirm_line(name, r.line_id)

	def to_confirmed(self, name):
		self.link_all(name)
		self.confirm_all(name)
		frappe.set_user(self.head)
		api.confirm_set(name)


class TestKhoiTao(NormBase):
	def test_TC_NORM_01_khoi_tao_6_dong_mang_ma_buoc_va_dong_goc(self):
		name = self.make_set()
		ns = frappe.get_doc("NC Norm Set", name)
		self.assertEqual(ns.status, "Nháp")
		self.assertEqual(len(ns.lines), 6)
		rows = {r.resource_row_id: r for r in frappe.get_doc("NC Clinical Procedure", self.proc.name).resources}
		for ln in ns.lines:
			self.assertTrue(ln.step_id)
			self.assertEqual(ln.step_id, rows[ln.procedure_resource_row].step_id)
		self.assertEqual([r.component for r in ns.lines], ["LABOR", "LABOR", "DRUG", "SUPPLY", "EQUIPMENT", "INFRA"])
		self.assertEqual(sum(1 for r in ns.lines if not r.resource), 3)

	def test_TC_NORM_02_quy_trinh_nhap_tu_choi_qua_api(self):
		frappe.set_user(self.clin)
		proc = make_procedure(self.service, DEPT)
		self.assertRaises(frappe.ValidationError, api.create_norm_set, proc.name)
		self.assertFalse(frappe.db.exists("NC Norm Set", {"procedure": proc.name}))


class TestSuaDong(NormBase):
	def test_TC_NORM_04_vuot_tran_hao_hut_can_ly_do(self):
		make_param_set().db_set("wastage_cap", 5)
		name = self.make_set()
		self.link_all(name)
		sup = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.component == "SUPPLY")
		with self.assertRaises(frappe.ValidationError) as cm:
			api.save_line(name, {"wastage_rate": 8}, sup.line_id)
		self.assertIn("Lý do vượt trần", str(cm.exception))
		res = api.save_line(name, {"wastage_rate": 8, "wastage_reason": "Hao hụt khi cắt"}, sup.line_id)
		self.assertTrue(res["saved"])

	def test_TC_NORM_07_loai_tru_can_ly_do_trong_danh_sach(self):
		name = self.make_set()
		sup = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.component == "SUPPLY")
		self.assertRaises(frappe.ValidationError, api.save_line, name, {"is_excluded": 1}, sup.line_id)
		self.assertRaises(
			frappe.ValidationError, api.save_line, name, {"is_excluded": 1, "exclude_reason": "Tùy ý"}, sup.line_id
		)
		res = api.save_line(name, {"is_excluded": 1, "exclude_reason": "Thanh toán riêng"}, sup.line_id)
		self.assertTrue(res["saved"])

	def test_TC_NORM_09_dong_them_phai_gan_buoc_hoac_chung(self):
		name = self.make_set()
		new = {
			"component": "UTILITY",
			"resource_doctype": "NC Item",
			"resource": "DIEN-N12",
			"hospital_qty": 0.5,
			"uom": "kWh",
			"basis": "Ước tính",
		}
		with self.assertRaises(frappe.ValidationError) as cm:
			api.save_line(name, json.dumps(new))
		self.assertIn("mã bước", str(cm.exception))
		self.assertTrue(api.save_line(name, {**new, "service_level": 1})["saved"])
		general = [r for r in frappe.get_doc("NC Norm Set", name).lines if r.service_level]
		self.assertEqual(len(general), 1)
		self.assertFalse(general[0].step_id)
		step = self.proc.steps[0].step_id
		other = {**new, "step_id": step}
		self.assertTrue(api.save_line(name, other)["saved"])

	def test_TC_NORM_10_thieu_don_vi_thieu_so_phut_tu_choi(self):
		name = self.make_set()
		ns = frappe.get_doc("NC Norm Set", name)
		sup = next(r for r in ns.lines if r.component == "SUPPLY")
		labor = ns.lines[0]
		with self.assertRaises(frappe.ValidationError) as cm:
			api.save_line(name, {"uom": ""}, sup.line_id)
		self.assertIn("Đơn vị", str(cm.exception))
		with self.assertRaises(frappe.ValidationError) as cm:
			api.save_line(name, {"hospital_qty": 0}, labor.line_id)
		self.assertIn("Số phút", str(cm.exception))
		self.assertEqual(frappe.db.get_value("NC Norm Line", sup.name, "uom"), "cái")
		self.assertEqual(frappe.db.get_value("NC Norm Line", labor.name, "hospital_qty"), 10)

	def test_TC_NORM_11_can_cu_va_tham_chieu(self):
		name = self.make_set()
		l03 = frappe.get_doc("NC Norm Set", name).lines[1]
		api.save_line(name, {"basis": "Định mức ban hành", "basis_ref": "QĐ 123/QĐ-BYT"}, l03.line_id)
		row = frappe.db.get_value("NC Norm Line", l03.name, ["basis", "basis_ref"], as_dict=True)
		self.assertEqual((row.basis, row.basis_ref), ("Định mức ban hành", "QĐ 123/QĐ-BYT"))
		self.assertRaises(frappe.ValidationError, api.save_line, name, {"basis": "Theo cảm tính"}, l03.line_id)
		self.assertEqual(frappe.db.get_value("NC Norm Line", l03.name, "basis"), "Định mức ban hành")

	def test_truong_khong_duoc_nhap_bi_tu_choi(self):
		name = self.make_set()
		line = frappe.get_doc("NC Norm Set", name).lines[0].line_id
		self.assertRaises(frappe.ValidationError, api.save_line, name, {"confirmed_by": "Administrator"}, line)

	def test_FR_NORM_014_canh_bao_trung(self):
		name = self.make_set()
		step = self.proc.steps[0].step_id
		row = {"step_id": step, "component": "SUPPLY", "resource_doctype": "NC Item", "resource": "VT-N12",
			"hospital_qty": 1, "uom": "cái", "basis": "Ước tính"}
		res = api.save_line(name, row)
		self.assertFalse(res["saved"])
		self.assertEqual(res["duplicates"][0]["resource"], "VT-N12")
		self.assertEqual(len(frappe.get_doc("NC Norm Set", name).lines), 6)
		self.assertTrue(api.save_line(name, row, allow_duplicate=1)["saved"])
		data = api.get_norm_set(name)
		flagged = [x for g in data["groups"] for x in g["lines"] if x["duplicate_of"]]
		self.assertEqual(len(flagged), 2)

	def test_xoa_dong(self):
		name = self.make_set()
		step = self.proc.steps[0].step_id
		api.save_line(name, {"step_id": step, "component": "SUPPLY", "resource_doctype": "NC Item",
			"resource": "DIEN-N12", "hospital_qty": 1, "uom": "cái", "basis": "Ước tính"})
		lines = frappe.get_doc("NC Norm Set", name).lines
		self.assertRaises(frappe.ValidationError, api.delete_line, name, lines[0].line_id)  # dòng gốc
		api.delete_line(name, lines[-1].line_id)
		self.assertEqual(len(frappe.get_doc("NC Norm Set", name).lines), 6)
		self.assertRaises(frappe.ValidationError, api.delete_line, name, "L999")

	def test_FR_NORM_016_get_norm_set_co_chi_phi_tam_tinh(self):
		make_param_set()
		name = self.make_set()
		data = api.get_norm_set(name)
		labor = data["groups"][0]["lines"][0]
		self.assertEqual(labor["component"], "LABOR")
		self.assertIn("amount", labor["cost"])
		thuoc = next(x for g in data["groups"] for x in g["lines"] if x["component"] == "DRUG")
		self.assertEqual(thuoc["cost"], {"missing": "Chưa có đơn giá"})  # chưa liên kết
		self.assertTrue(data["summary"]["incomplete"])
		self.assertEqual(data["summary"]["parameter_set"], frappe.get_all("NC Costing Parameter Set", pluck="name")[0])
		self.assertEqual(data["groups"][-1]["title"], "Chung cho cả dịch vụ")
		self.assertEqual(len(data["steps"]), 1)
		self.assertIn("save_line", data["actions"])


class TestXacNhan(NormBase):
	def test_TC_NORM_12_xac_nhan_mot_dong(self):
		name = self.make_set()
		self.link_all(name)
		l01 = frappe.get_doc("NC Norm Set", name).lines[0].line_id
		frappe.set_user(self.clin)
		api.confirm_line(name, l01)
		rows = frappe.get_doc("NC Norm Set", name).lines
		self.assertEqual(rows[0].confirmed_by, self.clin)
		self.assertIsNotNone(rows[0].confirmed_on)
		self.assertTrue(all(not r.confirmed_by for r in rows[1:]))
		frappe.set_user(self.clin2)  # Clinician khoa khác
		self.assertRaises(frappe.PermissionError, api.confirm_line, name, rows[1].line_id)

	def test_confirm_line_dong_chua_lien_ket_bi_tu_choi(self):
		name = self.make_set()
		drug = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.component == "DRUG")
		self.assertRaises(frappe.ValidationError, api.confirm_line, name, drug.line_id)

	def test_TC_NORM_05_con_dong_chua_xac_nhan_chua_lien_ket_tu_choi(self):
		name = self.make_set()
		lines = frappe.get_doc("NC Norm Set", name).lines
		drug = next(r for r in lines if r.component == "DRUG")  # sẽ chưa liên kết
		infra = next(r for r in lines if r.component == "INFRA")  # sẽ chưa xác nhận
		self.link_all(name, skip=(drug.line_id,))
		self.confirm_all(name, skip=(infra.line_id, drug.line_id))
		frappe.db.set_value("NC Norm Line", drug.name, "confirmed_by", self.clin)  # đã xác nhận nhưng chưa liên kết
		frappe.set_user(self.head)
		with self.assertRaises(frappe.ValidationError) as cm:
			api.confirm_set(name)
		msg = str(cm.exception)
		self.assertIn(drug.line_id, msg)
		self.assertIn(infra.line_id, msg)
		self.assertEqual(msg.count("<br>"), 1)  # đúng hai dòng
		self.assertEqual(frappe.db.get_value("NC Norm Set", name, "status"), "Nháp")
		# gỡ hết cản trở
		frappe.db.set_value("NC Norm Line", drug.name, "resource", "TH-N12")
		self.confirm_all(name, skip=[r.line_id for r in frappe.get_doc("NC Norm Set", name).lines if r.confirmed_by])
		frappe.set_user(self.head)
		out = api.confirm_set(name)
		self.assertEqual(out["doc"]["status"], "Đã xác nhận chuyên môn")

	def test_confirm_set_chi_nc_department_head(self):
		name = self.make_set()
		self.assertRaises(frappe.PermissionError, api.confirm_set, name)  # Clinician

	def test_dong_sua_sau_xac_nhan_mat_xac_nhan(self):
		name = self.make_set()
		self.link_all(name)
		l01 = frappe.get_doc("NC Norm Set", name).lines[0].line_id
		api.confirm_line(name, l01)
		api.save_line(name, {"hospital_qty": 12}, l01)
		self.assertFalse(frappe.get_doc("NC Norm Set", name).lines[0].confirmed_by)


class TestKhoa(NormBase):
	def test_TC_NORM_06_khoa_tu_choi_sua_tao_phien_ban_moi(self):
		name = self.make_set()
		self.to_confirmed(name)
		frappe.set_user(self.fin)
		out = api.lock_set(name)
		self.assertEqual(out["doc"]["status"], "Đã khóa")
		self.assertEqual(out["doc"]["locked_by"], self.fin)
		before = frappe.db.get_value("NC Norm Line", {"parent": name, "idx": 1}, "hospital_qty")
		frappe.set_user(self.head)
		line = frappe.get_doc("NC Norm Set", name).lines[0].line_id
		self.assertRaises(frappe.ValidationError, api.save_line, name, {"hospital_qty": 99}, line)
		doc = frappe.get_doc("NC Norm Set", name)
		doc.lines[0].hospital_qty = 99
		self.assertRaises(frappe.ValidationError, doc.save)
		frappe.set_user("Administrator")
		self.assertRaises(
			frappe.ValidationError, frappe.client.set_value, "NC Norm Set", name, "step_change_note", "x"
		)
		self.assertEqual(frappe.db.get_value("NC Norm Line", {"parent": name, "idx": 1}, "hospital_qty"), before)
		# phiên bản mới
		frappe.set_user(self.head)
		new = api.new_version(name)["name"]
		src = frappe.get_doc("NC Norm Set", name)
		nv = frappe.get_doc("NC Norm Set", new)
		self.assertEqual((nv.status, nv.version_no, nv.previous_version), ("Nháp", src.version_no + 1, name))
		self.assertEqual([r.line_id for r in nv.lines], [r.line_id for r in src.lines])
		self.assertTrue(all(not r.confirmed_by for r in nv.lines))
		self.assertEqual(api.new_version(name)["name"], new)  # không tạo thêm (ASM-012-09)
		self.assertEqual(src.status, "Đã khóa")

	def test_khoa_tu_nhap_bi_tu_choi_qua_api(self):
		name = self.make_set()
		frappe.set_user(self.fin)
		self.assertRaises(frappe.ValidationError, api.lock_set, name)

	def test_new_version_nguon_khong_khoa_bi_tu_choi(self):
		name = self.make_set()
		self.assertRaises(frappe.ValidationError, api.new_version, name)

	def test_tra_lai_can_ly_do(self):
		name = self.make_set()
		self.to_confirmed(name)
		frappe.set_user(self.fin)
		self.assertRaises(frappe.ValidationError, api.return_set, name, "  ")
		out = api.return_set(name, "Sai định mức vật tư")
		self.assertEqual(out["doc"]["status"], "Nháp")
		ev = frappe.get_all(
			"NC Audit Event",
			{"ref_doctype": "NC Norm Set", "ref_name": name},
			["to_state", "detail"],
			order_by="creation desc",
		)
		self.assertEqual(ev[0].detail, "Sai định mức vật tư")
		self.assertTrue(frappe.get_doc("NC Norm Set", name).lines[0].confirmed_by)  # giữ xác nhận

	def test_tra_lai_chi_nc_finance(self):
		name = self.make_set()
		self.to_confirmed(name)
		frappe.set_user(self.head)
		self.assertRaises(frappe.PermissionError, api.return_set, name, "x")
		self.assertRaises(frappe.PermissionError, api.lock_set, name)


class TestQuyen(NormBase):
	def test_quyen_norm_set_council_khong_co_quyen(self):
		name = self.make_set()
		frappe.set_user(self.council)
		self.assertRaises(frappe.PermissionError, api.get_norm_set, name)
		self.assertRaises(frappe.PermissionError, api.save_line, name, {"uom": "x"}, "L001")
		self.assertRaises(frappe.PermissionError, api.create_norm_set, self.proc.name)

	def test_quyen_norm_set_auditor_chi_doc(self):
		name = self.make_set()
		frappe.set_user(self.aud)
		self.assertEqual(api.get_norm_set(name)["doc"]["name"], name)
		self.assertEqual(api.get_norm_set(name)["actions"], [])
		for fn, args in (
			(api.save_line, (name, {"uom": "x"}, "L001")),
			(api.delete_line, (name, "L001")),
			(api.confirm_line, (name, "L001")),
			(api.confirm_set, (name,)),
			(api.return_set, (name, "x")),
			(api.lock_set, (name,)),
			(api.new_version, (name,)),
			(api.create_norm_set, (self.proc.name,)),
		):
			self.assertRaises(frappe.PermissionError, fn, *args)

	def test_quyen_norm_set_finance_khong_sua_khong_xac_nhan(self):
		name = self.make_set()
		frappe.set_user(self.fin)
		self.assertRaises(frappe.PermissionError, api.save_line, name, {"uom": "x"}, "L001")
		self.assertRaises(frappe.PermissionError, api.confirm_set, name)

	def test_quyen_norm_set_clinician_khong_confirm_set_lock(self):
		name = self.make_set()
		self.assertRaises(frappe.PermissionError, api.confirm_set, name)
		self.assertRaises(frappe.PermissionError, api.lock_set, name)

	def test_quyen_norm_set_clinician_khoa_khac_khong_ghi(self):
		name = self.make_set()
		frappe.set_user(self.clin2)
		self.assertRaises(frappe.PermissionError, api.save_line, name, {"uom": "x"}, "L001")
