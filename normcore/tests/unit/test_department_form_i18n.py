"""SCR-DSK-031 (FEAT-001): form NC Department có chuỗi qua __() đều có bản dịch vi.csv, không mã màu cứng."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "nc_core" / "doctype" / "nc_department" / "nc_department.js"


class TestDepartmentForm(unittest.TestCase):
	def test_chuoi_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}
		used = set(re.findall(r"__\(\s*[\"']([^\"']+)[\"']", JS.read_text(encoding="utf-8")))
		self.assertTrue(used)
		self.assertEqual(sorted(s for s in used if not vi.get(s, "").strip()), [])

	def test_khong_ma_mau_cung(self):
		self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", JS.read_text(encoding="utf-8")))
