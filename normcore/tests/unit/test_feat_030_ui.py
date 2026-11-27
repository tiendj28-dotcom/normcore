"""FEAT-030 T07: giao diện SCR-DSK-027 và mở rộng (ui-design.md): kiểm tĩnh mã nguồn JS, bản dịch, workspace."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PP = ROOT / "nc_benchmark" / "doctype" / "nc_price_proposal"
FORM = (PP / "nc_price_proposal.js").read_text(encoding="utf-8")
LIST = (PP / "nc_price_proposal_list.js").read_text(encoding="utf-8")
RUN_FORM = (ROOT / "nc_costing" / "doctype" / "nc_costing_run" / "nc_costing_run.js").read_text(
	encoding="utf-8"
)
SERVICE = (ROOT / "nc_procedure" / "doctype" / "nc_technical_service" / "nc_technical_service.js").read_text(
	encoding="utf-8"
)
EXPORT = (ROOT / "public" / "js" / "export_dialog.js").read_text(encoding="utf-8")
SHORTCUTS = (ROOT / "nc_core" / "workspace" / "normcore" / "shortcuts.d" / "FEAT-030.txt").read_text(
	encoding="utf-8"
)
FRAGMENT = {
	r[0]: r[1]
	for r in csv.reader((ROOT / "translations" / "vi.d" / "FEAT-030.csv").open(encoding="utf-8"))
	if len(r) > 1
}
BASE = {
	r[0]: r[1]
	for f in (ROOT / "translations" / "vi.d").glob("*.csv")
	for r in csv.reader(f.open(encoding="utf-8"))
	if len(r) > 1
}


def strings(text):
	return {m.group(1).replace('\\"', '"') for m in re.finditer(r'__\(\s*"((?:[^"\\]|\\.)*)"', text)}


class TestFeat030Ui(unittest.TestCase):
	def test_moi_chuoi_giao_dien_co_ban_dich(self):
		for text in (FORM, LIST):
			self.assertEqual([s for s in strings(text) if s not in BASE], [])
		for text in (RUN_FORM, SERVICE):
			for s in ("Create price proposal", "No approved price yet"):
				if s in text:
					self.assertIn(s, BASE)

	def test_nhan_theo_thiet_ke(self):
		self.assertEqual(FRAGMENT["Basis required"], "Cần căn cứ")
		self.assertEqual(FRAGMENT["Below cost"], "Dưới giá thành")
		self.assertEqual(FRAGMENT["Submit for review"], "Gửi duyệt")
		self.assertEqual(FRAGMENT["Record authority decision"], "Ghi kết quả phê duyệt")
		self.assertEqual(FRAGMENT["Export price comparison"], "Xuất bảng so sánh giá")
		self.assertEqual(FRAGMENT["No approved price yet"], "Chưa có giá đã duyệt")

	def test_form_goi_dung_api(self):
		self.assertIn('const PP_API = "normcore.api.price_proposal."', FORM)
		for fn in ("apply_action", "get_proposal", "record_authority_result", "export_price_comparison"):
			self.assertIn(fn, FORM)
		for action in ("Gửi duyệt", "Xác nhận", "Phê duyệt", "Từ chối", "Ghi kết quả phê duyệt"):
			self.assertIn(f'"{action}"', FORM)
		self.assertIn("reqd: 1", FORM)  # lý do từ chối bắt buộc
		self.assertIn("before_workflow_action", FORM)
		self.assertIn("Promise.reject()", FORM)  # không qua apply_workflow của Desk
		self.assertIn("aria-busy", FORM)
		self.assertIn("cannot_add_rows = true", FORM)

	def test_hop_thoai_phe_duyet_bat_xac_nhan_tung_dong(self):
		self.assertIn("below_cost", FORM)
		self.assertIn('"ack_" + i.name', FORM)
		self.assertIn("acknowledged: JSON.stringify(acked)", FORM)
		self.assertIn("acked.length < below.length", FORM)

	def test_khong_mau_tu_dat(self):
		for text in (FORM, LIST):
			self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", text), [])
			self.assertEqual(re.findall(r"\brgba?\(", text), [])

	def test_nhan_trang_thai_theo_design_md(self):
		for state, color in (
			("Nháp", "gray"),
			("Chờ khoa xác nhận", "orange"),
			("Chờ phê duyệt", "orange"),
			("Đã duyệt", "green"),
			("Đã duyệt nội bộ, chờ trình", "blue"),
			("Đã được cấp thẩm quyền duyệt", "green"),
		):
			self.assertRegex(LIST, rf'"{state}": \[__\("[^"]+"\), "{color}"\]')

	def test_nut_tao_phuong_an_chi_khi_da_khoa(self):
		block = RUN_FORM.split('__("Create price proposal"), () =>')[0].rsplit("if (", 1)[1]
		self.assertIn('"Đã khóa"', block)
		self.assertNotIn('"Đã tính"', block)
		self.assertIn("normcore.api.price_proposal.create_proposal", RUN_FORM)

	def test_giao_dien_dich_vu_va_hop_thoai_xuat(self):
		self.assertIn("approved_prices", SERVICE)
		self.assertIn("cannot_add_rows = true", SERVICE)
		self.assertIn('"price_comparison"', EXPORT)

	def test_shortcut_workspace(self):
		self.assertEqual(SHORTCUTS.strip(), "nc-pag-s|Phương án giá|NC Price Proposal|DocType|List")
