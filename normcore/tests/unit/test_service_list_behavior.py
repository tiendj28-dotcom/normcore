"""NORM-75: đổi khoa bằng cách gõ tay + Tab phải tính lại bộ lọc mã dịch vụ như khi chọn từ gợi ý."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "nc_procedure" / "doctype" / "nc_technical_service" / "nc_technical_service_list.js"
HARNESS = Path(__file__).resolve().parent / "js" / "service_list_harness.js"


def run_scenario(name):
	node = shutil.which("node")
	if not node:
		raise AssertionError("Cần Node để chạy test hành vi danh sách NC Technical Service")
	out = subprocess.run([node, str(HARNESS), str(JS), name], capture_output=True, text=True, timeout=60)
	if out.returncode != 0:
		raise AssertionError(out.stderr)
	result = json.loads(out.stdout.strip().splitlines()[-1])
	if "crash" in result:
		raise AssertionError(result)
	return result


class TestServiceListDepartmentTyped(unittest.TestCase):
	def test_go_tay_roi_tab_tinh_lai_bo_loc_ma(self):
		r = run_scenario("typed_tab")
		self.assertEqual(r["after_pick"], ["A", "B"])
		self.assertEqual(r["after_typed"], ["X", "Y", "Z"])

	def test_khong_tinh_hai_lan_khi_chon_tu_goi_y(self):
		r = run_scenario("typed_tab")
		# lần 1: đặt mức A (khoa trống); lần 2: chọn K01; lần 3: gõ THU-K02
		self.assertEqual(r["calls"], 3)
