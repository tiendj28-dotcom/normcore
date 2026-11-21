"""Provider AI thuần (không cần site): giả lập và bộ chuyển đổi Anthropic Messages (không gọi mạng)."""

import json
import unittest

from normcore.ai.providers import anthropic as anth
from normcore.ai.providers.mock import MOCK_RESPONSE, MockProvider


class TestProviders(unittest.TestCase):
	def test_mock_tra_json_co_dinh(self):
		r = MockProvider().complete("p", "DRAFT_PROCEDURE", {"a": 1}, [])
		self.assertEqual(json.loads(r.text), MOCK_RESPONSE)
		self.assertGreaterEqual(r.tokens_in, 0)
		self.assertGreaterEqual(r.tokens_out, 0)

	def test_anthropic_thieu_khoa_bao_loi(self):
		with self.assertRaises(anth.ProviderError):
			anth.AnthropicProvider(api_key="", model="m")
		with self.assertRaises(anth.ProviderError):
			anth.AnthropicProvider(api_key="k", model="")

	def test_anthropic_gui_dung_giao_thuc_khong_goi_mang(self):
		seen = {}

		def fake_post(url, headers, payload, timeout):
			seen.update(url=url, headers=headers, payload=payload)
			return {
				"content": [{"type": "text", "text": '{"ok": true}'}],
				"usage": {"input_tokens": 7, "output_tokens": 3},
			}

		p = anth.AnthropicProvider(api_key="SECRET-KEY", model="claude-sonnet-5-5", post=fake_post)
		r = p.complete("mục đích", "DRAFT_PROCEDURE", {"x": "y"}, ["S1"])
		self.assertEqual(r.text, '{"ok": true}')
		self.assertEqual((r.tokens_in, r.tokens_out), (7, 3))
		self.assertTrue(seen["url"].endswith("/v1/messages"))
		self.assertEqual(seen["headers"]["x-api-key"], "SECRET-KEY")
		self.assertEqual(seen["payload"]["model"], "claude-sonnet-5-5")

	def test_anthropic_loi_khong_lo_khoa(self):
		def bad_post(url, headers, payload, timeout):
			raise RuntimeError("401 key=SECRET-KEY")

		p = anth.AnthropicProvider(api_key="SECRET-KEY", model="m", post=bad_post)
		with self.assertRaises(anth.ProviderError) as e:
			p.complete("p", "T", {}, [])
		self.assertNotIn("SECRET-KEY", str(e.exception))
