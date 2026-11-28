"""NORM-92: tên DocType và Report NC phải có bản dịch tiếng Việt trong vi.d/."""

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _translated():
	keys = set()
	for f in (ROOT / "translations" / "vi.d").glob("*.csv"):
		with open(f, encoding="utf-8", newline="") as fh:
			keys |= {r[0] for r in csv.reader(fh) if len(r) >= 2 and r[1].strip()}
	return keys


class TestDoctypeLabels(unittest.TestCase):
	def test_every_doctype_and_report_has_vi(self):
		names = set()
		for pattern in ("nc_*/doctype/*/*.json", "nc_*/report/*/*.json"):
			for f in ROOT.glob(pattern):
				try:
					j = json.loads(f.read_text(encoding="utf-8"))
				except ValueError:
					continue
				if isinstance(j, dict) and str(j.get("name", "")).startswith("NC "):
					names.add(j["name"])
		self.assertTrue(names)
		self.assertEqual(sorted(names - _translated()), [])

	def test_shortcut_labels_match_translation(self):
		"""Lối tắt DocType phải có nhãn đúng bản dịch tên DocType; Report: nhãn chứa bản dịch."""
		tr = {}
		for f in (ROOT / "translations" / "vi.d").glob("*.csv"):
			with open(f, encoding="utf-8", newline="") as fh:
				for r in csv.reader(fh):
					if len(r) >= 2:
						tr[r[0]] = r[1]
		bad = []
		for f in (ROOT / "nc_core" / "workspace" / "normcore" / "shortcuts.d").glob("*.txt"):
			for line in f.read_text(encoding="utf-8").splitlines():
				p = line.split("|")
				if line.startswith("#") or len(p) < 4 or p[2] not in tr:
					continue
				label, target, kind = p[1], p[2], p[3]
				if (kind == "DocType" and label != tr[target]) or (
					kind == "Report" and tr[target].lower() not in label.lower()
				):
					bad.append((label, tr[target]))
		self.assertEqual(bad, [])
