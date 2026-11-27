"""FEAT-038: AI đề xuất định mức từ tài liệu của hãng (FR-LIB-013, FR-AI-016..018, UC-025).

Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import json
from pathlib import Path
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import prompts, prompts_install
from normcore.ai.providers.base import ProviderError, ProviderTimeout
from normcore.api import access
from normcore.api import cls_norm_ai as api
from normcore.api import norm as norm_api
from normcore.api.test_procedure_ai import FakeProvider, enable_ai
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document
from normcore.tests.cls_norm_ai_fixtures import (
	QUOTE_A,
	QUOTE_B,
	make_manufacturer_doc,
)
from normcore.tests.utils import (
	ensure,
	make_base,
	make_cls_data,
	make_procedure,
	make_qc_items,
	make_qc_plan,
	make_test_system,
	make_user,
	publish_procedure,
)

ROOT = Path(__file__).resolve().parents[2]
DEPT = "XN-N38"
OTHER = "XN2-N38"
TEXT_B = f"2. Chuẩn máy. {QUOTE_B}. Nội kiểm hai lần mỗi ngày."


class ClsAiBase(FrappeTestCase):
	"""GLU-A (EQ_A), HC_GLU (đơn giá 6.000.000), sản lượng 12.000; tài liệu A gắn HC_GLU, tài liệu B gắn mặt hàng
	khác, một Thông tư; bộ định mức Nháp của GLU-A; AI bật."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _eqs = make_cls_data(department=DEPT)
		make_base(service="DV-N38-B", department=OTHER)
		make_qc_items()
		ensure(
			"NC Item",
			"item_code",
			"HC_KHAC",
			item_name="Hóa chất khác",
			item_type="Hóa chất",
			uom="ml",
			norm_units_per_purchase_unit=1,
		)
		make_test_system("GLU-A", self.service, self.dept, "EQ_A", 75)
		make_qc_plan("GLU-A")
		frappe.get_doc(
			{
				"doctype": "NC Item Price",
				"item": "HC_GLU",
				"unit_price": 6000000,
				"price_source": "Hợp đồng",
				"document_no": "HD-38",
				"document_date": "2026-01-01",
				"valid_from": "2026-01-01",
			}
		).insert(ignore_permissions=True)
		frappe.get_doc(
			{
				"doctype": "NC Test System Volume",
				"fiscal_year": 2026,
				"scenario": "Thực tế 12 tháng",
				"test_system": "GLU-A",
				"patient_results": 12000,
			}
		).insert(ignore_permissions=True)
		self.proc = make_procedure(self.service, self.dept, minutes=10)
		self.proc.append(
			"resources",
			{
				"step_id": self.proc.steps[0].step_id,
				"resource_type": "Hóa chất",
				"resource_text": "Hóa chất GLU",
				"linked_doctype": "NC Item",
				"linked_name": "HC_GLU",
				"quantity": 1,
				"uom": "test",
			},
		)
		self.proc.save(ignore_permissions=True)
		publish_procedure(self.proc)
		self.docA, self.secA = make_manufacturer_doc("HG-GLU-1.0", [("NC Item", "HC_GLU")])
		self.docB, self.secB = make_manufacturer_doc(
			"HG-KHAC-1.0", [("NC Item", "HC_KHAC")], section_text=TEXT_B
		)
		self.docT = make_legal_document("TT-38/2026", doc_type="Thông tư", is_procedure_guideline=0)
		self.secT = frappe.get_doc(
			{
				"doctype": "NC Legal Section",
				"legal_document": self.docT.name,
				"section_no": "1",
				"heading": "T",
				"plain_text": "Thông tư: dùng 9 ml mỗi test.",
			}
		).insert(ignore_permissions=True)
		self.head = make_user("head.n38@normcore.test", "NC Department Head")
		self.clin = make_user("clin.n38@normcore.test", "NC Clinician")
		self.clin_other = make_user("clin2.n38@normcore.test", "NC Clinician")
		self.fin = make_user("fin.n38@normcore.test", "NC Finance")
		self.res = make_user("res.n38@normcore.test", "NC Resource Manager")
		self.aud = make_user("aud.n38@normcore.test", "NC Auditor")
		self.council = make_user("council.n38@normcore.test", "NC Council Member")
		for u in (self.head, self.clin):
			access.assign_department(u, DEPT)
		access.assign_department(self.clin_other, OTHER)
		frappe.set_user(self.head)
		self.ns_name = norm_api.create_norm_set(self.proc.name, "GLU-A")["name"]
		frappe.set_user("Administrator")
		enable_ai(1)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	# ---- tiện ích
	def reply(self, *items):
		return {"suggestions": list(items)}

	def sug(self, kind="REAGENT_PER_TEST", code="HC_GLU", value=0.02, uom="ml", cites=None, text=None):
		return {
			"suggestion_type": kind,
			"item_code": code,
			"item_text": text or code,
			"value": value,
			"uom": uom,
			"citations": [{"section": self.secA.name, "quote": QUOTE_A}] if cites is None else cites,
		}

	def run_ai(self, provider, user=None, system="GLU-A"):
		frappe.set_user(user or self.head)
		with patch("normcore.ai.gateway.get_provider", return_value=provider):
			out = api.start_cls_norm_suggestion(system)
		if not out.get("job_id"):
			return out
		return {**out, **api.get_cls_norm_suggestion_status(out["job_id"])}

	def listed(self, status="Đề xuất", user=None):
		frappe.set_user(user or self.head)
		return api.list_cls_norm_suggestions("GLU-A", status)


