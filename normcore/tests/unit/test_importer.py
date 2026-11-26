"""FEAT-004 — khung nhập Excel (FR-ADM-002, FR-RES-012, UC-008 luồng 2c). Không cần site."""

import io
import unittest
from datetime import date, datetime

from openpyxl import Workbook, load_workbook

from normcore.core import importer as im

_TC = unittest.TestCase()

SET = im.ImportSet(
	key="thu",
	label="Danh mục thử",
	doctype="NC Thu",
	key_field="ma",
	columns=(
		im.Column("ma", "Mã", "Data", required=True, example="VD-001"),
		im.Column("ten", "Tên", "Data", required=True, example="Tên ví dụ"),
		im.Column("so_luong", "Số lượng", "Int", example=3),
		im.Column("don_gia", "Đơn giá", "Float", example=1500.5),
		im.Column("ngay", "Ngày hiệu lực", "Date", example=date(2026, 1, 31)),
		im.Column("nhom", "Nhóm", "Select", options=("Một", "Hai"), example="Một"),
		im.Column("hoat_dong", "Hoạt động", "Check", example=1),
		im.Column("khoa", "Khoa", "Link", link_doctype="NC Department"),
	),
)

HEAD = ["Mã *", "Tên *", "Số lượng", "Đơn giá", "Ngày hiệu lực", "Nhóm", "Hoạt động", "Khoa"]
NONE5 = [None] * 5


def xlsx(rows):
	wb = Workbook()
	ws = wb.active
	for r in rows:
		ws.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


class Store:
	"""Kho giả thay cho lớp Frappe."""

	def __init__(self, existing=None):
		self.data = dict(existing or {})
		self.calls = []

	def lookup(self, key):
		return self.data.get(key)

	def write(self, action, key, values):
		self.calls.append((action, key, values))
		self.data.setdefault(key, {}).update(values)


def run(rows, mode="ghi", store=None, **kw):
	store = store or Store()
	res = im.process(SET, xlsx(rows), mode, store.lookup, store.write, **kw)
	return res, store


def test_FR_ADM_002_sinh_mau_co_tieu_de_va_dong_vi_du():
	ws = load_workbook(io.BytesIO(im.build_template(SET))).active
	rows = list(ws.iter_rows(values_only=True))
	assert len(rows) == 2
	assert list(rows[0]) == HEAD
	assert rows[1][0] == "VD-001" and rows[1][1] == "Tên ví dụ" and rows[1][5] == "Một"
	res, _ = run([list(r) for r in rows])  # nhập lại chính tệp mẫu: không lỗi
	assert res.errors == [] and res.created == 1


def test_FR_ADM_002_thieu_cot_bat_buoc():
	res, store = run([["Mã *", "Số lượng"], ["A", 1]])
	assert [e.text for e in res.errors] == ['Dòng tiêu đề (dòng 1), cột "Tên": thiếu cột bắt buộc']
	assert res.created == 0 and store.calls == []


def test_FR_ADM_002_o_bat_buoc_trong():
	res, store = run([HEAD, ["A", None], ["B", "Tên B"]])
	assert [e.text for e in res.errors] == ['Dòng 2, cột "Tên": ô bắt buộc đang để trống']
	assert (res.errors[0].row, res.errors[0].column) == (2, "Tên")
	assert res.created == 1 and [c[1] for c in store.calls] == ["B"]  # dòng lỗi bị bỏ qua


def test_FR_ADM_002_sai_kieu():
	res, _ = run(
		[
			HEAD,
			["A", "a", "abc", None, None, None, None, None],
			["B", "b", 1.5, None, None, None, None, None],
			["C", "c", None, "xx", None, None, None, None],
			["D", "d", None, None, "31/02/2026", None, None, None],
			["E", "e", None, None, None, "Ba", None, None],
			["F", "f", None, None, None, None, "có thể", None],
		]
	)
	assert [e.text for e in res.errors] == [
		'Dòng 2, cột "Số lượng": "abc" không phải số nguyên',
		'Dòng 3, cột "Số lượng": "1.5" không phải số nguyên',
		'Dòng 4, cột "Đơn giá": "xx" không phải số',
		'Dòng 5, cột "Ngày hiệu lực": "31/02/2026" không phải ngày hợp lệ (dd/mm/yyyy)',
		'Dòng 6, cột "Nhóm": "Ba" không nằm trong danh sách (Một, Hai)',
		'Dòng 7, cột "Hoạt động": "có thể" không hợp lệ (dùng 1/0 hoặc Có/Không)',
	]


def test_FR_ADM_002_kieu_hop_le_duoc_chuan_hoa():
	res, store = run(
		[
			HEAD,
			["A", "a", "5", "1,5", "03/02/2026", "hai", "Không", None],
			["B", "b", 2.0, 7, datetime(2026, 3, 4), "Một", "Có", None],
		]
	)
	assert res.errors == []
	assert store.data["A"] == {
		"ma": "A",
		"ten": "a",
		"so_luong": 5,
		"don_gia": 1.5,
		"ngay": "2026-02-03",
		"nhom": "Hai",
		"hoat_dong": 0,
	}
	assert store.data["B"]["so_luong"] == 2 and store.data["B"]["don_gia"] == 7.0
	assert store.data["B"]["ngay"] == "2026-03-04" and store.data["B"]["hoat_dong"] == 1


def test_FR_ADM_002_dong_trung():
	res, _ = run([HEAD, ["A", "a"], ["B", "b"], ["a", "a lại"], ["A", "a nữa"]])
	assert [e.text for e in res.errors] == [
		'Dòng 4, cột "Mã": trùng khóa "a" với dòng 2 trong cùng tệp',
		'Dòng 5, cột "Mã": trùng khóa "A" với dòng 2 trong cùng tệp',
	]
	assert res.created == 2


