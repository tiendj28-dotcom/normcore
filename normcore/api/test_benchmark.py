"""FEAT-026: nhập Excel giá tham chiếu, xác nhận, so sánh, giá hiệu chỉnh, phiếu khảo sát."""

import io

import frappe
from frappe.tests.utils import FrappeTestCase
from openpyxl import Workbook

from normcore.api import importer as importer_api
from normcore.core.importer import get_import_set, header_label
from normcore.tests.benchmark_utils import CATEGORY, FACILITY, make_category, make_facility, make_service
from normcore.tests.utils import make_user

KEY = "nc_benchmark_price"
DT = "NC Benchmark Price"

SERVICES = {
	"GTC-DV-01": "Định lượng Glucose máu",
	"GTC-DV-02": "Siêu âm ổ bụng tổng quát",
	"GTC-DV-03": "Chụp X-quang ngực thẳng",
	"GTC-DV-04": "Đo điện tim thường",
	"GTC-DV-05": "Công thức máu toàn phần",
}


def xlsx(rows):
	wb = Workbook()
	for r in rows:
		wb.active.append(r)
	buf = io.BytesIO()
	wb.save(buf)
	return buf.getvalue()


def head():
	return [header_label(c) for c in get_import_set(KEY).columns]


def row(**vals):
	base = {
		"facility": FACILITY,
		"price_category": CATEGORY,
		"effective_date": "2026-01-01",
		"source_doc_no": "123/QĐ-BV",
	}
	base.update(vals)
	return [base.get(c.fieldname) for c in get_import_set(KEY).columns]


def setup_data():
	frappe.set_user("Administrator")
	make_facility()
	make_category()
	for code, name in SERVICES.items():
		make_service(code, name)


class TestBenchmarkImport(FrappeTestCase):
	def setUp(self):
		setup_data()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _file5(self):
		return xlsx(
			[
				head(),
				row(technical_service="GTC-DV-01", price=25000),
				row(technical_service="GTC-DV-02", price=120000),
				row(technical_service="GTC-DV-03", price=90000),
				row(service_name_raw="Đo điện tim thường", price=40000),
				row(service_name_raw="cong thuc mau toan phan", price=60000),
			]
		)

	def test_TC_BM_01_nhap_tep_de_xuat_dich_vu(self):
		before = frappe.db.count(DT)
		dry = importer_api.run_import(KEY, self._file5(), "thu")
		self.assertEqual((dry["created"], dry["errors"]), (5, []))
		self.assertEqual(frappe.db.count(DT), before)  # chế độ thu không ghi
		res = importer_api.run_import(KEY, self._file5(), "ghi")
		self.assertEqual((res["created"], res["errors"]), (5, []))
		self.assertEqual(frappe.db.count(DT), before + 5)
		rows = frappe.get_all(
			DT,
			filters={"facility": FACILITY},
			fields=["service_name_raw", "technical_service", "status", "verified_by"],
		)
		by = {r.service_name_raw: r for r in rows}
		# 2 dòng chỉ có tên gốc: dịch vụ đề xuất, chờ xác nhận
		for raw, code in (("Đo điện tim thường", "GTC-DV-04"), ("cong thuc mau toan phan", "GTC-DV-05")):
			self.assertEqual(
				(by[raw].technical_service, by[raw].status, by[raw].verified_by), (code, "Đề xuất", None)
			)
		# 3 dòng có mã: đã xác nhận, tên gốc lấy từ dịch vụ (ASM-026-04)
		for code, name in list(SERVICES.items())[:3]:
			self.assertEqual((by[name].technical_service, by[name].status), (code, "Đã xác nhận"))

	def test_TC_BM_02_tu_choi_dong_trung(self):
		importer_api.run_import(KEY, self._file5(), "ghi")
		n = frappe.db.count(DT)
		# nhập lại một dòng trùng đơn vị, dịch vụ, loại giá, ngày
		again = xlsx([head(), row(technical_service="GTC-DV-01", price=26000)])
		for mode in ("thu", "ghi"):
			res = importer_api.run_import(KEY, again, mode)
			self.assertEqual(res["created"], 0)
			self.assertEqual(res["updated"], 0)
			self.assertEqual(len(res["errors"]), 1)
			self.assertIn("trùng", res["errors"][0]["message"])
		# trùng theo tên gốc (đã chuẩn hóa) với dòng chỉ có tên
		again = xlsx([head(), row(service_name_raw="ĐO ĐIỆN TIM THƯỜNG", price=41000)])
		res = importer_api.run_import(KEY, again, "ghi")
		self.assertEqual((res["created"], len(res["errors"])), (0, 1))
		self.assertEqual(frappe.db.count(DT), n)
		# cùng giá trị cũng không rơi vào "không đổi"
		same = xlsx([head(), row(technical_service="GTC-DV-01", price=25000)])
		res = importer_api.run_import(KEY, same, "thu")
		self.assertEqual((res["unchanged"], len(res["errors"])), (0, 1))

	def test_FR_BM_002_nhap_mau_khong_trung(self):
		# khác ngày hiệu lực thì nhập được
		f = xlsx([head(), row(technical_service="GTC-DV-01", price=26000, effective_date="2026-04-01")])
		res = importer_api.run_import(KEY, f, "ghi")
		self.assertEqual((res["created"], res["errors"]), (1, []))
		# thiếu tên gốc và mã
		f = xlsx([head(), row(price=1000)])
		res = importer_api.run_import(KEY, f, "thu")
		self.assertEqual(res["created"], 0)
		self.assertIn("Tên dịch vụ gốc", res["errors"][0]["column"])
		# thiếu nguồn
		f = xlsx([head(), row(technical_service="GTC-DV-01", price=1000, source_doc_no=None)])
		res = importer_api.run_import(KEY, f, "thu")
		self.assertIn("Số văn bản nguồn", res["errors"][0]["column"])
		# nguồn là đường dẫn
		f = xlsx(
			[
				head(),
				row(
					technical_service="GTC-DV-01",
					price=1000,
					source_doc_no=None,
					source_url="https://x.test/a",
				),
			]
		)
		self.assertEqual(importer_api.run_import(KEY, f, "thu")["created"], 1)
		# đơn vị không tồn tại
		f = xlsx([head(), row(technical_service="GTC-DV-01", price=1000, facility="Không có")])
		self.assertEqual(importer_api.run_import(KEY, f, "thu")["created"], 0)

	def test_FR_BM_002_mau_nhap_co_dung_cot(self):
		labels = head()
		self.assertEqual(
			labels,
			[
				"Đơn vị *",
				"Mã dịch vụ",
				"Tên dịch vụ gốc",
				"Giá *",
				"Loại giá *",
				"Ngày hiệu lực *",
				"Số văn bản nguồn",
				"Đường dẫn nguồn",
			],
		)
		_name, content = importer_api.build_template_file(KEY)
		self.assertTrue(content)

	def test_quyen_feat_026_nhap(self):
		auditor = make_user("bmimp.aud@normcore.test", "NC Auditor")
		clin = make_user("bmimp.cl@normcore.test", "NC Clinician")
		fin = make_user("bmimp.fin@normcore.test", "NC Finance")
		for email in (auditor, clin):
			frappe.set_user(email)
			with self.assertRaises(frappe.PermissionError):
				importer_api.run_import(KEY, self._file5(), "ghi")
			self.assertNotIn(KEY, [s["key"] for s in importer_api.list_import_sets()])
		frappe.set_user(fin)
		self.assertIn(KEY, [s["key"] for s in importer_api.list_import_sets()])
		res = importer_api.run_import(KEY, self._file5(), "ghi")
		self.assertEqual((res["created"], res["errors"]), (5, []))


