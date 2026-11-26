"""FEAT-034 T01: luật mới của norm.validation (cấp phát sinh, k, gắn với, nội kiểm, khoản mục mẫu, set_blockers)."""

import unittest

from normcore.norm.validation import (
	COST_LEVEL_LABELS,
	COST_LEVELS,
	is_placeholder,
	line_errors,
	mandatory_status,
	normalize_line,
	set_blockers,
)

CTX = {
	"step_ids": {"S001"},
	"wastage_cap": 5,
	"changed": True,
	"paraclinical": True,
	"has_test_system": True,
	"qc_items": {"QC_L"},
	"template_items": {"Hóa chất chính", "Thiết bị"},
}


def ln(**kw):
	base = {
		"line_id": "L001",
		"step_id": "S001",
		"component": "DRUG",
		"resource_doctype": "NC Item",
		"resource": "HC_GLU",
		"hospital_qty": 1,
		"uom": "test",
		"basis": "Quy trình",
		"procedure_resource_row": "R1",
		"cost_level": "RESULT",
	}
	base.update(kw)
	return base


def errs(line, **ctx):
	return line_errors(line, {**CTX, **ctx})


class TestConstants(unittest.TestCase):
	def test_nhan_du_5_cap(self):
		self.assertEqual(set(COST_LEVELS), set(COST_LEVEL_LABELS))
		self.assertEqual(COST_LEVEL_LABELS["BATCH"], "Theo mẻ")


class TestNormalize(unittest.TestCase):
	def test_khong_can_lam_sang_luon_result(self):
		out = normalize_line(
			ln(cost_level="TUBE", apply_k=1, attach_to="Thiết bị", attach_equipment="EQ_A"),
			{"paraclinical": False},
		)
		self.assertEqual(
			(out["cost_level"], out["apply_k"], out["attach_to"], out["attach_equipment"]),
			("RESULT", 0, None, None),
		)

	def test_cap_khac_day_period_xoa_gan_voi(self):
		out = normalize_line(ln(cost_level="BATCH", attach_to="Thiết bị", attach_equipment="EQ_A"), CTX)
		self.assertIsNone(out["attach_to"])
		self.assertIsNone(out["attach_equipment"])

	def test_gan_he_thong_xoa_thiet_bi(self):
		out = normalize_line(
			ln(cost_level="DAY", attach_to="Hệ thống xét nghiệm", attach_equipment="EQ_A"), CTX
		)
		self.assertEqual(out["attach_to"], "Hệ thống xét nghiệm")
		self.assertIsNone(out["attach_equipment"])

	def test_gan_thiet_bi_giu_nguyen(self):
		out = normalize_line(ln(cost_level="PERIOD", attach_to="Thiết bị", attach_equipment="EQ_A"), CTX)
		self.assertEqual(out["attach_equipment"], "EQ_A")

	def test_TC_CLS_30_bat_k_dua_hao_hut_ve_0(self):
		src = ln(apply_k=1, wastage_rate=5, wastage_reason="mẻ hỏng")
		out = normalize_line(src, CTX)
		self.assertEqual((out["wastage_rate"], out["wastage_reason"]), (0, None))
		self.assertEqual(src["wastage_rate"], 5)  # không đổi đầu vào

	def test_k_khong_hop_le_khong_dung_hao_hut(self):
		out = normalize_line(ln(apply_k=1, cost_level="BATCH", wastage_rate=5), CTX)
		self.assertEqual(out["wastage_rate"], 5)  # để line_errors từ chối
		out = normalize_line(ln(apply_k=1, wastage_rate=5), {**CTX, "has_test_system": False})
		self.assertEqual(out["wastage_rate"], 5)

	def test_cap_trong_thanh_result(self):
		self.assertEqual(normalize_line(ln(cost_level=None), CTX)["cost_level"], "RESULT")

	def test_cap_la_giu_de_bao_loi(self):
		self.assertEqual(normalize_line(ln(cost_level="XYZ"), CTX)["cost_level"], "XYZ")


