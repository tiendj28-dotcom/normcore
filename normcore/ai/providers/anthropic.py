"""Bộ chuyển đổi Anthropic Messages. Khóa chỉ đọc từ cấu hình (không commit); test truyền `post` giả, không gọi mạng."""

import json

from normcore.ai.providers.base import ProviderError, ProviderResponse

DEFAULT_BASE_URL = "https://api.anthropic.com"
API_VERSION = "2023-06-01"


def _http_post(url, headers, payload, timeout):
	import requests

	resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
	resp.raise_for_status()
	return resp.json()


class AnthropicProvider:
	def __init__(self, api_key, model, base_url=DEFAULT_BASE_URL, max_tokens=4096, timeout=180, post=None):
		if not api_key:
			raise ProviderError("Chưa cấu hình khóa API cho nhà cung cấp AI")
		if not model:
			raise ProviderError("Chưa cấu hình mô hình AI")
		self._api_key = api_key
		self.model = model
		self.base_url = base_url.rstrip("/")
		self.max_tokens = max_tokens
		self.timeout = timeout
		self._post = post or _http_post

	def complete(self, purpose, template_code, variables, sources):
		payload = {
			"model": self.model,
			"max_tokens": self.max_tokens,
			"system": f"Mục đích: {purpose}. Mẫu: {template_code}. Chỉ trả về JSON hợp lệ.",
			"messages": [
				{
					"role": "user",
					"content": json.dumps(
						{"variables": variables, "sources": sources}, ensure_ascii=False, default=str
					),
				}
			],
		}
		headers = {
			"x-api-key": self._api_key,
			"anthropic-version": API_VERSION,
			"content-type": "application/json",
		}
		try:
			data = self._post(f"{self.base_url}/v1/messages", headers, payload, self.timeout)
		except Exception as e:
			msg = str(e).replace(self._api_key, "***")
			raise ProviderError(f"Lỗi gọi nhà cung cấp AI: {type(e).__name__}: {msg}") from None
		text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
		usage = data.get("usage") or {}
		return ProviderResponse(text, int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0)))
