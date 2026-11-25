#!/usr/bin/env python3
"""Sửa tệp sinh sau khi gộp develop vào nhánh PR (NORM-37, scripts/pr_sync.sh bước c).

Dùng: python3 pr_sync_fix.py <thư_mục_gốc_của_nhánh_PR>
- vi.csv: sắp lại theo đúng quy tắc check_conventions (dùng lại sort_vi_csv, không đặt quy tắc mới).
- normcore.json: sinh lại từ shortcuts.txt bằng build_workspace.py.
In danh sách tệp đã sửa (mỗi dòng một đường dẫn tương đối); không in gì nếu không đổi.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_workspace as bw
import check_conventions as cc


def fix(root: Path) -> list:
	changed = []
	if cc.sort_vi_csv(root):
		changed.append(cc.VI_CSV)
	src = root / bw.REL / "shortcuts.txt"
	dst = root / bw.REL / "normcore.json"
	if src.exists():
		out = bw.render(bw.read_shortcuts(src))
		if not dst.exists() or dst.read_text(encoding="utf-8") != out:
			dst.write_text(out, encoding="utf-8")
			changed.append(str(bw.REL / "normcore.json"))
	return changed


def main(argv=None) -> int:
	argv = sys.argv[1:] if argv is None else argv
	for rel in fix(Path(argv[0])):
		print(rel)
	return 0


if __name__ == "__main__":
	sys.exit(main())
