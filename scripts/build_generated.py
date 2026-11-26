#!/usr/bin/env python3
"""Sinh vi.csv và normcore.json từ mảnh vi.d/*.csv, shortcuts.d/*.txt (NORM-60).

Dùng: python3 scripts/build_generated.py [thư_mục_gốc]
In đường dẫn mỗi tệp đã ghi. Thoát 1 nếu ghép lỗi (NC-09, NC-11).
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from normcore import generated


def main(argv=None) -> int:
	argv = sys.argv[1:] if argv is None else argv
	root = Path(argv[0]) if argv else ROOT
	try:
		for path in generated.build_all(root):
			print(path)
	except ValueError as e:
		print(e, file=sys.stderr)
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