class TestStartAndSources(ClsAiBase):
	def test_TC_CLS_41_noi_dung_gui_chi_gom_muc_da_gan(self):
		prov = FakeProvider(self.reply())
		out = self.run_ai(prov)
		self.assertEqual(out["status"], "done")
		self.assertEqual(len(prov.calls), 1)
		call = prov.calls[0]
		# chỉ mục của tài liệu của hãng đã gắn với HC_GLU của GLU-A
		self.assertEqual({s["name"] for s in call["sources"]}, {self.secA.name})
		for s in call["sources"]:
			self.assertEqual(set(s), {"name", "section_no", "heading", "plain_text"})
		v = call["variables"]
		self.assertEqual(set(v), {"service", "procedure", "items", "equipment"})
		self.assertEqual(v["procedure"]["name"], self.proc.name)  # bản "Đã ban hành"
		self.assertTrue(v["items"] and v["equipment"])
		for it in v["items"]:
			self.assertEqual(set(it), {"item_code", "item_name", "uom"})
		for eq in v["equipment"]:
			self.assertEqual(set(eq), {"equipment_code", "equipment_name"})
		self.assertIn("HC_GLU", {i["item_code"] for i in v["items"]})
		self.assertIn("EQ_A", {e["equipment_code"] for e in v["equipment"]})
		self.assertNotIn("HC_KHAC", {i["item_code"] for i in v["items"]})
		# không đơn giá, không sản lượng (NFR-SEC-005, FR-AI-011)
		blob = json.dumps(call, ensure_ascii=False)
		for banned in (
			"6000000",
			"6.000.000",
			"12000",
			"12.000",
			'"price"',
			'"unit_price"',
			'"volume"',
			'"result_count"',
		):
			self.assertNotIn(banned, blob)
		logs = frappe.get_all(
			"NC AI Log", {"ref_doctype": "NC Test System", "ref_name": "GLU-A"}, ["purpose", "status"]
		)
		self.assertEqual([(g.purpose, g.status) for g in logs], [("SUGGEST_CLS_NORM", "Thành công")])

	def test_FR_AI_016_khong_co_tai_lieu_khong_goi_ai(self):
		frappe.db.set_value("NC Legal Document", self.docA.name, "index_status", "Chưa lập")
		prov = FakeProvider(self.reply())
		out = self.run_ai(prov)
		self.assertIsNone(out["job_id"])
		self.assertIn("Chưa có tài liệu của hãng", out["message"])
		self.assertEqual(prov.calls, [])

	def test_FR_AI_016_he_thong_ngung_dung_va_quyen_bat_dau(self):
		frappe.db.set_value("NC Test System", "GLU-A", "status", "Ngừng dùng")
		with self.assertRaisesRegex(frappe.ValidationError, "ngừng dùng"):
			self.run_ai(FakeProvider(self.reply()))
		frappe.db.set_value("NC Test System", "GLU-A", "status", "Đang dùng")
		for user in (self.aud, self.council, self.clin_other, self.fin):
			with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
				self.run_ai(FakeProvider(self.reply()), user=user)


