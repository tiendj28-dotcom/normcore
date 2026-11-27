"""FEAT-038: phần thuần của AI đề xuất định mức từ tài liệu của hãng (FR-AI-016..018; TC-CLS-42, TC-CLS-43)."""

import pytest

from normcore.ai import guard
from normcore.norm import ai_cls_norm as m

QUOTE = "Mỗi test glucose dùng 0,02 ml thuốc thử"
SOURCES = [
	{
		"name": "LS-1",
		"section_no": "1",
		"heading": "TH",
		"plain_text": f"1. Thuốc thử. {QUOTE}. Hạn 28 ngày.",
	},
	{"name": "LS-2", "section_no": "2", "heading": "CM", "plain_text": "Chuẩn máy mỗi 90 ngày."},
]
CATALOG = {"HC_GLU": "NC Item", "EQ_A": "NC Equipment"}


def _sug(**kw):
	base = {
		"suggestion_type": "REAGENT_PER_TEST",
		"item_code": "HC_GLU",
		"item_text": "Thuốc thử glucose",
		"value": 0.02,
		"uom": "ml",
		"citations": [{"section": "LS-1", "quote": QUOTE}],
	}
	base.update(kw)
	return base


def test_FR_AI_016_pham_vi_tai_lieu():
	keys = m.system_resources(
		"EQ_A",
		[
			{"resource_doctype": "NC Item", "resource": "HC_GLU"},
			{"resource_doctype": "NC Room", "resource": "P1"},
			{"resource_doctype": "NC Item", "resource": None},
		],
		[{"qc_material": "QC_L"}],
		[{"calibrator": "CAL"}],
	)
	assert keys == {("NC Equipment", "EQ_A"), ("NC Item", "HC_GLU"), ("NC Item", "QC_L"), ("NC Item", "CAL")}
	assert m.system_resources(None, None, None, None) == set()

	def doc(name, **kw):
		d = {
			"name": name,
			"doc_type": "Tài liệu của hãng",
			"validity_status": "Còn hiệu lực",
			"index_status": "Đã lập",
			"related_resources": [{"linked_doctype": "NC Item", "linked_name": "HC_GLU"}],
		}
		d.update(kw)
		return d

	docs = [
		doc("LD-B"),
		doc("LD-A"),
		doc("LD-HET", validity_status="Hết hiệu lực"),
		doc("LD-CHUA", index_status="Chưa lập"),
		doc("LD-NGOAI", related_resources=[{"linked_doctype": "NC Item", "linked_name": "KHAC"}]),
		doc("LD-TT", doc_type="Thông tư"),
		doc("LD-TRONG", related_resources=[]),
		doc("LD-TB", related_resources=[{"linked_doctype": "NC Equipment", "linked_name": "EQ_A"}]),
	]
	assert m.docs_in_scope(docs, keys) == ["LD-A", "LD-B", "LD-TB"]
	# guard: chỉ mục của tài liệu trong phạm vi, và chỉ bốn khóa
	secs = [
		{
			"legal_document": "LD-A",
			"name": "S1",
			"section_no": "1",
			"heading": "h",
			"plain_text": "t",
			"x": 1,
		},
		{"legal_document": "LD-KHAC", "name": "S2", "section_no": "1", "heading": "h", "plain_text": "t"},
	]
	out = guard.manufacturer_sections(secs, ["LD-A"])
	assert out == [{"name": "S1", "section_no": "1", "heading": "h", "plain_text": "t"}]
	assert guard.manufacturer_sections(secs, []) == []
	vars_ = m.request_variables({"service_code": "GLU"}, None, [{"item_code": "HC_GLU"}], [])
	assert set(vars_) == {"service", "procedure", "items", "equipment"}