def _mk(**kw):
	from normcore.tests.benchmark_utils import make_price

	return make_price(**kw)


class TestBenchmarkApi(FrappeTestCase):
	def setUp(self):
		setup_data()

		frappe.db.delete("NC CPI Index")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_BM_03_so_sanh_chi_dung_gia_da_xac_nhan(self):
		from normcore.api import benchmark as api

		for i, d in enumerate(("2026-01-01", "2026-02-01", "2026-03-01")):
			make_facility(f"Đơn vị so sánh {i}")
			_mk(
				facility=f"Đơn vị so sánh {i}",
				technical_service="GTC-DV-01",
				effective_date=d,
				price=25000 + i,
			)
		confirmed = frappe.get_all(
			DT, filters={"technical_service": "GTC-DV-01", "status": "Đã xác nhận"}, pluck="name"
		)
		self.assertEqual(len(confirmed), 3)
		# 1 giá "Đề xuất" (khớp tên, chưa xác nhận)
		prop = _mk(service_name_raw="dinh luong glucose mau", effective_date="2026-04-01")
		self.assertEqual((prop.technical_service, prop.status), ("GTC-DV-01", "Đề xuất"))
		res = api.get_comparable_prices("GTC-DV-01")
		self.assertEqual(sorted(r["name"] for r in res["rows"]), sorted(confirmed))
		self.assertNotIn(prop.name, [r["name"] for r in res["rows"]])
		row = res["rows"][0]
		for k in (
			"facility_name",
			"province",
			"ownership",
			"facility_level",
			"price",
			"source_doc_no",
			"adjusted",
		):
			self.assertIn(k, row)
		# lọc theo loại giá
		self.assertEqual(api.get_comparable_prices("GTC-DV-01", price_category="khong-co")["rows"], [])

	def test_TC_BM_04_gia_hieu_chinh_tren_site(self):
		from decimal import Decimal

		from normcore.api import benchmark as api

		p = _mk(technical_service="GTC-DV-01", price=200000, effective_date="2026-01-15")
		# thiếu chỉ số: không hiệu chỉnh, nêu tháng thiếu
		out = api.get_adjusted_price(p.name, "2026-04-01")
		self.assertIsNone(out["adjusted_price"])
		self.assertEqual([str(m) for m in out["missing"]], ["2026-01-01", "2026-04-01"])
		frappe.get_doc({"doctype": "NC CPI Index", "month": "2026-01-20", "index_value": 100}).insert()
		frappe.get_doc({"doctype": "NC CPI Index", "month": "2026-04-01", "index_value": 104}).insert()
		out = api.get_adjusted_price(p.name, "2026-04-10")
		self.assertEqual(Decimal(str(out["adjusted_price"])), Decimal("208000.00"))
		self.assertEqual(out["price"], 200000)
		# mặc định: tháng có chỉ số mới nhất
		out = api.get_adjusted_price(p.name)
		self.assertEqual(Decimal(str(out["adjusted_price"])), Decimal("208000.00"))
		res = api.get_comparable_prices("GTC-DV-01")
		self.assertEqual(str(res["target_month"]), "2026-04-01")
		self.assertEqual(Decimal(str(res["rows"][0]["adjusted"]["adjusted_price"])), Decimal("208000.00"))

	def test_FR_BM_004_xac_nhan_cap_khop(self):
		from normcore.api import benchmark as api

		p1 = _mk(service_name_raw="dinh luong glucose mau")
		p2 = _mk(service_name_raw="Tên lạ không khớp", effective_date="2026-02-01")
		self.assertEqual((p1.status, p2.status, p2.technical_service), ("Đề xuất", "Đề xuất", None))
		res = api.confirm_prices([p1.name, p2.name])
		self.assertEqual(res["confirmed"], [p1.name])
		self.assertEqual([e["name"] for e in res["errors"]], [p2.name])
		p1.reload()
		self.assertEqual((p1.status, p1.verified_by), ("Đã xác nhận", "Administrator"))
		self.assertTrue(p1.verified_on)
		# đổi cặp khớp trước khi xác nhận (một dòng)
		res = api.confirm_prices([p2.name], technical_service="GTC-DV-02")
		self.assertEqual((res["confirmed"], res["errors"]), ([p2.name], []))
		self.assertEqual(frappe.db.get_value(DT, p2.name, "technical_service"), "GTC-DV-02")
		# đổi cặp khớp khi nhiều dòng: lỗi
		with self.assertRaises(frappe.ValidationError):
			api.confirm_prices([p1.name, p2.name], technical_service="GTC-DV-02")
		# loại bỏ, mở lại
		self.assertEqual(api.reject_prices([p1.name])["rejected"], [p1.name])
		self.assertEqual(frappe.db.get_value(DT, p1.name, ["status", "verified_by"]), ("Loại bỏ", None))
		self.assertEqual(api.confirm_prices([p1.name])["confirmed"], [])  # dòng Loại bỏ không xác nhận được
		self.assertEqual(api.reopen_prices([p1.name, p2.name])["reopened"], [p1.name, p2.name])
		self.assertEqual(frappe.db.get_value(DT, p2.name, ["status", "verified_by"]), ("Đề xuất", None))
		# names dạng chuỗi JSON
		self.assertEqual(api.confirm_prices(f'["{p1.name}"]')["confirmed"], [p1.name])

	def test_FR_BM_007_mo_lai_dong_trung_tra_loi(self):
		from normcore.api import benchmark as api

		a = _mk(technical_service="GTC-DV-01")
		self.assertEqual(api.reject_prices([a.name])["rejected"], [a.name])
		b = _mk(technical_service="GTC-DV-01")  # nhập lại đúng khóa, a đã Loại bỏ nên không trùng
		res = api.reopen_prices([a.name])
		self.assertEqual(res["reopened"], [])
		self.assertEqual([e["name"] for e in res["errors"]], [a.name])
		self.assertIn("Trùng", res["errors"][0]["message"])
		self.assertIn(b.name, res["errors"][0]["message"])
		self.assertEqual(frappe.db.get_value(DT, a.name, "status"), "Loại bỏ")
		# reject cũng trả errors (dòng đã Loại bỏ không loại bỏ lại được)
		res = api.reject_prices([a.name])
		self.assertEqual(res["rejected"], [])
		self.assertEqual([e["name"] for e in res["errors"]], [a.name])

	def test_quyen_feat_026_api(self):
		from normcore.api import benchmark as api

		p = _mk(service_name_raw="dinh luong glucose mau")
		clin = make_user("bmapi.cl@normcore.test", "NC Clinician")
		aud = make_user("bmapi.aud@normcore.test", "NC Auditor")
		fin = make_user("bmapi.fin@normcore.test", "NC Finance")
		dh = make_user("bmapi.dh@normcore.test", "NC Department Head")
		frappe.set_user(clin)
		for call in (
			lambda: api.get_comparable_prices("GTC-DV-01"),
			lambda: api.get_adjusted_price(p.name),
			lambda: api.confirm_prices([p.name]),
			lambda: api.reject_prices([p.name]),
			lambda: api.reopen_prices([p.name]),
		):
			self.assertRaises(frappe.PermissionError, call)
		for user in (aud, dh):
			frappe.set_user(user)
			self.assertEqual(api.get_comparable_prices("GTC-DV-01")["rows"], [])  # đọc được
			for call in (
				lambda: api.confirm_prices([p.name]),
				lambda: api.reject_prices([p.name]),
				lambda: api.reopen_prices([p.name]),
			):
				self.assertRaises(frappe.PermissionError, call)
		frappe.set_user(fin)
		self.assertEqual(api.confirm_prices([p.name])["confirmed"], [p.name])


