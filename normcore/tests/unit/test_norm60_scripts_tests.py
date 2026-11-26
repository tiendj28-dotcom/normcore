"""NORM-60 (Quyết định Lead, ASM-NORM60-06): đưa các test AC-1, AC-2 ở scripts/tests/ vào CI.

ci.yml chỉ chạy normcore/tests/unit và normcore/tests/golden; test bọc này gọi pytest con trên
scripts/tests/test_norm60_*.py (subprocess, không lồng pytest.main, không tính vào --cov). Thiếu git thì test
đỏ, không skip. Gỡ ra: xóa tệp này.
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def test_NORM60_scripts_tests_xanh():
	files = sorted(str(p.relative_to(REPO)) for p in (REPO / "scripts/tests").glob("test_norm60_*.py"))
	assert len(files) >= 2, f"thiếu test NORM-60 ở scripts/tests: {files}"
	r = subprocess.run(
		[sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider"],
		cwd=REPO,
		capture_output=True,
		text=True,
		timeout=600,
	)
	assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-1000:]
