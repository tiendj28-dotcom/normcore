"""NORM-31 S1: trang import-excel chọn sẵn bộ nhập theo frappe.route_options.import_set (ASM-131).

Chạy import_excel.js thật trong Node (tests/unit/js/import_excel_harness.js). Mã kịch bản N31-01…06.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "nc_core" / "page" / "import_excel" / "import_excel.js"
HARNESS = Path(__file__).resolve().parent / "js" / "import_excel_harness.js"
NO_PERM = "You do not have permission to import data."


def run_scenario(name):
	node = shutil.which("node")
	if not node:
		raise AssertionError("Cần Node để chạy test hành vi của trang import-excel")
	out = subprocess.run([node, str(HARNESS), str(JS), name], capture_output=True, text=True, timeout=60)
	if out.returncode != 0:
		raise AssertionError(out.stderr)
	result = json.loads(out.stdout.strip().splitlines()[-1])
	if "crash" in result:
		raise AssertionError(result)
	return result


class TestImportExcelRouteOptions(unittest.TestCase):
	def test_N31_01_chon_san_bo_nhap_theo_import_set(self):
		r = run_scenario("route_ok")
		self.assertEqual(r["value"], "nc_service_volume")
		self.assertEqual(r["consoleErrors"], [])

	def test_N31_01_chon_san_khi_danh_sach_da_tai_xong(self):
		r = run_scenario("route_before_load")
		self.assertEqual(r["value"], "nc_cost_center_driver")
		self.assertEqual(r["consoleErrors"], [])

	def test_N31_02_khoa_sai_giu_hanh_vi_cu_khong_bao_loi(self):
		r = run_scenario("route_bad")
		self.assertEqual(r["value"], "nc_account_mapping")
		self.assertEqual(r["msgprint_calls"], [])
		self.assertEqual(r["consoleErrors"], [])

	def test_N31_03_khong_co_tham_so_chon_bo_dau(self):
		r = run_scenario("no_route")
		self.assertEqual(r["value"], "nc_account_mapping")
		self.assertEqual(r["consoleErrors"], [])

	def test_N31_04_mo_lai_voi_bo_khac_doi_bo_va_xoa_tep(self):
		r = run_scenario("reopen_other")
		self.assertEqual(r["value"], "nc_service_volume")
		self.assertIsNone(r["file_url"])
		self.assertTrue(r["btn_check_disabled"])
		self.assertEqual(r["consoleErrors"], [])

	def test_N31_05_tieu_thu_tham_so_va_khong_ghi_de_lua_chon_tay(self):
		r = run_scenario("consumed")
		self.assertIsNone(r["route_options"])
		self.assertEqual(r["value"], "nc_cost_center_driver")
		self.assertEqual(r["consoleErrors"], [])

	def test_N31_06_danh_sach_rong_van_bao_khong_co_quyen(self):
		r = run_scenario("empty_sets")
		self.assertEqual(r["message"], NO_PERM)
		self.assertIsNone(r.get("value"))
		self.assertEqual(r["consoleErrors"], [])
