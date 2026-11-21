"""Logic thuần của quy trình: cấp mã, sắp lại, sao chép (FR-PROC-003, 006, 013; ADR-002). Không cần site."""

import unittest

from normcore.procedure.codes import next_code
from normcore.procedure.copying import copy_structure
from normcore.procedure.steps import add_step, move, remove_step, reorder


def _data(title):
	return {"phase": "Thực hiện", "step_title": title, "description": f"Mô tả {title}"}


class TestProcedureLogic(unittest.TestCase):
	def test_TC_PROC_03_ma_buoc_bat_bien_khi_sap_lai_va_xoa(self):
		steps, counter = [], 0
		for t in ("A", "B", "C"):
			steps, counter = add_step(steps, counter, _data(t))
		self.assertEqual([s["step_id"] for s in steps], ["S001", "S002", "S003"])

		# đổi thứ tự bước 1 và 3: mã không đổi, thứ tự đổi
		steps = reorder(steps, ["S003", "S002", "S001"])
		self.assertEqual([s["step_title"] for s in steps], ["C", "B", "A"])
		self.assertEqual(
			{s["step_title"]: s["step_id"] for s in steps}, {"A": "S001", "B": "S002", "C": "S003"}
		)

		# xóa S002, thêm bước mới: nhận S004, không tái dùng S002
		steps = remove_step(steps, "S002")
		steps, counter = add_step(steps, counter, _data("D"))
		self.assertEqual([s["step_id"] for s in steps], ["S003", "S001", "S004"])
		self.assertNotIn("S002", [s["step_id"] for s in steps])

	def test_TC_PROC_03_bo_dem_khong_tai_dung_khi_xoa_buoc_cuoi(self):
		steps, counter = add_step([], 0, _data("A"))
		steps = remove_step(steps, "S001")
		steps, counter = add_step(steps, counter, _data("B"))
		self.assertEqual(steps[0]["step_id"], "S002")

	def test_reorder_chi_nhan_hoan_vi_day_du(self):
		ids = ["S001", "S002", "S003"]
		for bad in (["S001", "S002"], ["S001", "S002", "S002"], ["S001", "S002", "S009"]):
			with self.assertRaises(ValueError):
				reorder([{"step_id": i} for i in ids], bad)

	def test_move_len_xuong_va_chan_bien(self):
		steps = [{"step_id": f"S00{i}"} for i in (1, 2, 3)]
		self.assertEqual([s["step_id"] for s in move(steps, "S003", -1)], ["S001", "S003", "S002"])
		self.assertEqual([s["step_id"] for s in move(steps, "S001", -1)], ["S001", "S002", "S003"])
		self.assertEqual([s["step_id"] for s in move(steps, "S003", 1)], ["S001", "S002", "S003"])
		with self.assertRaises(ValueError):
			move(steps, "S999", 1)

	def test_next_code(self):
		self.assertEqual(next_code("S", 0, []), (1, "S001"))
		self.assertEqual(next_code("R", 3, ["R001"]), (4, "R004"))
		self.assertEqual(next_code("S", 1, ["S007"]), (8, "S008"))

	def test_FR_PROC_013_sao_chep_cap_ma_moi_va_anh_xa(self):
		steps = [
			{"step_id": "S003", "step_title": "C"},
			{"step_id": "S001", "step_title": "A"},
		]
		resources = [{"resource_row_id": "R005", "step_id": "S001", "resource_text": "x"}]
		citations = [{"target_step_id": "S003", "target_section": None, "relation": "Khác biệt"}]
		out = copy_structure(steps, resources, citations)
		self.assertEqual([s["step_id"] for s in out["steps"]], ["S001", "S002"])
		self.assertEqual([s["step_title"] for s in out["steps"]], ["C", "A"])  # giữ thứ tự hiển thị
		self.assertEqual(out["resources"][0]["step_id"], "S002")  # S001 cũ (A) thành S002
		self.assertEqual(out["resources"][0]["resource_row_id"], "R001")
		self.assertEqual(out["citations"][0]["target_step_id"], "S001")
		self.assertEqual(out["next_step_seq"], 2)
		self.assertEqual(out["next_resource_seq"], 1)
		self.assertEqual(steps[0]["step_id"], "S003")  # đầu vào không bị sửa