def test_FR_ADM_002_tep_rong():
	for data, msg in (
		(xlsx([]), "Tệp rỗng: không có dòng tiêu đề"),
		(xlsx([HEAD]), "Tệp rỗng: không có dòng dữ liệu"),
		(xlsx([HEAD, [None] * 8]), "Tệp rỗng: không có dòng dữ liệu"),
	):
		res = im.process(SET, data, "thu", Store().lookup, Store().write)
		assert [e.text for e in res.errors] == [msg] and res.errors[0].row is None


def test_FR_ADM_002_khong_phai_excel():
	for data in (b"", b"ma,ten\nA,b\n", b"PK\x03\x04hong", "văn bản".encode()):
		res = im.process(SET, data, "thu", Store().lookup, Store().write)
		assert [e.text for e in res.errors] == ["Tệp không phải Excel .xlsx"]
	res = im.process(SET, xlsx([HEAD, ["A", "a"]]), "thu", Store().lookup, Store().write, filename="mau.xls")
	assert [e.text for e in res.errors] == ["Tệp không phải Excel .xlsx"]


def test_FR_ADM_002_vuot_nguong_tep():
	big = [HEAD] + [[f"M{i}", "t"] for i in range(im.MAX_ROWS + 1)]
	res = im.process(SET, xlsx(big), "thu", Store().lookup, Store().write)
	assert [e.text for e in res.errors] == [f"Tệp có hơn {im.MAX_ROWS} dòng dữ liệu, hãy tách tệp"]
	res = im.process(SET, b"x" * (im.MAX_BYTES + 1), "thu", Store().lookup, Store().write)
	assert "vượt quá" in res.errors[0].text


def test_FR_ADM_002_che_do_thu_khong_ghi():
	store = Store({"A": {"ma": "A", "ten": "cũ"}})
	res, _ = run([HEAD, ["A", "mới"], ["B", "b"], ["C", None]], mode="thu", store=store)
	assert (res.created, res.updated, res.unchanged, len(res.errors)) == (1, 1, 0, 1)
	assert res.mode == "thu" and store.calls == []


def test_FR_ADM_002_nhap_lai_khong_tao_trung():
	rows = [HEAD, ["A", "a", 1], ["B", "b", 2]]
	store = Store()
	r1, _ = run(rows, store=store)
	r2, _ = run(rows, store=store)
	assert (r1.created, r1.updated, r1.unchanged) == (2, 0, 0)
	assert (r2.created, r2.updated, r2.unchanged, r2.errors) == (0, 0, 2, [])
	assert len(store.calls) == 2 and len(store.data) == 2
	# đổi một dòng: cập nhật; ô trống không xóa giá trị cũ (G5)
	r3, _ = run([HEAD, ["A", "a mới", None], ["B", "b", 2]], store=store)
	assert (r3.created, r3.updated, r3.unchanged) == (0, 1, 1)
	assert store.data["A"]["so_luong"] == 1 and store.data["A"]["ten"] == "a mới"


def test_FR_ADM_002_cot_la_canh_bao_va_thu_tu_tu_do():
	res, store = run([["Tên *", "Cột lạ", "mã"], ["t", "x", "A"]])
	assert res.errors == [] and store.data["A"]["ten"] == "t"
	assert res.warnings == ['Cột "Cột lạ" không thuộc mẫu, đã bỏ qua']


def test_FR_ADM_002_loi_ghi_cua_tung_dong_khong_lam_hong_dong_khac():
	store = Store()

	def write(action, key, values):
		if key == "B":
			raise ValueError("Ngày lệch")
		store.data[key] = values

	res = im.process(SET, xlsx([HEAD, ["A", "a"], ["B", "b"], ["C", "c"]]), "ghi", store.lookup, write)
	assert res.created == 2
	assert [e.text for e in res.errors] == ['Dòng 3, cột "Mã": Ngày lệch']


def test_FR_ADM_002_link_phai_ton_tai_va_quyen_sua():
	rows = [HEAD, ["A", "a", *NONE5, "K1"], ["B", "b", *NONE5, "KX"]]
	res, _ = run(rows, link_exists=lambda dt, v: v == "K1")
	assert [e.text for e in res.errors] == ['Dòng 3, cột "Khoa": "KX" không tồn tại trong NC Department']
	store = Store({"A": {"ma": "A", "ten": "cũ"}})
	res, _ = run([HEAD, ["A", "mới"]], store=store, can_update=lambda key: False)
	assert [e.text for e in res.errors] == ['Dòng 2, cột "Mã": bạn không có quyền sửa bản ghi "A"']


def test_FR_ADM_002_so_dong_la_dong_excel_ke_ca_dong_trong():
	res, _ = run([HEAD, ["A", "a"], [None] * 8, ["B", None]])
	assert [e.text for e in res.errors] == ['Dòng 4, cột "Tên": ô bắt buộc đang để trống']


def test_FR_ADM_002_so_trong_o_data_thanh_chuoi_va_so_nghin():
	_, store = run([HEAD, [123, "t", None, "1.234,5"]])
	assert store.data["123"]["ma"] == "123" and store.data["123"]["don_gia"] == 1234.5


def test_FR_ADM_002_so_do_dang_ky():
	assert im.get_import_set("nc_job_title").doctype == "NC Job Title"
	with _TC.assertRaises(KeyError):
		im.get_import_set("khong_co")
	im.register(SET)
	try:
		with _TC.assertRaises(ValueError):
			im.register(SET)
	finally:
		im.REGISTRY.pop("thu")
