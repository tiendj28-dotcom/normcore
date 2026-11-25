"""FEAT-033: hàm thuần hồ sơ tuân thủ thiết bị (FR-CMP-001, 005, 006, 007, FR-ADM-006)."""

import unittest
from datetime import date, timedelta

from normcore.costing import compliance as c

TODAY = date(2026, 11, 23)


def rec(**kw):
	base = {
		"name": "HSTT-2026-0001",
		"record_code": "HS01",
		"equipment": "TB01",
		"department": "K01",
		"record_type": "Kiểm định",
		"cycle_months": 12,
		"provider": "Trung tâm KĐ",
		"cost_per_time": 1000000,
		"performed_on": date(2026, 1, 1),
		"expiry_date": TODAY + timedelta(days=20),
		"attachment": "/private/files/a.pdf",
	}
	base.update(kw)
	return base


class TestCompliance(unittest.TestCase):
	def test_reminder_days_mac_dinh_va_loi(self):
		self.assertEqual(c.reminder_days(None), 30)
		self.assertEqual(c.reminder_days(""), 30)
		self.assertEqual(c.reminder_days(10), 10)
		self.assertEqual(c.reminder_days(0), 0)
		with self.assertRaises(ValueError):
			c.reminder_days(-1)

	def test_compute_status_bien(self):
		cases = [
			(31, 30, "Còn hạn"),
			(30, 30, "Sắp hết hạn"),
			(20, 30, "Sắp hết hạn"),
			(20, 10, "Còn hạn"),
			(0, 30, "Sắp hết hạn"),
			(0, 0, "Sắp hết hạn"),
			(1, 0, "Còn hạn"),
			(-1, 30, "Hết hạn"),
		]
		for delta, n, expected in cases:
			with self.subTest(delta=delta, n=n):
				self.assertEqual(c.compute_status(TODAY + timedelta(days=delta), TODAY, n), expected)

	def test_compute_status_nhan_chuoi_ngay(self):
		self.assertEqual(c.compute_status("2026-12-13", "2026-11-23", 30), "Sắp hết hạn")

	def test_validate_record_hop_le(self):
		self.assertEqual(c.validate_record(rec()), [])

	def test_validate_record_thieu_truong_nen_tep(self):
		errs = c.validate_record(rec(attachment=None))
		self.assertEqual(len(errs), 1)
		self.assertIn("Tệp chứng từ", errs[0])
		self.assertEqual(len(c.validate_record(rec(provider="", equipment=None))), 2)

	def test_validate_record_rang_buoc(self):
		self.assertTrue(
			any("Chu kỳ" in e and "lớn hơn 0" in e for e in c.validate_record(rec(cycle_months=0)))
		)
		self.assertTrue(any("Chi phí" in e for e in c.validate_record(rec(cost_per_time=-1))))
		self.assertEqual(c.validate_record(rec(cost_per_time=0)), [])
		self.assertTrue(
			any("Ngày hết hạn" in e for e in c.validate_record(rec(expiry_date=date(2026, 1, 1))))
		)
		self.assertTrue(
			any("Ngày hết hạn" in e for e in c.validate_record(rec(expiry_date=date(2025, 1, 1))))
		)
		self.assertTrue(any("riêng tư" in e for e in c.validate_record(rec(attachment="/files/a.pdf"))))

	def test_is_valid_on_bien(self):
		r = rec()
		self.assertTrue(c.is_valid_on(r, r["performed_on"]))
		self.assertTrue(c.is_valid_on(r, r["expiry_date"]))
		self.assertFalse(c.is_valid_on(r, r["performed_on"] - timedelta(days=1)))
		self.assertFalse(c.is_valid_on(r, r["expiry_date"] + timedelta(days=1)))

	def test_has_valid_record(self):
		self.assertFalse(c.has_valid_record([], TODAY))
		old = rec(expiry_date=TODAY - timedelta(days=1))
		self.assertFalse(c.has_valid_record([old], TODAY))
		self.assertTrue(c.has_valid_record([old, rec()], TODAY))

	def test_missing_required(self):
		equipments = [
			{"name": "TB01", "compliance_required": 1},
			{"name": "TB02", "compliance_required": 1},
			{"name": "TB03", "compliance_required": 0},
			{"name": "TB04", "compliance_required": None},
		]
		by_eq = {"TB01": [rec()], "TB02": [rec(expiry_date=TODAY - timedelta(days=1))]}
		self.assertEqual([e["name"] for e in c.missing_required(equipments, by_eq, TODAY)], ["TB02"])

	def test_due_for_reminder(self):
		rs = [
			rec(name="A", expiry_date=TODAY + timedelta(days=20)),
			rec(name="B", expiry_date=TODAY + timedelta(days=40)),
			rec(name="C", expiry_date=TODAY - timedelta(days=1)),
		]
		self.assertEqual([r["name"] for r in c.due_for_reminder(rs, TODAY, 30)], ["A"])
		self.assertEqual(c.due_for_reminder(rs, TODAY, 10), [])

	def test_recipients(self):
		self.assertEqual(c.recipients(["b@x", "a@x", "b@x", ""], "a@x"), ["a@x", "b@x"])
		self.assertEqual(c.recipients(["b@x"], None), ["b@x"])
		self.assertEqual(c.recipients([], ""), [])

	def test_reminder_subject(self):
		s = c.reminder_subject(rec(expiry_date=date(2026, 12, 13)))
		for part in ("HS01", "TB01", "13/12/2026"):
			self.assertIn(part, s)
		# không có record_code thì dùng name
		self.assertIn("HSTT-2026-0001", c.reminder_subject(rec(record_code=None)))

	def test_build_expiry_report_thu_tu_va_loc(self):
		rs = [
			rec(name="A", department="K02", expiry_date=TODAY + timedelta(days=5)),
			rec(name="B", department="K01", expiry_date=TODAY + timedelta(days=10)),
			rec(name="C", department="K01", expiry_date=TODAY - timedelta(days=3)),
			rec(name="D", department="K01", expiry_date=TODAY + timedelta(days=90)),
		]
		missing = [{"name": "TB09", "department": "K01", "equipment_type": "T1"}]
		rows = c.build_expiry_report(rs, missing, TODAY, 30)
		self.assertEqual(
			[(r["department"], r["status"], r.get("record")) for r in rows],
			[
				("K01", "Hết hạn", "C"),
				("K01", "Sắp hết hạn", "B"),
				("K01", "Thiếu hồ sơ còn hạn", None),
				("K02", "Sắp hết hạn", "A"),
			],
		)
		self.assertEqual([r["days_left"] for r in rows[:3]], [-3, 10, None])
		self.assertEqual(rows[2]["equipment"], "TB09")
		only = c.build_expiry_report(rs, missing, TODAY, 30, department="K02")
		self.assertEqual([r["record"] for r in only], ["A"])
		missing_only = c.build_expiry_report(rs, missing, TODAY, 30, status="Thiếu hồ sơ còn hạn")
		self.assertEqual(missing_only[0]["equipment"], "TB09")
		due_only = c.build_expiry_report(rs, missing, TODAY, 10, status="Sắp hết hạn")
		self.assertEqual(due_only[0]["record"], "B")
