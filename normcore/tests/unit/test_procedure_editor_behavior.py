"""NORM-27: hành vi chạy được của ProcedureEditor khi frappe.call trả về jQuery Deferred (không có .finally).

Chạy khối <script> thật trong Node (tests/unit/js/procedure_editor_harness.js), không đọc chuỗi mã nguồn.
Mã kịch bản theo bảng nghiệm thu NORM-16: E1, E4, E12, K3.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VUE = ROOT / "public" / "js" / "procedure_editor" / "ProcedureEditor.vue"
HARNESS = Path(__file__).resolve().parent / "js" / "procedure_editor_harness.js"


def run_scenario(name):
	node = shutil.which("node")
	if not node:
		raise AssertionError("Cần Node để chạy test hành vi của trình soạn quy trình")
	out = subprocess.run([node, str(HARNESS), str(VUE), name], capture_output=True, text=True, timeout=60)
	if out.returncode != 0:
		raise AssertionError(out.stderr)
	result = json.loads(out.stdout.strip().splitlines()[-1])
	if "crash" in result:
		raise AssertionError(result)
	return result


class TestProcedureEditorDeferred(unittest.TestCase):
	def test_E4_busy_ve_false_sau_khi_thanh_cong(self):
		r = run_scenario("step_ok")
		self.assertFalse(r["busy"])
		self.assertFalse(r["loading"])
		self.assertEqual(r["consoleErrors"], [])

	def test_E4_busy_ve_false_sau_khi_loi(self):
		r = run_scenario("step_error")
		self.assertFalse(r["busy"])
		self.assertEqual(r["consoleErrors"], [])
		self.assertEqual(r["error"], "Lỗi máy chủ")

	def test_E1_tao_thanh_cong_khong_hien_dai_loi(self):
		r = run_scenario("create_ok")
		self.assertEqual(r["error"], "")
		self.assertEqual(r["existing"], "")
		self.assertNotIn("find_existing", r["calls"])
		self.assertFalse(r["busy"])
		self.assertFalse(r["loading"])
		self.assertEqual(r["consoleErrors"], [])

	def test_E12_sao_chep_thanh_cong_khong_hien_dai_loi(self):
		r = run_scenario("copy_ok")
		self.assertEqual(r["error"], "")
		self.assertEqual(r["existing"], "")
		self.assertNotIn("find_existing", r["calls"])
		self.assertFalse(r["loading"])
		self.assertEqual(r["consoleErrors"], [])

	def test_K3_xuong_giua_tieu_diem_o_lai_nut(self):
		r = run_scenario("move_S1_down")
		self.assertEqual(r["order"], ["S2", "S1", "S3"])
		self.assertEqual(r["focused"], "S1:down")
		self.assertFalse(r["busy"])
		self.assertEqual(r["consoleErrors"], [])

	def test_K3_len_giua_tieu_diem_o_lai_nut(self):
		r = run_scenario("move_S3_up")
		self.assertEqual(r["order"], ["S1", "S3", "S2"])
		self.assertEqual(r["focused"], "S3:up")
		self.assertEqual(r["consoleErrors"], [])

	def test_K3_bien_xuong_cuoi_chuyen_sang_nut_con_lai(self):
		r = run_scenario("move_S2_down")  # S2 xuống cuối: nút Xuống bị khóa → tiêu điểm sang Lên
		self.assertEqual(r["order"], ["S1", "S3", "S2"])
		self.assertEqual(r["focused"], "S2:up")
		self.assertEqual(r["consoleErrors"], [])

	def test_K3_bien_len_dau_chuyen_sang_nut_con_lai(self):
		r = run_scenario("move_S2_up")  # S2 lên đầu: nút Lên bị khóa → tiêu điểm sang Xuống
		self.assertEqual(r["order"], ["S2", "S1", "S3"])
		self.assertEqual(r["focused"], "S2:down")
		self.assertEqual(r["consoleErrors"], [])
