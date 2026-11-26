"""SCR-DSK-041 (FEAT-034): kiểm tĩnh form/list mẫu định mức, lối tắt Workspace, nhãn Select tiếng Việt."""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "nc_costing" / "doctype" / "nc_norm_template"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(")
I18N = re.compile(r"""__\(\s*(?:"((?:[^"\\]|\\.)*)"|'((?:[^'\\]|\\.)*)')""")


def _vi():
	with open(ROOT / "translations" / "vi.csv", encoding="utf-8", newline="") as f:
		return {row[0]: row[1] for row in csv.reader(f) if len(row) >= 2}


def test_tep_js_co_du_khong_ma_mau_cung():
	for name in ("nc_norm_template.js", "nc_norm_template_list.js"):
		text = (DIR / name).read_text(encoding="utf-8")
		assert not HEX.search(text), name


def test_chuoi_giao_dien_co_ban_dich():
	vi, used = _vi(), set()
	for name in ("nc_norm_template.js", "nc_norm_template_list.js"):
		for a, b in I18N.findall((DIR / name).read_text(encoding="utf-8")):
			used.add(a or b)
	assert used
	assert sorted(used - set(vi)) == []


def test_nhan_select_cap_phat_sinh_va_cau_phan_tieng_viet():
	vi = _vi()
	assert vi["RESULT"] == "Theo kết quả"
	assert vi["TUBE"] == "Theo ống mẫu"
	assert vi["BATCH"] == "Theo mẻ"
	assert vi["DAY"] == "Theo ngày-máy"
	assert vi["PERIOD"] == "Theo kỳ"
	assert vi["DRUG"] == "Thuốc và hóa chất"


def test_loi_tat_workspace():
	text = (ROOT / "nc_core" / "workspace" / "normcore" / "shortcuts.txt").read_text(encoding="utf-8")
	assert "|Mẫu định mức|NC Norm Template|DocType|List" in text
