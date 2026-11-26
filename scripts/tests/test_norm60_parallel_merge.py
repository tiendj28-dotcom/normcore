"""NORM-60 AC-1: hai nhánh song song, mỗi nhánh thêm một bản dịch, một lối tắt, một Test ref (cùng một tệp
perm_matrix và hook_registry) như một FEAT thật, gộp bằng cách GitHub gộp phía máy chủ (`git merge-tree
--write-tree`: không đọc .gitattributes của worktree, không có driver union): không conflict, không cần
commit sinh lại, check_conventions xanh.

Chạy bằng tay (ci.yml không chạy scripts/tests/, ASM-NORM60-06): pytest scripts/tests/test_norm60_parallel_merge.py
Cần git >= 2.38; git cũ hơn thì test đỏ (không skip, luật cứng 1).
"""

import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WS = "normcore/nc_core/workspace/normcore"


def git(cwd, *args, check=True):
	r = subprocess.run(
		["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, capture_output=True, text=True
	)
	if check and r.returncode:
		raise AssertionError(f"git {args}: {r.stderr}{r.stdout}")
	return r


def put(root: Path, rel: str, text: str):
	p = root / rel
	p.parent.mkdir(parents=True, exist_ok=True)
	p.write_text(text, encoding="utf-8")


def _git_version():
	m = re.search(r"(\d+)\.(\d+)", subprocess.check_output(["git", "--version"], text=True))
	return int(m.group(1)), int(m.group(2))


def clone_tree(dst: Path):
	"""Chép cây hiện tại của repo (tệp được theo dõi và tệp mới chưa theo dõi, trừ tệp bị ignore) vào repo tạm."""
	files = subprocess.check_output(
		["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=REPO
	).split(b"\0")
	for raw in files:
		if not raw:
			continue
		rel = raw.decode()
		src = REPO / rel
		if not src.is_file():
			continue
		(dst / rel).parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(src, dst / rel)
	git(dst, "init", "-q", "-b", "develop")
	git(dst, "add", "-A")
	git(dst, "commit", "-qm", "base")


def add_feat(root: Path, n: int):
	"""Một FEAT giả: đúng các tệp một FEAT thật được phép chạm trong bố cục mới."""
	put(root, f"normcore/translations/vi.d/FEAT-{n}.csv", f"Khóa thử {n},Bản dịch thử {n}\n")
	put(root, f"{WS}/shortcuts.d/FEAT-{n}.txt", f"t{n}|Lối tắt thử {n}|NC Item|DocType|List\n")
	put(
		root,
		f"docs/rtm-testref/FEAT-{n}.md",
		f"## FEAT-{n}\n\n| FR | Test thật |\n|---|---|\n| FR-X-{n} | test_x |\n",
	)
	put(
		root,
		f"scripts/conventions/perm_matrix/nc_thu_{n}.json",
		json.dumps(
			{"doctype": f"NC Thu {n}", "row": f"Dòng thử {n}", "codes": "R R - W R - R R W R", "delete": []}
		),
	)
	put(
		root,
		f"normcore/hook_registry/FEAT-{n}.json",
		json.dumps({"scheduler_events": {"daily": [f"normcore.api.thu_{n}.daily_job"]}}),
	)
	git(root, "add", "-A")
	git(root, "commit", "-qm", f"FEAT-{n}")


def test_AC1_hai_nhanh_song_song_khong_conflict(tmp_path):
	assert _git_version() >= (2, 38), "cần git >= 2.38 cho merge-tree --write-tree (R4)"
	repo = tmp_path / "r"
	repo.mkdir()
	clone_tree(repo)
	git(repo, "checkout", "-q", "-b", "A")
	add_feat(repo, 901)
	git(repo, "checkout", "-q", "develop")
	git(repo, "checkout", "-q", "-b", "B")
	add_feat(repo, 902)
	# merge nhánh A vào develop, rồi gộp B bằng merge-tree (như nút Merge của GitHub)
	git(repo, "checkout", "-q", "develop")
	git(repo, "merge", "-q", "--no-edit", "--ff-only", "A")
	r = git(repo, "merge-tree", "--write-tree", "develop", "B", check=False)
	assert r.returncode == 0, f"conflict khi gộp hai nhánh song song:\n{r.stdout}\n{r.stderr}"
	tree = r.stdout.split()[0]
	commit = git(repo, "commit-tree", tree, "-p", "develop", "-p", "B", "-m", "merge B").stdout.strip()
	git(repo, "checkout", "-q", "-b", "after", commit)
	# không cần commit sinh lại: sinh tệp ghép rồi cây vẫn sạch
	b = subprocess.run(
		[sys.executable, "scripts/build_generated.py"], cwd=repo, capture_output=True, text=True
	)
	assert b.returncode == 0, b.stderr
	assert git(repo, "status", "--porcelain").stdout.strip() == ""
	c = subprocess.run(
		[sys.executable, "scripts/check_conventions.py"], cwd=repo, capture_output=True, text=True
	)
	assert c.returncode == 0, c.stdout + c.stderr
	vi = (repo / "normcore/translations/vi.csv").read_text(encoding="utf-8")
	assert "Khóa thử 901,Bản dịch thử 901" in vi and "Khóa thử 902,Bản dịch thử 902" in vi
	with open(repo / "normcore/translations/vi.csv", encoding="utf-8", newline="") as fh:
		keys = [(r[0], r[2] if len(r) > 2 else "") for r in csv.reader(fh) if r]
	assert keys == sorted(keys), "vi.csv ghép phải sắp xếp (NC-10)"
	ws = json.loads((repo / WS / "normcore.json").read_text(encoding="utf-8"))
	assert {"Lối tắt thử 901", "Lối tắt thử 902"} <= {s["label"] for s in ws["shortcuts"]}
	hooks = subprocess.run(
		[
			sys.executable,
			"-c",
			"import json;from normcore.core import hook_registry as h;print(json.dumps(h.load()['scheduler_events']))",
		],
		cwd=repo,
		capture_output=True,
		text=True,
	)
	assert hooks.returncode == 0, hooks.stderr
	daily = json.loads(hooks.stdout)["daily"]
	assert "normcore.api.thu_901.daily_job" in daily and "normcore.api.thu_902.daily_job" in daily


def test_AC1_doi_chung_bo_cuc_cu_conflict(tmp_path):
	"""Đối chứng: cùng kịch bản trên bố cục cũ (hai nhánh chèn dòng vào cùng chỗ của vi.csv, shortcuts.txt,
	rtm-testref.md) thì merge-tree báo conflict: test AC-1 phân biệt được hai bố cục."""
	assert _git_version() >= (2, 38), "cần git >= 2.38 cho merge-tree --write-tree (R4)"
	repo = tmp_path / "old"
	repo.mkdir()
	git(repo, "init", "-q", "-b", "develop")
	put(repo, "normcore/translations/vi.csv", "Alpha,a\nOmega,o\n")
	put(repo, f"{WS}/shortcuts.txt", "s1|Một|NC Item|DocType|List\n")
	put(repo, "docs/rtm-testref.md", "| FR | Test thật |\n")
	git(repo, "add", "-A")
	git(repo, "commit", "-qm", "base")
	for name, n in (("A", 901), ("B", 902)):
		git(repo, "checkout", "-q", "-b", name, "develop")
		put(repo, "normcore/translations/vi.csv", f"Alpha,a\nKhóa thử {n},dịch {n}\nOmega,o\n")
		put(repo, f"{WS}/shortcuts.txt", f"s1|Một|NC Item|DocType|List\nt{n}|Lối {n}|NC Item|DocType|List\n")
		put(repo, "docs/rtm-testref.md", f"| FR | Test thật |\n| FR-X-{n} | test_x |\n")
		git(repo, "commit", "-qam", f"FEAT-{n}")
	git(repo, "checkout", "-q", "A")
	r = git(repo, "merge-tree", "--write-tree", "A", "B", check=False)
	assert r.returncode == 1, "bố cục cũ phải conflict khi hai nhánh cùng thêm dòng vào tệp chung"
	assert "vi.csv" in r.stdout and "shortcuts.txt" in r.stdout and "rtm-testref.md" in r.stdout
