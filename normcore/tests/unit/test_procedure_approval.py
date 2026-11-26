"""Luồng duyệt ba cấp, thay thế phiên bản, nhắc quá hạn (FR-WF-001..008, FR-WF-013). Thuần Python."""

import unittest
from datetime import date

from normcore.procedure import approval as ap


def _row(name, version, eff, svc="DV1", dept="K1"):
	return {
		"name": name,
		"technical_service": svc,
		"department": dept,
		"version_no": version,
		"effective_date": eff,
	}


class TestApproval(unittest.TestCase):
	def test_luong_bon_trang_thai(self):
		s = "Nháp"
		for action, expected in (
			("Gửi duyệt", "Chờ trưởng khoa duyệt"),
			("Đồng ý", "Chờ hội đồng thẩm định"),
			("Thông qua", "Chờ ban hành"),
			("Ban hành", "Đã ban hành"),
		):
			s = ap.next_state(s, action)
			self.assertEqual(s, expected)

	def test_tu_choi_ve_nhap_o_ba_cap(self):
		for st in ap.PENDING_STATES:
			self.assertEqual(ap.next_state(st, "Từ chối"), "Nháp")

	def test_hanh_dong_sai(self):
		for st, act in (("Nháp", "Ban hành"), ("Chờ ban hành", "Đồng ý"), ("Đã ban hành", "Từ chối")):
			with self.assertRaises(ValueError):
				ap.next_state(st, act)

	def test_transitions_la_du_lieu(self):
		self.assertEqual(len(ap.TRANSITIONS), 7)

	def test_reject_level(self):
		self.assertEqual(ap.reject_level("Chờ trưởng khoa duyệt"), "trưởng khoa")
		self.assertEqual(ap.reject_level("Chờ hội đồng thẩm định"), "hội đồng")
		self.assertEqual(ap.reject_level("Chờ ban hành"), "giám đốc")

	def test_TC_WF_04_truoc_ngay_khong_thay_den_ngay_thay(self):
		rows = [_row("v1", 1, date(2026, 1, 1)), _row("v2", 2, date(2026, 6, 1))]
		self.assertEqual(ap.to_supersede(rows, date(2026, 5, 31)), [])
		self.assertEqual(ap.to_supersede(rows, date(2026, 6, 1)), ["v1"])
		self.assertEqual(ap.to_supersede(rows, date(2027, 1, 1)), ["v1"])

	def test_TC_WF_04_cung_ngay_lay_phien_ban_lon(self):
		rows = [_row("v1", 1, date(2026, 6, 1)), _row("v2", 2, date(2026, 6, 1))]
		self.assertEqual(ap.to_supersede(rows, date(2026, 6, 1)), ["v1"])

	def test_to_supersede_khac_khoa_dich_vu_khong_dung(self):
		rows = [_row("a1", 1, date(2026, 1, 1)), _row("b2", 2, date(2026, 1, 1), dept="K2")]
		self.assertEqual(ap.to_supersede(rows, date(2026, 6, 1)), [])

	def test_effective_procedure(self):
		rows = [_row("v1", 1, date(2026, 1, 1)), _row("v2", 2, date(2026, 6, 1))]
		self.assertEqual(ap.effective_procedure(rows, "DV1", "K1", date(2026, 3, 1)), "v1")
		self.assertEqual(ap.effective_procedure(rows, "DV1", "K1", date(2026, 6, 1)), "v2")
		self.assertIsNone(ap.effective_procedure(rows, "DV1", "K1", date(2025, 1, 1)))
		self.assertIsNone(ap.effective_procedure(rows, "DV9", "K1", date(2026, 3, 1)))

	def test_overdue(self):
		pend = [
			{"name": "a", "state": "Chờ ban hành", "entered_on": date(2026, 1, 1)},
			{"name": "b", "state": "Chờ ban hành", "entered_on": date(2026, 1, 3)},
		]
		got = ap.overdue(pend, date(2026, 1, 8), 7)
		self.assertEqual([p["name"] for p in got], ["a"])
		self.assertEqual(ap.overdue(pend, date(2026, 1, 7), 7), [])


class TestWithdraw(unittest.TestCase):
	def test_thu_hoi_next_state(self):
		self.assertEqual(ap.next_state("Đã ban hành", "Thu hồi"), "Đã thu hồi")

	def test_thu_hoi_khong_vao_transitions(self):
		self.assertEqual(len(ap.TRANSITIONS), 7)
		self.assertIn(ap.WITHDRAW, ap.ACTIONS)
		self.assertNotIn(ap.WITHDRAW, ap.TRANSITIONS)

	def test_thu_hoi_sai_trang_thai(self):
		for st in ("Nháp", "Đã thay thế", "Đã thu hồi"):
			with self.assertRaises(ValueError):
				ap.next_state(st, "Thu hồi")
