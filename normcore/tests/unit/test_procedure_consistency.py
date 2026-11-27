import unittest

from normcore.procedure import consistency as c


def S(i, phase, idx=None):
	return {"step_id": f"B{i:02d}", "phase": phase, "step_title": f"Bước {i}", "idx": idx or i}


def R(rid, step, text, rtype="Vật tư", link=None):
	return {
		"resource_row_id": rid,
		"step_id": step,
		"resource_type": rtype,
		"resource_text": text,
		"linked_doctype": link[0] if link else None,
		"linked_name": link[1] if link else None,
	}


def LABOR(rid, step):
	return R(rid, step, "Bác sĩ", "Nhân lực")


class TestConsistency(unittest.TestCase):
	def test_FR_AI_006_nguon_luc_thieu_o_chuan_bi(self):
		steps = [S(1, "Chuẩn bị"), S(2, "Thực hiện")]
		res = [
			R("R1", "B01", "Găng tay"),
			R("R2", "B01", "Bơm tiêm 5ml"),
			R("R3", "B02", "  găng   tay "),
			R("R4", "B02", "Lidocain 2%", "Thuốc"),
		]
		out = c.preparation_gaps(steps, res)
		self.assertEqual(
			[(i["kind"], i["label"], i["step_ids"]) for i in out],
			[
				("unused_in_steps", "Bơm tiêm 5ml", ["B01"]),
				("missing_in_preparation", "Lidocain 2%", ["B02"]),
			],
		)
		# cùng khóa liên kết dù text khác -> một
		res = [R("R1", "B01", "A", link=("NC Item", "X")), R("R2", "B02", "B", link=("NC Item", "X"))]
		self.assertEqual(c.preparation_gaps(steps, res), [])
		# Nhân lực không vào kiểm (1); message có
		res = [LABOR("R1", "B02")]
		self.assertEqual(c.preparation_gaps(steps, res), [])
		msgs = [
			i["message"]
			for i in c.rule_issues(steps, [R("R4", "B02", "Lidocain", "Thuốc"), LABOR("R9", "B02")])
		]
		self.assertTrue(any("Lidocain" in m and "chuẩn bị" in m for m in msgs))
		self.assertTrue(any("chưa có người thực hiện" in m and "B01" in m for m in msgs))
		unused = c.rule_issues(steps, [R("R1", "B01", "Kim")])
		self.assertTrue(any("không dùng ở bước nào" in i["message"] for i in unused))

	def test_FR_AI_006_khong_co_buoc_chuan_bi(self):
		out = c.preparation_gaps([S(1, "Thực hiện")], [R("R1", "B01", "Kim")])
		self.assertEqual(out, [{"kind": "no_preparation_step"}])
		self.assertIn(
			"chưa có bước nào", c.rule_issues([S(1, "Thực hiện")], [LABOR("R", "B01")])[0]["message"]
		)

	def test_FR_AI_006_buoc_thieu_nguoi_thuc_hien(self):
		steps = [S(2, "Thực hiện"), S(1, "Chuẩn bị")]
		out = c.steps_without_performer(steps, [LABOR("R1", "B01"), R("R2", "B02", "Kim")])
		self.assertEqual(out, [{"kind": "no_performer", "step_ids": ["B02"], "label": "Bước 2"}])

	def test_FR_AI_006_loc_de_xuat_chong_chi_dinh(self):
		contra = "Không dùng cho người dị ứng lidocain. Phụ nữ có thai."
		good = {"step_id": "B02", "excerpt": "dị ứng lidocain", "explanation": " Có dùng lidocain "}
		data = {
			"issues": [
				good,
				{"step_id": "B02", "excerpt": "không có trong nguồn", "explanation": "x"},
				{"step_id": "B99", "excerpt": "dị ứng lidocain", "explanation": "x"},
				{"step_id": "B02", "section": "cautions", "excerpt": "dị ứng lidocain", "explanation": "x"},
				{"step_id": "B02", "excerpt": "dị ứng lidocain", "explanation": " "},
				{"resource_row_id": "R4", "excerpt": "Phụ nữ có thai", "explanation": "y" * 600},
				{"section": "overview", "excerpt": "Phụ nữ có thai", "explanation": "z"},
				{"section": "contraindications", "excerpt": "Phụ nữ có thai", "explanation": "z"},
				"rác",
			]
		}
		out, rej = c.parse_contra(data, ["B01", "B02"], ["R4"], contra)
		self.assertEqual(len(out), 3)
		self.assertEqual(rej, 6)
		self.assertEqual(out[0]["explanation"], "Có dùng lidocain")
		self.assertEqual(len(out[1]["explanation"]), 500)
		self.assertEqual(c.parse_contra({"mock": True}, [], [], contra), ([], 0))
		self.assertEqual(c.parse_contra({"issues": 3}, [], [], contra), ([], 0))
		v = c.contra_variables({"contraindications": "a", "overview": "o", "steps": [1]})
		self.assertEqual(v["contraindications"], "a")
		self.assertEqual(v["sections"]["overview"], "o")
