"""TC-CLS-44 (loại U): hàm thuần kiểm NC Auditor chỉ đọc (FR-ACC-007)."""

import importlib.util
import unittest
from pathlib import Path

from normcore.core import readonly as ro

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("check_conventions", ROOT / "scripts" / "check_conventions.py")
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)

AUD = "NC Auditor"
CLEAN = [
	{"role": "NC Admin", "permlevel": 0, "read": 1, "write": 1, "create": 1, "delete": 1},
	{"role": AUD, "permlevel": 0, "read": 1},
]


class TestPermViolations(unittest.TestCase):
	def test_TC_CLS_44_dau_vao_sach(self):
		self.assertEqual(ro.perm_violations("NC Norm Set", CLEAN, AUD), [])

	def test_TC_CLS_44_thieu_read(self):
		out = ro.perm_violations("NC Norm Set", [CLEAN[0]], AUD)
		self.assertEqual(len(out), 1)
		self.assertIn("thiếu quyền read", out[0])

	def test_TC_CLS_44_thieu_read_o_permlevel_0(self):
		out = ro.perm_violations("NC Norm Set", [{"role": AUD, "permlevel": 1, "read": 1}], AUD)
		self.assertTrue(any("thiếu quyền read" in v for v in out), out)

	def test_TC_CLS_44_tung_co_ghi_bi_bat(self):
		for ptype in ro.WRITE_PTYPES:
			perms = [{"role": AUD, "permlevel": 0, "read": 1, ptype: 1}]
			out = ro.perm_violations("NC Norm Set", perms, AUD)
			self.assertEqual(len(out), 1, ptype)
			self.assertIn(ptype, out[0])
			self.assertIn("NC Norm Set", out[0])

	def test_TC_CLS_44_permlevel_lon_hon_0(self):
		perms = [{"role": AUD, "permlevel": 0, "read": 1}, {"role": AUD, "permlevel": 2, "write": 1}]
		out = ro.perm_violations("NC Norm Set", perms, AUD)
		self.assertEqual(len(out), 1)
		self.assertIn("permlevel 2", out[0])

	def test_TC_CLS_44_co_gia_tri_chuoi_va_khong(self):
		perms = [{"role": AUD, "permlevel": 0, "read": "1", "write": "1", "create": 0}]
		out = ro.perm_violations("X", perms, AUD)
		self.assertEqual(len(out), 1)

	def test_TC_CLS_44_vai_tro_khac_khong_bi_bao(self):
		perms = [{"role": "NC Finance", "permlevel": 0, "read": 1, "write": 1}, {"role": AUD, "read": 1}]
		self.assertEqual(ro.perm_violations("X", perms, AUD), [])

	def test_TC_CLS_44_write_ptypes_bang_NC06(self):
		self.assertEqual(tuple(ro.WRITE_PTYPES), tuple(cc.AUDITOR_FORBIDDEN))
		self.assertEqual(ro.READ_ONLY_ROLE, cc.AUDITOR)


class TestWorkflowViolations(unittest.TestCase):
	def wf(self, allowed="NC Clinician", allow_edit="NC Clinician"):
		return {
			"name": "Quy trình",
			"document_type": "NC Clinical Procedure",
			"transitions": [{"state": "Nháp", "action": "Gửi duyệt", "allowed": allowed}],
			"states": [{"state": "Nháp", "allow_edit": allow_edit}],
		}

	def test_TC_CLS_44_workflow_sach(self):
		self.assertEqual(ro.workflow_violations([self.wf()], AUD), [])
		self.assertEqual(ro.workflow_violations([], AUD), [])

	def test_TC_CLS_44_chuyen_trang_thai(self):
		out = ro.workflow_violations([self.wf(allowed=AUD)], AUD)
		self.assertEqual(len(out), 1)
		self.assertIn("Gửi duyệt", out[0])
		self.assertIn("Nháp", out[0])

	def test_TC_CLS_44_allow_edit(self):
		out = ro.workflow_violations([self.wf(allow_edit=AUD)], AUD)
		self.assertEqual(len(out), 1)
		self.assertIn("allow_edit", out[0])

	def test_TC_CLS_44_thieu_khoa(self):
		self.assertEqual(ro.workflow_violations([{"name": "W"}], AUD), [])
