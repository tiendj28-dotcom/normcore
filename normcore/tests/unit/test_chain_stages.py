"""Năm mức tình trạng chuỗi (FR-OUT-010, FEAT-002). Không cần site."""

from normcore.procedure import chain


def _flags(service, p=False, n=False, c=False, price=False):
	return (service, p, n, c, price)


def test_FR_OUT_010_du_5_muc_theo_thu_tu():
	assert chain.STAGES == ("no_procedure", "procedure", "norm_locked", "costed", "price_approved")
	got = chain.count_stages([])
	assert [g["stage"] for g in got] == list(chain.STAGES)
	assert all(g["count"] == 0 and g["no_permission"] is False for g in got)
	assert got[0]["label"] == "Chưa có quy trình"


def test_FR_OUT_010_loai_tru_nhau_theo_muc_cao_nhat():
	rows = [
		_flags("S1"),
		_flags("S2", p=True),
		_flags("S3", p=True, n=True),
		_flags("S4", p=True, n=True, c=True),
		_flags("S5", p=True, n=True, c=True, price=True),
	]
	assert [g["count"] for g in chain.count_stages(rows)] == [1, 1, 1, 1, 1]
	assert chain.stage_of(True, True, True, True) == "price_approved"
	assert chain.stage_of(True, True, True) == "costed"
	assert chain.stage_of(True, False, False) == "procedure"
	assert chain.stage_of(False, False, False) == "no_procedure"


def test_FR_OUT_010_co_dinh_muc_khong_co_quy_trinh_la_norm_locked():
	assert chain.stage_of(False, True, False) == "norm_locked"
	assert chain.stage_of(False, False, True) == "costed"


def test_FR_OUT_010_muc_khong_doc_duoc_count_none():
	got = chain.count_stages([_flags("S1", True, True, True)], readable=("no_procedure", "procedure"))
	by = {g["stage"]: g for g in got}
	assert by["norm_locked"]["count"] is None and by["norm_locked"]["no_permission"] is True
	assert by["costed"]["count"] is None
	assert by["procedure"]["count"] == 1  # rơi về mức thấp hơn đọc được


def test_FR_OUT_010_dich_vu_roi_ve_muc_thap_hon():
	got = chain.count_stages([_flags("S1", False, True, True)], readable=("no_procedure", "norm_locked"))
	by = {g["stage"]: g for g in got}
	assert by["norm_locked"]["count"] == 1 and by["no_procedure"]["count"] == 0


def test_FR_OUT_010_price_approved_co_assumption():
	got = {g["stage"]: g for g in chain.count_stages([])}
	assert got["price_approved"]["assumption"] is True
	assert "assumption" not in got["costed"]
