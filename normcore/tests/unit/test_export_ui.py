"""FEAT-019 T07: kiểm tĩnh giao diện SCR-DSK-028 (nút, đường gọi API, chuỗi có bản dịch)."""

import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIALOG = ROOT / "public" / "js" / "export_dialog.js"
FORMS = {
	"nc_costing_run": ROOT / "nc_costing" / "doctype" / "nc_costing_run" / "nc_costing_run.js",
	"nc_service_cost": ROOT / "nc_costing" / "doctype" / "nc_service_cost" / "nc_service_cost.js",
	"nc_norm_set": ROOT / "nc_costing" / "doctype" / "nc_norm_set" / "nc_norm_set.js",
}
I18N = re.compile(r"__\(\s*(\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*')")


def text(p):
	return p.read_text(encoding="utf-8")


def strings(p):
	return {m[1:-1].replace('\\"', '"').replace("\\'", "'") for m in I18N.findall(text(p))}


class TestExportUi(unittest.TestCase):
	def test_hop_thoai_goi_du_api_va_realtime(self):
		js = text(DIALOG)
		for s in (
			"normcore.api.export.",
			"get_export_options",
			"export_file",
			"export_bundle",
			"nc_export_bundle",
			"open_url_post",
		):
			self.assertIn(s, js)
		self.assertIn("normcore.export.open", js)
		self.assertIn('role="alert"', js)
		self.assertIn("aria-live", js)

	def test_o_chon_mot_lua_chon_tu_chon(self):
		js = text(DIALOG)
		self.assertIn("costs.length === 1", js)
		self.assertIn("o.norm_sets || []).length === 1", js)

	def test_NORM_78_hop_thoai_cho_truong_khoa(self):
		js = text(DIALOG)
		self.assertIn("o.own_service", js)  # danh sách dịch vụ/bộ định mức khi không đọc được lần tính
		self.assertIn("run_locked", js)  # trạng thái khóa từ máy chủ, không suy từ nút
		self.assertIn("!state.service_cost", js)  # không hiện cost_empty khi đã có dịch vụ
		self.assertIn("o.source.run_readable !== false) a.run", js)  # không gửi run khi không đọc được lần tính
		sc = text(FORMS["nc_service_cost"])
		self.assertNotIn('frappe.db.get_value("NC Costing Run"', sc)  # tránh popup quyền

	def test_khong_ma_mau_cung(self):
		self.assertIsNone(re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", text(DIALOG)))

	def test_nut_mo_hop_thoai(self):
		for name, p in FORMS.items():
			self.assertIn("normcore.export.open", text(p), name)
		self.assertIn("run: frm.doc.name", text(FORMS["nc_costing_run"]))
		self.assertIn("service_cost: frm.doc.name", text(FORMS["nc_service_cost"]))
		self.assertIn("norm_set: frm.doc.name", text(FORMS["nc_norm_set"]))

	def test_hook_registry_khai_bao_tep(self):
		reg = json.loads(text(ROOT / "hook_registry" / "FEAT-019.json"))
		self.assertEqual(reg["app_include_js"], ["/assets/normcore/js/export_dialog.js"])

	def test_chuoi_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.d" / "FEAT-019.csv", encoding="utf-8", newline="") as f:
			vi = {r[0]: r[1] for r in csv.reader(f) if len(r) >= 2}
		used = set()
		for p in (DIALOG, *FORMS.values()):
			used |= strings(p)
		for s in ("Export documents", "Export explanation PDF", "Export norm set", *strings(DIALOG)):
			self.assertIn(s, vi)
		self.assertTrue(vi["Export documents"])
