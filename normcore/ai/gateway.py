"""AI gateway: một giao diện duy nhất `complete(...)` (ADR-005); mỗi lời gọi ghi đúng một NC AI Log (FR-AI-009).

Cấu hình đọc từ NC AI Settings ở MỖI lời gọi (FR-AI-012, không cần khởi động lại). Khóa dự phòng khi trường
`api_key` trống: biến môi trường NORMCORE_AI_API_KEY, rồi site_config `normcore_ai_api_key` (ASM-023-02).
Gateway không tự chặn khi AI tắt (ASM-023-03, Lead đã duyệt): API của từng nút AI gọi `ensure_enabled()`.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field

import frappe
from frappe import _
from frappe.utils import add_months, get_first_day, now_datetime

from normcore.ai import guard, prompts
from normcore.ai.providers.anthropic import DEFAULT_BASE_URL, AnthropicProvider
from normcore.ai.providers.base import ProviderError, ProviderTimeout
from normcore.ai.providers.mock import MockProvider
from normcore.ai.providers.openai_compat import OpenAICompatProvider

SETTINGS = "NC AI Settings"
TEMPLATE = "NC Prompt Template"
OK = "Thành công"
ERROR = "Lỗi"
TIMEOUT = "Quá hạn"
BLOCKED = "Bị chặn hạn mức"
PROTO_OPENAI = "OpenAI-compatible"
PROTO_ANTHROPIC = "Anthropic Messages"


@dataclass
class AIResult:
	ok: bool
	status: str
	data: dict | None = None
	text: str = ""
	error: str = ""
	tokens_in: int = 0
	tokens_out: int = 0
	duration_ms: int = 0
	log_name: str | None = None
	extra: dict = field(default_factory=dict)


def _is_masked(value) -> bool:
	return bool(value) and set(str(value)) <= {"*"}


def resolve_key(doc=None) -> str:
	"""Khóa theo thứ tự: giá trị vừa nhập, khóa đã lưu, biến môi trường, site_config."""
	if doc is not None:
		val = doc.get("api_key")
		if val and not _is_masked(val):
			return val
		stored = doc.get_password("api_key", raise_exception=False) if doc.get("name") else None
		if stored:
			return stored
	return os.environ.get("NORMCORE_AI_API_KEY") or frappe.conf.get("normcore_ai_api_key") or ""


def settings_from_doc(doc) -> frappe._dict:
	return frappe._dict(
		enabled=int(doc.get("enabled") or 0),
		protocol=doc.get("protocol") or PROTO_ANTHROPIC,
		base_url=(doc.get("base_url") or "").strip(),
		model=doc.get("model") or "",
		api_key=resolve_key(doc),
		timeout_seconds=int(doc.get("timeout_seconds") or 180),
		max_output_tokens=int(doc.get("max_output_tokens") or 4096),
		monthly_token_budget=int(doc.get("monthly_token_budget") or 0),
	)


def get_settings() -> frappe._dict:
	"""Đọc cấu hình mỗi lần gọi (không cache trong tiến trình)."""
	return settings_from_doc(frappe.get_doc(SETTINGS))


def is_enabled() -> bool:
	return bool(int(frappe.db.get_single_value(SETTINGS, "enabled") or 0))


def ensure_enabled():
	"""Các API của nút AI (FEAT-024 trở đi) gọi hàm này trước khi dùng gateway (FR-AI-015)."""
	if not is_enabled():
		frappe.throw(_("Tính năng AI đang tắt"), title=_("AI"))


def get_provider(settings=None):
	settings = settings or get_settings()
	if frappe.flags.in_test:  # CLAUDE.md mục 3 luật 6: test không gọi mạng
		transport = frappe.flags.get("normcore_ai_transport")
		if transport is None:
			return MockProvider()
		return _build_provider(settings, transport)
	if (frappe.conf.get("normcore_ai_provider") or "").lower() == "mock":
		return MockProvider()  # smoke dev/staging (ASM-023-11)
	return _build_provider(settings, None)


def _build_provider(settings, post):
	if settings.protocol == PROTO_OPENAI:
		return OpenAICompatProvider(
			api_key=settings.api_key,
			model=settings.model,
			base_url=settings.base_url,
			max_tokens=settings.max_output_tokens,
			timeout=settings.timeout_seconds,
			post=post,
		)
	if settings.protocol == PROTO_ANTHROPIC:
		return AnthropicProvider(
			api_key=settings.api_key,
			model=settings.model,
			base_url=settings.base_url or DEFAULT_BASE_URL,
			max_tokens=settings.max_output_tokens,
			timeout=settings.timeout_seconds,
			post=post,
		)
	raise ProviderError(f"Giao thức AI không hợp lệ: {settings.protocol}")


def monthly_usage(now=None) -> int:
	"""Tổng token vào + ra của NC AI Log tạo trong tháng dương lịch hiện tại (ASM-023-04)."""
	now = now or now_datetime()
	start = get_first_day(now)
	end = add_months(start, 1)
	row = frappe.db.sql(
		"select coalesce(sum(tokens_in + tokens_out), 0) from `tabNC AI Log` where creation >= %s and creation < %s",
		(start, end),
	)
	return int(row[0][0] or 0)


def _redact(text, key) -> str:
	text = text or ""
	return text.replace(key, "***") if key else text


def ping(settings=None) -> AIResult:
	"""Kiểm tra kết nối (UC-017 bước 4); không ghi NC AI Log, không tính hạn mức (ASM-023-12)."""
	settings = settings or get_settings()
	res = AIResult(ok=False, status=ERROR)
	start = time.monotonic()
	try:
		pr = get_provider(settings).complete(
			"PING", "PING", {}, [], system='Trả về JSON {"ok": true}', user="ping"
		)
		res.ok, res.status, res.text = True, OK, pr.text
	except ProviderTimeout as e:
		res.status, res.error = TIMEOUT, _redact(str(e), settings.api_key)
	except Exception as e:
		res.error = _redact(f"{type(e).__name__}: {e}", settings.api_key)
	res.duration_ms = int((time.monotonic() - start) * 1000)
	return res


def _write_log(purpose, ref_doctype, ref_name, sources, request_hash, response, res, prompt_template=None):
	log = frappe.get_doc(
		{
			"doctype": "NC AI Log",
			"purpose": purpose,
			"user": frappe.session.user,
			"ref_doctype": ref_doctype,
			"ref_name": ref_name,
			"prompt_template": prompt_template,
			"source_sections": "\n".join(str(s) for s in sources or []),
			"request_hash": request_hash,
			"response": response,
			"tokens_in": res.tokens_in,
			"tokens_out": res.tokens_out,
			"duration_ms": res.duration_ms,
			"status": res.status,
			"rejected_citations": 0,
		}
	)
	log.insert(ignore_permissions=True)  # bản ghi do mã máy chủ tạo; không vai trò nào có quyền tạo
	return log.name


def _notify_budget(used, budget, now=None):
	"""Notification Log cho mọi NC Admin đang bật; một lần mỗi tháng mỗi người (ASM-023-04)."""
	now = now or now_datetime()
	month = now.strftime("%m/%Y")
	subject = _("Đã vượt hạn mức token AI tháng {0}").format(month)
	content = _("Đã dùng {0} token, hạn mức tháng {1}. Các lần gọi AI mới bị chặn.").format(used, budget)
	admins = frappe.get_all("Has Role", filters={"role": "NC Admin", "parenttype": "User"}, pluck="parent")
	for user in sorted(set(admins) - {"Administrator", "Guest"}):
		if not frappe.db.get_value("User", user, "enabled"):
			continue
		if frappe.db.exists("Notification Log", {"for_user": user, "subject": subject}):
			continue
		frappe.get_doc(
			{
				"doctype": "Notification Log",
				"type": "Alert",
				"document_type": SETTINGS,
				"document_name": SETTINGS,
				"subject": subject,
				"email_content": content,
				"for_user": user,
				"from_user": "Administrator",
			}
		).insert(ignore_permissions=True)


def _active_template(code):
	name = frappe.db.get_value(TEMPLATE, {"template_code": code, "is_active": 1}, "name")
	return frappe.get_doc(TEMPLATE, name) if name else None


def complete(purpose, template_code, variables, sources, ref_doctype=None, ref_name=None, provider=None):
	"""Gọi AI qua provider đang cấu hình. Luôn trả AIResult và luôn ghi một NC AI Log, kể cả khi lỗi.

	Thứ tự: hạn mức, mẫu lệnh, gọi, kiểm lược đồ, ghi nhật ký. Không ghi gì ngoài NC AI Log và Notification Log
	(FR-AI-010: không bản nháp dở).
	"""
	variables = variables or {}
	sources = sources or []
	settings = get_settings()
	request_hash = hashlib.sha256(
		json.dumps(
			[purpose, template_code, variables, sources], ensure_ascii=False, sort_keys=True, default=str
		).encode()
	).hexdigest()
	start = time.monotonic()
	res = AIResult(ok=False, status=ERROR)
	response_text = ""
	template_name = None

	used = monthly_usage()
	if guard.budget_exceeded(used, settings.monthly_token_budget):
		res.status = BLOCKED
		res.error = _("Đã vượt hạn mức token tháng (đã dùng {0} / {1}). Liên hệ quản trị.").format(
			used, settings.monthly_token_budget
		)
		response_text = res.error
		_notify_budget(used, settings.monthly_token_budget)
	else:
		try:
			template = _active_template(template_code)
			if template is None:
				raise ProviderError(_("Chưa có mẫu lệnh đang dùng cho {0}").format(template_code))
			template_name = template.name
			user_text = prompts.render(template.user_prompt, variables, sources)
			provider = provider or get_provider(settings)
			pr = provider.complete(
				purpose, template_code, variables, sources, system=template.system_prompt, user=user_text
			)
			res.text = response_text = pr.text
			res.tokens_in, res.tokens_out = pr.tokens_in, pr.tokens_out
			res.data = json.loads(pr.text)
			errors = prompts.check_output(res.data, prompts.parse_schema(template.output_schema))
			if errors:
				res.data = None
				raise ProviderError("Kết quả AI không đúng lược đồ: " + "; ".join(errors))
			res.ok, res.status = True, OK
		except ProviderTimeout:
			res.status = TIMEOUT
			res.error = response_text = _(
				"Dịch vụ AI không phản hồi trong {0} giây. Dữ liệu của bạn được giữ nguyên; có thể soạn thủ công."
			).format(settings.timeout_seconds)
		except (ProviderError, prompts.PromptError) as e:
			res.error = response_text = str(e)
		except ValueError as e:
			res.error = f"Kết quả AI không phải JSON hợp lệ: {e}"
			response_text = res.text or res.error
		except Exception as e:
			res.error = response_text = f"{type(e).__name__}: {e}"
	res.error = _redact(res.error, settings.api_key)
	response_text = _redact(response_text, settings.api_key)
	res.duration_ms = int((time.monotonic() - start) * 1000)
	res.log_name = _write_log(
		purpose, ref_doctype, ref_name, sources, request_hash, response_text, res, template_name
	)
	return res
