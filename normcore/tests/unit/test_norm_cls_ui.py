"""SCR-DSK-014, SCR-DSK-013 (FEAT-034): kiểm tĩnh phần [1.1] của lưới định mức và hộp chọn hệ thống khi khởi tạo.
Chỉ test mới; test_norm_grid_ui.py của FEAT-012 giữ nguyên."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VUE = (ROOT / "public" / "js" / "norm_grid" / "NormGrid.vue").read_text(encoding="utf-8")
CREATE = (ROOT / "public" / "js" / "norm_create.js").read_text(encoding="utf-8")
LIST_JS = (ROOT / "nc_costing" / "doctype" / "nc_norm_set" / "nc_norm_set_list.js").read_text(encoding="utf-8")
PROC_JS = (
	ROOT / "nc_procedure" / "doctype" / "nc_clinical_procedure" / "nc_clinical_procedure.js"
).read_text(encoding="utf-8")
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
I18N = re.compile(r"""__\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')""")
API_NEW = {"save_head", "copy_norm_set", "export_norm_set", "create_options", "create_norm_set"}


class TestNormGridCls(unittest.TestCase):
	def test_ham_api_moi_qua_cls_chi_trong_danh_sach(self):
		methods = set(re.findall(r'this\.cls\("(\w+)"', VUE))
		self.assertEqual(methods, {"save_head", "copy_norm_set"})
		self.assertIn("this.call(method, args)", VUE)  # cùng một đường gọi normcore.api.norm.*

	def test_xuat_excel_qua_api_norm(self):
		self.assertIn("/api/method/normcore.api.norm.export_norm_set?name=", VUE)

	def test_cot_cls_chi_hien_khi_can_lam_sang(self):
		self.assertIn("meta.is_paraclinical", VUE)
		for col in ("Cost level", "Apply k"):
			self.assertRegex(VUE, r'<th v-if="isCls" scope="col">\{\{ __\("%s"\) \}\}</th>' % col)

	def test_nhan_k_chi_bat_duoc_theo_dieu_kien_di17(self):
		self.assertRegex(VUE, r'"RESULT" && MATERIAL\.includes\(component\)')
		self.assertIn("aria-disabled", VUE)
		self.assertIn("toggleK", VUE)

	def test_nut_sao_chep_theo_actions_va_xuat_luon_co(self):
		self.assertRegex(VUE, r"can\('copy_norm_set'\)")
		self.assertRegex(VUE, r'@click="exportExcel"')
		self.assertNotRegex(VUE, r"can\('export_norm_set'\)")  # ASM-034-24: mọi người đọc được đều xuất được

	def test_dai_canh_bao_va_ly_do_chan(self):
		self.assertIn("data.warnings", VUE)
		self.assertIn("setBlockers", VUE)
		self.assertGreaterEqual(VUE.count('role="alert"'), 4)  # thêm lỗi hộp sao chép

	def test_dong_giu_cho_va_qc_conflict(self):
		self.assertIn("nc-ng__row--hold", VUE)
		self.assertIn("l.qc_conflict", VUE)
		self.assertIn("var(--bg-yellow", VUE)

	def test_khong_ma_mau_cung(self):
		for text in (VUE, CREATE, LIST_JS, PROC_JS):
			self.assertIsNone(HEX.search(text))


class TestCreateDialog(unittest.TestCase):
	def test_chi_goi_api_norm(self):
		self.assertIn('const API = "normcore.api.norm."', CREATE)
		self.assertEqual(set(re.findall(r'method:\s*API \+ "(\w+)"', CREATE)), {"create_options", "create_norm_set"})
		self.assertEqual(len(re.findall(r"method:", CREATE)), 2)
		self.assertIn("silent: true", CREATE)  # lỗi hiện ở hộp thoại, không mở hộp của Desk
		self.assertIn('role="alert"', CREATE)

	def test_hai_noi_goi_dung_hop_chon_he_thong(self):
		for js in (LIST_JS, PROC_JS):
			self.assertIn("normcore.norm.create(", js)
			self.assertIn("/assets/normcore/js/norm_create.js", js)
			self.assertNotIn("normcore.api.norm.create_norm_set", js)

	def test_chuoi_giao_dien_co_ban_dich(self):
		with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
			vi = {row[0] for row in csv.reader(f) if row}
		used = set()
		for text in (VUE, CREATE, LIST_JS, PROC_JS):
			for a, b in I18N.findall(text):
				used.add((a or b).replace("\\'", "'"))
		self.assertEqual(sorted(used - vi), [])
