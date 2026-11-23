#!/usr/bin/env python3
"""Quét quy ước DocType của app normcore (CLAUDE.md mục 4).

Dùng: python3 scripts/check_conventions.py [thư_mục_gốc]
In mỗi lỗi một dòng `đường_dẫn: [mã luật] mô tả`; thoát 1 nếu có lỗi, 0 nếu sạch.
"""

import csv
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"docs", "tham-khao", ".git", "node_modules"}
NO_LABEL_TYPES = {"Section Break", "Column Break", "Tab Break", "HTML", "Button"}
AUDITOR = "NC Auditor"
AUDITOR_FORBIDDEN = ("write", "create", "delete", "submit", "cancel", "amend")
ROLES = (
	"NC Clinician",
	"NC Department Head",
	"NC Council Member",
	"NC Finance",
	"NC Resource Manager",
	"NC Document Controller",
	"NC Director",
	"NC Consultant",
	"NC Admin",
	"NC Auditor",
)
# Ma trận quyền (docs/data-model.md mục 4), theo thứ tự ROLES. R = đọc; W = đọc, sửa, tạo (ASM-015); - = không.
# "(khoa)" và "A" (duyệt theo luồng) không phải quyền DocType nên quy về R / W.
MATRIX = {
	"Dịch vụ kỹ thuật, chuyên khoa": "R R R R R W R R W R",
	"Quy trình": "W W R R R R R R R R",
	"Bộ tham số, chức danh, loại giá": "- - - W R - R R W R",
	"Bộ định mức": "W W - R R - R R R R",
	"Mặt hàng, đơn giá, thiết bị, phòng": "R R - W W - R R W R",
	"Loại thiết bị, hồ sơ tuân thủ": "R R - R W - R R W R",
	"Hệ thống xét nghiệm, kế hoạch chất lượng, chương trình ngoại kiểm": "W W - R R - R R R R",
	"Lần tính giá, kết quả, đối soát": "- - - W - - R - R R",
	"Số liệu kế toán, sản lượng, phân bổ": "- - - W - - R - R R",
	"Nhật ký AI, sổ sự kiện": "- - - - - - R - R R",
	# Ma trận không có dòng riêng: căn cứ ghi ở đây (ASM-008, G1 của NORM-12)
	"NC Department (ASM-008: theo dòng Dịch vụ kỹ thuật)": "R R R R R W R R W R",
	"NC Cost Center (G1: Admin, Finance ghi)": "R R R W R R R R W R",
}
DOCTYPE_ROW = {
	"NC Technical Service": "Dịch vụ kỹ thuật, chuyên khoa",
	"NC Specialty": "Dịch vụ kỹ thuật, chuyên khoa",
	"NC Clinical Procedure": "Quy trình",
	"NC Costing Parameter Set": "Bộ tham số, chức danh, loại giá",
	"NC Job Title": "Bộ tham số, chức danh, loại giá",
	"NC Item": "Mặt hàng, đơn giá, thiết bị, phòng",
	"NC Item Price": "Mặt hàng, đơn giá, thiết bị, phòng",
	"NC Price Category": "Bộ tham số, chức danh, loại giá",
	"NC Norm Set": "Bộ định mức",
	"NC Equipment": "Mặt hàng, đơn giá, thiết bị, phòng",
	"NC Room": "Mặt hàng, đơn giá, thiết bị, phòng",
	"NC Equipment Type": "Loại thiết bị, hồ sơ tuân thủ",
	"NC Test System": "Hệ thống xét nghiệm, kế hoạch chất lượng, chương trình ngoại kiểm",
	"NC Costing Run": "Lần tính giá, kết quả, đối soát",
	"NC Accounting Import": "Số liệu kế toán, sản lượng, phân bổ",
	"NC Account Mapping": "Số liệu kế toán, sản lượng, phân bổ",
	"NC Service Volume": "Số liệu kế toán, sản lượng, phân bổ",
	"NC Cost Center Driver": "Số liệu kế toán, sản lượng, phân bổ",
	"NC Allocation Rule": "Số liệu kế toán, sản lượng, phân bổ",
	"NC Service Cost": "Lần tính giá, kết quả, đối soát",
	"NC AI Log": "Nhật ký AI, sổ sự kiện",
	"NC Audit Event": "Nhật ký AI, sổ sự kiện",
	"NC Department": "NC Department (ASM-008: theo dòng Dịch vụ kỹ thuật)",
	"NC Cost Center": "NC Cost Center (G1: Admin, Finance ghi)",
}
# Q2 của NORM-12: duy nhất NC Admin được xóa, và chỉ trên các DocType danh mục (FEAT-005 thêm NC Specialty)
DELETE_ALLOWED = {
	"NC Admin": {
		"NC Department",
		"NC Cost Center",
		"NC Job Title",
		"NC Technical Service",
		"NC Specialty",
		"NC Equipment",
		"NC Room",
		"NC Equipment Type",
		"NC Price Category",
	}
}
PERM_TYPES = ("read", "write", "create", "delete", "submit", "cancel", "amend")
SNAKE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def find_doctype_files(root: Path):
	for path in sorted(root.glob("**/doctype/*/*.json")):
		rel = path.relative_to(root)
		if any(part in SKIP_DIRS for part in rel.parts[:-1]):
			continue
		if path.stem != path.parent.name:  # chỉ file <thư_mục>/<thư_mục>.json
			continue
		yield path


