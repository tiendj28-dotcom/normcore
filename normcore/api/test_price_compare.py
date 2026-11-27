"""FEAT-028: API Bàn so sánh giá (FR-ADJ-001..005, 008, 010)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import price_compare as api
from normcore.core import permissions
from normcore.tests import costing_fixtures as cf
from normcore.tests.benchmark_utils import make_facility, price_values
from normcore.tests.utils import make_base, make_user

COST, PRICE = "NC Service Cost", "NC Benchmark Price"
CAT = "PC-GOLD"


def _price(facility, price, eff, status="Đã xác nhận", **kw):
	doc = frappe.get_doc(
		price_values(
			facility=facility,
			price=price,
			price_category=kw.pop("price_category", CAT),
			technical_service=kw.pop("technical_service", "DV-TEST-A"),
			service_name_raw="Dịch vụ thử",
			effective_date=eff,
			**kw,
		)
	)
	doc.flags.keep_status = status != "Đã xác nhận"
	doc.insert(ignore_permissions=True)
	if status != "Đã xác nhận":
		frappe.db.set_value(PRICE, doc.name, "status", status)
	return doc


class PriceCompareBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fin = make_user("fin.n81b@normcore.test", "NC Finance")
		self.aud = make_user("aud.n81b@normcore.test", "NC Auditor")
		self.dir = make_user("dir.n81b@normcore.test", "NC Director")
		self.head = make_user("head.n81b@normcore.test", "NC Department Head")
		self.cons = make_user("cons.n81b@normcore.test", "NC Consultant")
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)
		self.run = cf.make_golden_run(self.params, accounting_import=self.imp)
		self.assertEqual(self.run.run_costing(), "Đã tính")
		self.cost = frappe.get_value(COST, {"costing_run": self.run.name, "technical_service": "DV-TEST-A"})
		for i, (prov, level, own) in enumerate(
			[("Hà Nội", "Hạng I", "Công lập"), ("Hà Nội", "Hạng II", "Tư nhân"), ("Huế", "Hạng I", "Công lập")]
		):
			make_facility(f"BV-N81-{i}", province=prov, facility_level=level, ownership=own)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def three_prices(self):
		_price("BV-N81-0", 250000, "2026-06-01")
		_price("BV-N81-1", 280000, "2026-06-01")
		_price("BV-N81-2", 300000, "2026-06-01")


class TestPriceCompare(PriceCompareBase):
	def test_FR_ADJ_001_chi_gia_xac_nhan_cung_loai_gia(self):
		self.three_prices()
		_price("BV-N81-0", 1, "2026-07-01", status="Đề xuất")
		_price("BV-N81-1", 2, "2026-07-01", status="Loại bỏ")
		from normcore.tests.benchmark_utils import make_category

		make_category("GTC-KHAC")
		_price("BV-N81-2", 3, "2026-07-01", price_category="GTC-KHAC")
		frappe.set_user(self.fin)
		d = api.get_service_detail(self.cost)
		self.assertEqual(sorted(p["price"] for p in d["prices"]), [250000, 280000, 300000])
		self.assertEqual(float(d["stats"]["median"]), 280000)
		self.assertEqual(float(d["stats"]["deviation_pct"]), 7.9)
		self.assertTrue(d["stats"]["sufficient"])
		self.assertEqual(float(d["breakdown"]["total"]), float(d["breakdown"]["full_cost"]))

	def test_TC_ADJ_01_cua_so_24_thang_tren_site(self):
		_price("BV-N81-0", 100000, "2025-01-01")
		_price("BV-N81-0", 120000, "2026-06-01", source_doc_no="2")
		_price("BV-N81-1", 90000, "2024-10-01")
		frappe.set_user(self.fin)
		d = api.get_service_detail(self.cost)
		self.assertEqual([p["price"] for p in d["prices"]], [120000])
		reasons = {e["reason"] for e in d["excluded"]}
		self.assertEqual(reasons, {"Ngoài cửa sổ 24 tháng", "Cũ hơn giá khác của đơn vị"})

	def test_TC_ADJ_03_chua_du_du_lieu(self):
		_price("BV-N81-0", 250000, "2026-06-01")
		_price("BV-N81-1", 280000, "2026-06-01")
		frappe.set_user(self.fin)
		d = api.get_service_detail(self.cost)
		self.assertFalse(d["stats"]["sufficient"])
		self.assertEqual(d["stats"]["label"], "Chưa đủ dữ liệu so sánh")
		self.assertIsNone(d["stats"]["median"])
		row = next(r for r in api.get_comparison(self.run.name)["rows"] if r["service_cost"] == self.cost)
		self.assertEqual((row["label"], row["count"], row["exceeds"]), ("Chưa đủ dữ liệu so sánh", 2, False))

	def test_FR_ADJ_004_loc_tinh_lai(self):
		self.three_prices()
		frappe.set_user(self.fin)
		res = api.get_comparison(self.run.name)
		self.assertEqual(res["filter_options"]["provinces"], sorted(["Hà Nội", "Huế"]))
		self.assertEqual(res["run"]["window_months"], 24)
		row = next(r for r in res["rows"] if r["service_cost"] == self.cost)
		self.assertEqual((row["count"], float(row["median"])), (3, 280000))
		# lọc Hạng I: còn 2 đơn vị -> chưa đủ dữ liệu
		row = next(
			r for r in api.get_comparison(self.run.name, levels='["Hạng I"]')["rows"] if r["service_cost"] == self.cost
		)
		self.assertEqual((row["count"], row["sufficient"]), (2, False))
		# lọc Hà Nội + tỉnh qua chi tiết
		d = api.get_service_detail(self.cost, provinces=["Hà Nội"])
		self.assertEqual(d["stats"]["count"], 2)

	def test_TC_ADJ_08_co_cau_gia(self):
		frappe.set_user(self.fin)
		b = api.get_service_detail(self.cost)["breakdown"]
		self.assertEqual(round(float(b["full_cost"]), 2), 287745.46)
		self.assertEqual(round(float(b["total"]), 2), 287745.46)
		self.assertEqual(len([r for r in b["rows"] if r["group"] == "Trực tiếp"]), 6)
		self.assertTrue(all(r["share_pct"] is not None for r in b["rows"]))
		self.assertEqual(round(sum(float(r["share_pct"]) for r in b["rows"])), 100)

	def test_quyen_so_sanh_truong_khoa_auditor(self):
		self.three_prices()
		# Auditor, Director: xem được, không sinh gợi ý/quyết định (Auditor)
		frappe.set_user(self.aud)
		d = api.get_service_detail(self.cost)
		self.assertFalse(d["can_generate"] or d["can_decide"])
		frappe.set_user(self.dir)
		d = api.get_service_detail(self.cost)
		self.assertFalse(d["can_generate"])
		self.assertTrue(d["can_decide"])
		frappe.set_user(self.fin)
		d = api.get_service_detail(self.cost)
		self.assertTrue(d["can_generate"] and d["can_decide"])
		# Trưởng khoa khác khoa: không thấy dịch vụ, không đọc chi tiết
		make_base("DV-N81-X", "KHOA-N81-X")
		frappe.set_user("Administrator")
		permissions.assign_department(self.head, "KHOA-N81-X")
		frappe.set_user(self.head)
		self.assertEqual(api.get_comparison(self.run.name)["rows"], [])
		with self.assertRaises(frappe.PermissionError):
			api.get_service_detail(self.cost)
		frappe.set_user("Administrator")
		permissions.assign_department(self.head, self.dept)
		frappe.set_user(self.head)
		self.assertEqual(len(api.get_comparison(self.run.name)["rows"]), 2)
		self.assertTrue(api.get_service_detail(self.cost)["can_decide"])
		# Consultant không đọc kết quả tính giá
		frappe.set_user(self.cons)
		with self.assertRaises(frappe.PermissionError):
			api.get_comparison(self.run.name)

	def test_lan_tinh_chua_co_ket_qua(self):
		frappe.set_user("Administrator")
		frappe.db.set_value("NC Costing Run", self.run.name, "status", "Nháp")
		frappe.set_user(self.fin)
		with self.assertRaises(frappe.ValidationError):
			api.get_comparison(self.run.name)
