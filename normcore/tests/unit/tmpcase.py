"""Lớp nền cho test cần thư mục tạm, không dùng pytest (bước `bench run-tests` của CI không cài pytest)."""

import tempfile
import unittest
from pathlib import Path


class TmpCase(unittest.TestCase):
	def setUp(self):
		td = tempfile.TemporaryDirectory()
		self.addCleanup(td.cleanup)
		self.tmp_path = Path(td.name)
