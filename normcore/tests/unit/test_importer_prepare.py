"""FEAT-035 T02 — cột `virtual`, hàm `prepare`, `RowValueError` của khung nhập (ASM-035-01). Không cần site."""

import io
import unittest

from openpyxl import Workbook

from normcore.core import importer as im

S = im.ImportSet(
	key="thu_prepare",
	label="Thử prepare",
	doctype="NC Thu",
	key_field="he",
	key_fields=("nam", "he"),
	prepare="x.y.prepare",
	columns=(
		im.Column("nam", "Năm", "Int", required=True, example=2026),
		im.Column("he", "Hệ thống", "Data", required=True, example="A"),
		im.Column("ma_ngoai", "Mã ngoài", "Data", required=True, virtual=True, example="LIS-1"),
		im.Column("so", "Số", "Float", example=1),
		im.Column("phu", "Phụ", "Float"),
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


HEAD = ["Năm *", "Hệ thống *", "Mã ngoài *", "Số", "Phụ"]


def run(rows, prepare=None, mode=im.MODE_WRITE, store=None):
	store = {} if store is None else store
	writes = []

	def write(action, key, values):
		writes.append((action, key, dict(values)))
		store[key] = {**store.get(key, {}), **values}

	res = im.process(S, xlsx([HEAD, *rows]), mode, lambda k: store.get(k), write, prepare=prepare)
	return res, writes


def prep(values):
	if values["ma_ngoai"] == "BAD":
		raise im.RowValueError([("Mã ngoài", "không có trong ánh xạ"), ("Số", "âm")])
	if values["ma_ngoai"] == "ONE":
		raise im.RowValueError("Mã ngoài", "lỗi một")
	return {"dich_vu": "DV-" + values["ma_ngoai"]}


class TestPrepare(unittest.TestCase):
	def test_stored_columns_bo_cot_virtual(self):
		self.assertEqual([c.fieldname for c in S.stored_columns], ["nam", "he", "so", "phu"])

	def test_virtual_mac_dinh_false(self):
		self.assertFalse(im.Column("a", "A").virtual)
		self.assertIsNone(im.ImportSet("k", "k", "NC K", (im.Column("a", "A"),), "a").prepare)

	def test_cot_virtual_khong_duoc_ghi_va_prepare_bo_sung(self):
		res, writes = run([[2026, "A", "X1", 5, None]], prepare=prep)
		self.assertEqual(res.created, 1)
		_, key, values = writes[0]
		self.assertEqual(key, (2026, "A"))
		self.assertNotIn("ma_ngoai", values)
		self.assertEqual(values["dich_vu"], "DV-X1")
		self.assertEqual(values["so"], 5)
		self.assertNotIn("phu", values)  # ô trống không có khóa (giữ NULL)

	def test_row_value_error_nhieu_loi_o_ca_hai_che_do(self):
		for mode in (im.MODE_DRY, im.MODE_WRITE):
			res, writes = run(
				[[2026, "A", "BAD", 5, None], [2026, "B", "OK", 1, None]], prepare=prep, mode=mode
			)
			self.assertEqual(len(res.errors), 2)
			self.assertEqual([e.row for e in res.errors], [2, 2])
			self.assertEqual([e.column for e in res.errors], ["Mã ngoài", "Số"])
			self.assertEqual(res.created, 1)
			if mode == im.MODE_DRY:
				self.assertEqual(writes, [])
			else:
				self.assertEqual([w[1] for w in writes], [(2026, "B")])

	def test_row_value_error_mot_loi(self):
		res, _ = run([[2026, "A", "ONE", 5, None]], prepare=prep)
		self.assertEqual([e.text for e in res.errors], ['Dòng 2, cột "Mã ngoài": lỗi một'])
		self.assertEqual(res.created, 0)

	def test_nhap_lai_unchanged_va_cap_nhat(self):
		store = {}
		run([[2026, "A", "X1", 5, None]], prepare=prep, store=store)
		res, writes = run([[2026, "A", "X1", 5, None]], prepare=prep, store=store)
		self.assertEqual((res.unchanged, res.created, res.updated), (1, 0, 0))
		res, writes = run([[2026, "A", "X1", 7, None]], prepare=prep, store=store)
		self.assertEqual(res.updated, 1)
		self.assertEqual(writes[0][2], {"so": 7})

	def test_khong_prepare_van_bo_cot_virtual(self):
		res, writes = run([[2026, "A", "X1", 5, None]])
		self.assertEqual(res.created, 1)
		self.assertNotIn("ma_ngoai", writes[0][2])

	def test_bo_nhap_cu_khong_doi(self):
		plain = im.ImportSet("p", "p", "NC P", (im.Column("a", "A", required=True), im.Column("b", "B")), "a")
		self.assertEqual(plain.stored_columns, plain.columns)
		store = {}
		res = im.process(plain, xlsx([["A *", "B"], ["x", "y"]]), im.MODE_WRITE, store.get, lambda *a: None)
		self.assertEqual(res.created, 1)
