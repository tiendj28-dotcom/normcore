#!/usr/bin/env python3
"""Sinh lại normcore/nc_core/workspace/normcore/normcore.json một cách tất định (NORM-32).

Nguồn: shortcuts.txt cạnh tệp đích, mỗi lối tắt một dòng `id|nhãn|link_to|loại|doc_view`
(dòng bắt đầu bằng # là chú thích). Tệp nguồn có merge=union nên nhiều FEAT cùng thêm dòng
không conflict. Gỡ conflict: gộp shortcuts.txt (giữ mọi dòng của hai bên), chạy lại script này.

Dùng: python3 scripts/build_workspace.py [--check] [thư_mục_gốc]
  --check: không ghi, thoát 1 nếu normcore.json khác kết quả sinh.
"""

import json
import sys
from pathlib import Path

REL = Path("normcore/nc_core/workspace/normcore")
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
	ids = [r[0] for r in rows]
	dup = {i for i in ids if ids.count(i) > 1}
	if dup:
		# union có thể nhân đôi nguyên dòng giống nhau: bỏ dòng trùng hệt, báo nếu cùng id khác nội dung
		uniq = []
		for r in rows:
			if r in uniq:
				continue
			if any(u[0] == r[0] for u in uniq):
				raise ValueError(f"{path}: id lối tắt trùng nhưng khác nội dung: {r[0]}")
			uniq.append(r)
		rows = uniq
	return rows


def render(rows: list) -> str:
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
	doc["content"] = json.dumps(blocks, ensure_ascii=False, separators=(",", ":"))
	doc["shortcuts"] = shortcuts
	if custom_blocks:
		doc["custom_blocks"] = custom_blocks
	return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv=None) -> int:
	argv = sys.argv[1:] if argv is None else argv
	check = "--check" in argv
	args = [a for a in argv if a != "--check"]
	root = Path(args[0]) if args else Path(__file__).resolve().parent.parent
	src = root / REL / "shortcuts.txt"
	dst = root / REL / "normcore.json"
	out = render(read_shortcuts(src))
	if check:
		return 0 if dst.exists() and dst.read_text(encoding="utf-8") == out else 1
	dst.write_text(out, encoding="utf-8")
	return 0


if __name__ == "__main__":
	sys.exit(main())
