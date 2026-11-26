"""NORM-60: sổ đăng ký hook theo tệp (normcore/core/hook_registry.py), Python thuần."""

import json
from pathlib import Path

from normcore.core import hook_registry as hr
from normcore.tests.unit.tmpcase import TmpCase as _Base

REPO = Path(__file__).resolve().parents[3]


def _w(d: Path, name: str, data):
	d.mkdir(parents=True, exist_ok=True)
	(d / name).write_text(json.dumps(data), encoding="utf-8")


class TestModulo(_Base):
	def test_ghep_hai_tep_theo_ten(self):
		tmp_path = self.tmp_path
		_w(tmp_path, "FEAT-010.json", {"app_include_js": ["/b.js"]})
		_w(tmp_path, "FEAT-002.json", {"app_include_js": ["/a.js"]})
		assert hr.load(tmp_path)["app_include_js"] == ["/a.js", "/b.js"]

	def test_bo_phan_tu_trung_giu_thu_tu(self):
		tmp_path = self.tmp_path
		_w(tmp_path, "A.json", {"fixtures": ["x", "y"]})
		_w(tmp_path, "B.json", {"fixtures": ["y", "z"]})
		assert hr.load(tmp_path)["fixtures"] == ["x", "y", "z"]

	def test_khoa_la_bao_loi_nem_ten_tep(self):
		tmp_path = self.tmp_path
		_w(tmp_path, "A.json", {"khong_biet": ["x"]})
		with self.assertRaisesRegex(ValueError, r"A\.json.*khong_biet"):
			hr.load(tmp_path)

	def test_tan_suat_scheduler_la_bao_loi(self):
		tmp_path = self.tmp_path
		_w(tmp_path, "A.json", {"scheduler_events": {"yearly": ["m.f"]}})
		with self.assertRaisesRegex(ValueError, "yearly"):
			hr.load(tmp_path)

	def test_scheduler_events_gop_theo_tan_suat(self):
		tmp_path = self.tmp_path
		_w(tmp_path, "A.json", {"scheduler_events": {"daily": ["m.a"], "hourly": ["m.h"]}})
		_w(tmp_path, "B.json", {"scheduler_events": {"daily": ["m.b", "m.a"]}})
		assert hr.load(tmp_path)["scheduler_events"] == {"daily": ["m.a", "m.b"], "hourly": ["m.h"]}

	def test_gia_tri_khong_phai_danh_sach_la_loi(self):
		tmp_path = self.tmp_path
		_w(tmp_path, "A.json", {"app_include_js": "/a.js"})
		with self.assertRaisesRegex(ValueError, "danh sách"):
			hr.load(tmp_path)

	def test_thu_muc_trong_hoac_khong_co(self):
		tmp_path = self.tmp_path
		assert hr.load(tmp_path / "khong_co")["app_include_js"] == []

	def test_so_dang_ky_thuc_cua_repo_hop_le_va_co_before_migrate(self):
		reg = hr.load()
		assert "normcore.generated.before_migrate" in reg["before_migrate"]

	def test_hooks_py_nhan_so_dang_ky_va_khong_mat_dong_cu(self):
		import ast

		src = (REPO / "normcore/hooks.py").read_text(encoding="utf-8")
		ast.parse(src)
		assert "hook_registry" in src and 'before_install = "normcore.install.before_install"' in src
