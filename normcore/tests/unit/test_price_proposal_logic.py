"""FEAT-030 T01: logic thuần của phương án giá (không import frappe). FR-PRICE-001..010."""

import sys
import unittest
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_engine as ge  # noqa: E402

from normcore.benchmark import proposal as pr  # noqa: E402

D = Decimal


def _golden_costs():
	res, _, _ = ge.run()
	out = []
	for svc, r in sorted(res.items()):
		out.append(
			{
				"technical_service": svc,
				"department": "KHOA-TEST",
				"full_cost": r["full"],
				"calculated_price": r["calc"],
				"rounded_price": r["rounded"],
				"calc_status": "Hoàn tất",
			}
		)
	return out


def _item(name, svc, dept, full, rounded, proposed=None, basis=None, **kw):
	return {
		"name": name,
		"technical_service": svc,
		"department": dept,
		"full_cost": D(str(full)),
		"rounded_price": D(str(rounded)),
		"proposed_price": D(str(proposed if proposed is not None else rounded)),
		"adjustment_basis": basis,
		"below_cost": 0,
		"director_ack": 0,
		"authority_price": None,
		**kw,
	}


class TestBuildItems(unittest.TestCase):
	def test_FR_PRICE_001_build_items(self):
		costs = _golden_costs()
		costs.append({"technical_service": "DV-LOI", "department": "K", "full_cost": D(1), "calculated_price": D(1), "rounded_price": D(1), "calc_status": "Lỗi"})
		items = pr.build_items(costs, {"DV-TEST-A": (D("300000"), 4)})
		self.assertEqual([i["technical_service"] for i in items], ["DV-TEST-A", "DV-TEST-B"])
		a, b = items
		self.assertEqual(a["proposed_price"], D("302100"))
		self.assertEqual(b["proposed_price"], D("92600"))
		self.assertEqual(a["full_cost"], D("287745.46"))
		self.assertEqual((a["benchmark_median"], a["benchmark_count"]), (D("300000"), 4))
		self.assertEqual((b["benchmark_median"], b["benchmark_count"]), (None, 0))
		self.assertEqual(a["below_cost"], 0)

	def test_FR_PRICE_001_build_items_dang_duoi_gia_thanh(self):
		items = pr.build_items([{"technical_service": "X", "department": "K", "full_cost": D(10), "calculated_price": D(12), "rounded_price": D(9), "calc_status": "Cảnh báo"}], {})
		self.assertEqual(len(items), 1)
		self.assertEqual(items[0]["below_cost"], 1)


class TestBelowCost(unittest.TestCase):
	def test_FR_PRICE_003_is_below_cost(self):
		self.assertTrue(pr.is_below_cost(D("280000"), D("287745.46")))
		self.assertFalse(pr.is_below_cost(D("287745.46"), D("287745.46")))
		self.assertFalse(pr.is_below_cost(D("300000"), D("287745.46")))
		self.assertFalse(pr.is_below_cost(D("1"), None))

	def test_FR_PRICE_003_approve_errors(self):
		items = [_item("r1", "DV-TEST-A", "K", "287745.46", 302100, 280000, "x"), _item("r2", "DV-TEST-B", "K", 50000, 92600)]
		items[0]["below_cost"] = 1
		errs = pr.approve_errors(items, [])
		self.assertEqual(len(errs), 1)
		self.assertIn("DV-TEST-A", errs[0])
		self.assertEqual(pr.approve_errors(items, ["r1"]), [])
		self.assertEqual(items[0]["director_ack"], 1)
		self.assertEqual(items[1]["director_ack"], 0)


class TestSubmit(unittest.TestCase):
	def test_FR_PRICE_002_needs_basis(self):
		self.assertFalse(pr.needs_basis(_item("r", "A", "K", 1, 302100)))
		self.assertTrue(pr.needs_basis(_item("r", "A", "K", 1, 302100, 295000)))

	def test_FR_PRICE_002_submit_errors_thieu_can_cu(self):
		items = [_item("r1", "DV-TEST-A", "K", 1, 302100, 295000), _item("r2", "DV-TEST-B", "K", 1, 92600)]
		errs = pr.submit_errors(items, pr.AUTHORITY, None)
		self.assertEqual(len(errs), 1)
		self.assertIn("DV-TEST-A", errs[0])
		self.assertIn("căn cứ", errs[0])
		items[0]["adjustment_basis"] = "   "
		self.assertEqual(len(pr.submit_errors(items, pr.AUTHORITY, None)), 1)
		items[0]["adjustment_basis"] = "Theo hội đồng"
		self.assertEqual(pr.submit_errors(items, pr.AUTHORITY, None), [])

	def test_FR_PRICE_002_submit_errors_khac(self):
		self.assertTrue(pr.submit_errors([], pr.AUTHORITY, None))
		bad = [_item("r1", "A", "K", 1, 100, 0, "x")]
		self.assertTrue(any("lớn hơn 0" in e for e in pr.submit_errors(bad, pr.AUTHORITY, None)))
		ok = [_item("r1", "A", "K", 1, 100)]
		self.assertTrue(any("ngày áp dụng" in e for e in pr.submit_errors(ok, pr.HOSPITAL, None)))
		self.assertEqual(pr.submit_errors(ok, pr.HOSPITAL, date(2027, 1, 1)), [])


