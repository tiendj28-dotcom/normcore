"""Dựng mẫu lệnh Jinja trong sandbox (FR-AI-014). Cần jinja2 (có trong môi trường Frappe), nên chạy ở bước test trên site."""

import unittest

from normcore.ai import prompts


class TestPromptsRender(unittest.TestCase):
	def test_render_tojson_giu_tieng_viet(self):
		out = prompts.render(
			"V={{ variables | tojson }} S={{ sources | join(',') }}", {"a": "Đã"}, ["S1", "S2"]
		)
		self.assertIn('"a": "Đã"', out)
		self.assertIn("S1,S2", out)

	def test_render_bien_thieu_bao_loi(self):
		with self.assertRaises(prompts.PromptError):
			prompts.render("{{ variables.khong_co }}", {}, [])

	def test_render_sandbox_chan_truy_cap_nguy_hiem(self):
		with self.assertRaises(prompts.PromptError):
			prompts.render("{{ ''.__class__.__mro__ }}", {}, [])

	def test_check_syntax(self):
		prompts.check_syntax("{{ variables | tojson }}")
		with self.assertRaises(prompts.PromptError):
			prompts.check_syntax("{% if %}")
