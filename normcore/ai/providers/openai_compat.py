"""Bộ chuyển đổi tương thích OpenAI Chat Completions (FR-AI-012). Test truyền `post` giả, không gọi mạng."""

import json

from normcore.ai.providers import http
from normcore.ai.providers.base import ProviderError, ProviderResponse


class OpenAICompatProvider:
	def __init__(self, api_key, model, base_url, max_tokens=4096, timeout=180, post=None):
		if not base_url:
			raise ProviderError("Chưa cấu hình địa chỉ nhà cung cấp AI")
		if not model:
			raise ProviderError("Chưa cấu hình mô hình AI")
		self._api_key = api_key or ""  # máy chủ tự host có thể không cần khóa (ASM-023-10)
		self.model = model
		self.base_url = base_url.rstrip("/")
		self.max_tokens = max_tokens
		self.timeout = timeout
		self._post = post or http.default_post

	def complete(self, purpose, template_code, variables, sources, *, system=None, user=None):
		if system is None:
			system = f"Mục đích: {purpose}. Mẫu: {template_code}. Chỉ trả về JSON hợp lệ."
		if user is None:
			user = json.dumps({"variables": variables, "sources": sources}, ensure_ascii=False, default=str)
		payload = {
			"model": self.model,
			"max_tokens": self.max_tokens,
			"messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
		}
		headers = {"content-type": "application/json"}
		if self._api_key:
			headers["Authorization"] = f"Bearer {self._api_key}"
		data = http.call(
			self._post, f"{self.base_url}/chat/completions", headers, payload, self.timeout, self._api_key
		)
		try:
			text = data["choices"][0]["message"]["content"] or ""
		except (KeyError, IndexError, TypeError):
			raise ProviderError("Nhà cung cấp AI trả về định dạng không hợp lệ") from None
		usage = data.get("usage") or {}
		return ProviderResponse(text, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)))