class TestSuggestions(ClsAiBase):
	def three(self):
		return self.reply(
			self.sug(),
			self.sug(
				kind="OPEN_STABILITY",
				value=28,
				uom="ngày",
				cites=[{"section": self.secA.name, "quote": "Hạn dùng sau mở là 28 ngày"}],
			),
			self.sug(
				kind="IQC_FREQ",
				code="QC_L",
				value=2,
				uom="lần",
				cites=[{"section": self.secA.name, "quote": "câu bịa không có trong tài liệu"}],
			),
		)

	def test_TC_CLS_42_trich_dan_va_nhan_de_xuat(self):
		out = self.run_ai(FakeProvider(self.three()))
		self.assertEqual(
			(out["status"], out["created"], out["unsupported"], out["rejected"]), ("done", 3, 1, 1)
		)
		rows = self.listed()["rows"]
		self.assertEqual(len(rows), 3)
		self.assertEqual({r["label"] for r in rows}, {"Đề xuất"})
		self.assertEqual({r["status"] for r in rows}, {"Đề xuất"})
		self.assertEqual(
			sorted(r["relation"] for r in rows), ["Chưa có căn cứ", "Theo hướng dẫn", "Theo hướng dẫn"]
		)
		wrong = next(r for r in rows if r["relation"] == "Chưa có căn cứ")
		self.assertEqual(wrong["suggestion_type"], "Tần suất nội kiểm")
		self.assertFalse(wrong["legal_section"] or wrong["quote"])
		for r in rows:
			if r["relation"] == "Theo hướng dẫn":
				self.assertEqual(r["legal_section"], self.secA.name)
				self.assertEqual(r["doc_number"], "HG-GLU-1.0")
				text = frappe.db.get_value("NC Legal Section", r["legal_section"], "plain_text")
				self.assertIn(r["quote"], text)
		log = frappe.get_all("NC AI Log", {"ref_name": "GLU-A"}, ["rejected_citations"])[0]
		self.assertEqual(log.rejected_citations, 1)

	def test_TC_CLS_42_trich_dan_ngoai_nguon_da_gui_bi_loai(self):
		# secB của tài liệu B không nằm trong nguồn đã gửi: trích dẫn tới nó bị loại
		data = self.reply(self.sug(cites=[{"section": self.secB.name, "quote": QUOTE_B}]))
		out = self.run_ai(FakeProvider(data))
		self.assertEqual((out["created"], out["unsupported"], out["rejected"]), (1, 1, 1))

	def _snapshot(self):
		ns = frappe.get_doc("NC Norm Set", self.ns_name)
		plan = frappe.get_doc("NC QC Plan", "KHCL-GLU-A")

		def clean(d):
			return {k: v for k, v in d.as_dict().items() if k != "modified"}

		return (
			[clean(r) for r in ns.lines],
			[clean(r) for r in plan.iqc_lines],
			[clean(r) for r in plan.calibration_lines],
			ns.status,
		)

	def test_TC_CLS_42_khong_vao_phep_tinh(self):
		before = self._snapshot()
		self.run_ai(FakeProvider(self.three()))
		self.assertEqual(self._snapshot(), before)
		self.assertEqual(frappe.db.get_value("NC Item", "HC_GLU", "open_stability_days"), 0)
		# không mã tính giá nào đọc DocType đề xuất (FR-AI-008)
		files = list((ROOT / "normcore/costing").rglob("*.py")) + list(
			(ROOT / "normcore/nc_costing/doctype/nc_costing_run").rglob("*.py")
		)
		self.assertTrue(files)
		for f in files:
			self.assertNotIn("NC AI Norm Suggestion", f.read_text(encoding="utf-8"), str(f))

	def test_UC025_3c_ai_loi_giu_nguyen(self):
		self.run_ai(FakeProvider(self.reply(self.sug())))
		before = self.listed()["rows"]
		snap = self._snapshot()
		for exc in (ProviderError("hỏng"), ProviderTimeout("quá hạn")):
			out = self.run_ai(FakeProvider(exc=exc))
			self.assertEqual(out["status"], "failed")
			self.assertTrue(out["message"])
			self.assertEqual(self.listed()["rows"], before)
			self.assertEqual(self._snapshot(), snap)
			self.assertEqual(frappe.db.count("NC AI Norm Suggestion", {"status": "Đã bỏ"}), 0)
		statuses = frappe.get_all("NC AI Log", {"ref_name": "GLU-A"}, pluck="status")
		self.assertCountEqual(statuses, ["Thành công", "Lỗi", "Quá hạn"])

	def test_FR_AI_017_dau_ra_khong_co_de_xuat_khong_loi(self):
		out = self.run_ai(FakeProvider({"mock": True}))  # staging dùng provider mock
		self.assertEqual((out["status"], out["created"]), ("done", 0))

	def test_FR_AI_017_bo_va_chay_lai(self):
		self.run_ai(FakeProvider(self.reply(self.sug())))
		first = [r["name"] for r in self.listed()["rows"]]
		self.run_ai(FakeProvider(self.reply(self.sug(value=0.03))))
		pending = self.listed()["rows"]
		self.assertEqual(len(pending), 1)
		self.assertNotIn(pending[0]["name"], first)
		self.assertEqual(frappe.db.get_value("NC AI Norm Suggestion", first[0], "status"), "Đã bỏ")
		self.assertEqual(len(self.listed("Tất cả")["rows"]), 2)
		self.assertEqual(self.listed()["pending"], 1)

	def test_FR_AI_016_xem_theo_quyen(self):
		self.run_ai(FakeProvider(self.reply(self.sug())))
		for user in (self.aud, self.fin, self.res, self.head, self.clin):
			self.assertEqual(len(self.listed(user=user)["rows"]), 1, user)
		self.assertFalse(self.listed(user=self.aud)["can_edit"])
		self.assertTrue(self.listed(user=self.head)["can_edit"])
		self.assertTrue(self.listed(user=self.head)["ai_enabled"])
		for user in (self.council, self.clin_other):
			with self.subTest(user=user), self.assertRaises(frappe.PermissionError):
				self.listed(user=user)

	def test_trang_thai_cong_viec_khac_nguoi_tao(self):
		out = self.run_ai(FakeProvider(self.reply()))
		frappe.set_user(self.fin)
		with self.assertRaises(frappe.PermissionError):
			api.get_cls_norm_suggestion_status(out["job_id"])
		self.assertEqual(api.get_cls_norm_suggestion_status("khong-co")["status"], "unknown")


