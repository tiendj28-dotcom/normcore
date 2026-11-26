"""FEAT-024: AI soạn dự thảo quy trình. Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import json
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import gateway, prompts_install
from normcore.ai.providers.base import ProviderResponse
from normcore.nc_library.doctype.nc_legal_document.library_fixtures import make_legal_document
from normcore.tests.utils import make_base, make_procedure, make_user


class FakeProvider:
	def __init__(self, data=None, exc=None, text=None):
		self.data, self.exc, self.text, self.calls = data, exc, text, []

	def complete(self, purpose, template_code, variables, sources, *, system=None, user=None):
		self.calls.append({"variables": variables, "sources": sources, "user": user})
		if self.exc:
			raise self.exc
		text = self.text if self.text is not None else json.dumps(self.data, ensure_ascii=False)
		return ProviderResponse(text=text, tokens_in=3, tokens_out=2)


def enable_ai(on=1):
	s = frappe.get_doc("NC AI Settings")
	s.update(dict(enabled=on, protocol="Anthropic Messages", model="m", api_key="SK-T", timeout_seconds=30,
		max_output_tokens=1000, monthly_token_budget=0))
	s.save(ignore_permissions=True)


TEXTS = {
	"1": "Người bệnh nhịn ăn 6 giờ trước khi thực hiện thủ thuật.",
	"2": "Theo dõi mạch và huyết áp mỗi 15 phút sau thủ thuật.",
	"3": "Mục chỉ được đề xuất ánh xạ, chưa xác nhận.",
	"4": "Mục đã hết hiệu lực không được gửi cho AI.",
	"5": "Mục chọn thêm thuộc dịch vụ khác nhưng còn hiệu lực.",
}


def make_sections(service, other_service="DV-TEST-OTHER"):
	"""M1, M2 xác nhận + còn hiệu lực; M3 chỉ đề xuất; M4 hết hiệu lực; M5 dịch vụ khác. Trả dict số mục → tên."""
	if not frappe.db.exists("NC Technical Service", other_service):
		frappe.get_doc({"doctype": "NC Technical Service", "service_code": other_service,
			"service_name": "Dịch vụ khác", "is_active": 1}).insert(ignore_permissions=True)
	doc = make_legal_document("AI/24/QĐ", effective_date="2020-01-01")
	plan = {"1": (service, "Đã xác nhận", None), "2": (service, "Đã xác nhận", None),
		"3": (service, "Đề xuất", None), "4": (service, "Đã xác nhận", "2021-01-01"),
		"5": (other_service, "Đã xác nhận", None)}
	out = {}
	for no, (svc, status, expiry) in plan.items():
		sec = frappe.get_doc({"doctype": "NC Legal Section", "legal_document": doc.name, "section_no": no,
			"heading": f"Mục {no}", "plain_text": TEXTS[no], "expiry_date": expiry,
			"service_mappings": [{"technical_service": svc, "mapping_status": status}]})
		out[no] = sec.insert(ignore_permissions=True).name
	return out


class TestGatewayPostprocess(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		enable_ai()

	def tearDown(self):
		frappe.db.rollback()

	def _run(self, post, provider=None):
		return gateway.complete(
			"DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {}, [], provider=provider or FakeProvider({"a": 1}), postprocess=post
		)

	def test_FR_AI_005_gateway_postprocess(self):
		res = self._run(lambda d: (d, 2))
		self.assertTrue(res.ok)
		self.assertEqual(frappe.db.get_value("NC AI Log", res.log_name, "rejected_citations"), 2)
		res = self._run(lambda d: (_ for _ in ()).throw(ValueError("hỏng")))
		self.assertFalse(res.ok)
		self.assertEqual(frappe.db.get_value("NC AI Log", res.log_name, "status"), "Lỗi")
		res = self._run(None)
		self.assertTrue(res.ok)
		self.assertEqual(frappe.db.get_value("NC AI Log", res.log_name, "rejected_citations"), 0)


class TestPromptV2(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.db.rollback()

	def test_mau_lenh_draft_procedure_v2(self):
		prompts_install.ensure_default_templates()
		for name in frappe.get_all("NC Prompt Template", {"template_code": "DRAFT_PROCEDURE"}, pluck="name"):
			frappe.db.sql("delete from `tabNC Prompt Template` where name=%s", name)
		prompts_install.ensure_default_templates()
		self.assertEqual(prompts_install.ensure_draft_procedure_v2(), "DRAFT_PROCEDURE-v2")
		self.assertEqual(prompts_install.ensure_draft_procedure_v2(), "DRAFT_PROCEDURE-v2")
		self.assertEqual(
			frappe.get_all("NC Prompt Template", {"template_code": "DRAFT_PROCEDURE"}, pluck="name", order_by="name"),
			["DRAFT_PROCEDURE-v1", "DRAFT_PROCEDURE-v2"],
		)
		self.assertEqual(frappe.db.get_value("NC Prompt Template", "DRAFT_PROCEDURE-v1", "is_active"), 0)


class TestDI08(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _job = make_base()
		self.proc = make_procedure(self.service, self.dept)
		self.sec = make_sections(self.service)

	def tearDown(self):
		frappe.db.rollback()

	def _cite(self, legal_section, quote):
		doc = frappe.get_doc("NC Clinical Procedure", self.proc.name)
		doc.append("citations", {"target_section": "Đại cương", "relation": "Theo hướng dẫn",
			"legal_section": legal_section, "quote": quote})
		doc.save()

	def test_DI_08_doan_trich_nguyen_van(self):
		self.assertRaises(frappe.ValidationError, self._cite, self.sec["1"], "nhịn ăn 8 giờ")
		self._cite(self.sec["1"], "nhịn ăn 6 giờ, trước khi  thực hiện")  # khác khoảng trắng/dấu câu
		self._cite("Điều 5", "chữ tự do không bị kiểm")
