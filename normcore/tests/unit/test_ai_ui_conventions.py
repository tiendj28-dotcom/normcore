"""FEAT-023 giao diện SCR-DSK-029 (ui-design.md): kiểm tĩnh trên mã JS, không mã màu cứng, không lộ khóa."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DT = ROOT / "nc_ai" / "doctype"
FILES = {
	"settings": DT / "nc_ai_settings" / "nc_ai_settings.js",
	"template": DT / "nc_prompt_template" / "nc_prompt_template.js",
	"template_list": DT / "nc_prompt_template" / "nc_prompt_template_list.js",
	"log_list": DT / "nc_ai_log" / "nc_ai_log_list.js",
	"global": ROOT / "public" / "js" / "normcore_ai.js",
}
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")


def _src(key):
	return FILES[key].read_text(encoding="utf-8")


class TestAiUi(unittest.TestCase):
	def test_tep_ton_tai_va_khong_ma_mau_cung(self):
		for key, p in FILES.items():
			self.assertTrue(p.is_file(), key)
			self.assertIsNone(HEX.search(p.read_text(encoding="utf-8")), key)

	def test_cau_hinh_goi_dung_api_va_chi_admin_co_nut(self):
		s = _src("settings")
		self.assertIn("normcore.api.ai.test_connection", s)
		self.assertIn("normcore.api.ai.get_ai_usage", s)
		self.assertIn('can_write("NC AI Settings")', s)
		self.assertIn("Kiểm tra kết nối", s)
		self.assertIn("Lưu cấu hình trước khi kiểm tra kết nối.", s)

	def test_khong_doc_khoa_ra_giao_dien(self):
		for key in ("settings", "template", "global"):
			self.assertNotIn("doc.api_key", _src(key), key)

	def test_mau_lenh_bat_bien_va_tao_phien_ban_moi(self):
		s = _src("template")
		for f in ("template_code", "system_prompt", "user_prompt", "output_schema"):
			self.assertIn(f'"{f}"', s)
		self.assertIn("normcore.api.ai.new_prompt_version", s)
		self.assertIn('can_create("NC Prompt Template")', s)

	def test_indicator_danh_sach_co_chu(self):
		self.assertIn("Đang dùng", _src("template_list"))
		self.assertIn("Ngừng dùng", _src("template_list"))
		for st in ("Thành công", "Lỗi", "Quá hạn", "Bị chặn hạn mức"):
			self.assertIn(st, _src("log_list"))

	def test_co_che_an_nut_ai(self):
		s = _src("global")
		self.assertIn("frappe.boot.normcore_ai_enabled", s)
		self.assertIn("normcore.ai.enabled", s)