class TestAccept(ClsAiBase):
	def make(self, *items, user=None):
		self.run_ai(FakeProvider(self.reply(*items)), user=user)
		return {(r["suggestion_type"], r["resource_text"]): r["name"] for r in self.listed(user=user)["rows"]}

	def one(self, **kw):
		return next(iter(self.make(self.sug(**kw)).values()))

	def line(self, resource="HC_GLU"):
		ns = frappe.get_doc("NC Norm Set", self.ns_name)
		return [r for r in ns.lines if r.resource == resource]

	def as_user(self, user, fn, *a):
		frappe.set_user(user)
		return fn(*a)

	def test_TC_CLS_43_mat_hang_ngoai_danh_muc(self):
		items_before = (frappe.db.count("NC Item"), frappe.db.count("NC Equipment"))
		name = self.one(code="HC_KHONG_CO", text="Hóa chất X")
		self.assertEqual((frappe.db.count("NC Item"), frappe.db.count("NC Equipment")), items_before)
		row = self.listed()["rows"][0]
		self.assertEqual(
			(row["not_in_catalog"], row["resource"], row["resource_text"], row["can_accept"]),
			(1, None, "Hóa chất X", False),
		)
		frappe.set_user(self.head)
		with self.assertRaisesRegex(frappe.ValidationError, "Liên kết mặt hàng"):
			api.accept_cls_norm_suggestion(name)
		self.assertEqual(frappe.db.get_value("NC AI Norm Suggestion", name, "status"), "Đề xuất")
		# liên kết thủ công: loại sai, bản ghi không tồn tại
		with self.assertRaises(frappe.ValidationError):
			api.link_cls_norm_suggestion(name, "NC Room", "P1")
		with self.assertRaises(frappe.ValidationError):
			api.link_cls_norm_suggestion(name, "NC Item", "KHONG_CO")
		linked = api.link_cls_norm_suggestion(name, "NC Item", "HC_GLU")
		self.assertEqual(
			(linked["resource"], linked["not_in_catalog"], linked["can_accept"]), ("HC_GLU", 0, True)
		)
		self.assertEqual(frappe.db.get_value("NC AI Norm Suggestion", name, "resource_text"), "Hóa chất X")
		self.assertEqual(api.accept_cls_norm_suggestion(name)["status"], "Đã chấp nhận")
		self.assertEqual((frappe.db.count("NC Item"), frappe.db.count("NC Equipment")), items_before)

	def test_FR_AI_016_chap_nhan_luong_hoa_chat(self):
		row = self.line()[0]
		frappe.db.set_value(
			"NC Norm Line", row.name, {"confirmed_by": "Administrator", "confirmed_on": frappe.utils.now()}
		)
		name = self.one(value=0.025)
		frappe.set_user(self.head)
		out = api.accept_cls_norm_suggestion(name)
		self.assertEqual(
			(out["status"], out["norm_set"], out["applied_ref"]), ("Đã chấp nhận", self.ns_name, row.line_id)
		)
		after = self.line()[0]
		self.assertEqual((after.hospital_qty, after.basis), (0.025, "Ước tính"))
		self.assertIn("HG-GLU-1.0", after.basis_ref)
		self.assertFalse(after.confirmed_by)  # đổi lượng phải xác nhận lại
		sug = frappe.get_doc("NC AI Norm Suggestion", name)
		self.assertEqual(
			(sug.status, sug.processed_by, sug.applied_ref), ("Đã chấp nhận", self.head, row.line_id)
		)
		self.assertEqual(self.listed()["pending"], 0)
		# hóa chất chưa có dòng trong bộ: thêm dòng chung
		name = self.one(code="HC_KHAC", value=5)
		frappe.set_user(self.head)
		out = api.accept_cls_norm_suggestion(name)
		new = self.line("HC_KHAC")[0]
		self.assertEqual(
			(new.line_id, new.service_level, new.component, new.cost_level, new.hospital_qty, new.uom),
			(out["applied_ref"], 1, "DRUG", "RESULT", 5, "ml"),
		)

	def test_FR_AI_016_chap_nhan_khong_ap_duoc_giu_de_xuat(self):
		name = self.one()
		frappe.db.set_value("NC Norm Set", self.ns_name, "status", "Đã xác nhận chuyên môn")
		frappe.set_user(self.head)
		with self.assertRaisesRegex(frappe.ValidationError, "Chưa có bộ định mức Nháp cho hệ thống GLU-A"):
			api.accept_cls_norm_suggestion(name)
		self.assertEqual(frappe.db.get_value("NC AI Norm Suggestion", name, "status"), "Đề xuất")
		frappe.db.set_value("NC Norm Set", self.ns_name, "status", "Nháp")
		eq = self.one(code="EQ_A")
		frappe.set_user(self.head)
		with self.assertRaisesRegex(frappe.ValidationError, "chỉ áp cho hóa chất"):
			api.accept_cls_norm_suggestion(eq)
		cal = self.one(kind="CALIBRATION_FREQ", code="HC_GLU", value=4)
		frappe.set_user(self.head)
		with self.assertRaisesRegex(frappe.ValidationError, "chưa có dòng chuẩn máy cho HC_GLU"):
			api.accept_cls_norm_suggestion(cal)
		iqc = self.one(kind="IQC_FREQ", code="HC_GLU", value=2)
		frappe.set_user(self.head)
		with self.assertRaisesRegex(frappe.ValidationError, "chưa có dòng nội kiểm cho HC_GLU"):
			api.accept_cls_norm_suggestion(iqc)
		# lần chạy mới đổi đề xuất chờ cũ sang "Đã bỏ" (ASM-038-11); đề xuất lỗi không đổi trạng thái
		self.assertEqual(frappe.db.get_value("NC AI Norm Suggestion", iqc, "status"), "Đề xuất")

	def test_FR_AI_016_chap_nhan_ke_hoach_va_han_dung(self):
		names = self.make(
			self.sug(kind="CALIBRATION_FREQ", code="CAL", value=4, uom="lần"),
			self.sug(kind="IQC_FREQ", code="QC_L", value=2, uom="lần"),
			self.sug(kind="OPEN_STABILITY", value=27.6, uom="ngày"),
		)
		cal, iqc, opn = (
			names[("Tần suất chuẩn máy", "CAL")],
			names[("Tần suất nội kiểm", "QC_L")],
			names[("Hạn dùng sau mở", "HC_GLU")],
		)
		frappe.set_user(self.head)
		self.assertEqual(api.accept_cls_norm_suggestion(cal)["status"], "Đã chấp nhận")
		self.assertEqual(api.accept_cls_norm_suggestion(iqc)["status"], "Đã chấp nhận")
		plan = frappe.get_doc("NC QC Plan", "KHCL-GLU-A")
		self.assertEqual(plan.calibration_lines[0].calibrations_per_year, 4)
		self.assertEqual(plan.iqc_lines[0].runs_per_day, 2)
		self.assertEqual(
			frappe.db.get_value("NC AI Norm Suggestion", cal, "applied_ref"), plan.calibration_lines[0].name
		)
		# hạn dùng sau mở: Clinician, Dept Head không có quyền ghi NC Item
		for user in (self.head, self.clin):
			frappe.set_user(user)
			with self.assertRaisesRegex(frappe.PermissionError, "Quản lý nguồn lực hoặc Tài chính"):
				api.accept_cls_norm_suggestion(opn)
		frappe.set_user(self.res)
		res = api.list_cls_norm_suggestions("GLU-A")
		self.assertEqual(
			[(r["suggestion_type"], r["can_accept"]) for r in res["rows"]], [("Hạn dùng sau mở", True)]
		)
		self.assertFalse(res["can_edit"])
		self.assertEqual(api.accept_cls_norm_suggestion(opn)["status"], "Đã chấp nhận")
		self.assertEqual(frappe.db.get_value("NC Item", "HC_GLU", "open_stability_days"), 28)
		self.assertEqual(frappe.db.get_value("NC AI Norm Suggestion", opn, "processed_by"), self.res)

	def test_FR_AI_017_bo_va_xu_ly_lan_hai(self):
		before = frappe.get_doc("NC Norm Set", self.ns_name).as_dict()["lines"]
		name = self.one()
		frappe.set_user(self.head)
		self.assertEqual(api.reject_cls_norm_suggestion(name)["status"], "Đã bỏ")
		for fn in (api.reject_cls_norm_suggestion, api.accept_cls_norm_suggestion):
			with self.assertRaisesRegex(frappe.ValidationError, "đã được xử lý"):
				fn(name)
		self.assertEqual(frappe.get_doc("NC Norm Set", self.ns_name).as_dict()["lines"], before)
		self.assertEqual(self.listed()["pending"], 0)
		self.assertEqual(len(self.listed("Đã bỏ")["rows"]), 1)

	def test_FR_AI_008_ai_tat_van_xu_ly(self):
		a, b = self.make(self.sug(), self.sug(kind="OPEN_STABILITY", value=28)).values()
		enable_ai(0)
		frappe.set_user(self.head)
		with self.assertRaisesRegex(frappe.ValidationError, "AI đang tắt"):
			api.start_cls_norm_suggestion("GLU-A")
		res = api.list_cls_norm_suggestions("GLU-A")
		self.assertEqual((len(res["rows"]), res["ai_enabled"]), (2, False))
		self.assertEqual(api.reject_cls_norm_suggestion(b)["status"], "Đã bỏ")
		self.assertEqual(api.accept_cls_norm_suggestion(a)["status"], "Đã chấp nhận")

	def test_quyen_nc_ai_norm_suggestion(self):
		name = self.one()
		meta = frappe.get_meta("NC AI Norm Suggestion")
		self.assertFalse(meta.istable)
		# NC Auditor: đọc được, mọi API ghi bị từ chối
		for fn, args in (
			(api.accept_cls_norm_suggestion, (name,)),
			(api.reject_cls_norm_suggestion, (name,)),
			(api.link_cls_norm_suggestion, (name, "NC Item", "HC_GLU")),
		):
			for user in (self.aud, self.council, self.clin_other, self.fin):
				frappe.set_user(user)
				with self.subTest(fn=fn.__name__, user=user), self.assertRaises(frappe.PermissionError):
					fn(*args)
		self.assertEqual(frappe.db.get_value("NC AI Norm Suggestion", name, "status"), "Đề xuất")
		frappe.set_user(self.aud)
		self.assertTrue(frappe.has_permission("NC AI Norm Suggestion", "read", doc=name))
		self.assertFalse(frappe.has_permission("NC AI Norm Suggestion", "write", doc=name))
		self.assertFalse(frappe.has_permission("NC AI Norm Suggestion", "create"))
		# Finance đọc được, không bỏ được
		frappe.set_user(self.fin)
		self.assertTrue(frappe.has_permission("NC AI Norm Suggestion", "read", doc=name))
		# Council, Clinician khoa khác không đọc được
		for user in (self.council, self.clin_other):
			frappe.set_user(user)
			self.assertFalse(frappe.has_permission("NC AI Norm Suggestion", "read", doc=name), user)
		# không ai xóa (kể cả quản trị vai trò)
		frappe.set_user(self.head)
		self.assertFalse(frappe.has_permission("NC AI Norm Suggestion", "delete", doc=name))


