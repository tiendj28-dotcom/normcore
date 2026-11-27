"""Khung nhập Excel dùng chung (FEAT-004, ADR-012, FR-ADM-002, FR-RES-012).

Module thuần Python: không import `frappe`. Việc tra cứu, kiểm quyền và ghi CSDL do lớp Frappe
(`normcore/api/importer.py`) truyền vào dưới dạng hàm gọi lại.
"""

from __future__ import annotations

import io
import re
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime

from openpyxl import Workbook, load_workbook

MAX_BYTES = 5 * 1024 * 1024  # G8
MAX_ROWS = 5000  # G8
MODE_DRY = "thu"
MODE_WRITE = "ghi"

NOT_XLSX = "Tệp không phải Excel .xlsx"
TRUE_VALUES = {"1", "có", "co", "true", "x", "yes"}
FALSE_VALUES = {"0", "không", "khong", "false", "no"}


class ImportFileError(ValueError):
	"""Lỗi mức tệp (không phải .xlsx, thiếu cột, tệp rỗng, quá lớn): không tạo bản ghi nào."""


@dataclass(frozen=True)
class Column:
	fieldname: str
	label: str
	fieldtype: str = "Data"  # Data, Int, Float, Select, Date, Check, Link
	required: bool = False
	options: tuple = ()
	link_doctype: str | None = None
	example: object = None
	virtual: bool = False  # đọc, kiểm Link, đưa vào `prepare` nhưng không so sánh, không ghi (ASM-035-01)


class RowValueError(ValueError):
	"""Lỗi của một dòng do `prepare` ném: danh sách (nhãn cột, thông báo)."""

	def __init__(self, errors, message=None):
		if isinstance(errors, str):
			errors = [(errors, message or "")]
		self.errors = list(errors)
		super().__init__("; ".join(f"{c}: {m}" for c, m in self.errors))


@dataclass(frozen=True)
class ImportSet:
	key: str
	label: str
	doctype: str
	columns: tuple
	key_field: str
	key_fields: tuple = ()  # khóa ghép (ASM-124); rỗng = chỉ dùng key_field
	prepare: str | None = None  # đường dẫn hàm lớp Frappe chuẩn bị dòng (ASM-035-01)

	@property
	def stored_columns(self) -> tuple:
		return tuple(c for c in self.columns if not c.virtual)

	@property
	def keys(self) -> tuple:
		return tuple(self.key_fields) or (self.key_field,)

	@property
	def composite(self) -> bool:
		return bool(self.key_fields)

	def key_of(self, values: dict):
		"""Khóa của một dòng: chuỗi/giá trị khi một khóa, tuple khi khóa ghép."""
		if self.composite:
			return tuple(values.get(k) for k in self.keys)  # khóa ghép có thành phần tùy chọn (ASM-026-13)
		return values[self.key_field]

	def column(self, fieldname):
		return next(c for c in self.columns if c.fieldname == fieldname)


@dataclass
class RowError:
	row: int | None
	column: str | None
	message: str

	@property
	def text(self):
		if self.row is None:
			return self.message
		if self.row == 1:
			return f'Dòng tiêu đề (dòng 1), cột "{self.column}": {self.message}'
		return f'Dòng {self.row}, cột "{self.column}": {self.message}'

	def as_dict(self):
		return {"row": self.row, "column": self.column, "message": self.message, "text": self.text}


@dataclass
class ImportResult:
	mode: str
	created: int = 0
	updated: int = 0
	unchanged: int = 0
	errors: list = field(default_factory=list)
	warnings: list = field(default_factory=list)

	def as_dict(self):
		return {
			"mode": self.mode,
			"created": self.created,
			"updated": self.updated,
			"unchanged": self.unchanged,
			"error_count": len(self.errors),
			"errors": [e.as_dict() for e in self.errors],
			"warnings": list(self.warnings),
		}


REGISTRY: dict[str, ImportSet] = {}


def register(import_set: ImportSet):
	if import_set.key in REGISTRY:
		raise ValueError(f"Bộ nhập '{import_set.key}' đã được đăng ký")
	REGISTRY[import_set.key] = import_set
	return import_set


def get_import_set(key: str) -> ImportSet:
	return REGISTRY[key]


# --- tiêu đề -----------------------------------------------------------------


def header_label(col: Column) -> str:
	return col.label + (" *" if col.required else "")


def _norm_header(text) -> str:
	t = re.sub(r"\s+", " ", str(text or "")).strip()
	t = re.sub(r"\s*\*$", "", t)
	return t.casefold()


def build_template(import_set: ImportSet) -> bytes:
	wb = Workbook()
	ws = wb.active
	ws.title = "Mẫu"[:31]
	ws.append([header_label(c) for c in import_set.columns])
	ws.append([c.example for c in import_set.columns])
	for c, cells in zip(import_set.columns, ws.iter_cols(min_row=1, max_row=2), strict=False):
		ws.column_dimensions[cells[0].column_letter].width = max(14, len(header_label(c)) + 4)
		if isinstance(c.example, date):
			cells[1].number_format = "dd/mm/yyyy"
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


