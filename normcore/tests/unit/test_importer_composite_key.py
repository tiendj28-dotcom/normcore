"""FEAT-016 T02 — khóa ghép và parse(unique=False) của khung nhập (ASM-124). Không cần site."""

import io
import unittest

from openpyxl import Workbook

from normcore.core import importer as im
from normcore.costing import accounting as a

COMPOSITE = im.ImportSet(
	key="thu_ghep",
	label="Thử khóa ghép",
	doctype="NC Thu",
	key_field="nam",
	key_fields=("nam", "ma"),
	columns=(
		im.Column("nam", "Năm", "Int", required=True, example=2026),
		im.Column("ma", "Mã", "Data", required=True, example="A"),
		im.Column("gia_tri", "Giá trị", "Float"),
	),
)


def xlsx(rows):
	wb = Workbook()
	ws = wb.active
	for r in rows:
		ws.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


class TestCompositeKey(unittest.TestCase):
	def test_keys(self):
		self.assertEqual(COMPOSITE.keys, ("nam", "ma"))
		self.assertTrue(COMPOSITE.composite)
		self.assertEqual(COMPOSITE.key_of({"nam": 2026, "ma": "A", "gia_tri": 1}), (2026, "A"))
		single = im.ImportSet("k", "k", "NC K", (im.Column("ma", "Mã"),), "ma")
		self.assertEqual(single.keys, ("ma",))
		self.assertFalse(single.composite)
		self.assertEqual(single.key_of({"ma": "X"}), "X")

	def test_trung_khoa_ghep_trong_tep(self):
		c = xlsx([["Năm *", "Mã *"], [2026, "A"], [2026, "B"], [2026, "a"]])
		valid, errors, _ = im.parse(COMPOSITE, c, "t.xlsx")
		self.assertEqual([ln for ln, _ in valid], [2, 3])
		self.assertEqual(len(errors), 1)
		self.assertEqual(errors[0].row, 4)
		self.assertIn("2026 / a", errors[0].message)
		self.assertIn("dòng 2", errors[0].message)

	def test_unique_false_bo_kiem_trung(self):
		c = xlsx([["Năm *", "Mã *"], [2026, "A"], [2026, "A"]])
		valid, errors, _ = im.parse(COMPOSITE, c, "t.xlsx", unique=False)
		self.assertEqual(len(valid), 2)
		self.assertEqual(errors, [])

	def test_process_truyen_khoa_tuple(self):
		c = xlsx([["Năm *", "Mã *", "Giá trị"], [2026, "A", 1], [2026, "B", 2], [2027, "A", 3]])
		db = {(2026, "A"): {"nam": 2026, "ma": "A", "gia_tri": 1.0}, (2026, "B"): {"gia_tri": 9.0}}
		wrote = []
		r = im.process(
			COMPOSITE, c, im.MODE_WRITE, db.get, lambda act, key, v: wrote.append((act, key, v)), filename="t.xlsx"
		)
		self.assertEqual((r.created, r.updated, r.unchanged, r.errors), (1, 1, 1, []))
		self.assertEqual(wrote, [("sua", (2026, "B"), {"gia_tri": 2.0}), ("tao", (2027, "A"), {"nam": 2027, "ma": "A", "gia_tri": 3.0})])

	def test_process_khong_quyen_sua_hien_khoa_ghep(self):
		c = xlsx([["Năm *", "Mã *", "Giá trị"], [2026, "A", 5]])
		r = im.process(
			COMPOSITE,
			c,
			im.MODE_WRITE,
			lambda k: {"gia_tri": 1.0},
			lambda *a: None,
			can_update=lambda k: False,
			filename="t.xlsx",
		)
		self.assertIn("2026 / A", r.errors[0].message)


def cc_exists(code):
	return code in {"K01", "HC"}


class TestParseLines(unittest.TestCase):
	H = ["Mã tài khoản *", "Tên tài khoản", "Mã trung tâm chi phí *", "Số tiền *"]

	def test_dong_trung_tai_khoan_hop_le(self):
		c = xlsx([self.H, ["61111.0", "Lương", "K01", 5], ["61111", "Phụ cấp", "K01", 6]])
		lines, errors = a.parse_lines(c, "kt.xlsx", cc_exists)
		self.assertEqual(errors, [])
		self.assertEqual([(ln["account_code"], ln["amount"], ln["source_row"]) for ln in lines], [("61111", 5.0, 2), ("61111", 6.0, 3)])

	def test_TC_ACCT_02_loi_dong(self):
		c = xlsx([self.H, ["61111", "", "K01", 5], ["61111", "", "K01", "abc"], ["61112", "", "K99", 7], [None, "", "K01", 1]])
		lines, errors = a.parse_lines(c, "kt.xlsx", cc_exists)
		self.assertEqual(len(lines), 1)
		self.assertEqual([(e.row, e.column) for e in errors], [(3, "Số tiền"), (4, "Mã trung tâm chi phí"), (5, "Mã tài khoản")])
		self.assertIn("K99", errors[1].message)

	def test_loi_muc_tep(self):
		with self.assertRaises(im.ImportFileError):
			a.parse_lines(b"khong phai excel", "kt.xlsx", cc_exists)
		with self.assertRaises(im.ImportFileError):
			a.parse_lines(xlsx([self.H, ["1", "", "K01", 1]]), "kt.csv", cc_exists)
		with self.assertRaises(im.ImportFileError):
			a.parse_lines(xlsx([["Mã tài khoản *", "Số tiền *"], ["1", 1]]), "kt.xlsx", cc_exists)
		with self.assertRaises(im.ImportFileError):
			a.parse_lines(xlsx([self.H]), "kt.xlsx", cc_exists)
