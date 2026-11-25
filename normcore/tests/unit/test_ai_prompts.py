"""Dựng mẫu lệnh và kiểm lược đồ đầu ra (FR-AI-014, ADR-005): thuần, không cần site."""

import unittest

from normcore.ai import prompts


class TestPrompts(unittest.TestCase):
	def test_parse_schema(self):
		self.assertEqual(prompts.parse_schema('{"type": "object"}'), {"type": "object"})
		for bad in ("", "[1]", "{khong json"):
			with self.assertRaises(prompts.PromptError):
				prompts.parse_schema(bad)

	def test_check_output(self):
		schema = {
			"type": "object",
			"required": ["items"],
			"properties": {
				"items": {
					"type": "array",
					"items": {"type": "object", "required": ["n"], "properties": {"n": {"type": "integer"}}},
				},
				"msg": {"type": "string"},
			},
		}
		self.assertEqual(prompts.check_output({"items": [{"n": 1}], "msg": "x"}, schema), [])
		self.assertTrue(prompts.check_output({}, schema))
		self.assertTrue(prompts.check_output({"items": [{"n": "a"}]}, schema))
		self.assertTrue(prompts.check_output({"items": {}}, schema))
		self.assertTrue(prompts.check_output([], schema))
		self.assertTrue(prompts.check_output({"items": [], "msg": 3}, schema))
		# bool không phải integer/number
		self.assertTrue(prompts.check_output({"items": [{"n": True}]}, schema))
		self.assertEqual(prompts.check_output({"anything": 1}, {"type": "object"}), [])

	def test_khong_import_frappe(self):
		import pathlib

		src = pathlib.Path(prompts.__file__).read_text(encoding="utf-8")
		self.assertNotIn("import frappe", src)
