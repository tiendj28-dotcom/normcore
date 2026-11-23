"""Logic thuần của tình trạng chuỗi (FR-SVC-004, FEAT-005). Không cần site."""

from datetime import date

from normcore.procedure import chain

TODAY = date(2026, 11, 22)


def _p(name, dept, v, eff):
	return {"name": name, "department": dept, "version_no": v, "effective_date": eff}


def test_FR_SVC_004_quy_trinh_chon_ban_da_hieu_luc_lon_nhat():
	rows = [
		_p("A1", "K01", 1, "2026-01-01"),
		_p("A2", "K01", 2, "2026-06-01"),
		_p("A3", "K01", 3, "2027-01-01"),
	]
	got = chain.pick_procedures(rows, TODAY)["K01"]
	assert got["name"] == "A2" and not got["not_effective"]


def test_FR_SVC_004_quy_trinh_chi_co_ban_tuong_lai_thi_danh_dau():
	got = chain.pick_procedures(
		[_p("A1", "K01", 1, date(2027, 1, 1)), _p("A2", "K01", 2, "2027-02-01")], TODAY
	)
	assert got["K01"]["name"] == "A2" and got["K01"]["not_effective"] is True


def test_FR_SVC_004_quy_trinh_trong_ngay_hieu_luc_coi_la_da_hieu_luc():
	got = chain.pick_procedures([_p("A1", "K01", 1, None), _p("A2", "K02", 1, "2026-11-22")], TODAY)
	assert not got["K01"]["not_effective"] and not got["K02"]["not_effective"]


def test_FR_SVC_004_quy_trinh_theo_tung_khoa():
	got = chain.pick_procedures([_p("A1", "K01", 1, None), _p("B1", "K02", 4, None)], TODAY)
	assert {k: v["name"] for k, v in got.items()} == {"K01": "A1", "K02": "B1"}
	assert chain.pick_procedures([], TODAY) == {}


def test_FR_SVC_004_dinh_muc_lay_phien_ban_lon_nhat():
	rows = [
		{"name": "N1", "department": "K01", "version_no": 1},
		{"name": "N2", "department": "K01", "version_no": 2},
		{"name": "N3", "department": "K02", "version_no": 1},
	]
	got = chain.pick_norm_sets(rows)
	assert got["K01"]["name"] == "N2" and got["K02"]["name"] == "N3"


def _c(name, dept, status, d, created, **kw):
	return {
		"name": name,
		"department": dept,
		"run_status": status,
		"costing_date": d,
		"run_creation": created,
		"calc_status": kw.get("calc", "Thành công"),
		"based_on_run": kw.get("based"),
	}


def test_FR_SVC_004_gia_thanh_bo_nhap_va_tinh_loi():
	rows = [
		_c("C1", "K01", "Nháp", "2026-11-01", "2026-11-01 08:00"),
		_c("C2", "K01", "Tính lỗi", "2026-11-02", "2026-11-02 08:00"),
		_c("C3", "K01", "Đã tính", "2026-10-01", "2026-10-01 08:00"),
	]
	assert chain.pick_costs(rows)["K01"]["name"] == "C3"


def test_FR_SVC_004_gia_thanh_cung_ngay_lay_lan_tao_sau():
	rows = [
		_c("C1", "K01", "Đã tính", "2026-10-01", "2026-10-01 08:00"),
		_c("C2", "K01", "Đã khóa", "2026-10-01", "2026-10-01 09:00"),
	]
	assert chain.pick_costs(rows)["K01"]["name"] == "C2"


def test_FR_SVC_004_gia_thanh_bo_kich_ban():
	rows = [
		_c("C1", "K01", "Đã tính", "2026-10-01", "2026-10-01 08:00"),
		_c("C2", "K01", "Đã tính", "2026-11-01", "2026-11-01 08:00", based="TG-1"),
	]
	assert chain.pick_costs(rows)["K01"]["name"] == "C1"


