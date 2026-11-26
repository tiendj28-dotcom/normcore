"""NORM-60 AC-2: pr-sync sinh và kiểm bằng script của cây đã gộp, không làm mất nội dung của nhánh PR.

Chạy bằng tay (ci.yml không chạy scripts/tests/, ASM-NORM60-06): pytest scripts/tests/test_norm60_pr_sync.py
Mỗi test dựng một remote giả (bare) + một bản làm việc, chạy scripts/pr_sync.sh với PR_SYNC_LOCAL=1.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WS = "normcore/nc_core/workspace/normcore"
COPY = [
	"scripts/pr_sync.sh",
	"scripts/pr_sync_fix.py",
	"scripts/check_conventions.py",
	"scripts/build_workspace.py",
	"scripts/build_generated.py",
	"normcore/__init__.py",
	"normcore/generated.py",
	".gitignore",
]


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


def copy_tools(root: Path):
	for rel in COPY:
		dst = root / rel
		dst.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(REPO / rel, dst)
	(root / "scripts/pr_sync.sh").chmod(0o755)


def make_remote(tmp: Path):
	bare = tmp / "origin.git"
	git(tmp, "init", "-q", "--bare", "-b", "develop", str(bare))
	work = tmp / "work"
	git(tmp, "clone", "-q", str(bare), str(work))
	git(work, "checkout", "-q", "-b", "develop")
	return bare, work


def run_sync(work: Path, branches: str):
	env = {**os.environ, "PR_SYNC_LOCAL": "1", "PR_SYNC_BRANCHES": branches, "GIT_TERMINAL_PROMPT": "0"}
	r = subprocess.run(
		["bash", "scripts/pr_sync.sh"], cwd=work, env=env, capture_output=True, text=True, timeout=120
	)
	assert r.returncode == 0, r.stderr + r.stdout
	return r.stdout


def _rows(n):
	return "".join(f"Khoa {i:03d},Giá trị {i:03d}\n" for i in range(n))


def test_AC2_pr_sync_dung_script_cua_nhanh_khong_mat_block(tmp_path):
	"""Tái hiện 0d15f23: nhánh sửa phần dựng workspace (loại block mới); develop không biết loại đó.
	Sau pr-sync, normcore.json sinh bằng script của NHÁNH có cả block của nhánh lẫn lối tắt của develop."""
	_bare, work = make_remote(tmp_path)
	copy_tools(work)
	put(work, f"{WS}/shortcuts.d/00-base.txt", "a1|Một|NC Item|DocType|List\n")
	put(work, "normcore/translations/vi.d/00-base.csv", _rows(5))
	git(work, "add", "-A")
	git(work, "commit", "-qm", "base")
	git(work, "push", "-q", "origin", "develop")
	# nhánh PR: render biết loại HomeBlock; thêm mảnh dùng loại đó
	git(work, "checkout", "-q", "-b", "feat/pr-1")
	gen = (work / "normcore/generated.py").read_text(encoding="utf-8")
	patched = gen.replace(
		'\tfor sid, label, link_to, typ, view in rows:\n\t\tif typ == "CustomBlock":',
		'\tfor sid, label, _link, typ, _view in rows:\n\t\tif typ == "HomeBlock":\n'
		'\t\t\tblocks.append({"id": sid, "type": "home_block", "data": {"name": label}})\n'
		'\tfor sid, label, link_to, typ, view in rows:\n\t\tif typ == "HomeBlock":\n\t\t\tcontinue\n'
		'\t\tif typ == "CustomBlock":',
	)
	assert patched != gen
	put(work, "normcore/generated.py", patched)
	put(work, f"{WS}/shortcuts.d/FEAT-902.txt", "h1|Trang chủ mới||HomeBlock|\n")
	git(work, "add", "-A")
	git(work, "commit", "-qm", "nhanh: block moi")
	git(work, "push", "-q", "origin", "feat/pr-1")
	# develop đi tiếp: thêm một lối tắt (develop không có loại HomeBlock)
	git(work, "checkout", "-q", "develop")
	put(work, f"{WS}/shortcuts.d/FEAT-901.txt", "b1|Hai|NC Room|DocType|List\n")
	put(work, "normcore/translations/vi.d/FEAT-901.csv", "Zzz,Zzz dịch\n")
	git(work, "add", "-A")
	git(work, "commit", "-qm", "develop them mot loi tat")
	git(work, "push", "-q", "origin", "develop")

	out = run_sync(work, "feat/pr-1")
	assert "DỪNG" not in out and "conflict" not in out.lower().replace("nhãn conflict", ""), out
	assert "đã đẩy" in out, out

	# nhánh đã đẩy lên remote: dựng lại bằng script CỦA NHÁNH đó
	check = tmp_path / "check"
	git(tmp_path, "clone", "-q", "-b", "feat/pr-1", str(tmp_path / "origin.git"), str(check))
	subprocess.run(["python3", "scripts/build_generated.py"], cwd=check, check=True, capture_output=True)
	doc = json.loads((check / WS / "normcore.json").read_text(encoding="utf-8"))
	content = json.loads(doc["content"])
	assert any(b["type"] == "home_block" for b in content), "mất block của nhánh (đúng lỗi 0d15f23)"
	assert {s["label"] for s in doc["shortcuts"]} == {"Một", "Hai"}
	# không có commit "sinh lại tệp sinh": tệp sinh không được theo dõi
	tracked = git(check, "ls-files").stdout.splitlines()
	assert f"{WS}/normcore.json" not in tracked
	# bản dựng trên bản làm việc của bot cũng đúng (script của nhánh)
	ws_doc = json.loads((work / WS / "normcore.json").read_text(encoding="utf-8"))
	assert any(b["type"] == "home_block" for b in json.loads(ws_doc["content"]))


def test_chuyen_tiep_pr_bo_cuc_cu(tmp_path):
	"""PR mở trước NORM-60 còn sửa vi.csv, shortcuts.txt, normcore.json, rtm-testref.md: sau khi develop chuyển
	sang mảnh, pr-sync đưa dòng của PR vào 00-base.*, bỏ theo dõi tệp sinh, check_conventions thoát 0."""
	_bare, work = make_remote(tmp_path)
	copy_tools(work)
	# bố cục cũ: các tệp chung được theo dõi, .gitignore chưa có hai tệp sinh
	(work / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
	put(work, "normcore/translations/vi.csv", _rows(30))
	put(work, f"{WS}/shortcuts.txt", "".join(f"s{i}|Lối {i}|NC Item|DocType|List\n" for i in range(12)))
	put(work, "docs/rtm-testref.md", "".join(f"| FR-{i:03d} | test_{i} |\n" for i in range(20)))
	sys_path = str(work)
	subprocess.run(
		["python3", "scripts/build_workspace.py", sys_path], cwd=work, check=True, capture_output=True
	)
	git(work, "add", "-A")
	git(work, "commit", "-qm", "bo cuc cu")
	git(work, "push", "-q", "origin", "develop")
	# nhánh PR bố cục cũ
	git(work, "checkout", "-q", "-b", "feat/pr-2")
	with open(work / "normcore/translations/vi.csv", "a", encoding="utf-8") as f:
		f.write("Khoa 999,Của PR cũ\n")
	subprocess.run(["python3", "scripts/pr_sync_fix.py", sys_path], cwd=work, capture_output=True)
	with open(work / WS / "shortcuts.txt", "a", encoding="utf-8") as f:
		f.write("pr|Lối của PR cũ|NC Room|DocType|List\n")
	with open(work / "docs/rtm-testref.md", "a", encoding="utf-8") as f:
		f.write("| FR-777 | test_pr_cu |\n")
	subprocess.run(
		["python3", "scripts/build_workspace.py", sys_path], cwd=work, check=True, capture_output=True
	)
	git(work, "add", "-A")
	git(work, "commit", "-qm", "pr cu: sua tep chung")
	git(work, "push", "-q", "origin", "feat/pr-2")
	# develop chuyển sang mảnh (đúng như NORM-60 T03)
	git(work, "checkout", "-q", "develop")
	git(work, "mv", "normcore/translations/vi.csv", "normcore/translations/vi.d/00-base.csv") if (
		work / "normcore/translations/vi.d"
	).exists() else (
		(work / "normcore/translations/vi.d").mkdir(parents=True),
		git(work, "mv", "normcore/translations/vi.csv", "normcore/translations/vi.d/00-base.csv"),
	)
	(work / f"{WS}/shortcuts.d").mkdir(parents=True)
	git(work, "mv", f"{WS}/shortcuts.txt", f"{WS}/shortcuts.d/00-base.txt")
	(work / "docs/rtm-testref").mkdir(parents=True)
	git(work, "mv", "docs/rtm-testref.md", "docs/rtm-testref/00-base.md")
	git(work, "rm", "-q", "--cached", f"{WS}/normcore.json")
	with open(work / ".gitignore", "a", encoding="utf-8") as f:
		f.write(f"normcore/translations/vi.csv\n{WS}/normcore.json\n")
	git(work, "add", "-A")
	git(work, "commit", "-qm", "develop: chuyen sang manh")
	git(work, "push", "-q", "origin", "develop")

	out = run_sync(work, "feat/pr-2")
	assert "DỪNG" not in out, out
	assert "đã đẩy" in out, out

	check = tmp_path / "check"
	git(tmp_path, "clone", "-q", "-b", "feat/pr-2", str(tmp_path / "origin.git"), str(check))
	assert "Khoa 999,Của PR cũ" in (check / "normcore/translations/vi.d/00-base.csv").read_text(
		encoding="utf-8"
	)
	assert "pr|Lối của PR cũ" in (check / f"{WS}/shortcuts.d/00-base.txt").read_text(encoding="utf-8")
	assert "| FR-777 | test_pr_cu |" in (check / "docs/rtm-testref/00-base.md").read_text(encoding="utf-8")
	tracked = git(check, "ls-files").stdout.splitlines()
	assert "normcore/translations/vi.csv" not in tracked and f"{WS}/normcore.json" not in tracked
	subprocess.run(["python3", "scripts/build_generated.py"], cwd=check, check=True, capture_output=True)
	r = subprocess.run(["python3", "scripts/check_conventions.py"], cwd=check, capture_output=True, text=True)
	assert r.returncode == 0, r.stdout + r.stderr
	assert "Khoa 999,Của PR cũ" in (check / "normcore/translations/vi.csv").read_text(encoding="utf-8")


def test_gop_tay_khi_git_khong_nhan_ra_doi_ten_van_giu_dong_cua_pr(tmp_path):
	"""pr_sync_fix: tệp chung cũ bị xóa ở develop và PR sửa mà git không ghép được đổi tên (tệp quá nhỏ):
	dòng PR thêm phải vào mảnh 00-base, không bị bỏ lặng lẽ."""
	_bare, work = make_remote(tmp_path)
	copy_tools(work)
	(work / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
	put(work, "normcore/translations/vi.csv", "A,a\n")
	git(work, "add", "-A")
	git(work, "commit", "-qm", "base")
	git(work, "checkout", "-q", "-b", "pr")
	put(work, "normcore/translations/vi.csv", "A,a\nPR,của pr\n")
	git(work, "commit", "-qam", "pr")
	git(work, "checkout", "-q", "develop")
	git(work, "rm", "-q", "normcore/translations/vi.csv")
	put(work, "normcore/translations/vi.d/00-base.csv", "Z,z\n")
	with open(work / ".gitignore", "a", encoding="utf-8") as f:
		f.write("normcore/translations/vi.csv\n")
	git(work, "add", "-A")
	git(work, "commit", "-qm", "develop")
	git(work, "checkout", "-q", "pr")
	r = git(work, "merge", "--no-edit", "develop", check=False)
	assert r.returncode != 0, "kịch bản phải sinh conflict sửa/xóa"
	out = subprocess.run(
		["python3", "scripts/pr_sync_fix.py", str(work)], cwd=work, capture_output=True, text=True
	)
	assert out.returncode == 0, out.stderr
	assert git(work, "diff", "--name-only", "--diff-filter=U").stdout.strip() == ""
	assert "PR,của pr" in (work / "normcore/translations/vi.d/00-base.csv").read_text(encoding="utf-8")
	assert "normcore/translations/vi.csv" not in git(work, "ls-files").stdout.splitlines()
