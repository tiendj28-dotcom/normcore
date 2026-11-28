"""NORM-87: title_field của DocType phải là trường thật (không phải "name"),
nếu không ListView Desk lỗi `reading 'fieldname'` và danh sách trống."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TestDocTypeTitleField(unittest.TestCase):
	def test_title_field_la_truong_that(self):
		files = sorted(ROOT.glob("nc_*/doctype/*/*.json"))
		self.assertTrue(files)
		for path in files:
			data = json.loads(path.read_text(encoding="utf-8"))
			title = data.get("title_field")
			if not title:
				continue
			names = {f["fieldname"] for f in data.get("fields", [])}
			with self.subTest(doctype=path.parent.name):
				self.assertIn(title, names, f"{path.parent.name}: title_field {title!r} không phải trường")