class TestConfirm(unittest.TestCase):
	def test_FR_PRICE_004_departments(self):
		items = [_item("r1", "A", "K2", 1, 1), _item("r2", "B", "K1", 1, 1), _item("r3", "C", "K1", 1, 1), _item("r4", "D", None, 1, 1)]
		self.assertEqual(pr.departments(items), ["K1", "K2"])

	def test_FR_PRICE_004_005_confirm(self):
		conf = [{"department": "K1", "confirmed_by": None, "confirmed_on": None}, {"department": "K2", "confirmed_by": None, "confirmed_on": None}]
		now = datetime(2026, 11, 27, 10, 0)
		n, done = pr.confirm(conf, ["K1"], "a@x", now)
		self.assertEqual((n, done), (1, False))
		self.assertEqual(conf[0]["confirmed_by"], "a@x")
		self.assertEqual(conf[0]["confirmed_on"], now)
		with self.assertRaises(ValueError):
			pr.confirm(conf, ["K1"], "a@x", now)
		with self.assertRaises(ValueError):
			pr.confirm(conf, ["K9"], "a@x", now)
		n, done = pr.confirm(conf, ["K2"], "b@x", now)
		self.assertEqual((n, done), (1, True))

	def test_FR_PRICE_009_reset(self):
		items = [_item("r1", "A", "K", 1, 1, director_ack=1)]
		conf = [{"department": "K"}]
		self.assertEqual(pr.reset_for_draft(items, conf), [])
		self.assertEqual(items[0]["director_ack"], 0)


class TestApproval(unittest.TestCase):
	def test_FR_PRICE_006_007_approved_state(self):
		self.assertEqual(pr.approved_state(pr.HOSPITAL), pr.APPROVED)
		self.assertEqual(pr.approved_state(pr.AUTHORITY), pr.WAIT_AUTHORITY)
		with self.assertRaises(ValueError):
			pr.approved_state("khác")
		with self.assertRaises(ValueError):
			pr.approved_state(None)

	def test_transitions_hop_le(self):
		for frm, act, to, role in pr.TRANSITIONS:
			self.assertIn(frm, pr.STATES)
			self.assertIn(to, pr.STATES)
			self.assertNotEqual(role, "NC Auditor")
		self.assertIn(pr.APPROVED, pr.LOCKED_STATES)
		self.assertIn(pr.WAIT_DEPT, pr.PENDING_STATES)

	def test_FR_PRICE_008_authority_errors(self):
		items = [_item("r1", "A", "K", 1, 100), _item("r2", "B", "K", 1, 200)]
		self.assertEqual(pr.authority_errors(items, {"r1": 110, "r2": "210"}, "QD-1", date(2027, 1, 5)), [])
		errs = pr.authority_errors(items, {"r1": 0}, "", None)
		self.assertEqual(len(errs), 4)
		self.assertTrue(any("số văn bản" in e for e in errs))
		self.assertTrue(any("ngày văn bản" in e for e in errs))
		self.assertTrue(any("B" in e for e in errs))


class TestHistory(unittest.TestCase):
	def test_FR_PRICE_010_history_rows(self):
		items = [_item("r1", "DV-TEST-A", "K", 1, 302100, authority_price=D("310000"))]
		rows = pr.history_rows(items, "GIA-01", date(2027, 1, 1), "PAG-2026-001")
		self.assertEqual(rows[0]["price"], D("302100"))
		self.assertEqual(rows[0]["technical_service"], "DV-TEST-A")
		self.assertIsNone(rows[0]["authority_doc_no"])
		rows = pr.history_rows(items, "GIA-01", date(2027, 1, 1), "PAG-2026-001", "QD-9", True)
		self.assertEqual(rows[0]["price"], D("310000"))
		self.assertEqual(rows[0]["authority_doc_no"], "QD-9")

	def test_FR_PRICE_010_history_conflicts(self):
		existing = {"DV-TEST-A": [{"price_category": "GIA-01", "effective_date": date(2026, 1, 1), "price_proposal": "PAG-0"}]}
		new = [
			{"technical_service": "DV-TEST-A", "price_category": "GIA-01", "effective_date": "2026-01-01"},
			{"technical_service": "DV-TEST-A", "price_category": "GIA-01", "effective_date": date(2027, 1, 1)},
			{"technical_service": "DV-TEST-B", "price_category": "GIA-01", "effective_date": date(2026, 1, 1)},
		]
		c = pr.history_conflicts(existing, new)
		self.assertEqual(len(c), 1)
		self.assertEqual(c[0]["price_proposal"], "PAG-0")
		self.assertEqual(c[0]["technical_service"], "DV-TEST-A")


if __name__ == "__main__":
	unittest.main()