def test_FR_SVC_004_gia_thanh_ket_qua_loi_van_duoc_chon():
	got = chain.pick_costs([_c("C1", "K01", "Đã tính", "2026-10-01", "x", calc="Lỗi")])["K01"]
	assert got["calc_status"] == "Lỗi"
	item = chain.build_item("cost", ["K01"], {"K01": got}, None)
	assert {"label": "Lỗi", "indicator": "red"} in item["rows"][0]["badges"]
	assert item["badges"] == [{"label": "Giả định — chờ xác nhận", "indicator": "yellow"}]


def test_FR_SVC_004_build_item_ok_va_lien_ket():
	picked = chain.pick_norm_sets([{"name": "DM-X-K01-v1", "department": "K01", "version_no": 1}])
	item = chain.build_item("norm_set", ["K01", "K02"], picked, None, {"K01": "Khoa 1", "K02": "Khoa 2"})
	assert item["state"] == "ok" and item["key"] == "norm_set"
	assert item["links"] == ["/app/nc-norm-set/DM-X-K01-v1"]
	assert [r["state"] for r in item["rows"]] == ["ok", "empty"]
	assert item["rows"][0]["doctype"] == "NC Norm Set"


def test_FR_ACC_005_khoa_ngoai_pham_vi_khong_lo_thong_tin():
	with_data = chain.pick_norm_sets([{"name": "DM-X-K01-v1", "department": "K01", "version_no": 1}])
	a = chain.build_item("norm_set", ["K01"], with_data, {"K02"}, {"K01": "Khoa 1"})
	b = chain.build_item("norm_set", ["K01"], {}, {"K02"}, {"K01": "Khoa 1"})
	assert a == b  # có hay không có bản ghi đều cho cùng kết quả
	assert a["state"] == "no_permission" and a["links"] == []
	# thiết kế 5.3 điểm 4-5: giữ dòng khoa, chỉ có tên khoa và state
	assert len(a["rows"]) == 1
	row = a["rows"][0]
	assert row["state"] == "no_permission" and row["department_name"] == "Khoa 1"
	for key in ("name", "route", "status", "date", "doctype"):
		assert not row[key], key
	assert row["badges"] == []
	# hai khoa: khoa trong phạm vi vẫn hiện bình thường
	two = chain.build_item("norm_set", ["K01", "K02"], with_data, {"K02"})
	assert [r["state"] for r in two["rows"]] == ["no_permission", "empty"]
	assert two == chain.build_item("norm_set", ["K01", "K02"], {}, {"K02"})


def test_FR_ACC_005_nguoi_bi_hep_chua_gan_khoa():
	item = chain.build_item("norm_set", ["K01"], {}, set())
	assert item["state"] == "no_permission" and item["links"] == []
	assert [r["state"] for r in item["rows"]] == ["no_permission"]
	item = chain.build_item("norm_set", ["K01"], {}, {"K01"})
	assert item["state"] == "empty" and item["message"] == "Chưa có trong phạm vi khoa của bạn"


def test_FR_SVC_004_route_ma_hoa_ky_tu_dac_biet():
	picked = chain.pick_norm_sets([{"name": "DM-A/B #1", "department": "K01", "version_no": 1}])
	item = chain.build_item("norm_set", ["K01"], picked, None)
	assert item["links"] == ["/app/nc-norm-set/DM-A%2FB%20%231"]


def test_FR_SVC_004_muc_khong_quyen_va_muc_gia():
	item = chain.no_permission_item("cost")
	assert item["state"] == "no_permission" and item["message"] == "Không có quyền xem"
	assert item["rows"] == [] and item["links"] == [] and item["badges"] == []
	price = chain.price_item()
	assert price["state"] == "empty" and price["links"] == ["#nc-chain-price"]
	assert price["message"] == "Chưa có giá đã duyệt"


def test_FR_SVC_004_khong_co_truong_tien():
	item = chain.build_item(
		"cost", ["K01"], chain.pick_costs([_c("C1", "K01", "Đã tính", "2026-10-01", "x")]), None
	)
	text = repr(item)
	for k in ("direct_labor", "full_cost", "calculated_price", "rounded_price", "amount"):
		assert k not in text


def test_FR_SVC_004_chain_khong_import_frappe():
	import inspect

	assert "frappe" not in inspect.getsource(chain)