def test_TC_CLS_42_phan_loai_trich_dan():
	data = {
		"suggestions": [
			_sug(),
			_sug(
				suggestion_type="OPEN_STABILITY",
				value=28,
				uom="ngày",
				citations=[{"section": "LS-1", "quote": "Hạn 28 ngày"}],
			),
			_sug(
				item_code="EQ_A",
				suggestion_type="CALIBRATION_FREQ",
				value=4,
				citations=[{"section": "LS-1", "quote": "không có trong tài liệu"}],
			),
		]
	}
	rows, rejected = m.parse_suggestions(data, SOURCES, CATALOG)
	assert len(rows) == 3
	assert [r["relation"] for r in rows] == ["Theo hướng dẫn", "Theo hướng dẫn", "Chưa có căn cứ"]
	assert rows[0]["legal_section"] == "LS-1" and rows[0]["quote"] == QUOTE
	assert rows[2]["legal_section"] is None and rows[2]["quote"] is None
	assert rejected == 1
	assert rows[0]["suggestion_type"] == "Lượng hóa chất mỗi test"
	# trích dẫn rỗng, mục lạ
	rows, rejected = m.parse_suggestions(
		{"suggestions": [_sug(citations=[]), _sug(citations=[{"section": "LS-9", "quote": QUOTE}])]},
		SOURCES,
		CATALOG,
	)
	assert [r["relation"] for r in rows] == ["Chưa có căn cứ"] * 2 and rejected == 1
	# nhiều trích dẫn: lấy trích dẫn đúng đầu tiên
	rows, _ = m.parse_suggestions(
		{
			"suggestions": [
				_sug(
					citations=[
						{"section": "LS-1", "quote": "sai"},
						{"section": "LS-2", "quote": "Chuẩn máy mỗi 90 ngày"},
					]
				)
			]
		},
		SOURCES,
		CATALOG,
	)
	assert rows[0]["legal_section"] == "LS-2"


def test_TC_CLS_42_cau_truc_sai_va_dau_ra_rong():
	bad = [
		"x",
		_sug(suggestion_type="KHAC"),
		_sug(value=0),
		_sug(value=-1),
		_sug(value="0,02"),
		_sug(value=True),
		_sug(value=float("inf")),
	]
	rows, rejected = m.parse_suggestions({"suggestions": bad}, SOURCES, CATALOG)
	assert rows == [] and rejected == len(bad)
	assert m.parse_suggestions({"mock": True}, SOURCES, CATALOG) == ([], 0)
	assert m.parse_suggestions({"suggestions": "x"}, SOURCES, CATALOG) == ([], 1)
	assert m.parse_suggestions(None, SOURCES, CATALOG) == ([], 0)
	rows, _ = m.parse_suggestions({"suggestions": [_sug(uom="", citations="x")]}, SOURCES, CATALOG)
	assert rows[0]["uom"] is None and rows[0]["relation"] == "Chưa có căn cứ"


def test_TC_CLS_43_ma_ngoai_danh_muc():
	rows, rejected = m.parse_suggestions(
		{
			"suggestions": [
				_sug(item_code="HC_KHONG_CO", item_text="Hóa chất X"),
				_sug(item_code=None, item_text=None),
			]
		},
		SOURCES,
		CATALOG,
	)
	assert rejected == 0
	r = rows[0]
	assert (r["not_in_catalog"], r["resource"], r["resource_doctype"], r["resource_text"]) == (
		1,
		None,
		None,
		"Hóa chất X",
	)
	assert rows[1]["not_in_catalog"] == 1 and rows[1]["resource_text"] == "—"
	rows, _ = m.parse_suggestions({"suggestions": [_sug(item_code="HC_GLU", item_text="")]}, SOURCES, CATALOG)
	assert (
		rows[0]["not_in_catalog"],
		rows[0]["resource"],
		rows[0]["resource_doctype"],
		rows[0]["resource_text"],
	) == (
		0,
		"HC_GLU",
		"NC Item",
		"HC_GLU",
	)
	rows, _ = m.parse_suggestions({"suggestions": [_sug(item_code="EQ_A")]}, SOURCES, CATALOG)
	assert rows[0]["resource_doctype"] == "NC Equipment"