class TestPromptTemplate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def _reset_v1(self):
		for name in frappe.get_all("NC Prompt Template", {"template_code": "SUGGEST_CLS_NORM"}, pluck="name"):
			frappe.db.sql("delete from `tabNC Prompt Template` where name=%s", name)
		prompts_install.ensure_default_templates()

	def test_mau_lenh_suggest_cls_norm_v2(self):
		self._reset_v1()
		self.assertEqual(prompts_install.ensure_suggest_cls_norm_v2(), "SUGGEST_CLS_NORM-v2")
		self.assertEqual(prompts_install.ensure_suggest_cls_norm_v2(), "SUGGEST_CLS_NORM-v2")
		self.assertEqual(
			frappe.get_all(
				"NC Prompt Template", {"template_code": "SUGGEST_CLS_NORM"}, pluck="name", order_by="name"
			),
			["SUGGEST_CLS_NORM-v1", "SUGGEST_CLS_NORM-v2"],
		)
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "SUGGEST_CLS_NORM-v1", "is_active"), 0)
		tpl = frappe.get_doc("NC Prompt Template", "SUGGEST_CLS_NORM-v2")
		out = prompts.render(
			tpl.user_prompt,
			{"service": {"service_code": "GLU"}, "procedure": None, "items": [], "equipment": []},
			[{"name": "LS-1"}],
		)
		self.assertIn("LS-1", out)

	def test_mau_lenh_suggest_cls_norm_v2_khong_cai_khi_admin_da_doi(self):
		self._reset_v1()
		# Admin đã tạo phiên bản mới của riêng mình: không cài đè
		custom = frappe.get_doc(
			{
				"doctype": "NC Prompt Template",
				"template_code": "SUGGEST_CLS_NORM",
				"is_active": 1,
				"system_prompt": "Lệnh do Admin sửa",
				"user_prompt": "Dữ liệu: {{ variables | tojson }}",
				"output_schema": '{"type": "object"}',
			}
		).insert(ignore_permissions=True)
		self.assertEqual(prompts_install.ensure_suggest_cls_norm_v2(), custom.name)
		self.assertEqual(frappe.db.count("NC Prompt Template", {"template_code": "SUGGEST_CLS_NORM"}), 2)
