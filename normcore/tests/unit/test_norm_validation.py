import unittest
from datetime import date

from normcore.norm.validation import (
	confirm_blockers,
	duplicates,
	effective_parameter_set,
	line_errors,
)

CTX = {"step_ids": {"S001", "S002"}, "wastage_cap": 5, "changed": True}


def ln(**kw):
	base = {
		"line_id": "L001",
		"step_id": "S001",
		"component": "SUPPLY",
		"resource_doctype": "NC Item",
		"resource": "GANG",
		"hospital_qty": 2,
		"uom": "cái",
		"basis": "Quy trình",
		"procedure_resource_row": "R1",
	}
	base.update(kw)
	return base


def errs(line, **ctx):
	return line_errors(line, {**CTX, **ctx})


class TestLineErrors(unittest.TestCase):
	def test_dong_hop_le(self):
		self.assertEqual(errs(ln()), [])

	def test_TC_NORM_10_thieu_don_vi(self):
		e = errs(ln(uom=""))
		self.assertIn("Đơn vị", e[0])
		self.assertIn("L001", e[0])

	def test_TC_NORM_10_thieu_so_phut(self):
		e = errs(
			ln(component="LABOR", resource_doctype="NC Job Title", resource="BS", headcount=1, hospital_qty=0)
		)
		self.assertIn("Số phút", e[0])

	def test_labor_thieu_so_nguoi(self):
		e = errs(ln(component="LABOR", resource_doctype="NC Job Title", resource="BS", headcount=0))
		self.assertIn("Số người", e[0])

	def test_thieu_cau_phan_va_dinh_muc(self):
		e = errs(ln(component="", hospital_qty=0, resource_doctype=None))
		self.assertIn("Cấu phần", e[0])
		self.assertIn("Định mức của bệnh viện", e[0])

	def test_khong_bat_nguon_luc_khi_khong_sua(self):
		self.assertEqual(errs(ln(resource=None), changed=False), [])
		self.assertIn("Nguồn lực", errs(ln(resource=None))[0])

	def test_loai_tru_khong_can_dinh_muc(self):
		self.assertEqual(errs(ln(hospital_qty=0, is_excluded=1, exclude_reason="Thanh toán riêng")), [])

	def test_cau_phan_la(self):
		self.assertTrue(any("không hợp lệ" in x for x in errs(ln(component="X", resource_doctype="NC Item"))))

	def test_TC_NORM_04_vuot_tran(self):
		e = errs(ln(wastage_rate=8))
		self.assertIn("Lý do vượt trần", e[0])
		self.assertEqual(errs(ln(wastage_rate=8, wastage_reason="Hao hụt do cắt")), [])
		self.assertEqual(errs(ln(wastage_rate=5)), [])
		self.assertEqual(
			errs(ln(component="LABOR", resource_doctype="NC Job Title", headcount=1, wastage_rate=8)), []
		)

	def test_hao_hut_ngoai_khoang(self):
		self.assertTrue(errs(ln(wastage_rate=101, wastage_reason="x")))
		self.assertTrue(errs(ln(wastage_rate=-1)))

	def test_dinh_muc_ban_hanh_am(self):
		self.assertTrue(errs(ln(authority_qty=-1)))

	def test_TC_NORM_09_dong_them_phai_chon_buoc_hoac_chung(self):
		new = ln(procedure_resource_row=None, component="UTILITY", step_id=None)
		self.assertIn("mã bước", errs(new)[0])
		self.assertEqual(errs({**new, "service_level": 1}), [])
		self.assertEqual(errs({**new, "step_id": "S002"}), [])
		self.assertTrue(errs({**new, "step_id": "S002", "service_level": 1}))  # cả hai

	def test_DI04_ma_buoc_khong_ton_tai(self):
		self.assertIn("không tồn tại", errs(ln(step_id="S999"))[0])

	def test_DI05_sai_loai_nguon_luc(self):
		self.assertIn("phải gắn NC Equipment", errs(ln(component="EQUIPMENT"))[0])

	def test_FR_NORM_008_can_cu(self):
		self.assertIn("căn cứ", errs(ln(basis="Theo cảm tính"))[0])
		self.assertEqual(errs(ln(basis="Định mức ban hành")), [])

	def test_TC_NORM_07_loai_tru(self):
		self.assertIn("Lý do loại trừ", errs(ln(is_excluded=1))[0])
		self.assertTrue(errs(ln(is_excluded=1, exclude_reason="Tùy ý")))
		self.assertEqual(errs(ln(is_excluded=1, exclude_reason="Thanh toán riêng")), [])

	def test_mac_dinh_tran_va_dong_moi(self):
		self.assertEqual(line_errors(ln(), {"step_ids": {"S001"}}), [])
		self.assertTrue(line_errors({"component": "SUPPLY"}, {}))  # dòng mới, thiếu nhiều


class TestDuplicates(unittest.TestCase):
	def test_trung_cung_buoc(self):
		d = duplicates([ln(line_id="L1"), ln(line_id="L2"), ln(line_id="L3", step_id="S002")])
		self.assertEqual(d, {"L1": ["L2"], "L2": ["L1"]})

	def test_dong_chung(self):
		a = ln(line_id="L1", step_id=None, service_level=1)
		b = ln(line_id="L2", step_id=None, service_level=1)
		self.assertEqual(set(duplicates([a, b])), {"L1", "L2"})

	def test_bo_qua_chua_lien_ket_va_loai_tru(self):
		d = duplicates(
			[
				ln(line_id="L1", resource=None),
				ln(line_id="L2", resource=None),
				ln(line_id="L3", is_excluded=1),
				ln(line_id="L4"),
			]
		)
		self.assertEqual(d, {})


class TestConfirmBlockers(unittest.TestCase):
	def test_TC_NORM_05_hai_dong(self):
		ok = lambda i: ln(line_id=i, confirmed_by="a@x")  # noqa: E731
		lines = [ok("L001"), ln(line_id="L002", resource="IT"), ok("L003") | {"resource": None}, ok("L004")]
		b = confirm_blockers(lines)
		self.assertEqual([x["line_id"] for x in b], ["L002", "L003"])
		self.assertEqual(b[0]["reasons"], ["Chưa xác nhận"])
		self.assertEqual(b[1]["reasons"], ["Chưa liên kết danh mục"])

	def test_ai_va_thu_tu_ly_do(self):
		b = confirm_blockers([ln(line_id="L1", resource=None, ai_suggested=1)])
		self.assertEqual(
			b[0]["reasons"], ["Chưa xác nhận", "Chưa liên kết danh mục", "Còn đề xuất AI chưa xử lý"]
		)

	def test_sach(self):
		self.assertEqual(confirm_blockers([ln(confirmed_by="a@x")]), [])


class TestEffectiveParameterSet(unittest.TestCase):
	def test_chon(self):
		rows = [
			{"name": "A", "effective_from": date(2026, 1, 1)},
			{"name": "B", "effective_from": date(2026, 6, 1)},
			{"name": "C", "effective_from": date(2027, 1, 1)},
			{"name": "D", "effective_from": date(2026, 6, 1)},
			{"name": "E", "effective_from": None},
		]
		self.assertEqual(effective_parameter_set(rows, date(2026, 11, 1))["name"], "D")

	def test_khong_co(self):
		self.assertIsNone(
			effective_parameter_set([{"name": "C", "effective_from": date(2027, 1, 1)}], date(2026, 1, 1))
		)
