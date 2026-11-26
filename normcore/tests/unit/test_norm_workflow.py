import unittest
from pathlib import Path

from normcore.norm import workflow as w

DOC = Path(__file__).resolve().parents[3] / "docs" / "data-model.md"


class TestNormWorkflow(unittest.TestCase):
	def test_next_status(self):
		self.assertEqual(w.next_status("Nháp", "confirm_set"), "Đã xác nhận chuyên môn")
		self.assertEqual(w.next_status("Đã xác nhận chuyên môn", "lock_set"), "Đã khóa")
		self.assertEqual(w.next_status("Đã xác nhận chuyên môn", "return_set"), "Nháp")
		self.assertEqual(w.next_status("Đã khóa", "replace"), "Đã thay thế")

	def test_khong_khoa_tu_nhap(self):
		self.assertIsNone(w.next_status("Nháp", "lock_set"))
		self.assertIsNone(w.next_status("Đã khóa", "confirm_set"))

	def test_chi_nhap_sua_duoc(self):
		self.assertEqual(w.EDITABLE, {"Nháp"})

	def test_vai_tro(self):
		self.assertEqual(w.ROLE_OF_ACTION["confirm_set"], ("NC Department Head",))
		self.assertEqual(w.ROLE_OF_ACTION["lock_set"], ("NC Finance",))

	def test_khop_data_model_5_2(self):
		text = DOC.read_text(encoding="utf-8")
		sec = text.split("### 5.2", 1)[1].split("### 5.3", 1)[0]
		rows = [
			[c.strip() for c in ln.strip("|").split("|")]
			for ln in sec.splitlines()
			if ln.startswith("|") and not ln.startswith("| :--") and not ln.startswith("| Từ")
		]
		doc = {(r[0], r[2]) for r in rows}
		code = {(a, b) for (a, _), b in w.TRANSITIONS.items()}
		self.assertEqual(doc, code)
