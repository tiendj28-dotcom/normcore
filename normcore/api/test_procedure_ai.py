"""FEAT-024: AI soạn dự thảo quy trình. Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import json
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.ai import gateway, prompts_install
from normcore.ai.providers.base import ProviderTimeout
from normcore.api import access
from normcore.api import procedure as api
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


SECTION_KEYS = ("overview", "indications", "contraindications", "cautions", "preparation_notes", "monitoring", "references")
Q1 = "nhịn ăn 6 giờ trước khi thực hiện"
Q2 = "Theo dõi mạch và huyết áp mỗi 15 phút"


def ai_json(secs, n=5, bad=None, deviation=None):
	"""Dự thảo n bước; mỗi phần/bước trích M1 hoặc M2. `bad`: chỉ số bước trích sai; `deviation`: (chỉ số, excerpt)."""
	cits = lambda: [{"section": secs["1"], "quote": Q1, "relation": "Theo hướng dẫn"}]  # noqa: E731
	steps = []
	for i in range(n):
		c = cits()
		if i == bad:
			c = [{"section": secs["1"], "quote": "đoạn không hề có trong mục", "relation": "Theo hướng dẫn"}]
		if deviation and i == deviation[0]:
			c = [{"section": secs["2"], "quote": Q2, "relation": "Khác biệt", "request_excerpt": deviation[1]}]
		steps.append({"phase": "Thực hiện", "step_title": f"Bước {i + 1}", "description": f"Mô tả {i + 1}",
			"reference_minutes": 5, "citations": c,
			"resources": [{"resource_type": "Vật tư", "resource_text": "Bơm tiêm", "quantity": 1, "uom": "cái"}]})
	return {"sections": {k: {"text": f"Nội dung {k}", "citations": [{"section": secs["2"], "quote": Q2,
		"relation": "Theo hướng dẫn"}]} for k in SECTION_KEYS}, "steps": steps}


class AIDraftBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		enable_ai()
		self.service, self.dept, _job = make_base()
		self.sec = make_sections(self.service)
		self.clin = make_user("clin.ai@normcore.test", "NC Clinician")
		access.assign_department(self.clin, self.dept)
		self.auditor = make_user("aud.ai@normcore.test", "NC Auditor")
		self.finance = make_user("fin.ai@normcore.test", "NC Finance")
		frappe.set_user(self.clin)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def run_draft(self, provider, request="Yêu cầu soạn thảo", service=None, **kw):
		with patch("normcore.ai.gateway.get_provider", return_value=provider):
			job = api.start_ai_draft(service or self.service, self.dept, request, **kw)
		return api.get_ai_draft_status(job["job_id"])

	def draft(self, name):
		return frappe.get_doc("NC Clinical Procedure", name)


class TestAIDraft(AIDraftBase):
	def test_TC_AI_01_du_thao_5_buoc_co_trich_dan(self):
		prov = FakeProvider(ai_json(self.sec))
		st = self.run_draft(prov, "Dùng gói vô khuẩn")
		self.assertEqual(st["status"], "done", st)
		doc = self.draft(st["procedure"])
		self.assertEqual((doc.version_no, doc.workflow_state, doc.doctor_request), (1, "Nháp", "Dùng gói vô khuẩn"))
		self.assertEqual([s.step_id for s in doc.steps], ["S001", "S002", "S003", "S004", "S005"])
		self.assertTrue(all(s.ai_suggested for s in doc.steps))
		self.assertEqual(len(doc.resources), 5)
		self.assertEqual([r.step_id for r in doc.resources], [s.step_id for s in doc.steps])
		self.assertTrue(all(getattr(doc, k) for k in SECTION_KEYS))
		by_target = {}
		for c in doc.citations:
			by_target.setdefault(c.target_step_id or c.target_section, []).append(c)
		self.assertEqual(len(by_target), 7 + 5)
		for rows in by_target.values():
			self.assertTrue(all(c.relation == "Theo hướng dẫn" and c.legal_section in (self.sec["1"], self.sec["2"])
				for c in rows))
		sent = {s["name"] for s in prov.calls[0]["sources"]}
		self.assertEqual(sent, {self.sec["1"], self.sec["2"]})
		log = frappe.get_doc("NC AI Log", doc.ai_log)
		self.assertEqual((log.status, log.rejected_citations), ("Thành công", 0))
		self.assertIn(self.sec["1"], log.source_sections)
		for no in ("3", "4", "5"):
			self.assertNotIn(self.sec[no], log.source_sections)

	def test_TC_AI_02_nhat_ky_ghi_trich_dan_bi_loai(self):
		st = self.run_draft(FakeProvider(ai_json(self.sec, bad=1)))
		doc = self.draft(st["procedure"])
		rows = [c for c in doc.citations if c.target_step_id == "S002"]
		self.assertEqual([c.relation for c in rows], ["Chưa có căn cứ"])
		self.assertFalse(any("không hề có" in (c.quote or "") for c in doc.citations))
		self.assertEqual(frappe.db.get_value("NC AI Log", doc.ai_log, "rejected_citations"), 1)
		self.assertEqual(st["rejected"], 1)

	def test_TC_AI_03_khac_biet_lay_ly_do_tu_yeu_cau(self):
		req = "Khoa dùng máy siêu âm cầm tay thay máy siêu âm tại giường"
		st = self.run_draft(FakeProvider(ai_json(self.sec, deviation=(2, "dùng máy siêu âm cầm tay"))), req)
		doc = self.draft(st["procedure"])
		c = next(c for c in doc.citations if c.target_step_id == "S003")
		self.assertEqual((c.relation, c.deviation_reason), ("Khác biệt", "dùng máy siêu âm cầm tay"))
		st = self.run_draft_fresh(FakeProvider(ai_json(self.sec, deviation=(2, "không có trong yêu cầu"))), req)
		c = next(c for c in self.draft(st["procedure"]).citations if c.target_step_id == "S003")
		self.assertEqual(c.deviation_reason, req)
		api.update_citation(st["procedure"], c.name, deviation_reason="Lý do đã sửa")
		self.assertEqual(frappe.db.get_value("NC Procedure Citation", c.name, "deviation_reason"), "Lý do đã sửa")

	def run_draft_fresh(self, provider, request):
		frappe.db.delete("NC Clinical Procedure", {"technical_service": self.service})
		return self.run_draft(provider, request)

	def test_TC_AI_04_khong_co_nguon_canh_bao_roi_chua_co_can_cu(self):
		svc = "DV-TEST-NOSRC"
		frappe.set_user("Administrator")
		frappe.get_doc({"doctype": "NC Technical Service", "service_code": svc, "service_name": "Không nguồn",
			"is_active": 1}).insert(ignore_permissions=True)
		frappe.set_user(self.clin)
		self.assertTrue(api.prepare_ai_draft(svc, self.dept)["no_sources"])
		logs = frappe.db.count("NC AI Log")
		prov = FakeProvider(ai_json(self.sec))
		with patch("normcore.ai.gateway.get_provider", return_value=prov):
			self.assertRaises(api.NoSourceError, api.start_ai_draft, svc, self.dept, "yc")
		self.assertEqual(frappe.db.count("NC AI Log"), logs)
		self.assertFalse(frappe.db.exists("NC Clinical Procedure", {"technical_service": svc}))
		st = self.run_draft(prov, service=svc, confirm_no_source=1)
		self.assertEqual(st["status"], "done", st)
		self.assertEqual(prov.calls[0]["sources"], [])
		doc = self.draft(st["procedure"])
		self.assertEqual({c.relation for c in doc.citations}, {"Chưa có căn cứ"})
		self.assertEqual(len(doc.citations), 7 + 5)

	def test_UC004_1a_ai_tat_soan_tay(self):
		frappe.set_user("Administrator")
		enable_ai(0)
		frappe.set_user(self.clin)
		self.assertFalse(api.prepare_ai_draft(self.service, self.dept)["ai_enabled"])
		logs = frappe.db.count("NC AI Log")
		with patch("normcore.ai.gateway.get_provider", return_value=FakeProvider({})):
			self.assertRaises(frappe.ValidationError, api.start_ai_draft, self.service, self.dept, "yc")
		self.assertEqual(frappe.db.count("NC AI Log"), logs)
		name = api.create_procedure(self.service, self.dept)["name"]
		self.assertEqual(len(api.get_procedure(name)["sections"]), 8)

	def test_UC004_1b_da_co_ban_nhap(self):
		existing = api.create_procedure(self.service, self.dept)["name"]
		self.assertEqual(api.prepare_ai_draft(self.service, self.dept)["existing"], existing)
		with patch("normcore.ai.gateway.get_provider", return_value=FakeProvider(ai_json(self.sec))):
			with self.assertRaises(api.ExistingProcedureError) as cm:
				api.start_ai_draft(self.service, self.dept, "yc")
		self.assertEqual(cm.exception.existing, existing)

	def test_UC004_1b_ban_nhap_xuat_hien_giua_luc_job_chay(self):
		other = {}

		class Racing(FakeProvider):
			def complete(inner, *a, **k):
				other["name"] = frappe.get_doc({"doctype": "NC Clinical Procedure", "technical_service": self.service,
					"department": self.dept, "version_no": 1}).insert().name
				return super().complete(*a, **k)

		st = self.run_draft(Racing(ai_json(self.sec)))
		self.assertEqual(st["status"], "failed")
		self.assertIn(other["name"], st["error"])
		self.assertEqual(frappe.db.count("NC Clinical Procedure", {"technical_service": self.service}), 1)

	def test_UC004_4a_ai_loi_khong_tao_ban_nhap(self):
		for prov, status in ((FakeProvider(exc=ProviderTimeout("hết giờ")), "Quá hạn"),
				(FakeProvider({"sections": {}}), "Lỗi")):
			st = self.run_draft(prov, "Yêu cầu giữ lại")
			self.assertEqual(st["status"], "failed", st)
			self.assertFalse(frappe.db.exists("NC Clinical Procedure", {"technical_service": self.service}))
			self.assertEqual(frappe.db.get_value("NC AI Log", st["log"], "status"), status)
		st = self.run_draft(FakeProvider(ai_json(self.sec)), "Yêu cầu giữ lại")  # thử lại với cùng tham số
		self.assertEqual(st["status"], "done")
		frappe.db.delete("NC Clinical Procedure", {"technical_service": self.service})
		name = api.create_procedure(self.service, self.dept, doctor_request="Yêu cầu giữ lại")["name"]
		self.assertEqual(self.draft(name).doctor_request, "Yêu cầu giữ lại")

	def test_FR_AI_001_nguon_chon_them_va_quy_trinh_hien_hanh(self):
		frappe.set_user("Administrator")
		cur = make_procedure(self.service, self.dept)
		from normcore.tests.utils import publish_procedure

		publish_procedure(cur, "QĐ-AI", "2026-12-01")
		frappe.db.delete("NC Clinical Procedure", {"name": ["!=", cur.name]})
		frappe.set_user(self.clin)
		self.assertEqual(api.prepare_ai_draft(self.service, self.dept)["current_procedure"]["name"], cur.name)
		with patch("normcore.ai.gateway.get_provider", return_value=FakeProvider({})):
			self.assertRaises(frappe.ValidationError, api.start_ai_draft, self.service, self.dept, "yc",
				extra_sections=json.dumps([self.sec["4"]]))
		prov = FakeProvider(ai_json(self.sec))
		frappe.db.delete("NC Clinical Procedure", {"name": cur.name})
		st = self.run_draft(prov, extra_sections=[self.sec["5"]])
		self.assertEqual(st["status"], "done", st)
		names = {s["name"] for s in prov.calls[0]["sources"]}
		self.assertEqual(names, {self.sec[k] for k in ("1", "2", "5")})
		for src in prov.calls[0]["sources"]:
			self.assertEqual(set(src), {"name", "section_no", "heading", "plain_text"})
		self.assertIn("current_procedure", prov.calls[0]["variables"])


class TestAISuggestions(AIDraftBase):
	def make_ai_draft(self):
		st = self.run_draft(FakeProvider(ai_json(self.sec)))
		self.assertEqual(st["status"], "done", st)
		return st["procedure"]

	def test_TC_AI_10_con_de_xuat_tu_choi_gui_duyet(self):
		from normcore.api import procedure_workflow as wf

		name = self.make_ai_draft()
		doc = self.draft(name)
		rows = [r.resource_row_id for r in doc.resources]
		out = api.accept_suggestions(name, step_ids=["S001", "S002", "S004", "S005"], resource_row_ids=rows)
		self.assertEqual(out["remaining"], 1)
		with self.assertRaises(frappe.ValidationError) as cm:
			wf.apply_action(name, "Gửi duyệt")
		self.assertIn("Bước S003 còn là đề xuất AI chưa xử lý", str(cm.exception))
		self.assertEqual(self.draft(name).workflow_state, "Nháp")
		api.accept_suggestions(name, step_ids=["S003"])
		self.assertEqual(wf.apply_action(name, "Gửi duyệt")["workflow_state"], "Chờ trưởng khoa duyệt")

	def test_TC_AI_10_bo_de_xuat(self):
		name = self.make_ai_draft()
		out = api.reject_suggestion(name, "S003")
		self.assertEqual(out, {"deleted": "S003", "resources": 1, "citations": 1})
		doc = self.draft(name)
		self.assertNotIn("S003", [s.step_id for s in doc.steps])
		self.assertFalse([c for c in doc.citations if c.target_step_id == "S003"])
		self.assertFalse([r for r in doc.resources if r.step_id == "S003"])
		new = api.add_step(name, "Thực hiện", "Bước mới", "Mô tả")
		self.assertEqual(new["step_id"], "S006")  # mã không tái dùng
		api.accept_suggestions(name, step_ids=["S001"])
		self.assertRaises(frappe.ValidationError, api.reject_suggestion, name, "S001")
		self.assertRaises(frappe.ValidationError, api.accept_suggestions, name, step_ids=["S999"])
		out = api.accept_suggestions(name, all=1)
		self.assertEqual(out["remaining"], 0)

	def test_get_procedure_tra_de_xuat_quan_he_va_nhan(self):
		name = self.make_ai_draft()
		data = api.get_procedure(name)
		self.assertTrue(all(s["ai_suggested"] for s in data["steps"]))
		self.assertTrue(all(r["ai_suggested"] for r in data["resources"]))
		self.assertEqual(data["relations"]["step:S001"], ["Theo hướng dẫn"])
		self.assertEqual(data["ai_log"], self.draft(name).ai_log)
		self.assertTrue(data["citations"][0]["section_label"].startswith("AI/24/QĐ — "))

	def test_quyen_ai_draft(self):
		name = self.make_ai_draft()
		call = lambda f, *a, **k: self.assertRaises(frappe.PermissionError, f, *a, **k)  # noqa: E731
		for user in (self.auditor, self.finance):
			frappe.set_user(user)
			call(api.prepare_ai_draft, self.service, self.dept)
			call(api.start_ai_draft, self.service, self.dept, "yc")
			call(api.accept_suggestions, name, all=1)
			call(api.reject_suggestion, name, "S001")
		frappe.set_user("Administrator")
		other = make_base(service="DV-TEST-B", department="KHOA-KHAC-AI")[1]
		frappe.set_user(self.clin)
		with patch("normcore.ai.gateway.get_provider", return_value=FakeProvider({})):
			call(api.start_ai_draft, self.service, other, "yc")
		st_job = frappe.generate_hash(length=16)
		frappe.cache().set_value(api.AI_JOB_KEY.format(st_job), {"status": "done", "user": "Administrator"})
		call(api.get_ai_draft_status, st_job)
		self.assertEqual(api.get_ai_draft_status("khong-co")["status"], "unknown")
