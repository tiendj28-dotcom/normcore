#!/usr/bin/env python3
"""Sửa tệp sinh sau khi gộp develop vào nhánh PR (NORM-37, NORM-60), chạy bởi scripts/pr_sync.sh.

Dùng: python3 scripts/pr_sync_fix.py <thư_mục_gốc_của_nhánh_PR>   (chạy bản trong cây ĐÃ GỘP)
- Chuyển tiếp từ bố cục cũ (NORM-60): tệp chung cũ (vi.csv, shortcuts.txt, rtm-testref.md) bị xóa ở develop
  mà PR còn sửa và git không ghép được đổi tên: dòng PR thêm được đưa vào mảnh 00-base.*, rồi gỡ tệp cũ.
- Tệp sinh (vi.csv, normcore.json) còn bị conflict hoặc còn được theo dõi khi đã có bố cục mảnh: git rm --cached.
- Mảnh 00-base.* còn conflict (union không áp dụng): ghép hai bên.
- Bố cục mảnh: sinh lại vi.csv, normcore.json bằng normcore/generated.py của cây đã gộp.
- Bố cục cũ (chưa có vi.d/, shortcuts.d/): sắp lại vi.csv, sinh lại normcore.json như trước NORM-60.
In danh sách tệp đã sửa (mỗi dòng một đường dẫn tương đối); không in gì nếu không đổi.
"""

import csv
import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT))

import build_workspace as bw
import check_conventions as cc

from normcore import generated

VI_NEW = "normcore/translations/vi.d/00-base.csv"
SC_NEW = str(bw.REL / "shortcuts.d/00-base.txt")
RTM_NEW = "docs/rtm-testref/00-base.md"
LEGACY = {  # tệp chung cũ -> mảnh nền
	cc.VI_CSV: VI_NEW,
	str(bw.REL / "shortcuts.txt"): SC_NEW,
	"docs/rtm-testref.md": RTM_NEW,
}
GENERATED = (cc.VI_CSV, str(bw.REL / "normcore.json"))


def _git(root: Path, *args, check=True):
	r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
	if check and r.returncode:
		raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
	return r


def _stage(root: Path, n: int, rel: str):
	r = _git(root, "show", f":{n}:{rel}", check=False)
	return r.stdout if r.returncode == 0 else None


def _is_repo(root: Path) -> bool:
	return _git(root, "rev-parse", "--git-dir", check=False).returncode == 0


def _unmerged(root: Path) -> set:
	if not _is_repo(root):  # test thuần trên thư mục không có git
		return set()
	return set(_git(root, "diff", "--name-only", "--diff-filter=U").stdout.split("\n")) - {""}


def _tracked(root: Path) -> set:
	if not _is_repo(root):
		return set()
	return set(_git(root, "ls-files").stdout.split("\n")) - {""}


def _append_lines(path: Path, lines: list):
	existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
	add = [ln for ln in lines if ln not in existing]
	if add:
		path.parent.mkdir(parents=True, exist_ok=True)
		with open(path, "a", encoding="utf-8") as fh:
			if existing and not path.read_text(encoding="utf-8").endswith("\n"):
				fh.write("\n")
			fh.write("\n".join(add) + "\n")
	return bool(add)


def _migrate_legacy(root: Path, unmerged: set) -> list:
	changed = []
	for legacy, new in LEGACY.items():
		if legacy not in unmerged:
			continue
		ours = _stage(root, 2, legacy)
		if ours is None:  # PR xóa tệp, develop sửa: không còn gì để giữ lại của PR
			continue
		base = (_stage(root, 1, legacy) or "").splitlines()
		added = [ln for ln in ours.splitlines() if ln and ln not in base]
		if _append_lines(root / new, added):
			changed.append(new)
		_git(root, "rm", "--cached", "-q", "--", legacy)
		if legacy not in GENERATED:
			(root / legacy).unlink(missing_ok=True)
	return changed


def _union_fragment(root: Path, rel: str) -> None:
	"""Mảnh 00-base còn conflict: giữ cả hai bên (dòng trùng bỏ); .csv sắp lại như generated."""
	ours, theirs = _stage(root, 2, rel) or "", _stage(root, 3, rel) or ""
	if rel.endswith(".csv"):
		rows = []
		for text in (ours, theirs):
			for row in csv.reader(io.StringIO(text)):
				if row and row not in rows:
					rows.append(row)
		rows.sort(key=generated.csv_key)
		with open(root / rel, "w", encoding="utf-8", newline="") as fh:
			csv.writer(fh, lineterminator="\n").writerows(rows)
	else:
		lines = ours.splitlines()
		lines += [ln for ln in theirs.splitlines() if ln not in lines]
		(root / rel).write_text("\n".join(lines) + "\n", encoding="utf-8")
	_git(root, "add", "--", rel)


def fix(root: Path) -> list:
	root = Path(root)
	changed = []
	unmerged = _unmerged(root)
	changed += _migrate_legacy(root, unmerged)
	unmerged = _unmerged(root)
	for rel in (VI_NEW, SC_NEW, RTM_NEW):
		if rel in unmerged:
			_union_fragment(root, rel)
			changed.append(rel)
	layered = (root / cc.VI_DIR).is_dir() or (root / bw.REL / "shortcuts.d").is_dir()
	if layered:
		unmerged = _unmerged(root)
		tracked = _tracked(root)
		for rel in GENERATED:
			if rel in unmerged or rel in tracked:
				_git(root, "rm", "--cached", "-q", "--", rel)
				changed.append(rel)
		generated.build_all(root)  # lỗi ghép (NC-09, NC-11): ValueError, pr_sync.sh báo lỗi
		return changed
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
