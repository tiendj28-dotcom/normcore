from datetime import date

import pytest

from normcore.norm import time_study as ts


def _case(d, minutes, step="S002", job="BS"):
	return {
		"observed_on": d,
		"lines": [{"step_id": step, "job_title": job, "headcount": 1, "labor_minutes": minutes}],
	}


def test_TC_TS_01_trung_vi_5_ca_va_6_ca():
	cases = [_case(date(2026, 11, i + 1), m) for i, m in enumerate([18, 22, 20, 25, 19])]
	r = ts.summarize(cases, 5, {"S002": 2})
	assert r["rows"][0]["median_minutes"] == 20 and r["rows"][0]["n"] == 5
	assert r["sufficient"] and r["n_cases"] == 5
	r6 = ts.summarize([*cases, _case(date(2026, 11, 6), 21)], 5, {"S002": 2})
	assert r6["rows"][0]["median_minutes"] == 20.5 and r6["n_cases"] == 6


def test_thieu_ca_va_ngay():
	r = ts.summarize([_case(date(2026, 11, 3), 10), _case(date(2026, 11, 1), 12)], 5, {})
	assert (
		not r["sufficient"] and r["first_date"] == date(2026, 11, 1) and r["last_date"] == date(2026, 11, 3)
	)
	empty = ts.summarize([], 5, {})
	assert empty["first_date"] is None and empty["rows"] == []


def test_ca_0_phut_bi_bo():
	cases = [_case(None, 0), _case(None, 10), _case(None, 20)]
	assert ts.summarize(cases, 1, {})["rows"][0]["median_minutes"] == 15
	assert ts.summarize([_case(None, 0)], 1, {})["rows"] == []


def test_sap_xep_hang():
	case = {
		"lines": [
			{"step_id": "S2", "equipment": "EQ1", "machine_minutes": 5},
			{"step_id": "S2", "job_title": "DD", "labor_minutes": 5},
			{"step_id": "S1", "job_title": "BS", "labor_minutes": 5},
		]
	}
	rows = ts.summarize([case], 1, {"S1": 1, "S2": 2})["rows"]
	assert [(r["step_id"], r["kind"]) for r in rows] == [
		("S1", "labor"),
		("S2", "labor"),
		("S2", "equipment"),
	]


def test_lines_from_procedure():
	steps = [{"step_id": f"S00{i}", "idx": i} for i in (3, 1, 2, 4)]
	res = [
		{"step_id": "S001", "resource_type": "Nhân lực", "linked_name": "BS", "headcount": 2},
		{"step_id": "S001", "resource_type": "Thiết bị", "linked_name": "EQ1"},
		{"step_id": "S002", "resource_type": "Nhân lực", "linked_name": "DD", "headcount": None},
		{"step_id": "S002", "resource_type": "Vật tư", "linked_name": "X"},
	]
	out = ts.lines_from_procedure(steps, res)
	assert [o["step_id"] for o in out] == ["S001", "S001", "S002", "S003", "S004"]
	assert out[0] == {"step_id": "S001", "job_title": "BS", "headcount": 2}
	assert out[1] == {"step_id": "S001", "equipment": "EQ1"}
	assert out[2]["headcount"] == 1


@pytest.mark.parametrize(
	"line,frag",
	[
		({"step_id": "SX"}, "không có trong quy trình"),
		({"step_id": "S1", "job_title": "BS", "equipment": "EQ"}, "không có cả hai"),
		({"step_id": "S1", "labor_minutes": -1}, "không được âm"),
		({"step_id": "S1", "labor_minutes": 5, "headcount": 1}, "chưa chọn chức danh"),
		({"step_id": "S1", "machine_minutes": 5}, "chưa chọn thiết bị"),
		({"step_id": "S1", "job_title": "BS", "labor_minutes": 5, "headcount": 0}, "số người"),
	],
)
def test_line_errors_nhanh(line, frag):
	errs = ts.line_errors([line], {"S1"})
	assert any(frag in e for e in errs)


def test_line_errors_trung_va_hop_le():
	ok = [
		{"step_id": "S1", "job_title": "BS", "headcount": 1, "labor_minutes": 5},
		{"step_id": "S1", "equipment": "EQ1", "machine_minutes": 5},
		{"step_id": "S1"},
		{"step_id": "S1"},
	]
	assert ts.line_errors(ok, {"S1"}) == []
	dup = ok[:1] + ok[:1] + ok[1:2] + ok[1:2]
	assert len([e for e in ts.line_errors(dup, {"S1"}) if "trùng" in e]) == 2


def test_basis_ref():
	assert ts.basis_ref(6, date(2026, 11, 1), date(2026, 11, 20)) == "6 ca bấm giờ, 01/11/2026–20/11/2026"  # noqa: RUF001
	assert ts.basis_ref(6, "2026-11-01", "2026-11-20").endswith("20/11/2026")
	assert ts.basis_ref(3, None, None) == "3 ca bấm giờ"


def test_plan_apply():
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
	assert [(u["line_id"], u["hospital_qty"]) for u in ups] == [("L1", 20), ("L2", 18)]
	assert all(u["basis"] == "Bấm giờ" and u["basis_ref"] == "ref" for u in ups)
	assert un == [{"step_id": "S009", "kind": "labor", "resource": "BS"}]
