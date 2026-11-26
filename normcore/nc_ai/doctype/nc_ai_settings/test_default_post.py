"""`http.default_post` ánh xạ quá hạn của requests (FR-AI-010). Cần requests (có trong môi trường Frappe)."""

import unittest

import requests

from normcore.ai.providers import http
from normcore.ai.providers.base import ProviderTimeout


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
