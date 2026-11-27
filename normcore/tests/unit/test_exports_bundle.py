"""Unit test FEAT-019 T04: exports/bundle.py (FR-OUT-009)."""

import io
import unittest
import zipfile
from datetime import datetime

from normcore.exports import bundle

META = {"run": "CR-1", "exported_at": datetime(2026, 1, 1), "exported_by": "u", "file_type": "Hồ sơ nén"}


class TestBundle(unittest.TestCase):
	def test_thu_tu_ten_trung_va_thong_tin(self):
		b = bundle.zip_files([("a.xlsx", b"1"), ("a.xlsx", b"2"), ("b.pdf", b"3")], META)
		zf = zipfile.ZipFile(io.BytesIO(b))
		self.assertEqual(zf.namelist(), ["a.xlsx", "a-2.xlsx", "b.pdf", bundle.INFO_NAME])
		self.assertEqual(zf.read("a-2.xlsx"), b"2")
		self.assertIn("CR-1", zf.read(bundle.INFO_NAME).decode())

	def test_tat_dinh(self):
		files = [("a.xlsx", b"1" * 100)]
		self.assertEqual(bundle.zip_files(files, META), bundle.zip_files(files, META))

	def test_ten_khong_duoi(self):
		names = zipfile.ZipFile(io.BytesIO(bundle.zip_files([("x", b""), ("x", b"")], META))).namelist()
		self.assertEqual(names[:2], ["x", "x-2"])
