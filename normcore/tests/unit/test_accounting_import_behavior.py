"""NORM-31 S3: nút "Sửa loại chi phí của dòng" (ASM-132). Chạy nc_accounting_import.js thật trong Node.

Mã kịch bản N31-09…11.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "nc_costing" / "doctype" / "nc_accounting_import" / "nc_accounting_import.js"
HARNESS = Path(__file__).resolve().parent / "js" / "accounting_import_harness.js"


def run_scenario(name):
	node = shutil.which("node")
	if not node:
		raise AssertionError("Cần Node để chạy test hành vi của form NC Accounting Import")
	out = subprocess.run([node, str(HARNESS), str(JS), name], capture_output=True, text=True, timeout=60)
	if out.returncode != 0:
		raise AssertionError(out.stderr)
	result = json.loads(out.stdout.strip().splitlines()[-1])
	if "crash" in result:
		raise AssertionError(result)
	return result


class TestEditLineButton(unittest.TestCase):
	def test_N31_09_khong_tich_dong_khong_mo_hop_thoai(self):
		r = run_scenario("none")
		self.assertEqual(r["dialogs"], [])
		self.assertEqual(r["msgprint_calls"], ["Select one line in the Lines table first."])
		self.assertEqual(r["consoleErrors"], [])

	def test_N31_10_mot_dong_tieu_de_co_so_dong_va_ma_tai_khoan(self):
		r = run_scenario("one")
		self.assertEqual(len(r["dialogs"]), 1)
		d = r["dialogs"][0]
		self.assertEqual(d["title"], "Edit cost category: line 3, account 6421")
		cat = next(f for f in d["fields"] if f.get("fieldname") == "cost_category")
		self.assertEqual(cat["default"], "MANAGEMENT")
		self.assertEqual(r["msgprint_calls"], [])
		self.assertEqual(r["consoleErrors"], [])

	def test_N31_10_ma_tai_khoan_duoc_thoat_html(self):
		r = run_scenario("html")
		title = r["dialogs"][0]["title"]
		self.assertNotIn("<b>", title)
		self.assertIn("&lt;b&gt;6421", title)

	def test_N31_11_tich_hai_dong_khong_mo_hop_thoai(self):
		r = run_scenario("many")
		self.assertEqual(r["dialogs"], [])
		self.assertEqual(r["msgprint_calls"], ["Select only one line to edit."])
		self.assertEqual(r["consoleErrors"], [])
