#!/usr/bin/env python3
"""Trích ngữ cảnh của một FEAT từ bộ tài liệu normcore thành một tệp Markdown gọn.

Agent đọc tệp này thay vì đọc cả srs.md, data-model.md, test-cases.md. Chỉ đọc tài liệu, không ghi gì
vào docs/. Tệp kết quả là bản tóm lược để tra cứu; khi cần chính xác từng chữ, nguồn gốc vẫn là docs/.

Cách dùng:
	python3 scripts/feat_context.py FEAT-006                 # in ra màn hình
	python3 scripts/feat_context.py FEAT-006 -o /tmp/ctx.md  # ghi ra tệp
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ID_RANGE = re.compile(r"\b((?:FR|NFR|BR|DI|UC|SCR|TC)(?:-[A-Z]+)*)-(\d+)\.\.(\d+)\b")
ID = re.compile(r"\b(?:FR|NFR|BR)-[A-Z]+-\d+\b|\bDI-\d+\b|\bUC-\d+\b|\bSCR-[A-Z]+-\d+\b")
GOLDEN_BR = re.compile(r"\bBR-(?:COST|ADJ|CLS)-\d+\b")


def read(path: Path) -> list[str]:
	return path.read_text(encoding="utf-8").splitlines() if path.exists() else []


def cells(row: str) -> list[str]:
	return [c.strip() for c in row.strip().strip("|").split("|")]


def expand_ranges(text: str) -> str:
	"""FR-PROC-001..007 -> FR-PROC-001 FR-PROC-002 ... FR-PROC-007."""

	def repl(m: re.Match) -> str:
		prefix, start, end = m.group(1), m.group(2), m.group(3)
		width = len(start)
		return " ".join(f"{prefix}-{n:0{width}d}" for n in range(int(start), int(end) + 1))

	return ID_RANGE.sub(repl, text)


def ids_in(text: str) -> list[str]:
	seen: dict[str, None] = {}
	for i in ID.findall(expand_ranges(text)):
		seen.setdefault(i, None)
	return list(seen)


def table_rows(lines: list[str], first_cell: set[str]) -> dict[str, str]:
	"""Dòng bảng Markdown có ô đầu thuộc first_cell (bỏ đánh dấu ** **)."""
	found: dict[str, str] = {}
	for line in lines:
		if not line.startswith("|"):
			continue
		key = cells(line)[0].replace("*", "").split()[0] if cells(line)[0] else ""
		if key in first_cell and key not in found:
			found[key] = line
	return found


def section(lines: list[str], heading_re: str) -> list[str]:
	"""Từ tiêu đề khớp heading_re đến tiêu đề cùng cấp hoặc cao hơn kế tiếp."""
	pat = re.compile(heading_re)
	for i, line in enumerate(lines):
		if pat.match(line):
			level = len(line) - len(line.lstrip("#"))
			out = [line]
			for nxt in lines[i + 1 :]:
				if nxt.startswith("#") and len(nxt) - len(nxt.lstrip("#")) <= level:
					break
				out.append(nxt)
			return out
	return []


def doctype_block(lines: list[str], name: str) -> list[str]:
	"""Đoạn mô tả DocType **NC X** trong data-model.md, đến DocType hoặc tiêu đề kế tiếp."""
	start = re.compile(rf"^\*\*{re.escape(name)}\*\*(\s|\*\*|$)")
	for i, line in enumerate(lines):
		if start.match(line):
			out = [line]
			for nxt in lines[i + 1 :]:
				if nxt.startswith("#") or re.match(r"^\*\*NC [^*]+\*\*", nxt):
					break
				out.append(nxt)
			while out and not out[-1].strip():
				out.pop()
			return out
	return []


def build_order(root: Path) -> dict[str, tuple[str, list[str]]]:
	order: dict[str, tuple[str, list[str]]] = {}
	for line in read(root / ".autopilot" / "build-order.txt"):
		if line.startswith("FEAT-"):
			feat, release, deps = ([*line.split("|"), "", ""])[:3]
			order[feat] = (release, [d for d in deps.split(",") if d])
	return order


def done_on_develop(root: Path, feat: str) -> bool:
	try:
		subprocess.run(
			["git", "cat-file", "-e", f"origin/develop:docs/features/{feat}/DONE"],
			cwd=root,
			check=True,
			capture_output=True,
		)
		return True
	except (subprocess.CalledProcessError, FileNotFoundError):
		return (root / "docs" / "features" / feat / "DONE").exists()


def render(root: Path, feat: str) -> str:
	docs = root / "docs"
	plan = read(docs / "implementation-plan.md")
	srs = read(docs / "srs.md")
	tcs = read(docs / "test-cases.md")
	ucs = read(docs / "use-cases.md")
	dm = read(docs / "data-model.md")
	ux = read(docs / "ux-foundations.md")

	row = next((r for r in plan if r.startswith("|") and cells(r)[0].split()[0] == feat), None)
	if row is None:
		raise SystemExit(f"Không thấy {feat} trong bảng mục 3 của docs/implementation-plan.md")
	c = cells(row) + [""] * 7
	name, fr_col, uc_col, scr_col, blocks, data = c[1], c[2], c[3], c[4], c[5], c[6]

	out: list[str] = [f"# Ngữ cảnh {feat}: {name.replace('**', '')}", ""]
	out.append(f"_Sinh bởi `scripts/feat_context.py {feat}`. Bản trích để tra cứu; nguồn gốc là `docs/`._")
	out.append("")

	# Phụ thuộc
	order = build_order(root)
	release, deps = order.get(feat, ("?", []))
	out += ["## Phát hành và phụ thuộc", "", f"- Bản phát hành: {release}"]
	for d in deps:
		state = "DONE" if done_on_develop(root, d) else "**chưa DONE**"
		asb = docs / "as-built" / f"{d}.md"
		out.append(f"- {d}: {state}" + (f" — As-Built: `docs/as-built/{d}.md`" if asb.exists() else ""))
	out.append("")

	# Dòng kế hoạch
	header = next((p for p in plan if p.startswith("| ID | Feature")), "")
	out += [
		"## Dòng trong implementation-plan.md mục 3",
		"",
		header,
		"| :- | :- | :- | :- | :- | :- | :- |",
		row,
		"",
	]
	out += [
		f"- Khối / endpoint: {blocks}",
		f"- DocType: {data}",
		"",
	]
	mentions = [
		l
		for l in plan
		if feat in l
		and l != row
		and not l.strip().startswith(("F0", "F1", "F2", "F3", "-->", "%%"))
		and "-->" not in l
	]
	if mentions:
		out += (
			["Các chỗ khác trong kế hoạch nhắc tới FEAT này:", ""]
			+ [f"> {m.strip()}" for m in mentions]
			+ [""]
		)

	# FR
	fr_ids = [i for i in ids_in(fr_col) if i.startswith("FR-")]
	fr_rows = table_rows(srs, set(fr_ids))
	out += ["## Yêu cầu chức năng (srs.md)", ""]
	if "phần sửa" in fr_col:
		out += [f"_Cột FR ghi: {fr_col}_", ""]
	out += ["| ID | Mô tả | Mức | Trạng thái | Ghi chú |", "| :-- | :-- | :-- | :-- | :-- |"]
	for i in fr_ids:
		out.append(fr_rows.get(i, f"| {i} | _không thấy trong srs.md_ | | | |"))
	out.append("")

	# BR, NFR, DI được FR nhắc tới
	refs = ids_in(" ".join(fr_rows.values()))
	br_ids = [i for i in refs if i.startswith(("BR-", "NFR-"))]
	br_rows = table_rows(srs, set(br_ids))
	if br_rows:
		out += ["## Quy tắc nghiệp vụ và NFR được FR dẫn tới", ""]
		out += [br_rows[i] for i in br_ids if i in br_rows] + [""]

	golden = sorted({b for b in GOLDEN_BR.findall(" ".join([*fr_rows.values(), *br_rows.values()]))})
	if golden:
		out += ["## Đối chiếu golden (chỉ đọc, bậc 1)", ""]
		for gfile in ("golden_engine.py", "golden_cls.py"):
			glines = read(docs / "golden" / gfile)
			hits = [
				f"`docs/golden/{gfile}:{n}` {l.strip()}"
				for n, l in enumerate(glines, 1)
				if any(b in l for b in golden)
			]
			out += [f"- {h}" for h in hits]
		out += ["", f"BR cần khớp golden: {', '.join(golden)}", ""]

	# Use case
	uc_ids = [i for i in ids_in(uc_col) if i.startswith("UC-")]
	if uc_ids:
		out += ["## Use case (use-cases.md)", ""]
		for u in uc_ids:
			block = section(ucs, rf"^#+ {re.escape(u)}\b")
			out += (block or [f"_Không thấy {u}_"]) + [""]

	# Test case
	tc_rows = [
		l
		for l in tcs
		if l.startswith("| TC-") and (len(cells(l)) > 2 and (cells(l)[2] == feat or cells(l)[1] in fr_ids))
	]
	out += ["## Test case (test-cases.md)", ""]
	if tc_rows:
		out += [
			"| TC | FR | FEAT | Loại | Bước | Kết quả mong đợi |",
			"| :-- | :-- | :-- | :-- | :-- | :-- |",
		]
		out += tc_rows
	else:
		out.append("_Không có TC nào gắn FEAT hoặc FR này._")
	out += ["", "Tên test phải mang mã TC, ví dụ `test_TC_PROC_01_tao_ban_nhap`.", ""]

	# Màn hình
	scr_ids = [i for i in ids_in(scr_col) if i.startswith("SCR-")]
	scr_rows = table_rows(ux, set(scr_ids))
	if scr_ids:
		out += ["## Màn hình (ux-foundations.md)", ""]
		out += [scr_rows.get(s, f"| {s} | _không thấy_ |") for s in scr_ids] + [""]

	# DocType
	doctypes = [d.strip().strip("`").replace("**", "") for d in re.split(r"[,;]", data)]
	doctypes = [d for d in doctypes if d.startswith("NC ")]
	if doctypes:
		out += ["## DocType (data-model.md)", ""]
		blocks_text: list[str] = []
		for d in doctypes:
			note = re.search(r"\(([^)]*)\)\s*$", d)
			block = doctype_block(dm, re.sub(r"\s*\([^)]*\)\s*$", "", d))
			if block and note:
				block = [f"_Kế hoạch chỉ nhắc: {note.group(1)}_", *block]
			blocks_text += block
			out += (block or [f"**{d}** — _không thấy đặc tả_"]) + [""]
		# DI được nhắc trực tiếp, hoặc nhắc tới một trường của các DocType trên
		fields = {
			cells(l)[0].split()[0] for l in blocks_text if l.startswith("| ") and not l.startswith("| Trường")
		}
		fields = {f for f in fields if re.fullmatch(r"[a-z_]+", f)}
		di_ids = {
			i for i in ids_in(" ".join(blocks_text) + " ".join(fr_rows.values())) if i.startswith("DI-")
		}
		for l in dm:
			if l.startswith("| DI-") and any(f"`{f}`" in l for f in fields):
				di_ids.add(cells(l)[0])
		di_rows = table_rows(dm, di_ids)
		if di_rows:
			out += ["### Ràng buộc toàn vẹn liên quan", "", *list(di_rows.values()), ""]
		matrix = section(dm, r"^## 4\. Ma trận quyền")
		if matrix:
			out += ["### Ma trận quyền (data-model.md mục 4)", "", *matrix[1:], ""]

	# Trạng thái FEAT hiện có
	fdir = docs / "features" / feat
	if fdir.exists():
		out += ["## Tệp trạng thái đã có", ""]
		out += [f"- `docs/features/{feat}/{p.name}`" for p in sorted(fdir.iterdir())] + [""]

	return "\n".join(out).replace("\n\n\n", "\n\n")


def main() -> int:
	ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
	ap.add_argument("feat", help="Mã FEAT, ví dụ FEAT-006")
	ap.add_argument("-o", "--output", help="Ghi ra tệp thay vì in ra màn hình")
	ap.add_argument("--root", default=str(Path(__file__).resolve().parent.parent), help="Gốc kho")
	args = ap.parse_args()

	feat = args.feat.upper()
	if not re.fullmatch(r"FEAT-\d{3}", feat):
		ap.error("mã FEAT phải có dạng FEAT-NNN")
	text = render(Path(args.root), feat)
	for stream in (sys.stdout, sys.stderr):
		if hasattr(stream, "reconfigure"):
			stream.reconfigure(encoding="utf-8")
	if args.output:
		Path(args.output).write_text(text + "\n", encoding="utf-8")
		print(f"Đã ghi {args.output} ({len(text.splitlines())} dòng)", file=sys.stderr)
	else:
		print(text)
	return 0


if __name__ == "__main__":
	sys.exit(main())
