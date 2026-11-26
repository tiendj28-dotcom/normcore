"""SCR-DSK-015 (FEAT-014, NFR-USE-003): kiểm tĩnh bảng ghi theo bước trên máy tính bảng."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "nc_costing" / "doctype" / "nc_time_study"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
I18N = re.compile(r"__\(\s*\"((?:[^\"\\]|\\.)*)\"")


class TestTimeStudyUi(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.js = (DIR / "nc_time_study.js").read_text(encoding="utf-8")
		cls.lst = (DIR / "nc_time_study_list.js").read_text(encoding="utf-8")

	def test_o_so_cho_ban_phim_so_va_cao_44px(self):
		self.assertIn('inputmode="decimal"', self.js)
		self.assertIn('type="number"', self.js)
		self.assertRegex(self.js, r"\.nc-ts-input \{[^}]*min-height: 44px")
		self.assertRegex(self.js, r"\.nc-ts-panel \.btn \{[^}]*min-height: 44px[^}]*min-width: 44px")

	def test_khong_chieu_rong_co_dinh_lon_hon_768(self):
		for px in re.findall(r"(?<!max-)(?:min-)?width:\s*(\d+)px", self.js):
			self.assertLessEqual(int(px), 768)
		self.assertIn("flex-wrap: wrap", self.js)

	def test_khong_ma_mau_cung(self):
		self.assertIsNone(HEX.search(self.js))
		self.assertIsNone(HEX.search(self.lst))

	def test_chi_goi_api_time_study_va_set_value(self):
		self.assertEqual(
			set(re.findall(r'method:\s*"([^"]+)"', self.js)), {"normcore.api.time_study.get_entry"}
		)
		self.assertIn("frappe.model.set_value", self.js)
		self.assertNotIn("frappe.client.", self.js)

	def test_chuoi_qua_dich_va_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {r[0] for r in csv.reader(f) if len(r) >= 2}
		used = set(I18N.findall(self.js))
		self.assertTrue(used)
		self.assertEqual(sorted(used - vi), [])

	def test_cuon_vao_giua_khi_focus(self):
		self.assertIn('scrollIntoView({ block: "center" })', self.js)


class TestNormSetFormButton(unittest.TestCase):
	"""AMD-014-01: nút trên form NC Norm Set chỉ điều hướng, không gọi API."""

	@classmethod
	def setUpClass(cls):
		cls.js = (ROOT / "nc_costing" / "doctype" / "nc_norm_set" / "nc_norm_set.js").read_text(
			encoding="utf-8"
		)
		cls.block = cls.js.split("FEAT-014, AMD-014-01", 1)[1].split("NC Finance", 1)[0]

	def test_chi_hien_o_nhap_va_co_quyen_ghi(self):
		self.assertIn('frm.doc.status === "Nháp"', self.block)
		self.assertIn('frappe.model.can_write("NC Norm Set")', self.block)

	def test_dieu_huong_toi_report_voi_bo_loc(self):
		self.assertIn('frappe.set_route("query-report", "NC Time Study Result"', self.block)
		for key in ("technical_service", "department", "procedure", "norm_set"):
			self.assertIn(key, self.block)

	def test_khong_goi_api(self):
		self.assertNotIn("frappe.call", self.block)

	def test_luoi_va_api_norm_khong_doi(self):
		import subprocess

		root = ROOT.parent
		out = subprocess.run(
			["git", "diff", "origin/develop", "--", "normcore/public/js/norm_grid/", "normcore/api/norm.py"],
			cwd=root,
			capture_output=True,
			text=True,
		)
		self.assertEqual(out.stdout, "")


class TestTimeStudyReportUi(unittest.TestCase):
	"""SCR-DSK-016 (FEAT-014): Script Report chỉ ghi qua api.time_study.apply_to_norm_set, có xác nhận thiếu ca."""

	@classmethod
	def setUpClass(cls):
		cls.js = (
			ROOT / "nc_costing" / "report" / "nc_time_study_result" / "nc_time_study_result.js"
		).read_text(encoding="utf-8")

	def test_chi_goi_apply_to_norm_set(self):
		self.assertEqual(
			set(re.findall(r'method:\s*"([^"]+)"', self.js)), {"normcore.api.time_study.apply_to_norm_set"}
		)

	def test_xac_nhan_thieu_ca_goi_lai_confirm_1(self):
		self.assertIn("res.needs_confirm", self.js)
		self.assertIn("frappe.confirm(", self.js)
		self.assertIn("nc_ts_apply(report, normSet, true)", self.js)

	def test_nut_chi_hien_khi_co_quyen_ghi_bo_dinh_muc(self):
		self.assertIn('frappe.model.can_write("NC Norm Set")', self.js)

	def test_hop_chon_loc_bo_nhap(self):
		self.assertIn('status: "Nháp"', self.js)
		self.assertIn("f.norm_set", self.js)

	def test_chuoi_co_ban_dich_va_khong_ma_mau(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {r[0] for r in csv.reader(f) if len(r) >= 2}
		used = {m.replace('\\"', '"') for m in I18N.findall(self.js)}
		self.assertTrue(used)
		self.assertEqual(sorted(used - vi), [])
		self.assertIsNone(HEX.search(self.js))


class TestTimeStudyFormFixes(unittest.TestCase):
	"""Sửa theo QA (verdict rework 90cb6b0): bảng con lines ẩn dưới 1200 px; procedure không bắt buộc ở form."""

	def test_bang_con_lines_an_duoi_1200px(self):
		js = (DIR / "nc_time_study.js").read_text(encoding="utf-8")
		self.assertRegex(
			js, r"@media \(max-width: 1199px\) \{[^}]*\[data-fieldname=\"lines\"\][^}]*display: none"
		)

	def test_procedure_khong_reqd_de_luu_phieu_moi(self):
		import json

		fields = {
			f["fieldname"]: f
			for f in json.loads((DIR / "nc_time_study.json").read_text(encoding="utf-8"))["fields"]
		}
		self.assertFalse(fields["procedure"].get("reqd"))
		self.assertEqual(fields["procedure"]["fieldtype"], "Link")
