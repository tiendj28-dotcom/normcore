"""FEAT-019: API xuất hồ sơ (TC-OUT-01..04; FR-OUT-001..006, 008, 009; FR-AUD-004)."""

import io
import sys
import zipfile
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import load_workbook

sys.path.insert(0, frappe.get_app_path("normcore", "..", "docs", "golden"))
import golden_engine as g

from normcore.api import access
from normcore.api import costing as costing_api
from normcore.api import export as api
from normcore.api import norm as norm_api
from normcore.exports import annex
from normcore.exports import meta as meta_mod
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_user

FIN = "fin.out19@normcore.test"
AUD = "aud.out19@normcore.test"
CLIN = "clin.out19@normcore.test"
HEAD = "head.out19@normcore.test"
HEAD2 = "head2.out19@normcore.test"


def wb_of(content):
	return load_workbook(io.BytesIO(content))


class TestExportApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		for email, role in (
			(FIN, "NC Finance"),
			(AUD, "NC Auditor"),
			(CLIN, "NC Clinician"),
			(HEAD, "NC Department Head"),
			(HEAD2, "NC Department Head"),
		):
			make_user(email, role)
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)
		cf.ensure(
			"NC Department",
			"department_code",
			"KHOA-KHAC",
			department_name="Khoa khác",
			department_type="Lâm sàng",
			cost_center=self.dept,
		)
		access.assign_department(HEAD, self.dept)
		access.assign_department(HEAD2, "KHOA-KHAC")
		self.run = cf.make_golden_run(self.params, accounting_import=self.imp)
		frappe.set_user(FIN)
		costing_api.start_costing(self.run.name)
		frappe.set_user("Administrator")
		name = frappe.db.get_value(
			"NC Reconciliation Line", {"costing_run": self.run.name, "cost_category": "DRUG_SUPPLY"}
		)
		frappe.db.set_value("NC Reconciliation Line", name, "explanation", "Nhập thuốc chưa xuất kho")
		frappe.set_user(FIN)
		costing_api.lock_run(self.run.name)
		frappe.set_user("Administrator")
		self.cost_a = self._cost("DV-TEST-A")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.response.pop("filecontent", None)

	def _cost(self, service):
		return frappe.db.get_value("NC Service Cost", {"costing_run": self.run.name, "technical_service": service})

	def _export(self, file_type, user=FIN, **kw):
		frappe.set_user(user)
		frappe.response.pop("filecontent", None)
		api.export_file(file_type, **kw)
		frappe.set_user("Administrator")
		return frappe.response["filename"], frappe.response["filecontent"]

	def _events(self, ref_name):
		return frappe.get_all(
			"NC Audit Event",
			{"event_type": "Xuất tệp", "ref_name": ref_name},
			["user", "ref_doctype", "detail"],
			order_by="creation",
		)

	def _info(self, wb):
		info = wb[meta_mod.INFO_SHEET]
		return {info.cell(r, 1).value: info.cell(r, 2).value for r in range(1, info.max_row + 1)}

	# ---- TC-OUT-01 ----
	def test_TC_OUT_01_xuat_phu_luc_cot_khop_mau(self):
		for ft, code in (("annex_ii", "II"), ("annex_iii", "III"), ("annex_v", "V")):
			name, content = self._export(ft, run=self.run.name)
			self.assertEqual(name, f"PL-{code}-{self.run.name}.xlsx")
			wb = wb_of(content)
			ws = wb.worksheets[0]
			self.assertEqual(annex.header_of(ws, code), annex.ANNEX[code]["columns"])
			self.assertEqual(annex.header_of(ws, code), annex.header_of(annex.load_template(code).active, code))
		wb = wb_of(self._export("annex_ii", run=self.run.name)[1])
		self.assertEqual(wb.sheetnames, ["DV-TEST-A", "DV-TEST-B", meta_mod.INFO_SHEET])
		ws = wb["DV-TEST-A"]
		self.assertEqual(ws.cell(7, 3).value, float(g.run()[0]["DV-TEST-A"]["direct"]))
		ws3 = wb_of(self._export("annex_iii", run=self.run.name)[1]).worksheets[0]
		self.assertEqual(ws3.cell(6, 11).value, 287745.46)
		self.assertEqual([round(ws3.cell(6, c).value, 2) for c in range(6, 11)], [121152.60, 49550.0, 75000.0, 4900.0, 37142.86])
		ws5 = wb_of(self._export("annex_v", run=self.run.name)[1]).worksheets[0]
		self.assertEqual((ws5.cell(6, 7).value, ws5.cell(6, 8).value, ws5.cell(6, 9).value), (287745.46, 302132.73, 302100))
		self.assertEqual(ws5.cell(7, 9).value, 92600)

	def test_phu_luc_iv_xuat_duoc(self):
		wb = wb_of(self._export("annex_iv", run=self.run.name)[1])
		ws = wb.worksheets[0]
		self.assertEqual(annex.header_of(ws, "IV"), annex.ANNEX_IV_COLUMNS)
		rules = [ws.cell(r, 3).value for r in range(6, 14)]
		self.assertEqual(rules.count("Phân bổ"), 5)

	# ---- TC-OUT-02 ----
	def test_TC_OUT_02_giai_trinh_pdf_nhom_cau_phan_buoc(self):
		name, content = self._export("explanation_pdf", service_cost=self.cost_a)
		self.assertTrue(content.startswith(b"%PDF"))
		self.assertEqual(name, f"giai-trinh-DV-TEST-A-{self.run.name}.pdf")
		frappe.set_user(FIN)
		html, _sc = api.explanation_html(self.cost_a)
		expl = costing_api.get_explanation(self.cost_a)
		frappe.set_user("Administrator")
		self.assertIn("287.745,46", html)
		self.assertEqual(html.count("<h2>Chi phí phân bổ</h2>"), 1)
		pos = [html.index(f">{grp['label']}<") for grp in expl["direct_groups"]]
		self.assertEqual(pos, sorted(pos))
		labor = [x for x in expl["direct_groups"] if x["component"] == "LABOR"][0]
		self.assertEqual(len(labor["steps"]), 3)
		for grp in expl["direct_groups"]:
			self.assertIn(f"{grp['label']}</td>", html)
			for st in grp["steps"]:
				self.assertIn(st["step_label"], html)
				for ln in st["lines"]:
					self.assertEqual(html.count(f"<td>{ln['norm_line_id']}</td>"), 1, ln["norm_line_id"])
		self.assertEqual(len(expl["allocation_lines"]), 5)

	# ---- TC-OUT-03 ----
	def test_TC_OUT_03_thong_tin_truy_vet_va_nhat_ky(self):
		ps = self.params.name
		for ft in ("annex_ii", "annex_iii", "annex_iv", "annex_v", "norm_set_xlsx"):
			kw = {"norm_set": self.sets[0].name, "run": self.run.name} if ft == "norm_set_xlsx" else {"run": self.run.name}
			ref = self.sets[0].name if ft == "norm_set_xlsx" else self.run.name
			before = len(self._events(ref))
			name, content = self._export(ft, **kw)
			wb = wb_of(content)
			info = self._info(wb)
			self.assertEqual(info["Mã lần tính giá"], self.run.name)
			self.assertTrue(info["Bộ tham số"].startswith(f"{ps} — "))
			self.assertRegex(info["Thời điểm xuất"], r"^\d{2}/\d{2}/\d{4} ")
			self.assertIn(FIN, info["Người xuất"])
			for ws in wb.worksheets:
				self.assertIn(self.run.name, ws.oddFooter.center.text)
			ev = self._events(ref)
			self.assertEqual(len(ev), before + 1, ft)
			self.assertEqual(ev[-1]["user"], FIN)
			self.assertIn(api.FILE_TYPES[ft][0], ev[-1]["detail"])
			self.assertIn(name, ev[-1]["detail"])
		self.assertEqual(self._events(self.run.name)[0]["ref_doctype"], "NC Costing Run")
		# PDF: khối thông tin trong HTML và một sự kiện
		before = len(self._events(self.cost_a))
		self._export("explanation_pdf", service_cost=self.cost_a)
		self.assertEqual(len(self._events(self.cost_a)), before + 1)
		frappe.set_user(FIN)
		html, _sc = api.explanation_html(self.cost_a)
		frappe.set_user("Administrator")
		for s in (self.run.name, f"{ps} — ", "Thông tin xuất", FIN):
			self.assertIn(s, html)

	# ---- TC-OUT-04 ----
	def test_TC_OUT_04_bo_dinh_muc_excel_pdf_11_dong(self):
		ns = self.sets[0]
		for ln in ns.lines:
			frappe.db.set_value("NC Norm Line", ln.name, {"confirmed_by": HEAD, "confirmed_on": "2026-02-01 08:00:00"})
		name, content = self._export("norm_set_xlsx", norm_set=ns.name, run=self.run.name)
		ws = wb_of(content).worksheets[0]
		hrow = [r for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value == "Bước"][0]
		header = [c.value for c in ws[hrow]]
		rows = [r for r in ws.iter_rows(min_row=hrow + 1, values_only=True) if r[2]]
		self.assertEqual(len(rows), 11)
		self.assertEqual([r[2] for r in rows][:2], ["L01", "L02"])
		self.assertEqual({r[header.index("Căn cứ")] for r in rows}, {"Quy trình"})
		self.assertEqual({r[header.index("Người xác nhận")] for r in rows}, {HEAD})
		_n, pdf = self._export("norm_set_pdf", norm_set=ns.name, run=self.run.name)
		self.assertTrue(pdf.startswith(b"%PDF"))
		frappe.set_user(FIN)
		data = norm_api._export_data(frappe.get_doc("NC Norm Set", ns.name))
		html = api.norm_set_html(data, api._meta("norm_set_pdf", "x", self.run.name))
		frappe.set_user("Administrator")
		for i in range(1, 12):
			self.assertEqual(html.count(f"<td>L{i:02d}</td>"), 1)
		for s in ("Bước 1", "Bước 3", "Chung cho cả dịch vụ", "Căn cứ", "Người xác nhận", HEAD):
			self.assertIn(s, html)

	# ---- nén ----
	def test_ho_so_nen_chay_nen_va_loi(self):
		frappe.set_user(FIN)
		with mock.patch("frappe.enqueue") as enq:
			out = api.export_bundle(self.run.name)
		self.assertTrue(out["queued"])
		self.assertEqual(enq.call_args.kwargs["queue"], "long")
		frappe.set_user("Administrator")
		url = api.build_bundle(self.run.name, FIN)
		f = frappe.get_doc("File", {"file_url": url})
		self.assertEqual(f.is_private, 1)
		self.assertEqual((f.attached_to_doctype, f.attached_to_name), ("NC Costing Run", self.run.name))
		names = zipfile.ZipFile(io.BytesIO(f.get_content())).namelist()
		for n in ("PL-II", "PL-III", "PL-IV", "PL-V"):
			self.assertIn(f"{n}-{self.run.name}.xlsx", names)
		self.assertEqual(len([n for n in names if n.startswith("giai-trinh-")]), 2)
		self.assertEqual(len([n for n in names if n.endswith(".pdf") and not n.startswith("giai-trinh")]), 2)
		self.assertIn("thong-tin-xuat.txt", names)
		ev = [e for e in self._events(self.run.name) if "Hồ sơ nén" in e["detail"]]
		self.assertEqual(len(ev), 1)
		# lỗi
		frappe.set_user("Administrator")
		with mock.patch("normcore.api.export.ANNEX_BUILDERS", {**api.ANNEX_BUILDERS, "annex_iii": mock.Mock(side_effect=RuntimeError("hỏng"))}):
			api.build_bundle(self.run.name, FIN)
		self.assertEqual(len([e for e in self._events(self.run.name) if "Hồ sơ nén" in e["detail"]]), 1)
		self.assertEqual(frappe.db.count("File", {"attached_to_name": self.run.name, "file_name": f"ho-so-{self.run.name}.zip"}), 1)
		self.assertTrue(frappe.db.exists("Error Log", {"method": ["like", f"%Xuất hồ sơ nén {self.run.name}%"]}))

	# ---- quyền ----
	def test_quyen_xuat_theo_vai_tro(self):
		self._export("annex_v", user=AUD, run=self.run.name)
		self._export("explanation_pdf", user=AUD, service_cost=self.cost_a)
		self._export("explanation_pdf", user=HEAD, service_cost=self.cost_a)
		frappe.set_user(CLIN)
		with self.assertRaises(frappe.PermissionError):
			api.export_file("annex_v", run=self.run.name)
		frappe.set_user(HEAD2)
		with self.assertRaises(frappe.PermissionError):
			api.export_file("explanation_pdf", service_cost=self.cost_a)
		frappe.set_user(FIN)
		with self.assertRaisesRegex(frappe.ValidationError, "Loại tệp không hợp lệ"):
			api.export_file("zzz", run=self.run.name)
		with self.assertRaisesRegex(frappe.ValidationError, "Chọn dịch vụ"):
			api.export_file("explanation_pdf")
		with self.assertRaisesRegex(frappe.ValidationError, "Chọn bộ định mức"):
			api.export_file("norm_set_pdf")
		frappe.set_user("Administrator")
		other = cf.make_golden_run(self.params, accounting_import=self.imp)
		frappe.set_user(FIN)
		with self.assertRaisesRegex(frappe.ValidationError, "Chỉ xuất hồ sơ từ lần tính giá đã khóa"):
			api.export_file("annex_v", run=other.name)
		opts = api.get_export_options(run=other.name)
		self.assertTrue(all(not o["enabled"] for o in opts["options"]))
		ok = api.get_export_options(run=self.run.name)
		self.assertTrue(all(o["enabled"] for o in ok["options"]))
		self.assertEqual(len(ok["service_costs"]), 2)
		self.assertEqual(len(ok["norm_sets"]), 2)
