"""Bộ chuyển đổi OpenAI-compatible, thời hạn và system/user của Anthropic (FR-AI-010, FR-AI-012). Không gọi mạng."""

import socket
import unittest

import requests

from normcore.ai.providers import anthropic as anth
from normcore.ai.providers import http
from normcore.ai.providers.base import ProviderError, ProviderTimeout
from normcore.ai.providers.openai_compat import OpenAICompatProvider


def _ok_openai(seen):
	def post(url, headers, payload, timeout):
		seen.update(url=url, headers=headers, payload=payload, timeout=timeout)
		return {
			"choices": [{"message": {"content": '{"ok": true}'}}],
			"usage": {"prompt_tokens": 11, "completion_tokens": 5},
		}

	return post


class TestOpenAICompat(unittest.TestCase):
	def test_thieu_cau_hinh(self):
		with self.assertRaises(ProviderError):
			OpenAICompatProvider(api_key="k", model="m", base_url="")
		with self.assertRaises(ProviderError):
			OpenAICompatProvider(api_key="k", model="", base_url="http://x")

	def test_gui_dung_giao_thuc(self):
		seen = {}
		p = OpenAICompatProvider(
			"SECRET-KEY", "gpt-x", "http://llm.local/v1/", timeout=7, post=_ok_openai(seen)
		)
		r = p.complete("p", "T", {"a": 1}, [], system="SYS", user="USR")
		self.assertEqual(seen["url"], "http://llm.local/v1/chat/completions")
		self.assertEqual(seen["headers"]["Authorization"], "Bearer SECRET-KEY")
		self.assertEqual(seen["timeout"], 7)
		self.assertEqual(seen["payload"]["model"], "gpt-x")
		self.assertEqual(
			seen["payload"]["messages"],
			[{"role": "system", "content": "SYS"}, {"role": "user", "content": "USR"}],
		)
		self.assertEqual((r.text, r.tokens_in, r.tokens_out), ('{"ok": true}', 11, 5))

	def test_khoa_trong_bo_header_authorization(self):
		seen = {}
		OpenAICompatProvider("", "m", "http://x", post=_ok_openai(seen)).complete("p", "T", {}, [])
		self.assertNotIn("Authorization", seen["headers"])

	def test_khong_co_system_user_dung_cach_cu(self):
		seen = {}
		OpenAICompatProvider("k", "m", "http://x", post=_ok_openai(seen)).complete("p", "T", {"v": 1}, ["S"])
		roles = [m["role"] for m in seen["payload"]["messages"]]
		self.assertEqual(roles, ["system", "user"])

	def test_qua_han(self):
		def post(url, headers, payload, timeout):
			raise requests.exceptions.Timeout("read timed out")

		p = OpenAICompatProvider("k", "m", "http://x", timeout=5, post=post)
		with self.assertRaises(ProviderTimeout) as e:
			p.complete("p", "T", {}, [])
		self.assertIn("không phản hồi", str(e.exception))
		self.assertIn("5", str(e.exception))

	def test_loi_khong_lo_khoa(self):
		def post(url, headers, payload, timeout):
			raise RuntimeError("401 key=SECRET-KEY")

		p = OpenAICompatProvider("SECRET-KEY", "m", "http://x", post=post)
		with self.assertRaises(ProviderError) as e:
			p.complete("p", "T", {}, [])
		self.assertNotIn("SECRET-KEY", str(e.exception))

	def test_ket_qua_sai_dinh_dang(self):
		p = OpenAICompatProvider("k", "m", "http://x", post=lambda *a: {"choices": []})
		with self.assertRaises(ProviderError):
			p.complete("p", "T", {}, [])


class TestAnthropicMoRong(unittest.TestCase):
	def test_nhan_system_user_va_timeout(self):
		seen = {}

		def post(url, headers, payload, timeout):
			seen.update(payload=payload, timeout=timeout)
			return {"content": [{"type": "text", "text": "{}"}], "usage": {}}

		p = anth.AnthropicProvider("k", "m", timeout=9, max_tokens=123, post=post)
		p.complete("p", "T", {}, [], system="SYS", user="USR")
		self.assertEqual(seen["payload"]["system"], "SYS")
		self.assertEqual(seen["payload"]["messages"], [{"role": "user", "content": "USR"}])
		self.assertEqual(seen["payload"]["max_tokens"], 123)
		self.assertEqual(seen["timeout"], 9)

	def test_qua_han(self):
		def post(url, headers, payload, timeout):
			raise TimeoutError("timed out")

		with self.assertRaises(ProviderTimeout):
			anth.AnthropicProvider("k", "m", timeout=3, post=post).complete("p", "T", {}, [])

	def test_base_url_tuy_chinh(self):
		seen = {}

		def post(url, headers, payload, timeout):
			seen["url"] = url
			return {"content": [], "usage": {}}

		anth.AnthropicProvider("k", "m", base_url="http://proxy.local/", post=post).complete("p", "T", {}, [])
		self.assertEqual(seen["url"], "http://proxy.local/v1/messages")


class TestDefaultPost(unittest.TestCase):
	def test_timeout_thanh_provider_timeout(self):
		orig = requests.post
		try:

			def boom(*a, **k):
				raise requests.exceptions.ReadTimeout("x")

			requests.post = boom
			with self.assertRaises(ProviderTimeout):
				http.default_post("http://x", {}, {}, 2)
		finally:
			requests.post = orig
