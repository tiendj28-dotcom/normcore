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


class TestSuggestions(PriceCompareBase):
	def over_tolerance(self):
		# DV-TEST-A trong TC-ADJ-04: hệ số sử dụng EQ1 = 0,4 (golden mặc định 0,5)
		frappe.db.set_value("NC Equipment", "EQ1", "utilization_rate", 0.4)
		_price("BV-N81-0", 250000, "2026-06-01")
		_price("BV-N81-1", 250000, "2026-06-02")
		_price("BV-N81-2", 250000, "2026-06-03")

	def test_TC_ADJ_03_khong_sinh_goi_y_khi_chua_du_du_lieu(self):
		_price("BV-N81-0", 250000, "2026-06-01")
		_price("BV-N81-1", 250000, "2026-06-02")
		frappe.set_user(self.fin)
		self.assertEqual(api.generate_suggestions(self.cost), [])
		self.assertEqual(frappe.db.count("NC Adjustment Suggestion"), 0)

	def test_FR_ADJ_005_trong_nguong_khong_goi_y(self):
		for i, p in enumerate((300000, 301000, 302000)):
			_price(f"BV-N81-{i}", p, f"2026-06-0{i + 1}")
		frappe.set_user(self.fin)
		self.assertEqual(api.generate_suggestions(self.cost), [])

	def test_FR_ADJ_005_sinh_goi_y_vuot_nguong(self):
		self.over_tolerance()
		frappe.set_user(self.fin)
		out = api.generate_suggestions(self.cost)
		by = {s["rule_code"]: s for s in out}
		eq1 = by["BR-ADJ-001"]
		self.assertEqual((eq1["target_ref"], eq1["current_value"], eq1["suggested_value"]), ("EQ1", "0,4", "0,5"))
		self.assertLess(eq1["estimated_impact"], 0)
		self.assertEqual(eq1["status"], "Mới")
		self.assertTrue(eq1["text"])
		impacts = [abs(s["estimated_impact"]) for s in out if s["estimated_impact"] is not None]
		self.assertEqual(impacts, sorted(impacts, reverse=True))

	def test_FR_ADJ_005_sinh_lai_khong_trung(self):
		self.over_tolerance()
		frappe.set_user(self.fin)
		first = api.generate_suggestions(self.cost)
		n = frappe.db.count("NC Adjustment Suggestion", {"service_cost": self.cost})
		api.decide_suggestion(first[0]["name"], "Từ chối", "Không khả thi")
		again = api.generate_suggestions(self.cost)
		self.assertEqual(frappe.db.count("NC Adjustment Suggestion", {"service_cost": self.cost}), n)
		self.assertEqual(len(again), len(first))
		decided = next(s for s in again if s["name"] == first[0]["name"])
		self.assertEqual(decided["status"], "Từ chối")
		# đủ trong ngưỡng sau khi giá tham chiếu đổi: bản "Mới" không còn kích hoạt bị xóa, bản đã quyết giữ
		for name in frappe.get_all(PRICE, pluck="name"):
			frappe.db.set_value(PRICE, name, "price", 300000)
		left = api.generate_suggestions(self.cost)
		self.assertEqual([s["name"] for s in left], [first[0]["name"]])

	def test_FR_ADJ_008_tu_choi_can_ly_do(self):
		self.over_tolerance()
		frappe.set_user(self.fin)
		s = api.generate_suggestions(self.cost)[0]
		for reason in (None, "  "):
			with self.assertRaises(frappe.ValidationError):
				api.decide_suggestion(s["name"], "Từ chối", reason)
		with self.assertRaises(frappe.ValidationError):
			api.decide_suggestion(s["name"], "Không rõ")
		d = api.decide_suggestion(s["name"], "Từ chối", "Máy mới nhập")
		self.assertEqual((d["status"], d["decision_reason"], d["decided_by"]), ("Từ chối", "Máy mới nhập", self.fin))
		self.assertTrue(d["decided_on"])
		with self.assertRaises(frappe.ValidationError):  # đã quyết, không quyết lại
			api.decide_suggestion(s["name"], "Chấp nhận")

	def test_FR_ADJ_008_chap_nhan_luu_nguoi_va_thoi_diem(self):
		self.over_tolerance()
		frappe.set_user(self.fin)
		s = api.generate_suggestions(self.cost)[0]
		d = api.decide_suggestion(s["name"], "Chấp nhận")
		self.assertEqual((d["status"], d["decided_by"]), ("Chấp nhận", self.fin))

	def test_FR_ADJ_008_chap_nhan_can_sua_quy_trinh_bi_chan(self):
		self.over_tolerance()
		frappe.set_user("Administrator")
		doc = frappe.get_doc(
			{
				"doctype": "NC Adjustment Suggestion",
				"service_cost": self.cost,
				"rule_code": "BR-ADJ-003",
				"direction": "Giảm",
				"component": "DRUG",
				"target_ref": "L05",
				"requires_procedure_change": 1,
			}
		)
		doc.flags.adj_system = True
		doc.insert()
		frappe.set_user(self.fin)
		with self.assertRaises(frappe.ValidationError) as ctx:
			api.decide_suggestion(doc.name, "Chấp nhận")
		self.assertIn("sửa quy trình", str(ctx.exception))
		self.assertEqual(api.decide_suggestion(doc.name, "Từ chối", "Chưa phù hợp")["status"], "Từ chối")

	def test_quyen_quyet_dinh_goi_y(self):
		self.over_tolerance()
		frappe.set_user(self.fin)
		names = [s["name"] for s in api.generate_suggestions(self.cost)]
		self.assertGreaterEqual(len(names), 2)
		extra = frappe.get_doc(
			{
				"doctype": "NC Adjustment Suggestion",
				"service_cost": self.cost,
				"rule_code": "BR-ADJ-004",
				"direction": "Giảm",
				"component": "DRUG",
				"target_ref": "L05",
			}
		)
		extra.flags.adj_system = True
		extra.insert(ignore_permissions=True)
		names = names[:2] + [extra.name]
		# Director, Trưởng khoa khoa mình: được; không có Sinh gợi ý
		frappe.set_user(self.dir)
		self.assertEqual(api.decide_suggestion(names[0], "Chấp nhận")["decided_by"], self.dir)
		with self.assertRaises(frappe.PermissionError):
			api.generate_suggestions(self.cost)
		frappe.set_user("Administrator")
		permissions.assign_department(self.head, self.dept)
		frappe.set_user(self.head)
		self.assertEqual(api.decide_suggestion(names[1], "Chấp nhận")["decided_by"], self.head)
		# Trưởng khoa khoa khác, Consultant, Auditor: bị từ chối
		make_base("DV-N81-X", "KHOA-N81-X")
		frappe.set_user("Administrator")
		head2 = make_user("head2.n81b@normcore.test", "NC Department Head")
		permissions.assign_department(head2, "KHOA-N81-X")
		for user in (head2, self.cons, self.aud):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.decide_suggestion(names[2], "Từ chối", "x")
			with self.assertRaises(frappe.PermissionError):
				api.generate_suggestions(self.cost)
