"""TC-ACC-04 (loại U): quét quyền DocType theo ma trận data-model mục 4; không cấp quyền cho All (FR-ACC-002)."""

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_spec = importlib.util.spec_from_file_location("check_conventions", ROOT / "scripts" / "check_conventions.py")
cc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cc)

SAMPLE = {
	"doctype": "DocType",
	"name": "NC Technical Service",
	"track_changes": 1,
	"fields": [],
	"permissions": [
		{"role": "NC Clinician", "read": 1},
		{"role": "NC Department Head", "read": 1},
		{"role": "NC Council Member", "read": 1},
		{"role": "NC Finance", "read": 1},
		{"role": "NC Resource Manager", "read": 1},
		{"role": "NC Document Controller", "read": 1, "write": 1, "create": 1},
		{"role": "NC Director", "read": 1},
		{"role": "NC Consultant", "read": 1},
		{"role": "NC Admin", "read": 1, "write": 1, "create": 1, "delete": 1},
		{"role": "NC Auditor", "read": 1},
	],
}


class TestTCACC04(unittest.TestCase):
	def test_TC_ACC_04_app_hien_tai_sach(self):
		self.assertEqual(cc.run(ROOT), [])

	def test_TC_ACC_04_mau_hop_le_khong_loi(self):
		self.assertEqual(cc.check_permissions(SAMPLE, "mau.json"), [])

	def test_TC_ACC_04_cap_quyen_cho_All_bi_bao_loi(self):
		bad = copy.deepcopy(SAMPLE)
		bad["permissions"].append({"role": "All", "read": 1})
		errs = cc.check_permissions(bad, "mau.json")
		self.assertTrue(any("NC-07" in e for e in errs), errs)

	def test_TC_ACC_04_lech_ma_tran_bi_bao_loi(self):
		bad = copy.deepcopy(SAMPLE)
		bad["permissions"][0]["write"] = 1  # Clinician ghi danh mục dịch vụ: ma trận chỉ cho đọc
		errs = cc.check_permissions(bad, "mau.json")
		self.assertTrue(any("NC-08" in e and "NC Clinician" in e for e in errs), errs)

	def test_TC_ACC_04_xoa_chi_NC_Admin_tren_bon_danh_muc(self):
		bad = copy.deepcopy(SAMPLE)
		bad["permissions"][3]["delete"] = 1  # NC Finance xóa
		self.assertTrue(any("NC Finance" in e for e in cc.check_permissions(bad, "mau.json")))
		other = copy.deepcopy(SAMPLE)
		other["name"] = "NC Norm Set"  # NC Admin có delete ở DocType nghiệp vụ là lỗi
		self.assertTrue(any("NC Admin" in e for e in cc.check_permissions(other, "mau.json")))

	def test_TC_ACC_04_doctype_chua_co_dong_ma_tran_bi_bao_loi(self):
		bad = copy.deepcopy(SAMPLE)
		bad["name"] = "NC Khong Ton Tai"
		self.assertTrue(any("NC-08" in e for e in cc.check_permissions(bad, "mau.json")))

	def test_TC_ACC_04_dong_ma_tran_thieu_cot_bi_bao_loi(self):
		saved = cc.MATRIX["Dịch vụ kỹ thuật, chuyên khoa"]
		try:
			cc.MATRIX["Dịch vụ kỹ thuật, chuyên khoa"] = "R R R"  # thiếu 7 cột
			errs = cc.check_permissions(SAMPLE, "mau.json")
		finally:
			cc.MATRIX["Dịch vụ kỹ thuật, chuyên khoa"] = saved
		self.assertTrue(any("NC-08" in e and "cột" in e for e in errs), errs)


class TestTCCLS44NC06(unittest.TestCase):
	def _errs(self, **extra):
		bad = copy.deepcopy(SAMPLE)
		bad["permissions"][-1].update(extra)
		return cc.check_doctype(bad, "mau.json")

	def test_TC_CLS_44_nc06_mau_sach(self):
		self.assertEqual([e for e in self._errs() if "NC-06" in e], [])

	def test_TC_CLS_44_nc06_import(self):
		self.assertTrue(any("NC-06" in e and "import" in e for e in self._errs(**{"import": 1})))

	def test_TC_CLS_44_nc06_share(self):
		self.assertTrue(any("NC-06" in e and "share" in e for e in self._errs(share=1)))

	def test_TC_CLS_44_nc06_set_user_permissions(self):
		self.assertTrue(
			any("NC-06" in e and "set_user_permissions" in e for e in self._errs(set_user_permissions=1))
		)

	def test_TC_CLS_44_nc06_thieu_read(self):
		bad = copy.deepcopy(SAMPLE)
		bad["permissions"] = [p for p in bad["permissions"] if p["role"] != "NC Auditor"]
		self.assertTrue(any("NC-06" in e and "thiếu quyền đọc" in e for e in cc.check_doctype(bad, "m.json")))
