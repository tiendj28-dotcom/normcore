"""Provider AI thuần (không cần site): giả lập và bộ chuyển đổi Anthropic Messages (không gọi mạng)."""

import json

import pytest

from normcore.ai.providers import anthropic as anth
from normcore.ai.providers.mock import MOCK_RESPONSE, MockProvider


def test_mock_tra_json_co_dinh():
	r = MockProvider().complete("p", "DRAFT_PROCEDURE", {"a": 1}, [])
	assert json.loads(r.text) == MOCK_RESPONSE
	assert r.tokens_in >= 0 and r.tokens_out >= 0


def test_anthropic_thieu_khoa_bao_loi():
	with pytest.raises(anth.ProviderError):
		anth.AnthropicProvider(api_key="", model="m")


def test_anthropic_gui_dung_giao_thuc_khong_goi_mang():
	seen = {}

	def fake_post(url, headers, payload, timeout):
		seen.update(url=url, headers=headers, payload=payload)
		return {
			"content": [{"type": "text", "text": '{"ok": true}'}],
			"usage": {"input_tokens": 7, "output_tokens": 3},
		}

	p = anth.AnthropicProvider(api_key="SECRET-KEY", model="claude-sonnet-5-5", post=fake_post)
	r = p.complete("mục đích", "DRAFT_PROCEDURE", {"x": "y"}, ["S1"])
	assert r.text == '{"ok": true}'
	assert (r.tokens_in, r.tokens_out) == (7, 3)
	assert seen["url"].endswith("/v1/messages")
	assert seen["headers"]["x-api-key"] == "SECRET-KEY"
	assert seen["payload"]["model"] == "claude-sonnet-5-5"


def test_anthropic_loi_khong_lo_khoa():
	def bad_post(url, headers, payload, timeout):
		raise RuntimeError("401 key=SECRET-KEY")

	p = anth.AnthropicProvider(api_key="SECRET-KEY", model="m", post=bad_post)
	with pytest.raises(anth.ProviderError) as e:
		p.complete("p", "T", {}, [])
	assert "SECRET-KEY" not in str(e.value)
