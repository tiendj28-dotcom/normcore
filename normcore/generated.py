"""Ghép mảnh theo FEAT thành tệp mà Frappe đọc (NORM-60). Python thuần: không import frappe ở mức module.

Nguồn (mỗi FEAT/issue một tệp, hai nhánh song song chỉ thêm tệp khác tên nên không conflict):
- normcore/translations/vi.d/*.csv                 -> normcore/translations/vi.csv (không commit)
- normcore/nc_core/workspace/normcore/shortcuts.d/*.txt -> .../normcore.json (không commit)
Thứ tự ghép: `00-base` trước, rồi theo tên tệp. Gọi từ: before_install, before_migrate (hook Frappe),
normcore/tests/conftest.py và scripts/build_generated.py.
"""

import csv
import json
from pathlib import Path

REL = Path("normcore/nc_core/workspace/normcore")
VI_REL = Path("normcore/translations/vi.csv")
VI_DIR = Path("normcore/translations/vi.d")
HEADER = {
	"id": "nc-imp-h",
	"type": "header",
	"data": {"text": '<span class="h4">Normcore</span>', "col": 12},
}
BASE = {
	"charts": [],
	"creation": "2026-11-21 00:00:00.000000",
	"docstatus": 0,
	"doctype": "Workspace",
	"for_user": "",
	"hide_custom": 0,
	"idx": 0,
	"is_hidden": 0,
	"label": "Normcore",
	"links": [],
	"modified": "2026-11-26 10:00:00.000000",
	"modified_by": "Administrator",
	"module": "NC Core",
	"name": "Normcore",
	"number_cards": [],
	"owner": "Administrator",
	"parent_page": "",
	"public": 1,
	"quick_lists": [],
	"roles": [],
	"sequence_id": 1,
	"title": "Normcore",
}


def fragment_files(directory: Path, pattern: str) -> list:
	"""Các mảnh trong thư mục: `00-base.*` trước, rồi theo tên tệp."""
	if not directory.is_dir():
		return []
	return sorted(directory.glob(pattern), key=lambda p: (not p.name.startswith("00-base"), p.name))


# ---------- bản dịch ----------


def csv_key(row):
	return (row[0], row[2] if len(row) > 2 else "")


def merge_translations(root: Path):
	"""Ghép vi.d/*.csv. Trả (rows đã sắp, errors). Dòng trùng hệt bị bỏ; trùng khóa khác bản dịch là NC-09."""
	rows, errors, seen = [], [], {}
	for path in fragment_files(root / VI_DIR, "*.csv"):
		with open(path, encoding="utf-8", newline="") as fh:
			for row in csv.reader(fh):
				if not row:
					continue
				key = csv_key(row)
				if key in seen:
					prev_row, prev_file = seen[key]
					if prev_row != row:
						errors.append(
							f"{VI_DIR}: [NC-09] khóa trùng '{key[0]}' (ngữ cảnh '{key[1]}') "
							f"khác bản dịch giữa {prev_file} và {path.name}"
						)
					continue
				seen[key] = (row, path.name)
				rows.append(row)
	return sorted(rows, key=csv_key), errors


def write_translations(root: Path) -> bool:
	"""Ghi vi.csv từ mảnh. Trả True nếu tệp đổi. Lỗi ghép: ValueError, không ghi."""
	if not (root / VI_DIR).is_dir():
		return False
	rows, errors = merge_translations(root)
	if errors:
		raise ValueError("; ".join(errors))
	dst = root / VI_REL
	dst.parent.mkdir(parents=True, exist_ok=True)
	tmp = dst.with_suffix(".tmp")
	with open(tmp, "w", encoding="utf-8", newline="") as fh:
		csv.writer(fh, lineterminator="\n").writerows(rows)
	new = tmp.read_bytes()
	tmp.unlink()
	if dst.exists() and dst.read_bytes() == new:
		return False
	dst.write_bytes(new)
	return True


# ---------- Workspace ----------


def _dedupe(rows: list, where: str) -> list:
	"""Bỏ dòng trùng hệt; cùng id khác nội dung là lỗi NC-11."""
	uniq = []
	for r in rows:
		if r in uniq:
			continue
		if any(u[0] == r[0] for u in uniq):
			raise ValueError(f"{where}: [NC-11] id lối tắt trùng nhưng khác nội dung: {r[0]}")
		uniq.append(r)
	return uniq


def read_shortcuts(path: Path) -> list:
	rows = []
	for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
		line = line.strip()
		if not line or line.startswith("#"):
			continue
		parts = line.split("|")
		if len(parts) != 5:
			raise ValueError(f"{path}:{n}: cần 5 cột id|nhãn|link_to|loại|doc_view")
		rows.append(parts)
	return _dedupe(rows, str(path))