def _s(kind, **kw):
	base = {
		"test_system": "GLU-A",
		"suggestion_type": m.TYPE_LABELS[kind],
		"resource_doctype": "NC Item",
		"resource": "HC_GLU",
		"not_in_catalog": 0,
		"value": 0.02,
	}
	base.update(kw)
	return base


def test_FR_AI_016_plan_accept():
	lines = [{"line_id": "L1", "resource_doctype": "NC Item", "resource": "HC_GLU", "cost_level": "RESULT"}]
	assert m.plan_accept(_s("REAGENT_PER_TEST"), lines, None, None) == {
		"target": "norm_line",
		"line_id": "L1",
		"value": 0.02,
	}
	assert m.plan_accept(_s("REAGENT_PER_TEST"), [], None, None)["line_id"] is None
	# dòng khác cấp, dòng loại trừ không khớp
	other = [
		{"line_id": "L2", "resource_doctype": "NC Item", "resource": "HC_GLU", "cost_level": "TUBE"},
		{"line_id": "L3", "resource_doctype": "NC Item", "resource": "HC_GLU", "is_excluded": 1},
	]
	assert m.plan_accept(_s("REAGENT_PER_TEST"), other, None, None)["line_id"] is None
	assert "2 dòng cùng hóa chất" in m.plan_accept(_s("REAGENT_PER_TEST"), lines * 2, None, None)["error"]
	assert (
		"Chưa có bộ định mức Nháp cho hệ thống GLU-A"
		in m.plan_accept(_s("REAGENT_PER_TEST"), None, None, None)["error"]
	)
	assert (
		"chỉ áp cho hóa chất"
		in m.plan_accept(_s("REAGENT_PER_TEST", resource_doctype="NC Equipment"), [], None, None)["error"]
	)
	# ngoài danh mục
	assert (
		"Liên kết mặt hàng"
		in m.plan_accept(_s("REAGENT_PER_TEST", not_in_catalog=1, resource=None), lines, None, None)["error"]
	)
	# chuẩn máy, nội kiểm
	cal = [{"name": "r1", "calibrator": "CAL"}]
	assert m.plan_accept(_s("CALIBRATION_FREQ", resource="CAL", value=4), None, [], cal) == {
		"target": "calibration",
		"row": "r1",
		"value": 4,
	}
	assert (
		"dòng chuẩn máy cho CAL"
		in m.plan_accept(_s("CALIBRATION_FREQ", resource="CAL"), None, None, None)["error"]
	)
	iqc = [{"idx": 2, "qc_material": "QC_L"}]
	assert m.plan_accept(_s("IQC_FREQ", resource="QC_L", value=2), None, iqc, []) == {
		"target": "iqc",
		"row": 2,
		"value": 2,
	}
	assert "dòng nội kiểm cho QC_L" in m.plan_accept(_s("IQC_FREQ", resource="QC_L"), None, [], [])["error"]
	# hạn dùng sau mở: làm tròn
	assert m.plan_accept(_s("OPEN_STABILITY", value=27.6), None, None, None) == {
		"target": "item",
		"value": 28,
	}
	assert (
		"chỉ áp cho mặt hàng"
		in m.plan_accept(_s("OPEN_STABILITY", resource_doctype="NC Equipment"), None, None, None)["error"]
	)
	assert m.plan_accept({"resource": "X", "suggestion_type": "?"}, None, None, None)["error"]


def test_FR_AI_016_basis_ref_va_nhan():
	assert m.basis_ref("HG-1.0", "2") == "HG-1.0 mục 2"
	assert m.basis_ref(None, None) == "AI — Chưa có căn cứ"
	assert list(m.TYPE_LABELS.values()) == list(m.TYPE_ORDER)
	assert m.TYPE_CODE["Hạn dùng sau mở"] == "OPEN_STABILITY"


@pytest.mark.parametrize("src", ["import frappe", "from frappe"])
def test_module_thuan_khong_import_frappe(src):
	import pathlib

	text = pathlib.Path(m.__file__).read_text(encoding="utf-8")
	assert src not in text
