#!/usr/bin/env python3
"""Sinh lại normcore/nc_core/workspace/normcore/normcore.json một cách tất định (NORM-32).

(NORM-60: mã dựng ở normcore/generated.py; bố cục mới dùng shortcuts.d/*.txt, xem scripts/build_generated.py.)
Nguồn: shortcuts.txt cạnh tệp đích, mỗi lối tắt một dòng `id|nhãn|link_to|loại|doc_view`
(dòng bắt đầu bằng # là chú thích). Tệp nguồn có merge=union nên nhiều FEAT cùng thêm dòng
không conflict. Gỡ conflict: gộp shortcuts.txt (giữ mọi dòng của hai bên), chạy lại script này.

Dùng: python3 scripts/build_workspace.py [--check] [thư_mục_gốc]
  --check: không ghi, thoát 1 nếu normcore.json khác kết quả sinh.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Phần dựng nằm ở normcore/generated.py (Frappe chạy từ gói normcore); giữ tên cũ cho check_conventions,
# pr_sync_fix và test cũ.
from normcore.generated import BASE, HEADER, REL, read_shortcuts, read_sources, render


def main(argv=None) -> int:
	argv = sys.argv[1:] if argv is None else argv
	check = "--check" in argv
	args = [a for a in argv if a != "--check"]
	root = Path(args[0]) if args else ROOT
	dst = root / REL / "normcore.json"
	out = render(read_sources(root))
	if check:
		return 0 if dst.exists() and dst.read_text(encoding="utf-8") == out else 1
	dst.write_text(out, encoding="utf-8")
	return 0


if __name__ == "__main__":
	sys.exit(main())
