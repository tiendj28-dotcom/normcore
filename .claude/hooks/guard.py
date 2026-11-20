#!/usr/bin/env python3
"""PreToolUse hook — chặn những việc agent không được làm khi chạy không người duyệt.

Claude Code gửi JSON của lời gọi công cụ qua stdin. Thoát mã 2 = chặn; nội dung stderr
được trả lại cho agent để nó biết vì sao bị chặn và làm cách khác.
"""
import json
import os
import re
import subprocess
import sys

# Tệp/thư mục agent không được ghi (tương đối với gốc kho)
READ_ONLY = [
    "docs/srs.md",
    "docs/test-cases.md",
    "docs/use-cases.md",
    "docs/implementation-plan.md",
    "docs/README.md",
    "docs/golden/",
    "docs/tools/",
    "docs/sua-doi-1.1/",
    "CLAUDE.md",
    "PLAYBOOK.md",
    ".claude/",
    ".autopilot/",
    "scripts/autopilot.sh",
]
ALLOWED_INSIDE_READ_ONLY = [".autopilot/HALT"]

STAGE = os.environ.get("AUTOPILOT_STAGE", "")
FEAT_STAGES = {"design", "ui", "implement", "verify"}  # không được commit lên develop/main
PROTECTED_BRANCHES = {"develop", "main"}


def block(msg: str) -> None:
    print(f"[guard] BỊ CHẶN: {msg}. Xem CLAUDE.md mục 2, 3, 7.", file=sys.stderr)
    sys.exit(2)


def repo_root(cwd: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return cwd


def rel(path: str, root: str, cwd: str) -> str:
    p = os.path.normpath(os.path.join(cwd, os.path.expanduser(path)))
    try:
        return os.path.relpath(p, root).replace(os.sep, "/")
    except ValueError:
        return p


def is_read_only(relpath: str) -> bool:
    if relpath in ALLOWED_INSIDE_READ_ONLY:
        return False
    for ro in READ_ONLY:
        if ro.endswith("/") and (relpath + "/").startswith(ro):
            return True
        if relpath == ro:
            return True
    return False


def current_branch(cwd: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def check_file_tool(tool_input: dict, root: str, cwd: str) -> None:
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if path and is_read_only(rel(path, root, cwd)):
        block(f"không được ghi tệp chỉ đọc {rel(path, root, cwd)}")


WRITE_VERBS = re.compile(
    r"(\bsed\s+(-[a-zA-Z]*i|--in-place)|\btee\b|\bcp\b|\bmv\b|\brm\b|\btruncate\b|\bperl\s+-[a-zA-Z]*i|"
    r"\bdd\b|\bln\b|\bchmod\b|open\([^)]*['\"][wa]|write_text|write_bytes|\binstall\b)"
)
REDIRECT = re.compile(r"(?<![0-9&])>>?\s*([^\s;&|]+)")


def check_bash(cmd: str, root: str, cwd: str) -> None:
    c = " ".join(cmd.split())

    # 1. Ghi vào tệp chỉ đọc qua shell
    for target in REDIRECT.findall(c):
        if is_read_only(rel(target, root, cwd)):
            block(f"không được chuyển hướng ghi vào {target}")
    if WRITE_VERBS.search(c):
        for ro in READ_ONLY:
            if ro.rstrip("/") in c:
                block(f"lệnh có dấu hiệu ghi/xóa và chạm '{ro}'")

    # 2. Git nguy hiểm
    if re.search(r"\bgit\s+push\b", c):
        if re.search(r"(\s-f\b|--force|--force-with-lease|\s\+\S+)", c):
            block("không được push --force")
        if re.search(r"(\bmain\b|:main\b)", c) and STAGE != "release":
            block("chỉ giai đoạn release được push lên main")
    if re.search(r"\bgit\s+(filter-branch|filter-repo)\b", c):
        block("không được viết lại lịch sử")
    branch = current_branch(cwd)
    if branch in PROTECTED_BRANCHES:
        if re.search(r"\bgit\s+(reset\s+--hard|rebase|commit\s+--amend)\b", c):
            block(f"không được reset/rebase/amend trên {branch}")
        if STAGE in FEAT_STAGES and re.search(r"\bgit\s+(commit|merge|cherry-pick)\b", c):
            block(f"giai đoạn {STAGE} phải làm trên nhánh feat/*, không commit lên {branch}")
    if re.search(r"\bgh\s+pr\s+merge\b", c) and STAGE not in {"integrate", "release"}:
        block("chỉ giai đoạn integrate/release được merge PR")

    # 3. Xóa bừa
    if re.search(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+(/|~|\$HOME|\.\.)(\s|/?$)", c):
        block("lệnh rm -rf nhắm vào thư mục gốc/home/thư mục cha")

    # 4. Site Frappe: chỉ site *.test được xóa/cài lại
    m = re.search(r"\bbench\b.*?\b(drop-site|reinstall)\b", c)
    if m:
        site = re.search(r"--site\s+(\S+)|drop-site\s+(\S+)", c)
        name = next((g for g in (site.groups() if site else ()) if g), "")
        if not name.endswith(".test"):
            block("chỉ được drop/reinstall site có đuôi .test")

    # 5. Production
    prod = os.environ.get("PROD_HOST", "")
    if prod and prod in c and not (STAGE == "release" and os.environ.get("AUTO_DEPLOY_PROD") == "true"):
        block("không được chạm production ngoài giai đoạn release có AUTO_DEPLOY_PROD=true")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    cwd = data.get("cwd") or os.getcwd()
    root = repo_root(cwd)

    if tool in {"Edit", "Write", "MultiEdit", "NotebookEdit"}:
        check_file_tool(tool_input, root, cwd)
    elif tool == "Bash":
        check_bash(tool_input.get("command", ""), root, cwd)
    sys.exit(0)


if __name__ == "__main__":
    main()