def read_sources(root: Path) -> list:
	"""Có shortcuts.d/ thì ghép các mảnh; không thì đọc shortcuts.txt (bố cục cũ)."""
	frag_dir = root / REL / "shortcuts.d"
	if frag_dir.is_dir():
		rows = []
		for path in fragment_files(frag_dir, "*.txt"):
			rows.extend(read_shortcuts(path))
		return _dedupe(rows, str(REL / "shortcuts.d"))
	return read_shortcuts(root / REL / "shortcuts.txt")


def render(rows: list, modified: str | None = None) -> str:
	blocks = [HEADER]
	shortcuts = []
	custom_blocks = []
	# Custom HTML Block (loại CustomBlock, link_to trống): đặt ngay sau tiêu đề, trước các lối tắt (FEAT-002)
	for sid, label, _link, typ, _view in rows:
		if typ == "CustomBlock":
			blocks.append(
				{"id": sid, "type": "custom_block", "data": {"custom_block_name": label, "col": 12}}
			)
			custom_blocks.append({"custom_block_name": label, "label": label})
	for sid, label, link_to, typ, view in rows:
		if typ == "CustomBlock":
			continue
		blocks.append({"id": sid, "type": "shortcut", "data": {"shortcut_name": label, "col": 4}})
		s = {"label": label, "link_to": link_to, "type": typ}
		if view:
			s["doc_view"] = view
		shortcuts.append(s)
	doc = dict(BASE)
	if modified:
		doc["modified"] = modified
	doc["content"] = json.dumps(blocks, ensure_ascii=False, separators=(",", ":"))
	doc["shortcuts"] = shortcuts
	if custom_blocks:
		doc["custom_blocks"] = custom_blocks
	return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def write_workspace(root: Path, modified: str | None = None) -> bool:
	if not ((root / REL / "shortcuts.d").is_dir()):
		return False
	out = render(read_sources(root), modified)
	dst = root / REL / "normcore.json"
	if dst.exists() and dst.read_text(encoding="utf-8") == out:
		return False
	dst.write_text(out, encoding="utf-8")
	return True


def build_all(root: Path, modified: str | None = None) -> list:
	"""Sinh vi.csv và normcore.json từ mảnh. Trả danh sách tệp đã ghi; lỗi ghép: ValueError."""
	root = Path(root)
	written = []
	if write_translations(root):
		written.append(str(root / VI_REL))
	if write_workspace(root, modified):
		written.append(str(root / REL / "normcore.json"))
	return written


def before_migrate():
	"""Hook Frappe (before_install gọi cùng hàm này). `modified` đóng dấu lúc chạy để Frappe luôn nhập lại
	Workspace (Frappe bỏ qua tệp JSON không mới hơn bản trong CSDL)."""
	import frappe

	build_all(Path(frappe.get_app_path("normcore")).parent, modified=frappe.utils.now())


def selfcheck():
	"""`bench --site <site> execute normcore.generated.selfcheck` (NORM-60 T09): Frappe có đọc được tệp ghép không.

	Trả: số khóa dịch của mảnh có mặt trong `get_all_translations("vi")` trên tổng số khóa ghép, số lối tắt
	Workspace "Normcore" trên số lối tắt của mảnh (không tính Custom HTML Block). `ok` chỉ đúng khi đủ cả hai.
	"""
	import frappe
	import frappe.translate

	root = Path(frappe.get_app_path("normcore")).parent
	rows, _errors = merge_translations(root)
	frappe.translate.clear_cache()
	got = frappe.translate.get_all_translations("vi")
	# Cùng cách Frappe đọc CSV (get_translation_dict_from_file): "\\n" thành xuống dòng, khóa có ngữ cảnh là
	# "nguồn:ngữ cảnh", bản dịch bị strip.
	found = 0
	for r in rows:
		src, tr = r[0].replace("\\n", "\n"), r[1].replace("\\n", "\n").strip()
		key = f"{src}:{r[2]}" if len(r) > 2 and r[2] else src
		found += got.get(key) == tr
	expected = [r for r in read_sources(root) if r[3] != "CustomBlock"]
	ws = frappe.get_doc("Workspace", "Normcore")
	out = {
		"translations_found": found,
		"translations_total": len(rows),
		"shortcuts_in_workspace": len(ws.shortcuts),
		"shortcuts_in_fragments": len(expected),
	}
	out["ok"] = found == len(rows) and len(ws.shortcuts) == len(expected)
	print(json.dumps(out))
	return out
