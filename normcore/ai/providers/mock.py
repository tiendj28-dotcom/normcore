"""Provider giả lập: trả JSON cố định, không gọi mạng. Mặc định khi chưa cấu hình và trong mọi test."""

import json

from normcore.ai.providers.base import ProviderResponse

MOCK_RESPONSE = {"mock": True, "message": "Kết quả giả lập", "items": []}


class MockProvider:
	def complete(self, purpose, template_code, variables, sources, *, system=None, user=None):
		text = json.dumps(MOCK_RESPONSE, ensure_ascii=False)
		return ProviderResponse(
			text=text, tokens_in=len(json.dumps(variables, default=str)) // 4, tokens_out=len(text) // 4
		)
