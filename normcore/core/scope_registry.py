"""Sổ đăng ký phạm vi khoa và danh sách chặn xóa, đọc từ thư mục tệp (NORM-37, phần B).

Không import frappe: dùng được trong hooks.py, pytest thuần và scripts/check_conventions.py.
Mỗi DocType một tệp nên hai FEAT thêm DocType khác nhau không sửa chung một tệp (không conflict).

- normcore/core/scope_rules/<ten_doctype>.json: {"doctype", "department_field", "public_read"}.
  Tệp có "scoped": false (kèm "reason") ghi nhận DocType có trường khoa nhưng cố ý không hẹp theo khoa.
- normcore/core/delete_guard/<ten_doctype>.json: {"doctype"}: DocType bị chặn xóa khi còn được tham chiếu.
"""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCOPE_DIR = HERE / "scope_rules"
DELETE_GUARD_DIR = HERE / "delete_guard"


def file_stem(doctype: str) -> str:
	return doctype.lower().replace(" ", "_")


def _read_dir(directory: Path) -> list:
	out = []
	for path in sorted(Path(directory).glob("*.json")):
		data = json.loads(path.read_text(encoding="utf-8"))
		data["_file"] = path.name
		out.append(data)
	return out


def load_scope_rules(directory=None) -> dict:
	"""{doctype: {"department_field", "public_read"}} của các DocType hẹp theo khoa."""
	rules = {}
	for data in _read_dir(directory or SCOPE_DIR):
		if data.get("scoped") is False:
			continue
		rules[data["doctype"]] = {
			"department_field": data.get("department_field") or "department",
			"public_read": dict(data.get("public_read") or {}),
		}
	return rules


def load_declared_doctypes(directory=None) -> set:
	"""Mọi DocType có tệp scope_rules, kể cả khai "scoped": false."""
	return {data["doctype"] for data in _read_dir(directory or SCOPE_DIR)}


def scope_doctypes(directory=None) -> list:
	return sorted(load_scope_rules(directory))


def load_delete_guard(directory=None) -> list:
	return sorted(data["doctype"] for data in _read_dir(directory or DELETE_GUARD_DIR))