# --- chuẩn hóa giá trị -------------------------------------------------------


def _is_blank(v) -> bool:
	return v is None or (isinstance(v, str) and not v.strip())


def _number(v):
	if isinstance(v, bool):
		raise ValueError
	if isinstance(v, int | float):
		return float(v)
	s = str(v).strip().replace(" ", "")
	if "," in s and "." in s:
		s = s.replace(".", "").replace(",", ".")
	elif "," in s:
		s = s.replace(",", ".")
	return float(s)


def _fmt(v) -> str:
	if isinstance(v, float) and v == int(v):
		return str(int(v))
	return str(v)


def normalize(col: Column, v):
	"""Trả giá trị đã chuẩn hóa kiểu; ném ValueError(thông báo) nếu sai."""
	t = col.fieldtype
	if t in ("Data", "Link"):
		return _fmt(v).strip() if not isinstance(v, str) else v.strip()
	if t == "Int":
		try:
			n = _number(v)
		except ValueError:
			raise ValueError(f'"{_fmt(v)}" không phải số nguyên') from None
		if n != int(n):
			raise ValueError(f'"{v}" không phải số nguyên')
		return int(n)
	if t == "Float":
		try:
			return _number(v)
		except ValueError:
			raise ValueError(f'"{_fmt(v)}" không phải số') from None
	if t == "Date":
		if isinstance(v, datetime):
			return v.date().isoformat()
		if isinstance(v, date):
			return v.isoformat()
		s = str(v).strip()
		for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
			try:
				return datetime.strptime(s, fmt).date().isoformat()
			except ValueError:
				pass
		raise ValueError(f'"{s}" không phải ngày hợp lệ (dd/mm/yyyy)')
	if t == "Select":
		s = str(v).strip()
		for o in col.options:
			if o.casefold() == s.casefold():
				return o
		raise ValueError(f'"{s}" không nằm trong danh sách ({", ".join(col.options)})')
	if t == "Check":
		s = _fmt(v).strip().casefold()
		if s in TRUE_VALUES:
			return 1
		if s in FALSE_VALUES:
			return 0
		raise ValueError(f'"{v}" không hợp lệ (dùng 1/0 hoặc Có/Không)')
	raise ValueError(f"Kiểu cột không hỗ trợ: {t}")


def normalize_existing(col: Column, v):
	"""Đưa giá trị đang lưu về cùng dạng với `normalize` để so sánh."""
	if _is_blank(v):
		return None
	if isinstance(v, date):
		return v.isoformat() if not isinstance(v, datetime) else v.date().isoformat()
	try:
		return normalize(col, v)
	except ValueError:
		return v


# --- đọc tệp -----------------------------------------------------------------


def _file_error(msg):
	return [RowError(None, None, msg)]


def _read_rows(content: bytes, filename):
	"""Trả (rows, lỗi tệp). rows: list[(số_dòng_excel, tuple)]."""
	if filename is not None and not str(filename).lower().endswith(".xlsx"):
		return None, _file_error(NOT_XLSX)
	if len(content) > MAX_BYTES:
		return None, _file_error(f"Tệp vượt quá {MAX_BYTES // (1024 * 1024)} MB")
	if not content[:4] == b"PK\x03\x04" or not zipfile.is_zipfile(io.BytesIO(content)):
		return None, _file_error(NOT_XLSX)
	try:
		wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
		ws = wb.worksheets[0]
		rows = []
		for i, r in enumerate(ws.iter_rows(values_only=True), start=1):
			rows.append((i, tuple(r)))
			if i > MAX_ROWS + 1 + 1000 and all(_is_blank(x) for x in r):
				break
	except Exception:
		return None, _file_error(NOT_XLSX)
	while rows and all(_is_blank(x) for x in rows[-1][1]):
		rows.pop()
	return rows, []


