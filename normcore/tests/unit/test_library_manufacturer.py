"""FEAT-038: hàm thuần kiểm bảng mặt hàng, thiết bị của tài liệu của hãng (FR-LIB-013)."""

from normcore.library import manufacturer as m

MFR = "Tài liệu của hãng"


def test_FR_LIB_013_loai_hang_bang_trong_bi_tu_choi():
	assert m.resource_link_errors(MFR, []) == [
		"Tài liệu của hãng phải gắn ít nhất một mặt hàng hoặc thiết bị"
	]
	assert m.resource_link_errors(MFR, None)


def test_FR_LIB_013_loai_khac_giu_bang_khong_loi():
	assert m.resource_link_errors("Thông tư", []) == []
	assert m.resource_link_errors("Thông tư", [{"linked_doctype": "NC Room", "linked_name": "X"}]) == []


def test_FR_LIB_013_loai_danh_muc_va_trung():
	ok = [{"idx": 1, "linked_doctype": "NC Item", "linked_name": "HC_GLU"}]
	assert m.resource_link_errors(MFR, ok) == []
	bad = [*ok, {"idx": 2, "linked_doctype": "NC Room", "linked_name": "P1"}]
	assert m.resource_link_errors(MFR, bad) == ["Dòng 2: Chỉ gắn được mặt hàng hoặc thiết bị"]
	dup = [
		*ok,
		{"idx": 2, "linked_doctype": "NC Equipment", "linked_name": "EQ_A"},
		{"idx": 3, "linked_doctype": "NC Item", "linked_name": "HC_GLU"},
	]
	assert m.resource_link_errors(MFR, dup) == ["Dòng 3 trùng với dòng 1"]
