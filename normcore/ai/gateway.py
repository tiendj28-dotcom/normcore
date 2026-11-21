"""AI gateway: một giao diện duy nhất `complete(...)` (ADR-005); mỗi lời gọi ghi đúng một NC AI Log (FR-AI-009).

Cấu hình skeleton (G4) đọc từ site_config.json: normcore_ai_provider (mặc định "mock"),
normcore_ai_model, normcore_ai_api_key; biến môi trường NORMCORE_AI_API_KEY thay được khóa.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field

import frappe

from normcore.ai.providers.anthropic import AnthropicProvider
from normcore.ai.providers.base import ProviderError
from normcore.ai.providers.mock import MockProvider

OK = "Thành công"
ERROR = "Lỗi"


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


def get_provider():
	if frappe.flags.in_test:  # CLAUDE.md mục 3 luật 6: test luôn dùng provider giả lập, không gọi mạng
		return MockProvider()
	kind = (frappe.conf.get("normcore_ai_provider") or "mock").lower()
	if kind == "mock":
		return MockProvider()
	if kind == "anthropic":
		api_key = os.environ.get("NORMCORE_AI_API_KEY") or frappe.conf.get("normcore_ai_api_key")
		return AnthropicProvider(api_key=api_key, model=frappe.conf.get("normcore_ai_model"))
	raise ProviderError(f"Nhà cung cấp AI không hợp lệ: {kind}")


def _write_log(purpose, ref_doctype, ref_name, sources, request_hash, response, res):
	log = frappe.get_doc(
		{
			"doctype": "NC AI Log",
			"purpose": purpose,
			"user": frappe.session.user,
			"ref_doctype": ref_doctype,
			"ref_name": ref_name,
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


def complete(purpose, template_code, variables, sources, ref_doctype=None, ref_name=None, provider=None):
	"""Gọi AI qua provider đang cấu hình. Luôn trả AIResult và luôn ghi một NC AI Log, kể cả khi lỗi."""
	variables = variables or {}
	sources = sources or []
	request_hash = hashlib.sha256(
		json.dumps(
			[purpose, template_code, variables, sources], ensure_ascii=False, sort_keys=True, default=str
		).encode()
	).hexdigest()
	start = time.monotonic()
	res = AIResult(ok=False, status=ERROR)
	response_text = ""
	try:
		provider = provider or get_provider()
		pr = provider.complete(purpose, template_code, variables, sources)
		res.text = response_text = pr.text
		res.tokens_in, res.tokens_out = pr.tokens_in, pr.tokens_out
		res.data = json.loads(pr.text)
		res.ok, res.status = True, OK
	except ProviderError as e:
		res.error = response_text = str(e)
	except ValueError as e:
		res.error = f"Kết quả AI không phải JSON hợp lệ: {e}"
		response_text = res.text or res.error
	except Exception as e:
		res.error = response_text = f"{type(e).__name__}: {e}"
	res.duration_ms = int((time.monotonic() - start) * 1000)
	res.log_name = _write_log(purpose, ref_doctype, ref_name, sources, request_hash, response_text, res)
	return res