class TestPriceSurvey(FrappeTestCase):
	def setUp(self):
		setup_data()
		spec = frappe.db.get_value("NC Specialty", {}, "name")
		if not spec:
			spec = (
				frappe.get_doc(
					{
						"doctype": "NC Specialty",
						"specialty_code": "GTC-CK",
						"specialty_name": "Chuyên khoa thử GTC",
					}
				)
				.insert()
				.name
			)
		self.spec = spec
		frappe.db.set_value("NC Technical Service", {"name": ["in", list(SERVICES)]}, "specialty", None)
		for code in ("GTC-DV-01", "GTC-DV-02"):
			frappe.db.set_value("NC Technical Service", code, "specialty", spec)
		frappe.db.set_value("NC Technical Service", "GTC-DV-03", {"specialty": spec, "is_active": 0})

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _download(self, **kw):
		from normcore.api import benchmark as api

		api.download_price_survey(FACILITY, CATEGORY, **kw)
		return frappe.response["filename"], frappe.response["filecontent"]

	def test_FR_BM_008_phieu_khao_sat(self):
		from openpyxl import load_workbook

		name, content = self._download(specialty=self.spec)
		self.assertTrue(name.endswith(".xlsx"))
		ws = load_workbook(io.BytesIO(content)).worksheets[0]
		header = [c.value for c in ws[1]]
		self.assertEqual(header, head())
		rows = [[c.value for c in r] for r in ws.iter_rows(min_row=2)]
		# chỉ dịch vụ đang dùng của chuyên khoa (DV-03 không hoạt động bị bỏ)
		codes = [r[1] for r in rows if r[1] in SERVICES]
		self.assertEqual(codes, ["GTC-DV-01", "GTC-DV-02"])
		# điền giá, ngày, nguồn rồi nhập lại bằng bộ nhập
		wb = load_workbook(io.BytesIO(content))
		sheet = wb.worksheets[0]
		for r in range(2, sheet.max_row + 1):
			if sheet.cell(r, 2).value in SERVICES:
				sheet.cell(r, 4, 30000)
				sheet.cell(r, 6, "2026-03-01")
				sheet.cell(r, 7, "KS-01")
			else:
				sheet.delete_rows(r)
		buf = io.BytesIO()
		wb.save(buf)
		res = importer_api.run_import(KEY, buf.getvalue(), "ghi")
		self.assertEqual((res["created"], res["errors"]), (2, []))
		# theo danh sách mã
		_name, content = self._download(services=["GTC-DV-04", "GTC-DV-05"])
		ws = load_workbook(io.BytesIO(content)).worksheets[0]
		self.assertEqual([r[1].value for r in ws.iter_rows(min_row=2)], ["GTC-DV-04", "GTC-DV-05"])

	def test_FR_BM_008_nhom_dich_vu_trong(self):
		from normcore.api import benchmark as api

		frappe.db.set_value("NC Technical Service", "GTC-DV-01", "is_active", 0)
		frappe.db.set_value("NC Technical Service", "GTC-DV-02", "is_active", 0)
		self.assertRaises(
			frappe.ValidationError, api.download_price_survey, FACILITY, CATEGORY, specialty=self.spec
		)
		self.assertRaises(frappe.ValidationError, api.download_price_survey, FACILITY, CATEGORY)

	def test_quyen_feat_026_phieu(self):
		from normcore.api import benchmark as api

		clin = make_user("bmsv.cl@normcore.test", "NC Clinician")
		aud = make_user("bmsv.aud@normcore.test", "NC Auditor")
		for user in (clin, aud):
			frappe.set_user(user)
			self.assertRaises(
				frappe.PermissionError, api.download_price_survey, FACILITY, CATEGORY, specialty=self.spec
			)