def check_doctype(data: dict, path: str) -> list:
	errors = []

	def err(code, msg):
		errors.append(f"{path}: [{code}] {msg}")

	name = data.get("name", "")
	is_table = data.get("istable") in (1, True, "1")

	if not str(name).startswith("NC "):
		err("NC-01", f"tên DocType '{name}' không bắt đầu bằng 'NC '")

	seen = set()
	for f in data.get("fields") or []:
		if not isinstance(f, dict):
			err("NC-02", "mục trong fields không phải đối tượng")
			continue
		fname = f.get("fieldname")
		ftype = f.get("fieldtype", "")
		if fname is not None:
			if not isinstance(fname, str):
				err("NC-02", f"fieldname {fname!r} không phải chuỗi")
				seen.add(fname)
				continue
			if not SNAKE.match(fname):
				err("NC-02", f"fieldname '{fname}' không phải snake_case tiếng Anh")
			if fname in seen:
				err("NC-02", f"fieldname '{fname}' bị trùng trong DocType")
			seen.add(fname)
		elif ftype not in NO_LABEL_TYPES:
			err("NC-02", "field thiếu fieldname")
		if ftype not in NO_LABEL_TYPES and not str(f.get("label") or "").strip():
			err("NC-03", f"field '{fname}' thiếu label")

	if not is_table:
		if data.get("track_changes") not in (1, True, "1"):
			err("NC-04", "DocType chưa bật track_changes")
		if not data.get("permissions"):
			err("NC-05", "DocType không có permissions")

	for perm in data.get("permissions") or []:
		if isinstance(perm, dict) and perm.get("role") == AUDITOR:
			bad = [p for p in AUDITOR_FORBIDDEN if perm.get(p) in (1, True, "1")]
			if bad:
				err("NC-06", f"{AUDITOR} có quyền không được phép: {', '.join(bad)}")
	if not is_table:
		errors.extend(check_permissions(data, path))
	return errors


def _flag(perm, ptype):
	return perm.get(ptype) in (1, True, "1")


def check_permissions(data: dict, path: str) -> list:
	"""FR-ACC-002, TC-ACC-04: không cấp quyền cho All; quyền từng vai trò khớp ma trận mục 4."""
	errors = []
	name = data.get("name", "")
	perms = [p for p in data.get("permissions") or [] if isinstance(p, dict)]
	for p in perms:
		if p.get("role") == "All" and any(_flag(p, t) for t in PERM_TYPES):
			errors.append(f"{path}: [NC-07] cấp quyền cho vai trò All")
	row = DOCTYPE_ROW.get(name)
	if row is None:
		errors.append(f"{path}: [NC-08] DocType '{name}' chưa có dòng ma trận trong DOCTYPE_ROW")
		return errors
	codes = MATRIX[row].split()
	if len(codes) != len(ROLES):
		errors.append(f"{path}: [NC-08] dòng ma trận '{row}' có {len(codes)} cột, cần {len(ROLES)}")
		return errors
	granted = {}
	for p in perms:
		role = p.get("role")
		if role == "All":
			continue
		if role not in ROLES:
			errors.append(f"{path}: [NC-08] vai trò '{role}' không thuộc 10 vai trò NC")
			continue
		granted.setdefault(role, set()).update(t for t in PERM_TYPES if _flag(p, t))
	for role, code in zip(ROLES, codes, strict=True):
		expected = {"R": {"read"}, "W": {"read", "write", "create"}, "-": set()}[code]
		if name in DELETE_ALLOWED.get(role, ()):
			expected = expected | {"delete"}
		got = granted.get(role, set())
		if got != expected:
			errors.append(
				f"{path}: [NC-08] {role} có quyền {sorted(got)}, ma trận ({row}) yêu cầu {sorted(expected)}"
			)
	return errors


VI_CSV = "normcore/translations/vi.csv"


def _csv_key(row):
	return (row[0], row[2] if len(row) > 2 else "")


def check_vi_csv(root: Path) -> list:
	"""NORM-24: vi.csv xếp theo cột đầu (rồi cột ngữ cảnh) và không trùng khóa (cột 1 + ngữ cảnh)."""
	path = root / VI_CSV
	if not path.exists():
		return []
	with open(path, encoding="utf-8", newline="") as fh:
		rows = [r for r in csv.reader(fh) if r]
	errors = []
	seen = set()
	for n, row in enumerate(rows, 1):
		key = _csv_key(row)
		if key in seen:
			errors.append(f"{VI_CSV}: [NC-09] khóa trùng '{key[0]}' (ngữ cảnh '{key[1]}') ở dòng {n}")
		seen.add(key)
	keys = [_csv_key(r) for r in rows]
	for n in range(1, len(keys)):
		if keys[n] < keys[n - 1]:
			errors.append(
				f"{VI_CSV}: [NC-10] chưa sắp xếp theo cột đầu: dòng {n + 1} '{keys[n][0]}' đứng sau '{keys[n - 1][0]}'"
			)
			break
	return errors


def run(root: Path) -> list:
	errors = check_vi_csv(root)
	for path in find_doctype_files(root):
		rel = str(path.relative_to(root))
		try:
			data = json.loads(path.read_text(encoding="utf-8"))
		except (OSError, ValueError) as e:
			errors.append(f"{rel}: [NC-00] không đọc được JSON: {e}")
			continue
		if isinstance(data, dict) and data.get("doctype") != "DocType":
			continue  # JSON phụ (test_records, báo cáo...) không phải định nghĩa DocType
		if not isinstance(data, dict):
			errors.append(f"{rel}: [NC-00] JSON không phải đối tượng")
			continue
		errors.extend(check_doctype(data, rel))
	return errors


def main(argv=None) -> int:
	argv = sys.argv[1:] if argv is None else argv
	root = Path(argv[0]) if argv else Path(__file__).resolve().parent.parent
	errors = run(root)
	for e in errors:
		print(e)
	return 1 if errors else 0


if __name__ == "__main__":
	sys.exit(main())
