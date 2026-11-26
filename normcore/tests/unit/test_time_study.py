"""Unit test thuần khảo sát bấm giờ: FR-TS-001..005, TC-TS-01 (unittest, chạy được cả bench và pytest)."""

import unittest
from datetime import date

from normcore.norm import time_study as ts


def _case(d, minutes, step="S002", job="BS"):
	return {
		"observed_on": d,
		"lines": [{"step_id": step, "job_title": job, "headcount": 1, "labor_minutes": minutes}],
	}


class TestTimeStudy(unittest.TestCase):
	def test_TC_TS_01_trung_vi_5_ca_va_6_ca(self):
		cases = [_case(date(2026, 11, i + 1), m) for i, m in enumerate([18, 22, 20, 25, 19])]
		r = ts.summarize(cases, 5, {"S002": 2})
		self.assertEqual(r["rows"][0]["median_minutes"], 20)
		self.assertEqual(r["rows"][0]["n"], 5)
		self.assertTrue(r["sufficient"])
		self.assertEqual(r["n_cases"], 5)
		r6 = ts.summarize([*cases, _case(date(2026, 11, 6), 21)], 5, {"S002": 2})
		self.assertEqual(r6["rows"][0]["median_minutes"], 20.5)
		self.assertEqual(r6["n_cases"], 6)

	def test_thieu_ca_va_ngay(self):
		r = ts.summarize([_case(date(2026, 11, 3), 10), _case(date(2026, 11, 1), 12)], 5, {})
		self.assertFalse(r["sufficient"])
		self.assertEqual(r["first_date"], date(2026, 11, 1))
		self.assertEqual(r["last_date"], date(2026, 11, 3))
		empty = ts.summarize([], 5, {})
		self.assertIsNone(empty["first_date"])
		self.assertEqual(empty["rows"], [])

	def test_ca_0_phut_bi_bo(self):
		cases = [_case(None, 0), _case(None, 10), _case(None, 20)]
		self.assertEqual(ts.summarize(cases, 1, {})["rows"][0]["median_minutes"], 15)
		self.assertEqual(ts.summarize([_case(None, 0)], 1, {})["rows"], [])

	def test_sap_xep_hang(self):
		case = {
			"lines": [
				{"step_id": "S2", "equipment": "EQ1", "machine_minutes": 5},
				{"step_id": "S2", "job_title": "DD", "labor_minutes": 5},
				{"step_id": "S1", "job_title": "BS", "labor_minutes": 5},
			]
		}
		rows = ts.summarize([case], 1, {"S1": 1, "S2": 2})["rows"]
		self.assertEqual(
			[(r["step_id"], r["kind"]) for r in rows], [("S1", "labor"), ("S2", "labor"), ("S2", "equipment")]
		)

	def test_lines_from_procedure(self):
		steps = [{"step_id": f"S00{i}", "idx": i} for i in (3, 1, 2, 4)]
		res = [
			{"step_id": "S001", "resource_type": "Nhân lực", "linked_name": "BS", "headcount": 2},
			{"step_id": "S001", "resource_type": "Thiết bị", "linked_name": "EQ1"},
			{"step_id": "S002", "resource_type": "Nhân lực", "linked_name": "DD", "headcount": None},
			{"step_id": "S002", "resource_type": "Vật tư", "linked_name": "X"},
		]
		out = ts.lines_from_procedure(steps, res)
		self.assertEqual([o["step_id"] for o in out], ["S001", "S001", "S002", "S003", "S004"])
		self.assertEqual(out[0], {"step_id": "S001", "job_title": "BS", "headcount": 2})
		self.assertEqual(out[1], {"step_id": "S001", "equipment": "EQ1"})
		self.assertEqual(out[2]["headcount"], 1)

	def test_line_errors_nhanh(self):
		cases = [
			({"step_id": "SX"}, "không có trong quy trình"),
			({"step_id": "S1", "job_title": "BS", "equipment": "EQ"}, "không có cả hai"),
			({"step_id": "S1", "labor_minutes": -1}, "không được âm"),
			({"step_id": "S1", "labor_minutes": 5, "headcount": 1}, "chưa chọn chức danh"),
			({"step_id": "S1", "machine_minutes": 5}, "chưa chọn thiết bị"),
			({"step_id": "S1", "job_title": "BS", "labor_minutes": 5, "headcount": 0}, "số người"),
		]
		for line, frag in cases:
			with self.subTest(frag=frag):
				errs = ts.line_errors([line], {"S1"})
				self.assertTrue(any(frag in e for e in errs), errs)

	def test_line_errors_trung_va_hop_le(self):
		ok = [
			{"step_id": "S1", "job_title": "BS", "headcount": 1, "labor_minutes": 5},
			{"step_id": "S1", "equipment": "EQ1", "machine_minutes": 5},
			{"step_id": "S1"},
			{"step_id": "S1"},
		]
		self.assertEqual(ts.line_errors(ok, {"S1"}), [])
		dup = ok[:1] + ok[:1] + ok[1:2] + ok[1:2]
		self.assertEqual(len([e for e in ts.line_errors(dup, {"S1"}) if "trùng" in e]), 2)

	def test_basis_ref(self):
		self.assertEqual(
			ts.basis_ref(6, date(2026, 11, 1), date(2026, 11, 20)),
			"6 ca bấm giờ, 01/11/2026–20/11/2026",  # noqa: RUF001
		)
		self.assertTrue(ts.basis_ref(6, "2026-11-01", "2026-11-20").endswith("20/11/2026"))
		self.assertEqual(ts.basis_ref(3, None, None), "3 ca bấm giờ")

	def test_plan_apply(self):
		nl = [
			{"line_id": "L1", "step_id": "S002", "resource_doctype": "NC Job Title", "resource": "BS"},
			{"line_id": "L2", "step_id": "S002", "resource_doctype": "NC Equipment", "resource": "EQ1"},
			{"line_id": "L3", "step_id": "S002", "resource_doctype": "NC Job Title", "resource": "DD"},
			{
				"line_id": "L4",
				"step_id": "S002",
				"resource_doctype": "NC Job Title",
				"resource": "BS",
				"service_level": 1,
			},
		]
		rows = [
			{"step_id": "S002", "kind": "labor", "resource": "BS", "median_minutes": 20, "n": 5},
			{"step_id": "S002", "kind": "equipment", "resource": "EQ1", "median_minutes": 18, "n": 5},
			{"step_id": "S009", "kind": "labor", "resource": "BS", "median_minutes": 3, "n": 5},
		]
		ups, un = ts.plan_apply(nl, rows, "ref")
		self.assertEqual([(u["line_id"], u["hospital_qty"]) for u in ups], [("L1", 20), ("L2", 18)])
		self.assertTrue(all(u["basis"] == "Bấm giờ" and u["basis_ref"] == "ref" for u in ups))
		self.assertEqual(un, [{"step_id": "S009", "kind": "labor", "resource": "BS"}])