class TestLineErrorsCls(unittest.TestCase):
	def test_dong_hop_le(self):
		self.assertEqual(errs(ln()), [])
		self.assertEqual(errs(ln(apply_k=1)), [])

	def test_cap_ngoai_danh_sach(self):
		self.assertIn("cấp phát sinh XYZ", " ".join(errs(ln(cost_level="XYZ"))))

	def test_TC_CLS_30_k_o_dong_theo_me(self):
		e = errs(ln(apply_k=1, cost_level="BATCH", attach_to=None))
		self.assertIn("Dòng L001: chỉ bật Nhân k ở dòng Theo kết quả", e)

	def test_TC_CLS_30_k_o_nhan_luc(self):
		e = errs(ln(apply_k=1, component="LABOR", resource_doctype="NC Job Title", headcount=1))
		self.assertIn("Dòng L001: chỉ bật Nhân k ở dòng thuốc, hóa chất, vật tư", e)

	def test_k_khong_co_he_thong(self):
		e = errs(ln(apply_k=1), has_test_system=False)
		self.assertIn("Dòng L001: chỉ bật Nhân k ở bộ có hệ thống xét nghiệm", e)

	def test_day_thieu_gan_voi(self):
		self.assertIn("Dòng L001 thiếu: Gắn với", errs(ln(cost_level="DAY")))

	def test_gan_voi_ngoai_danh_sach(self):
		self.assertTrue(
			any("không thuộc danh sách" in x for x in errs(ln(cost_level="DAY", attach_to="Khác")))
		)

	def test_gan_he_thong_khi_bo_khong_co_he_thong(self):
		e = errs(ln(cost_level="PERIOD", attach_to="Hệ thống xét nghiệm"), has_test_system=False)
		self.assertTrue(any("chỉ gắn với Hệ thống xét nghiệm" in x for x in e))

	def test_gan_thiet_bi_thieu_thiet_bi(self):
		self.assertIn("Dòng L001 thiếu: Thiết bị được gắn", errs(ln(cost_level="DAY", attach_to="Thiết bị")))

	def test_gan_hop_le(self):
		self.assertEqual(errs(ln(cost_level="DAY", attach_to="Hệ thống xét nghiệm")), [])
		self.assertEqual(errs(ln(cost_level="DAY", attach_to="Thiết bị", attach_equipment="EQ_A")), [])

	def test_TC_CLS_31_dong_dung_qc_l(self):
		e = errs(ln(resource="QC_L"))
		self.assertEqual(len(e), 1)
		self.assertIn("QC_L", e[0])
		self.assertIn("kế hoạch", e[0])

	def test_qc_l_dong_khong_doi_khong_bao(self):
		self.assertEqual(errs(ln(resource="QC_L"), changed=False), [])

	def test_qc_khac_doctype_khong_trung(self):
		self.assertEqual(
			errs(ln(resource="QC_L", resource_doctype="NC Equipment", component="EQUIPMENT")), []
		)

	def test_khoan_muc_ngoai_mau(self):
		self.assertEqual(errs(ln(template_item="Hóa chất chính")), [])
		self.assertTrue(any("không thuộc mẫu" in x for x in errs(ln(template_item="Lạ"))))
		self.assertTrue(
			any("không thuộc mẫu" in x for x in errs(ln(template_item="Thiết bị"), template_items=()))
		)


class TestPlaceholder(unittest.TestCase):
	def holder(self, **kw):
		base = {
			"line_id": "L009",
			"service_level": 1,
			"component": "EQUIPMENT",
			"resource_doctype": "NC Equipment",
			"template_item": "Thiết bị",
			"hospital_qty": None,
			"basis": "Ước tính",
		}
		base.update(kw)
		return base

	def test_nhan_dien(self):
		self.assertTrue(is_placeholder(self.holder()))
		self.assertFalse(is_placeholder(self.holder(template_item=None)))
		self.assertFalse(is_placeholder(self.holder(procedure_resource_row="R1")))
		self.assertFalse(is_placeholder(self.holder(hospital_qty=2)))
		self.assertFalse(is_placeholder(self.holder(is_excluded=1)))

	def test_chua_sua_khong_bao_thieu(self):
		self.assertEqual(errs(self.holder(), changed=False), [])

	def test_sua_roi_kiem_day_du(self):
		e = errs(self.holder(), changed=True)
		self.assertIn("Nguồn lực", e[0])
		self.assertIn("Đơn vị", e[0])
		self.assertIn("Định mức của bệnh viện", e[0])

	def test_nhan_luc_giu_cho_khong_bao_thieu_so_phut(self):
		h = self.holder(component="LABOR", resource_doctype="NC Job Title", template_item="Hóa chất chính")
		self.assertEqual(errs(h, changed=False), [])


