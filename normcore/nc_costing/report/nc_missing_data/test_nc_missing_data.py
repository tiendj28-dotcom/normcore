"""FEAT-037: báo cáo thiếu dữ liệu (FR-OUT-012; TC-CLS-39)."""

import frappe
from frappe.permissions import add_user_permission
from frappe.tests.utils import FrappeTestCase

from normcore.nc_costing.report.nc_missing_data.nc_missing_data import execute
from normcore.tests import cls_fixtures as fx
from normcore.tests.utils import make_user

FIN = "fin.miss37@normcore.test"
HEAD = "head.miss37@normcore.test"
CLIN = "clin.miss37@normcore.test"


class TestNCMissingDataReport(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.world = fx.make_cls_golden()
		for u, r in ((FIN, "NC Finance"), (HEAD, "NC Department Head"), (CLIN, "NC Clinician")):
			make_user(u, r)
		self.filters = {
			"fiscal_year": 2026,
			"costing_date": "2026-12-31",
			"parameter_set": self.world.params.name,
			"price_category": "PC-GOLD",
		}

	def tearDown(self):
		frappe.set_user("Administrator")

	def _gaps(self, **extra):
		_cols, rows, _msg, _chart, _summary = execute({**self.filters, **extra})
		return sorted({(r["service"], r["kind"]) for r in rows})

	def test_khong_thieu_gi(self):
		_c, rows, msg, _ch, summary = execute(self.filters)
		self.assertEqual(rows, [])
		self.assertIn("Nothing is missing", msg)
		self.assertTrue(all(x["value"] == 0 for x in summary))

	def test_TC_CLS_39_ba_dich_vu_thieu(self):
		self.assertEqual(frappe.db.count("NC Costing Run"), 0)  # chạy được khi chưa có lần tính nào
		frappe.db.delete("NC Item Price", {"item": "THUOCX"})  # DV-TEST-A thiếu đơn giá
		frappe.db.delete("NC Service Volume", {"technical_service": "DV-TEST-B"})  # thiếu sản lượng
		frappe.delete_doc("NC QC Plan", "KHCL-GLU-B", force=True)  # hệ thống GLU-B thiếu kế hoạch chất lượng
		got = self._gaps()
		self.assertEqual(
			got,
			[
				("DV-TEST-A", "Thiếu đơn giá"),
				("DV-TEST-B", "Thiếu sản lượng"),
				("GLU", "Thiếu kế hoạch chất lượng"),
			],
		)
		self.assertEqual(frappe.db.count("NC Costing Run"), 0)  # không tạo bản ghi
		_c, rows, _m, _ch, summary = execute(self.filters)
		self.assertEqual({x["label"]: x["value"] for x in summary}["Thiếu kế hoạch chất lượng"], 1)
		self.assertEqual(self._gaps(technical_service="GLU"), [("GLU", "Thiếu kế hoạch chất lượng")])
		self.assertEqual(self._gaps(kind="Thiếu sản lượng"), [("DV-TEST-B", "Thiếu sản lượng")])

	def test_truong_khoa_bi_ep_khoa(self):
		frappe.db.delete("NC Service Volume", {"technical_service": "DV-TEST-B"})
		add_user_permission("NC Department", fx.DEPT, HEAD)
		frappe.set_user(HEAD)
		self.assertEqual(self._gaps(), [])  # DV-TEST-B ở khoa khác: không thấy
		self.assertEqual(self._gaps(department=self.world.other_dept), [])  # đòi khoa ngoài quyền vẫn rỗng
		frappe.set_user("Administrator")
		add_user_permission("NC Department", self.world.other_dept, HEAD)
		frappe.set_user(HEAD)
		self.assertEqual(self._gaps(), [("DV-TEST-B", "Thiếu sản lượng")])

	def test_clinician_khong_mo_duoc(self):
		frappe.set_user(CLIN)
		with self.assertRaises(frappe.PermissionError):
			execute(self.filters)
		self.assertFalse(frappe.get_doc("Report", "NC Missing Data").is_permitted())
		frappe.set_user(FIN)
		self.assertTrue(frappe.get_doc("Report", "NC Missing Data").is_permitted())
