"""FEAT-027: trích bảng giá PDF bằng AI. Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import json
import os
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import prompts, prompts_install
from normcore.ai.providers.base import ProviderError, ProviderTimeout
from normcore.api import benchmark as price_api
from normcore.api import benchmark_ai as api
from normcore.api.test_procedure_ai import FakeProvider, enable_ai
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_file
from normcore.tests.benchmark_utils import (
	CATEGORY,
	FACILITY,
	make_category,
	make_facility,
	make_price,
	make_service,
)
from normcore.tests.utils import make_user

HERE = os.path.dirname(__file__)
PDF = os.path.join(
	HERE, "..", "nc_benchmark", "doctype", "nc_benchmark_price", "test_files", "bang_gia_4_dong.pdf"
)
BLANK = os.path.join(
	HERE, "..", "nc_library", "doctype", "nc_legal_document", "test_files", "khong_lop_van_ban.pdf"
)
DT = "NC Benchmark Price"
LOG = "NC AI Log"
ROWS4 = [
	("Định lượng Glucose máu", 25000, 1),
	("Siêu âm ổ bụng tổng quát", "120.000", 1),
	("Chụp X-quang ngực thẳng", 90000, 2),
	("Đo điện tim thường", "40.000 đ", 2),
]


def reply(rows=ROWS4, date="2026-01-15"):
	return {
		"rows": [{"service_name": n, "price": p, "effective_date": date, "page": pg} for n, p, pg in rows]
	}


def read(path):
	with open(path, "rb") as f:
		return f.read()


class BenchAiBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		make_facility()
		make_category()
		make_service("AIP-DV-01", "Định lượng Glucose máu")
		self.finance = make_user("aip.fin@normcore.test", "NC Finance")
		self.consultant = make_user("aip.con@normcore.test", "NC Consultant")
		self.clin = make_user("aip.cli@normcore.test", "NC Clinician")
		self.auditor = make_user("aip.aud@normcore.test", "NC Auditor")
		enable_ai(1)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def upload(self, user=None, name="bang-gia-aip.pdf", content=None):
		frappe.set_user(user or self.finance)
		return make_legal_file(name, read(PDF) if content is None else content)

	def run_ai(self, provider, user=None, file_url=None, **kw):
		user = user or self.finance
		file_url = file_url or self.upload(user)
		frappe.set_user(user)
		args = {"facility": FACILITY, "price_category": CATEGORY, "file_url": file_url, "source_doc_no": "BG-1"}
		args.update(kw)
		with patch("normcore.ai.gateway.get_provider", return_value=provider):
			out = api.start_price_list_extraction(**args)
		return {**out, **api.get_price_list_extraction_status(out["job_id"])}

	def new_rows(self, before):
		return frappe.get_all(
			DT,
			{"facility": FACILITY, "name": ["not in", before or [""]]},
			[
				"name",
				"status",
				"ai_log",
				"price",
				"service_name_raw",
				"source_url",
				"source_file",
				"verified_by",
				"technical_service",
				"effective_date",
			],
			order_by="creation, name",
		)

	def existing(self):
		return frappe.get_all(DT, pluck="name")


class TestExtraction(BenchAiBase):
	def test_TC_BM_05_trich_bang_gia_pdf_de_xuat(self):
		before = self.existing()
		out = self.run_ai(FakeProvider(reply()))
		self.assertEqual(out["status"], "done", out)
		self.assertEqual(out["created"], 4)
		rows = self.new_rows(before)
		self.assertEqual(len(rows), 4)
		log = frappe.get_doc(LOG, out["log"])
		self.assertEqual(
			(log.purpose, log.status, log.ref_doctype, log.ref_name),
			("EXTRACT_PRICE_LIST", "Thành công", "NC Benchmark Facility", FACILITY),
		)
		for r in rows:
			self.assertEqual(r.status, "Đề xuất")
			self.assertEqual(r.ai_log, log.name)
			self.assertFalse(r.verified_by)
			self.assertIn("#page=", r.source_url)
			self.assertTrue(r.source_file)
		self.assertEqual({str(r.effective_date) for r in rows}, {"2026-01-15"})
		self.assertEqual(sorted(float(r.price) for r in rows), [25000, 40000, 90000, 120000])
		glu = next(r for r in rows if r.service_name_raw == "Định lượng Glucose máu")
		self.assertEqual(glu.technical_service, "AIP-DV-01")  # FR-BM-004 bằng quy tắc
		frappe.set_user(self.finance)
		cmp_rows = price_api.get_comparable_prices("AIP-DV-01")["rows"]
		self.assertFalse({r["name"] for r in cmp_rows} & {r.name for r in rows})

	def test_FR_AI_011_chi_gui_chu_cua_tep(self):
		prov = FakeProvider(reply())
		self.run_ai(prov)
		call = prov.calls[0]
		self.assertEqual(set(call["variables"]), {"facility_name", "file_name"})
		self.assertEqual(call["variables"]["file_name"], "bang-gia-aip.pdf")
		self.assertEqual([set(s) for s in call["sources"]], [{"page", "text"}] * 2)
		self.assertIn("Glucose", call["sources"][0]["text"])

	def test_FR_BM_003_bo_dong_khong_hop_le_va_trung(self):
		make_price(
			service_name_raw="Chụp X-quang ngực thẳng",
			technical_service=None,
			price=1,
			source_doc_no="x",
			effective_date="2026-01-15",
		)
		before = self.existing()
		data = reply(
			[
				("Định lượng Glucose máu", 25000, 1),
				("Siêu âm ổ bụng tổng quát", "abc", 1),
				("Nội soi dạ dày", 500000, 2),
				("Đo điện tim thường", 40000, 2),
				("Chụp X-quang ngực thẳng", 90000, 2),
			]
		)
		out = self.run_ai(FakeProvider(data))
		self.assertEqual(out["status"], "done", out)
		self.assertEqual(out["created"], 2)
		self.assertEqual(
			sorted(s["reason"] for s in out["skipped"]), ["Giá không hợp lệ", "Không thấy trong tệp"]
		)
		self.assertEqual(out["not_in_file"], 1)
		self.assertEqual(len(out["duplicates"]), 1)
		self.assertEqual(out["duplicates"][0]["service_name"], "Chụp X-quang ngực thẳng")
		self.assertEqual(len(self.new_rows(before)), 2)
		self.assertEqual(frappe.db.get_value(LOG, out["log"], "rejected_citations"), 1)

	def test_FR_AI_010_ai_loi_khong_tao_dong(self):
		for prov, status in [
			(FakeProvider(exc=ProviderTimeout("t")), "Quá hạn"),
			(FakeProvider(exc=ProviderError("lỗi")), "Lỗi"),
			(FakeProvider({"khac": 1}), "Lỗi"),
		]:
			before, logs = self.existing(), frappe.db.count(LOG)
			out = self.run_ai(prov)
			self.assertEqual(out["status"], "failed", out)
			self.assertIn("nhập tay", out["message"])
			self.assertEqual(self.existing(), before)
			self.assertEqual(frappe.db.count(LOG), logs + 1)
			self.assertEqual(frappe.db.get_value(LOG, out["log"], "status"), status)

	def test_FR_BM_003_tep_khong_hop_le(self):
		prov = FakeProvider(reply())
		bad_ext = self.upload(name="bang-gia.docx", content=b"x")
		with self.assertRaisesRegex(frappe.ValidationError, "Chỉ nhận tệp PDF"):
			api.start_price_list_extraction(FACILITY, CATEGORY, bad_ext, "BG")
		with self.assertRaisesRegex(frappe.ValidationError, "Không tìm thấy tệp"):
			api.start_price_list_extraction(FACILITY, CATEGORY, "/private/files/khong-co.pdf", "BG")
		good = self.upload(name="b2.pdf")
		with self.assertRaisesRegex(frappe.ValidationError, "Loại giá"):
			api.start_price_list_extraction(FACILITY, "KHONG-CO", good, "BG")
		with self.assertRaises(frappe.ValidationError):
			api.start_price_list_extraction(FACILITY, CATEGORY, good, "BG", "không phải ngày")
		logs = frappe.db.count(LOG)
		url = self.upload(name="trang.pdf", content=read(BLANK))  # không lớp văn bản
		with patch("normcore.library.extract.available_ocr", return_value=None):
			out = self.run_ai(prov, file_url=url)
		self.assertEqual(out["status"], "failed")
		self.assertIn("bộ nhận dạng", out["message"])
		with patch.object(api.px, "MAX_PAGES", 1):  # vượt giới hạn trang
			out = self.run_ai(prov)
		self.assertEqual(out["status"], "failed")
		self.assertIn("vượt 1 trang", out["message"])
		self.assertEqual(frappe.db.count(LOG), logs)
		self.assertEqual(prov.calls, [])


class TestPromptTemplate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def _reset_v1(self):
		for name in frappe.get_all("NC Prompt Template", {"template_code": "EXTRACT_PRICE_LIST"}, pluck="name"):
			frappe.db.sql("delete from `tabNC Prompt Template` where name=%s", name)
		prompts_install.ensure_default_templates()

	def test_FR_AI_014_mau_lenh_trich_bang_gia(self):
		self._reset_v1()
		self.assertEqual(prompts_install.ensure_extract_price_list_v2(), "EXTRACT_PRICE_LIST-v2")
		self.assertEqual(prompts_install.ensure_extract_price_list_v2(), "EXTRACT_PRICE_LIST-v2")
		self.assertEqual(
			frappe.get_all(
				"NC Prompt Template", {"template_code": "EXTRACT_PRICE_LIST"}, pluck="name", order_by="name"
			),
			["EXTRACT_PRICE_LIST-v1", "EXTRACT_PRICE_LIST-v2"],
		)
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "EXTRACT_PRICE_LIST-v1", "is_active"), 0)
		tpl = frappe.get_doc("NC Prompt Template", "EXTRACT_PRICE_LIST-v2")
		out = prompts.render(
			tpl.user_prompt, {"facility_name": "BV Mẫu", "file_name": "bg.pdf"}, [{"page": 1, "text": "Glucose"}]
		)
		self.assertIn("BV Mẫu", out)
		self.assertIn("Glucose", out)

	def test_FR_AI_014_mau_lenh_trich_bang_gia_khong_ghi_de_ban_admin(self):
		self._reset_v1()
		custom = frappe.get_doc(
			{
				"doctype": "NC Prompt Template",
				"template_code": "EXTRACT_PRICE_LIST",
				"is_active": 1,
				"system_prompt": "Lệnh do Admin sửa",
				"user_prompt": "Dữ liệu: {{ variables | tojson }}",
				"output_schema": '{"type": "object"}',
			}
		).insert(ignore_permissions=True)
		self.assertEqual(prompts_install.ensure_extract_price_list_v2(), custom.name)
		self.assertEqual(frappe.db.count("NC Prompt Template", {"template_code": "EXTRACT_PRICE_LIST"}), 2)
