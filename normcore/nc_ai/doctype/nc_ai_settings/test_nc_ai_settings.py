import json

import frappe
import requests
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_months, now_datetime

from normcore.ai import gateway
from normcore.tests.utils import make_base, make_procedure, make_user

SECRET = "SK-TEST-123"


def _ok_anthropic(seen):
	def post(url, headers, payload, timeout):
		seen.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
		return {"content": [{"type": "text", "text": '{"ok": true}'}], "usage": {"input_tokens": 3, "output_tokens": 2}}

	return post


def _ok_openai(seen):
	def post(url, headers, payload, timeout):
		seen.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
		return {"choices": [{"message": {"content": '{"ok": true}'}}], "usage": {"prompt_tokens": 4, "completion_tokens": 1}}

	return post


def _configure(**kw):
	s = frappe.get_doc("NC AI Settings")
	values = dict(
		enabled=0,
		protocol="Anthropic Messages",
		base_url="",
		model="claude-test",
		api_key=SECRET,
		timeout_seconds=180,
		max_output_tokens=4096,
		monthly_token_budget=0,
	)
	values.update(kw)
	s.update(values)
	s.save(ignore_permissions=True)
	return s


def _make_log(tokens_in, tokens_out, when=None):
	name = frappe.get_doc(
		{
			"doctype": "NC AI Log",
			"purpose": "DRAFT_PROCEDURE",
			"status": "Thành công",
			"tokens_in": tokens_in,
			"tokens_out": tokens_out,
		}
	).insert(ignore_permissions=True).name
	if when:
		frappe.db.set_value("NC AI Log", name, "creation", when, update_modified=False)
	return name


