#!/usr/bin/env python3
"""Quét quy ước DocType của app normcore (CLAUDE.md mục 4).

Dùng: python3 scripts/check_conventions.py [thư_mục_gốc]
In mỗi lỗi một dòng `đường_dẫn: [mã luật] mô tả`; thoát 1 nếu có lỗi, 0 nếu sạch.
"""
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {"docs", "tham-khao", ".git", "node_modules"}
NO_LABEL_TYPES = {"Section Break", "Column Break", "Tab Break", "HTML", "Button"}
AUDITOR = "NC Auditor"
AUDITOR_FORBIDDEN = ("write", "create", "delete", "submit", "cancel", "amend")
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
    return errors


def run(root: Path) -> list:
    errors = []
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
