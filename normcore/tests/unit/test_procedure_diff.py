"""So sánh phiên bản và bước thêm, bỏ, đổi (FR-WF-010, FR-WF-011). Thuần Python."""

import unittest

from normcore.procedure import diff as d

SECTIONS = [("overview", "Đại cương"), ("indications", "Chỉ định"), ("steps", "Các bước")]


def _step(i, title=None, minutes=5):
	return {"step_id": i, "phase": "P", "step_title": title or f"bước {i}", "description": "", "reference_minutes": minutes}


def _res(rid, step, text="vật tư", qty=1):
	return {"resource_row_id": rid, "step_id": step, "resource_type": "Vật tư", "resource_text": text, "quantity": qty}


def _v1():
	return {
		"overview": "a",
		"indications": "b",
		"steps": [_step("S001"), _step("S002"), _step("S003"), _step("S004")],
		"resources": [_res("R001", "S001"), _res("R002", "S002"), _res("R003", "S003", qty=1)],
	}


def _v2():
	return {
		"overview": "a",
		"indications": "b sửa",
		"steps": [_step("S001"), _step("S003"), _step("S004"), _step("S005")],
		"resources": [_res("R001", "S001"), _res("R003", "S003", qty=2)],
	}


class TestDiff(unittest.TestCase):
	def test_TC_WF_06_step_changes_them_bo_doi(self):
		ch = d.step_changes(_v1(), _v2())
		self.assertEqual(ch, {"added": ["S005"], "removed": ["S002"], "changed": ["S003"]})
		self.assertEqual(d.format_step_note(ch), "thêm S005; bỏ S002; đổi S003")

	def test_TC_WF_07_diff_theo_phan_buoc_nguon_luc(self):
		r = d.diff_procedures(_v1(), _v2(), SECTIONS)
		self.assertEqual({s["key"]: s["status"] for s in r["sections"]}, {"overview": "same", "indications": "changed"})
		st = {s["step_id"]: s["status"] for s in r["steps"]}
		self.assertEqual(st, {"S001": "same", "S002": "removed", "S003": "same", "S004": "same", "S005": "added"})
		rs = {x["resource_row_id"]: x for x in r["resources"]}
		self.assertEqual(rs["R003"]["status"], "changed")
		self.assertEqual(rs["R003"]["fields"], ["quantity"])
		self.assertEqual(rs["R002"]["status"], "removed")
		self.assertEqual(r["summary"]["steps"], {"added": 1, "removed": 1, "changed": 0})
		self.assertEqual(r["summary"]["resources"], {"added": 0, "removed": 1, "changed": 1})
		self.assertEqual(r["summary"]["sections"], {"added": 0, "removed": 0, "changed": 1})

	def test_thu_tu_bo_chen_sau_buoc_truoc(self):
		order = [s["step_id"] for s in d.diff_steps(_v1()["steps"], _v2()["steps"])]
		self.assertEqual(order, ["S001", "S002", "S003", "S004", "S005"])

	def test_nguon_luc_chuyen_buoc(self):
		a, b = _v1(), _v1()
		b["resources"][2]["step_id"] = "S004"
		self.assertEqual(d.step_changes(a, b), {"added": [], "removed": [], "changed": ["S003", "S004"]})

	def test_nguon_luc_cua_buoc_bi_bo_khong_lam_doi(self):
		a, b = _v1(), _v1()
		b["steps"] = [s for s in b["steps"] if s["step_id"] != "S002"]
		b["resources"] = [r for r in b["resources"] if r["step_id"] != "S002"]
		self.assertEqual(d.step_changes(a, b), {"added": [], "removed": ["S002"], "changed": []})

	def test_chi_doi_thu_tu(self):
		a, b = _v1(), _v1()
		b["steps"][0], b["steps"][1] = b["steps"][1], b["steps"][0]
		items = d.diff_steps(a["steps"], b["steps"])
		self.assertTrue(all(i["status"] == "same" for i in items))
		self.assertTrue(any(i.get("moved") for i in items))
		self.assertEqual(d.step_changes(a, b), {"added": [], "removed": [], "changed": []})

	def test_hai_ban_giong_nhau(self):
		r = d.diff_procedures(_v1(), _v1(), SECTIONS)
		self.assertTrue(all(i["status"] == "same" for k in ("sections", "steps", "resources") for i in r[k]))
		self.assertEqual(d.format_step_note(d.step_changes(_v1(), _v1())), "Không có bước thêm, bỏ, đổi")

	def test_chuan_hoa_rong_va_so(self):
		a = {"overview": None, "steps": [_step("S001", minutes=5)], "resources": []}
		b = {"overview": "  ", "steps": [_step("S001", minutes=5.0)], "resources": []}
		r = d.diff_procedures(a, b, SECTIONS)
		self.assertEqual(r["sections"][0]["status"], "same")
		self.assertEqual(r["steps"][0]["status"], "same")

	def test_phan_them_va_bo(self):
		a = {"overview": "", "indications": "x", "steps": [], "resources": []}
		b = {"overview": "y", "indications": "", "steps": [], "resources": []}
		st = {s["key"]: s["status"] for s in d.diff_sections(a, b, SECTIONS)}
		self.assertEqual(st, {"overview": "added", "indications": "removed"})

	def test_buoc_doi_truong_va_buoc_dau_bi_bo(self):
		a = {"steps": [_step("S001"), _step("S002")], "resources": []}
		b = {"steps": [_step("S002", title="mới")], "resources": []}
		items = d.diff_steps(a["steps"], b["steps"])
		self.assertEqual([(i["step_id"], i["status"]) for i in items], [("S001", "removed"), ("S002", "changed")])
		self.assertEqual(items[1]["fields"], ["step_title"])

	def test_ghi_chu_nhieu_ma(self):
		note = d.format_step_note({"added": ["S005", "S006"], "removed": [], "changed": ["S003"]})
		self.assertEqual(note, "thêm S005, S006; đổi S003")