def parse(import_set: ImportSet, content: bytes, filename=None, unique=True):
	"""Đọc và kiểm kiểu từng dòng. Trả (dòng hợp lệ, lỗi, cảnh báo).

	Dòng hợp lệ: list[(số_dòng, values)] với values chỉ gồm các ô không trống (đã chuẩn hóa).
	Chưa kiểm Link, quyền và trùng với dữ liệu đang có — xem `process`.
	`unique=False` bỏ kiểm trùng khóa trong tệp (dòng kế toán trùng tài khoản là hợp lệ, ASM-124).
	"""
	rows, errors = _read_rows(content, filename)
	if errors:
		return [], errors, []
	if not rows:
		return [], _file_error("Tệp rỗng: không có dòng tiêu đề"), []
	header = rows[0][1]
	index, warnings = {}, []
	by_name = {_norm_header(c.label): c for c in import_set.columns}
	for pos, h in enumerate(header):
		if _is_blank(h):
			continue
		col = by_name.get(_norm_header(h))
		if col is None or col.fieldname in index:
			warnings.append(f'Cột "{str(h).strip()}" không thuộc mẫu, đã bỏ qua')
		else:
			index[col.fieldname] = pos
	missing = [c for c in import_set.columns if c.required and c.fieldname not in index]
	if missing:
		return [], [RowError(1, c.label, "thiếu cột bắt buộc") for c in missing], warnings
	data = rows[1:]
	if not data:
		return [], _file_error("Tệp rỗng: không có dòng dữ liệu"), warnings
	if len(data) > MAX_ROWS:
		return [], _file_error(f"Tệp có hơn {MAX_ROWS} dòng dữ liệu, hãy tách tệp"), warnings

	valid, seen = [], {}
	for line, cells in data:
		if all(_is_blank(x) for x in cells):
			continue
		values, row_errors = {}, []
		for col in import_set.columns:
			pos = index.get(col.fieldname)
			raw = cells[pos] if pos is not None and pos < len(cells) else None
			if _is_blank(raw):
				if col.required:
					row_errors.append(RowError(line, col.label, "ô bắt buộc đang để trống"))
				continue
			try:
				values[col.fieldname] = normalize(col, raw)
			except ValueError as e:
				row_errors.append(RowError(line, col.label, str(e)))
		if unique and not row_errors:
			key = " / ".join(str(values.get(k, "")) for k in import_set.keys)
			norm_key = key.casefold()
			if norm_key in seen:
				label = import_set.column(import_set.key_field).label
				row_errors.append(
					RowError(line, label, f'trùng khóa "{key}" với dòng {seen[norm_key]} trong cùng tệp')
				)
			else:
				seen[norm_key] = line
		if row_errors:
			errors.extend(row_errors)
		else:
			valid.append((line, values))
	if not valid and not errors:
		return [], _file_error("Tệp rỗng: không có dòng dữ liệu"), warnings
	return valid, errors, warnings


# --- chạy nhập ---------------------------------------------------------------


def process(
	import_set: ImportSet,
	content: bytes,
	mode: str,
	lookup: Callable,
	write: Callable,
	*,
	link_exists: Callable | None = None,
	can_update: Callable | None = None,
	filename=None,
	prepare: Callable | None = None,
) -> ImportResult:
	"""Kiểm và (ở chế độ ghi) ghi từng dòng.

	lookup(key) -> dict giá trị đang lưu (theo fieldname) hoặc None nếu chưa có.
	write("tao"|"sua", key, values) -> ghi một dòng; ném lỗi nếu CSDL từ chối (thành lỗi của dòng).
	link_exists(doctype, value) -> bool; can_update(key) -> bool (kiểm quyền sửa dòng cập nhật).
	prepare(values) -> dict bổ sung giá trị, hoặc ném RowValueError (lỗi dòng); chạy ở cả hai chế độ.
	"""
	result = ImportResult(mode=mode)
	valid, errors, result.warnings = parse(import_set, content, filename)
	result.errors = list(errors)
	key_col = import_set.column(import_set.key_field)
	columns = {c.fieldname: c for c in import_set.columns}
	for line, values in valid:
		bad = False
		if link_exists:
			for col in import_set.columns:
				v = values.get(col.fieldname)
				if col.fieldtype == "Link" and v is not None and not link_exists(col.link_doctype, v):
					result.errors.append(
						RowError(line, col.label, f'"{v}" không tồn tại trong {col.link_doctype}')
					)
					bad = True
		if bad:
			continue
		if prepare:
			try:
				values = {**values, **prepare(values)}
			except RowValueError as e:
				result.errors.extend(RowError(line, c, m) for c, m in e.errors)
				continue
		virtual = {c.fieldname for c in import_set.columns if c.virtual}
		values = {k: v for k, v in values.items() if k not in virtual}
		key = import_set.key_of(values)
		existing = lookup(key)
		if existing is None:
			action = "tao"
		else:
			changed = {
				k: v
				for k, v in values.items()
				if k not in import_set.keys
				and k in columns
				and normalize_existing(columns[k], existing.get(k)) != v
			}
			if not changed:
				result.unchanged += 1
				continue
			if can_update and not can_update(key):
				shown = " / ".join(map(str, key)) if import_set.composite else key
				result.errors.append(
					RowError(line, key_col.label, f'bạn không có quyền sửa bản ghi "{shown}"')
				)
				continue
			action, values = "sua", changed
		if mode == MODE_WRITE:
			try:
				write(action, key, values)
			except Exception as e:
				result.errors.append(RowError(line, key_col.label, str(e)))
				continue
		if action == "tao":
			result.created += 1
		else:
			result.updated += 1
	result.errors.sort(key=lambda e: e.row or 0)
	return result