class TestMandatoryStatus(unittest.TestCase):
	ITEMS = ({"item_name": "Thiết bị", "is_mandatory": 1}, {"item_name": "Hóa chất chính", "is_mandatory": 1})

	def test_dat_khi_co_luong(self):
		st = mandatory_status(self.ITEMS, [ln(template_item="Hóa chất chính")])
		self.assertEqual([s["satisfied"] for s in st], [False, True])

	def test_dat_khi_loai_tru_hop_le(self):
		lines = [ln(template_item="Thiết bị", is_excluded=1, exclude_reason="Không áp dụng", hospital_qty=0)]
		self.assertTrue(mandatory_status(self.ITEMS, lines)[0]["satisfied"])

	def test_khong_dat_khi_loai_tru_ly_do_la(self):
		lines = [ln(template_item="Thiết bị", is_excluded=1, exclude_reason="", hospital_qty=0)]
		self.assertFalse(mandatory_status(self.ITEMS, lines)[0]["satisfied"])

	def test_khong_dat_khi_luong_0(self):
		self.assertFalse(
			mandatory_status(self.ITEMS, [ln(template_item="Thiết bị", hospital_qty=0)])[0]["satisfied"]
		)

	def test_mau_rong(self):
		self.assertEqual(mandatory_status(None, []), [])


class TestSetBlockers(unittest.TestCase):
	def test_sach(self):
		head = {"test_system": "GLU-A", "tests_per_tube": 4}
		self.assertEqual(set_blockers(head, [ln()], {"ts_required": True, "qc_items": {"QC_L"}}), [])

	def test_thieu_he_thong(self):
		self.assertEqual(
			set_blockers({"test_system": None}, [], {"ts_required": True}), ["Chưa gắn hệ thống xét nghiệm"]
		)
		self.assertEqual(set_blockers({"test_system": None}, [], {"ts_required": False}), [])

	def test_TC_CLS_32_thieu_so_xn_moi_ong(self):
		lines = [ln(line_id="L001", cost_level="TUBE"), ln(line_id="L002", cost_level="TUBE", is_excluded=1)]
		e = set_blockers({"test_system": "GLU-A", "tests_per_tube": 0}, lines, {})
		self.assertEqual(len(e), 1)
		self.assertIn("Số xét nghiệm bình quân trên một ống mẫu", e[0])
		self.assertIn("L001", e[0])
		self.assertNotIn("L002", e[0])
		self.assertEqual(set_blockers({"tests_per_tube": 4}, lines, {}), [])

	def test_khong_co_dong_tube_khong_can_so_xn(self):
		self.assertEqual(set_blockers({"tests_per_tube": 0}, [ln()], {}), [])

	def test_TC_CLS_32_thieu_khoan_muc_bat_buoc(self):
		ctx = {
			"mandatory_items": [
				{"item_name": "Thiết bị", "is_mandatory": 1},
				{"item_name": "Điện nước", "is_mandatory": 0},
				{"item_name": "Hóa chất chính"},
			]
		}
		e = set_blockers({"tests_per_tube": 1}, [], ctx)
		self.assertEqual(e, ["Thiếu khoản mục bắt buộc của mẫu: Thiết bị, Hóa chất chính"])

	def test_dong_dung_mat_hang_ke_hoach(self):
		e = set_blockers({"tests_per_tube": 1}, [ln(resource="QC_L")], {"qc_items": {"QC_L"}})
		self.assertEqual(e, ["Dòng L001 dùng mặt hàng của kế hoạch chất lượng: QC_L"])
		self.assertEqual(
			set_blockers({"tests_per_tube": 1}, [ln(resource="QC_L", is_excluded=1)], {"qc_items": {"QC_L"}}),
			[],
		)