class TestNCAISettings(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.flags.normcore_ai_transport = None

	def tearDown(self):
		frappe.flags.pop("normcore_ai_transport", None)
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_AI_05_qua_han_giu_du_lieu(self):
		service, dept, _job = make_base()
		proc = make_procedure(service, dept)
		modified, n_proc = proc.modified, frappe.db.count("NC Clinical Procedure")
		seen = []

		def slow(url, headers, payload, timeout):
			seen.append(timeout)
			raise requests.exceptions.Timeout("read timed out")

		frappe.flags.normcore_ai_transport = slow
		_configure(timeout_seconds=5)
		logs = frappe.db.count("NC AI Log")
		res = gateway.complete(
			"DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {"a": 1}, [], "NC Clinical Procedure", proc.name
		)
		self.assertFalse(res.ok)
		self.assertEqual(res.status, "Quá hạn")
		self.assertIn("không phản hồi", res.error)
		self.assertEqual(seen, [5])
		self.assertEqual(frappe.db.count("NC AI Log"), logs + 1)
		self.assertEqual(frappe.db.get_value("NC AI Log", res.log_name, "status"), "Quá hạn")
		self.assertEqual(frappe.db.count("NC Clinical Procedure"), n_proc)
		self.assertEqual(str(frappe.db.get_value("NC Clinical Procedure", proc.name, "modified")), str(modified))
		ping = gateway.ping()
		self.assertEqual(ping.status, "Quá hạn")
		self.assertFalse(ping.ok)

	def test_TC_AI_08_log_du_truong(self):
		seen = []
		frappe.flags.normcore_ai_transport = _ok_anthropic(seen)
		_configure()
		service, dept, _job = make_base()
		proc = make_procedure(service, dept)
		res = gateway.complete(
			"DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {"a": 1}, ["LS-0000001"], "NC Clinical Procedure", proc.name
		)
		self.assertTrue(res.ok)
		log = frappe.get_doc("NC AI Log", res.log_name)
		self.assertEqual(log.purpose, "DRAFT_PROCEDURE")
		self.assertEqual(log.user, "Administrator")
		self.assertEqual((log.ref_doctype, log.ref_name), ("NC Clinical Procedure", proc.name))
		active = frappe.db.get_value(
			"NC Prompt Template", {"template_code": "DRAFT_PROCEDURE", "is_active": 1}, "name"
		)
		self.assertEqual(log.prompt_template, active)
		self.assertRegex(log.prompt_template, r"^DRAFT_PROCEDURE-v\d+$")
		self.assertEqual(log.source_sections, "LS-0000001")
		self.assertEqual((log.tokens_in, log.tokens_out), (3, 2))
		self.assertIsNotNone(log.duration_ms)
		self.assertEqual(log.status, "Thành công")
		# mẫu lệnh được dựng gửi đi
		self.assertIn('"a": 1', seen[0]["payload"]["messages"][0]["content"])

	def test_TC_AI_09_chan_han_muc(self):
		seen = []
		frappe.flags.normcore_ai_transport = _ok_anthropic(seen)
		admin = make_user("admin.ai@normcore.test", "NC Admin")
		_configure(monthly_token_budget=1000)
		_make_log(700, 500)
		_make_log(5000, 5000, add_months(now_datetime(), -1))  # tháng trước không tính
		self.assertEqual(gateway.monthly_usage(), 1200)
		before = frappe.db.count("NC AI Log")
		res = gateway.complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {}, [])
		self.assertFalse(res.ok)
		self.assertEqual(res.status, "Bị chặn hạn mức")
		self.assertEqual(seen, [])
		self.assertEqual(frappe.db.count("NC AI Log"), before + 1)
		self.assertEqual(frappe.db.get_value("NC AI Log", res.log_name, "status"), "Bị chặn hạn mức")
		month = now_datetime().strftime("%m/%Y")
		notes = frappe.get_all(
			"Notification Log", {"for_user": admin, "subject": ["like", f"%{month}%"]}, pluck="name"
		)
		self.assertEqual(len(notes), 1)
		gateway.complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {}, [])
		self.assertEqual(
			frappe.db.count("Notification Log", {"for_user": admin, "subject": ["like", f"%{month}%"]}), 1
		)

	def test_TC_AI_09_bien_bang_han_muc_khong_chan(self):
		seen = []
		frappe.flags.normcore_ai_transport = _ok_anthropic(seen)
		_configure(monthly_token_budget=1000)
		base = gateway.monthly_usage()
		_make_log(1000 - base, 0)
		self.assertEqual(gateway.monthly_usage(), 1000)
		res = gateway.complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {}, [])
		self.assertTrue(res.ok)
		self.assertEqual(len(seen), 1)

	def test_TC_AI_11_doi_dia_chi(self):
		seen = []
		frappe.flags.normcore_ai_transport = lambda *a: _ok_anthropic(seen)(*a)
		_configure(base_url="http://a.local")
		self.assertTrue(gateway.complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {}, []).ok)
		self.assertEqual(seen[-1]["url"], "http://a.local/v1/messages")
		self.assertEqual(seen[-1]["headers"]["x-api-key"], SECRET)

		oa = []
		frappe.flags.normcore_ai_transport = _ok_openai(oa)
		_configure(protocol="OpenAI-compatible", base_url="http://b.local/v1", model="m2")
		res = gateway.complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {}, [])
		self.assertTrue(res.ok)
		self.assertEqual(oa[-1]["url"], "http://b.local/v1/chat/completions")
		self.assertEqual(oa[-1]["headers"]["Authorization"], f"Bearer {SECRET}")
		self.assertEqual(oa[-1]["payload"]["model"], "m2")
		self.assertEqual(len(seen), 1)

	def test_TC_NFR_04_khoa_khong_lo(self):
		seen = []
		frappe.flags.normcore_ai_transport = _ok_anthropic(seen)
		_configure()
		self.assertEqual(frappe.get_doc("NC AI Settings").get_password("api_key"), SECRET)
		doc = frappe.get_doc("NC AI Settings")
		self.assertNotIn(SECRET, json.dumps(doc.as_dict(), default=str))
		self.assertNotIn(SECRET, json.dumps(frappe.client.get("NC AI Settings"), default=str))
		versions = frappe.get_all("Version", {"ref_doctype": "NC AI Settings"}, pluck="data")
		self.assertNotIn(SECRET, json.dumps(versions))

		def leaky(url, headers, payload, timeout):
			raise RuntimeError(f"401 key={SECRET}")

		frappe.flags.normcore_ai_transport = leaky
		res = gateway.complete("DRAFT_PROCEDURE", "DRAFT_PROCEDURE", {}, [])
		self.assertFalse(res.ok)
		self.assertNotIn(SECRET, res.error)
		log = frappe.get_doc("NC AI Log", res.log_name)
		self.assertNotIn(SECRET, json.dumps(log.as_dict(), default=str))
		self.assertNotIn(SECRET, gateway.ping().error)
		errs = frappe.get_all("Error Log", pluck="error")
		self.assertFalse(any(SECRET in (e or "") for e in errs))

	def test_UC017_4c_bat_ai_kiem_ket_noi(self):
		def down(url, headers, payload, timeout):
			raise ConnectionError("không kết nối được")

		frappe.flags.normcore_ai_transport = down
		with self.assertRaises(frappe.ValidationError):
			_configure(enabled=1)
		self.assertEqual(int(frappe.db.get_single_value("NC AI Settings", "enabled") or 0), 0)
		seen = []
		frappe.flags.normcore_ai_transport = _ok_anthropic(seen)
		_configure(enabled=1)
		self.assertEqual(int(frappe.db.get_single_value("NC AI Settings", "enabled")), 1)
		self.assertEqual(len(seen), 1)  # kiểm tra kết nối đã chạy
		self.assertEqual(seen[0]["payload"]["messages"][0]["content"], "ping")

	def test_validate_gia_tri(self):
		for bad in (
			dict(timeout_seconds=0),
			dict(timeout_seconds=601),
			dict(max_output_tokens=0),
			dict(monthly_token_budget=-1),
			dict(base_url="ftp://x"),
			dict(protocol="OpenAI-compatible", base_url=""),
		):
			with self.subTest(bad=bad):
				with self.assertRaises(frappe.ValidationError):
					_configure(**bad)
		s = _configure(base_url="http://x.local/")
		self.assertEqual(s.base_url, "http://x.local")

	def test_quyen_ai_settings_auditor_chi_doc_finance_khong_doc(self):
		auditor = make_user("auditor.as@normcore.test", "NC Auditor")
		finance = make_user("fin.as@normcore.test", "NC Finance")
		admin = make_user("admin.as@normcore.test", "NC Admin")
		frappe.set_user(auditor)
		self.assertTrue(frappe.has_permission("NC AI Settings", "read"))
		self.assertFalse(frappe.has_permission("NC AI Settings", "write"))
		frappe.set_user(finance)
		self.assertFalse(frappe.has_permission("NC AI Settings", "read"))
		frappe.set_user(admin)
		self.assertTrue(frappe.has_permission("NC AI Settings", "write"))
