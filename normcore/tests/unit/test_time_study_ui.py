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
		for px in re.findall(r"(?:min-)?width:\s*(\d+)px", self.js):
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
