"""FEAT-026: giao diện giá tham chiếu (ui-design.md): kiểm tĩnh mã nguồn JS, bản dịch, lối tắt Workspace."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DT = ROOT / "nc_benchmark" / "doctype"


def read(name, ext):
	return (DT / name / f"{name}.{ext}").read_text(encoding="utf-8")


PRICE_LIST = (DT / "nc_benchmark_price" / "nc_benchmark_price_list.js").read_text(encoding="utf-8")
PRICE_FORM = read("nc_benchmark_price", "js")
FACILITY = read("nc_benchmark_facility", "js")
CPI_LIST = (DT / "nc_cpi_index" / "nc_cpi_index_list.js").read_text(encoding="utf-8")
FRAGMENT = {
	r[0]: r[1]
	for r in csv.reader((ROOT / "translations" / "vi.d" / "FEAT-026.csv").open(encoding="utf-8"))
	if len(r) > 1
}
VI = {r[0]: r[1] for r in csv.reader((ROOT / "translations" / "vi.csv").open(encoding="utf-8")) if len(r) > 1}


def strings(text):
	return {m.group(1).replace('\\"', '"') for m in re.finditer(r'__\(\s*"((?:[^"\\]|\\.)*)"', text)}


class TestFeat026Ui(unittest.TestCase):
	def test_moi_chuoi_giao_dien_co_ban_dich(self):
		for text in (PRICE_LIST, PRICE_FORM, FACILITY, CPI_LIST):
			self.assertEqual([s for s in strings(text) if s not in VI], [])

	def test_nhan_theo_thiet_ke(self):
		self.assertEqual(VI["Confirmed"], "Đã xác nhận")
		self.assertEqual(VI["Proposed"], "Đề xuất")
		self.assertEqual(VI["No service code"], "Chưa gắn mã")
		self.assertEqual(VI["Rejected"], "Loại bỏ")
		self.assertEqual(VI["Reopen"], "Mở lại để rà soát")
		self.assertEqual(VI["Price survey"], "Lập phiếu khảo sát giá")
		self.assertEqual(VI["Confirm {0} reference prices?"], "Xác nhận {0} giá tham chiếu?")

	def test_danh_sach_bon_mau_trang_thai(self):
		for color in ('"green"', '"purple"', '"orange"', '"gray"'):
			self.assertIn(color, PRICE_LIST)

	def test_danh_sach_goi_dung_api(self):
		for fn in ("confirm_prices", "reject_prices", "reopen_prices"):
			self.assertIn(fn, PRICE_LIST)
		self.assertIn("download_template?import_set=nc_benchmark_price", PRICE_LIST)
		self.assertIn('frappe.set_route("import-excel", { import_set: "nc_benchmark_price" })', PRICE_LIST)
		# nút ghi chỉ cho người có quyền (Auditor, Dept Head, Director, Admin chỉ xem)
		self.assertIn('frappe.model.can_create("NC Benchmark Price")', PRICE_LIST)
		self.assertIn('frappe.model.can_write("NC Benchmark Price")', PRICE_LIST)
		self.assertIn("frappe.confirm(", PRICE_LIST)

	def test_form_goi_xac_nhan_va_gia_hieu_chinh(self):
		for fn in ("confirm_prices", "reject_prices", "reopen_prices", "get_adjusted_price"):
			self.assertIn(fn, PRICE_FORM)
		self.assertIn("technical_service: frm.doc.technical_service", PRICE_FORM)
		self.assertIn("alert-warning", PRICE_FORM)
		self.assertIn("frm.perm[0].write", PRICE_FORM)

	def test_form_trang_thai_chi_doc(self):
		import json

		meta = json.loads(read("nc_benchmark_price", "json"))
		status = next(f for f in meta["fields"] if f["fieldname"] == "status")
		self.assertEqual(status.get("read_only"), 1)

	def test_don_vi_lap_phieu_khao_sat(self):
		self.assertIn("download_price_survey", FACILITY)
		self.assertIn('frappe.model.can_create("NC Benchmark Price")', FACILITY)
		self.assertIn("Choose a specialty or services", FACILITY)

	def test_chi_so_hien_thang_mm_yyyy(self):
		self.assertIn('format("MM/YYYY")', CPI_LIST)

	def test_khong_co_chu_ai(self):
		for text in (PRICE_LIST, PRICE_FORM, FACILITY, CPI_LIST):
			self.assertEqual(re.findall(r"\bAI\b", text), [])
		self.assertEqual([k for k in FRAGMENT if re.search(r"\bAI\b", k)], [])

	def test_loi_tat_workspace(self):
		text = (ROOT / "nc_core" / "workspace" / "normcore" / "shortcuts.d" / "FEAT-026.txt").read_text(
			encoding="utf-8"
		)
		targets = [ln.split("|")[2] for ln in text.splitlines() if ln and not ln.startswith("#")]
		self.assertEqual(targets, ["NC Benchmark Facility", "NC Benchmark Price", "NC CPI Index"])
