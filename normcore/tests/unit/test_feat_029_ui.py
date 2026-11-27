"""FEAT-029: giao diện kịch bản điều chỉnh và yêu cầu sửa quy trình (ui-design.md): kiểm tĩnh mã nguồn, bản dịch."""

import csv
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(*parts):
	return ROOT.joinpath(*parts).read_text(encoding="utf-8")


VUE = read("public", "js", "price_compare", "PriceCompare.vue")
PCR = ROOT / "nc_benchmark" / "doctype" / "nc_procedure_change_request"
PCR_FORM = (PCR / "nc_procedure_change_request.js").read_text(encoding="utf-8")
PCR_LIST = (PCR / "nc_procedure_change_request_list.js").read_text(encoding="utf-8")
RUN = ROOT / "nc_costing" / "doctype" / "nc_costing_run"
RUN_FORM = (RUN / "nc_costing_run.js").read_text(encoding="utf-8")
RUN_LIST = (RUN / "nc_costing_run_list.js").read_text(encoding="utf-8")
PROC_FORM = read("nc_procedure", "doctype", "nc_clinical_procedure", "nc_clinical_procedure.js")
FRAGMENT = {
	r[0]: r[1]
	for r in csv.reader((ROOT / "translations" / "vi.d" / "FEAT-029.csv").open(encoding="utf-8"))
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


class TestFeat029Ui(unittest.TestCase):
	def test_moi_chuoi_giao_dien_co_ban_dich(self):
		for text in (VUE, PCR_FORM, PCR_LIST, RUN_FORM, RUN_LIST, PROC_FORM):
			self.assertEqual([s for s in strings(text) if s not in BASE], [])

	def test_nhan_theo_thiet_ke(self):
		self.assertEqual(FRAGMENT["Scenario price"], "Giá kịch bản")
		self.assertEqual(FRAGMENT["Send procedure change request"], "Chuyển yêu cầu sửa quy trình")
		self.assertEqual(FRAGMENT["Propose procedure change"], "Đề xuất sửa quy trình")
		self.assertEqual(FRAGMENT["New scenario"], "Kịch bản mới")
		self.assertEqual(FRAGMENT["Show scenario"], "Xem kịch bản")
		self.assertEqual(FRAGMENT["Accept and open revision"], "Tiếp nhận và mở bản sửa đổi")

	def test_vue_goi_dung_api(self):
		self.assertIn('const SCENARIO_API = "normcore.api.scenario."', VUE)
		for fn in ("accept_suggestion", "get_open_scenario", "create_scenario", "request_procedure_change"):
			self.assertIn(fn, VUE)
		self.assertNotIn("(coming)", VUE)
		self.assertIn('@click="accept(s)"', VUE)
		self.assertIn("accepting === s.name", VUE)
		self.assertIn("aria-busy", VUE)
		self.assertIn('role="region"', VUE)
		self.assertIn('scope="col"', VUE)
		self.assertIn("detail.can_request_change", VUE)
		self.assertIn("reqd: 1", VUE)

	def test_vue_khong_mau_tu_dat(self):
		self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b", VUE), [])
		self.assertEqual(re.findall(r"\brgba?\(", VUE), [])

	def test_form_yeu_cau_goi_dung_api(self):
		self.assertIn("normcore.api.scenario.", PCR_FORM)
		self.assertIn("act_on_change_request", PCR_FORM)
		self.assertIn("change_request_actions", PCR_FORM)
		self.assertIn("procedure-editor", PCR_FORM)
		for color in ('"blue"', '"orange"', '"gray"', '"green"'):
			self.assertIn(color, PCR_LIST)

	def test_form_lan_tinh_kich_ban(self):
		self.assertIn("based_on_run", RUN_FORM)
		self.assertIn('frappe.set_route("price-compare", { run: frm.doc.based_on_run })', RUN_FORM)
		self.assertIn("based_on_run", RUN_LIST)
		self.assertIn('"purple"', RUN_LIST)

	def test_dai_nhac_tren_form_quy_trinh(self):
		self.assertIn("NC Procedure Change Request", PROC_FORM)
		self.assertIn("nc_change_request_banner(frm)", PROC_FORM)
