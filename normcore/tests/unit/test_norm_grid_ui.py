"""SCR-DSK-014 (FEAT-012): kiểm tĩnh trang norm-grid — chỉ gọi API norm, không mã màu cứng, chuỗi qua __(), lỗi role=alert."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "public" / "js" / "norm_grid"
PAGE_DIR = ROOT / "nc_costing" / "page" / "norm_grid"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
I18N = re.compile(r"""__\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')""")
VUE = (UI_DIR / "NormGrid.vue").read_text(encoding="utf-8")
API_FUNCS = {
	"get_norm_set",
	"save_line",
	"delete_line",
	"confirm_line",
	"confirm_set",
	"return_set",
	"lock_set",
	"new_version",
	"search_resources",
}


def _sources():
	return [*UI_DIR.glob("*"), *PAGE_DIR.glob("*.js")]


class TestNormGridUI(unittest.TestCase):
	def test_tep_ton_tai(self):
		for name in ("NormGrid.vue", "norm_grid.bundle.js"):
			self.assertTrue((UI_DIR / name).is_file(), name)
		self.assertTrue((PAGE_DIR / "norm_grid.js").is_file())
		self.assertTrue((PAGE_DIR / "norm_grid.json").is_file())

	def test_khong_ma_mau_cung(self):
		for p in _sources():
			self.assertIsNone(HEX.search(p.read_text(encoding="utf-8")), p.name)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0] for row in csv.reader(f) if row}
		used = set()
		for p in _sources():
			for a, b in I18N.findall(p.read_text(encoding="utf-8")):
				used.add((a or b).replace("\\'", "'"))
		self.assertTrue(used)
		self.assertEqual(sorted(used - vi), [])

	def test_chi_goi_api_norm(self):
		self.assertIn('const API = "normcore.api.norm."', VUE)
		methods = set(re.findall(r'this\.call\("(\w+)"', VUE))
		self.assertTrue(methods)
		self.assertLessEqual(methods, API_FUNCS)
		# không ghi thẳng DocType từ trình duyệt (ADR-010)
		for banned in (
			"frappe.client",
			"frappe.db",
			"frappe.desk.form",
			"run_doc_method",
			"make_control",
			"validate_link",
		):
			self.assertNotIn(banned, VUE)
		self.assertEqual(re.findall(r"method:\s*([^,]+),", VUE), ["API + method"])  # mọi lệnh gọi qua API

	def test_loi_hien_o_dai_role_alert(self):
		self.assertGreaterEqual(VUE.count('role="alert"'), 3)  # tải, hàng, hành động
		self.assertIn("silent: true", VUE)  # không mở hộp thoại của Desk

	def test_nut_an_theo_actions(self):
		for action in (
			"confirm_set",
			"lock_set",
			"new_version",
			"return_set",
			"save_line",
			"confirm_line",
			"delete_line",
		):
			self.assertRegex(VUE, rf"can\('{action}'\)")
		self.assertIn("this.actions.includes", VUE)

	def test_sua_o_chi_khi_co_quyen_sua(self):
		self.assertIn('v-if="canEdit"', VUE)

	def test_bang_luoi_truy_cap(self):
		self.assertIn('role="grid"', VUE)
		self.assertIn('scope="col"', VUE)
		self.assertIn(":aria-expanded", VUE)

	def test_trang_khai_bao_vai_tro_va_module(self):
		import json

		d = json.loads((PAGE_DIR / "norm_grid.json").read_text(encoding="utf-8"))
		self.assertEqual((d["name"], d["module"]), ("norm-grid", "NC Costing"))
		roles = {r["role"] for r in d["roles"]}
		self.assertIn("NC Auditor", roles)
		self.assertNotIn("NC Council Member", roles)


class TestNormSetListUI(unittest.TestCase):
	def test_cot_ten_khong_dung_formatter_html(self):
		"""QA: formatter `name` trả HTML làm cột tiêu đề hiện nguyên chuỗi thẻ <a>; liên kết đặt qua nút của dòng."""
		js = (ROOT / "nc_costing" / "doctype" / "nc_norm_set" / "nc_norm_set_list.js").read_text(
			encoding="utf-8"
		)
		self.assertNotRegex(js, r"formatters:\s*\{[^}]*\bname\s*\(")
		self.assertNotIn("<a href", js)
		self.assertIn("button:", js)
		self.assertIn('frappe.set_route("norm-grid"', js)


class TestNormGridFeat013(unittest.TestCase):
	"""FEAT-013 (FR-NORM-015): nút theo `actions`, nhóm Bước đã bỏ, dải thay đổi role=status."""

	def test_FR_NORM_015_nut_tao_phien_ban_theo_quy_trinh_moi(self):
		self.assertIn("can('new_version')", VUE)
		self.assertIn("data.doc.newer_procedure", VUE)
		self.assertIn('__("Create version from new procedure")', VUE)

	def test_FR_NORM_015_nhom_buoc_da_bo(self):
		self.assertIn("g.removed", VUE)
		self.assertIn('__("Removed step")', VUE)
		self.assertIn("l.step_removed", VUE)

	def test_FR_NORM_015_dai_thay_doi_co_role_status(self):
		self.assertRegex(VUE, r'<section v-if="changeStrip"[^>]*role="status"')
		self.assertIn("steps_without_lines", VUE)

	def test_FR_NORM_015_chip_buoc_thieu_co_aria_label(self):
		self.assertIn("__('Add line for step {0}', [m.step_id])", VUE)

	def test_FR_NORM_015_chi_goi_api_norm(self):
		called = set(re.findall(r'this\.call\("(\w+)"', VUE))
		self.assertTrue(called)
		self.assertLessEqual(called, API_FUNCS)
