import unittest

from normcore.procedure import ai_draft as d

SRC = [{"name": "LS-1", "doc_number": "12/QĐ", "plain_text": "Nhịn ăn 6 giờ. Đặt đường truyền."}]


def cit(q, rel="Theo hướng dẫn", **kw):
	return dict({"section": "LS-1", "quote": q, "relation": rel}, **kw)


def raw(n=5, bad_step=None):
	steps = []
	for i in range(n):
		q = "Nhịn ăn 6 giờ" if i != bad_step else "không có trong nguồn"
		steps.append(
			{
				"phase": "Thực hiện",
				"step_title": f"B{i}",
				"description": f"mô tả {i}",
				"reference_minutes": 5,
				"resources": [
					{"resource_type": "Vật tư", "resource_text": "bơm tiêm", "quantity": 2, "uom": "cái"}
				],
				"citations": [cit(q)],
			}
		)
	secs = {k: {"text": f"<b>{k}</b>\nhai", "citations": [cit("Đặt đường truyền")]} for k in d.SECTION_KEYS}
	return {"sections": secs, "steps": steps}


def test_parse_va_build_5_buoc():
	r = d.build_rows(d.parse_draft(raw()), SRC, "yc")
	assert len(r.steps) == 5 and r.rejected == 0
	assert all(rows[0]["relation"] == "Theo hướng dẫn" for rows in r.citations.values())
	assert r.sections["overview"].startswith("<p>&lt;b&gt;")
	assert r.steps[0]["ai_suggested"] == 1 and r.resources[0][0]["ai_suggested"] == 1
	assert r.citations[("step", 0)][0]["legal_document"] == "12/QĐ"


def test_TC_AI_02_build_rows_mot_trich_dan_sai():
	r = d.build_rows(d.parse_draft(raw(bad_step=1)), SRC, "yc")
	assert r.rejected == 1 and r.rejected_reasons == {"not_verbatim": 1}
	assert [c["relation"] for c in r.citations[("step", 1)]] == ["Chưa có căn cứ"]
	assert r.citations[("step", 0)][0]["relation"] == "Theo hướng dẫn"


def test_khong_nguon_moi_muc_chua_co_can_cu():
	r = d.build_rows(d.parse_draft(raw()), [], "yc")
	assert all([c["relation"] for c in rows] == ["Chưa có căn cứ"] for rows in r.citations.values())
	assert len(r.citations) == 7 + 5


def test_khac_biet_ly_do():
	data = raw()
	data["steps"][2]["citations"] = [cit("Nhịn ăn 6 giờ", "Khác biệt", request_excerpt="dùng máy cầm tay")]
	r = d.build_rows(d.parse_draft(data), SRC, "Khoa dùng máy cầm tay thay máy giường")
	c = r.citations[("step", 2)][0]
	assert c["relation"] == "Khác biệt" and c["deviation_reason"] == "dùng máy cầm tay"
	data["steps"][2]["citations"][0]["request_excerpt"] = "không có"
	r = d.build_rows(d.parse_draft(data), SRC, "Khoa dùng máy cầm tay")
	assert r.citations[("step", 2)][0]["deviation_reason"] == "Khoa dùng máy cầm tay"


def test_parse_loi_cau_truc():
	for bad in ("x", {}, {"sections": {}, "steps": []}, {"sections": {}, "steps": [{"step_title": "a"}]}):
		with unittest.TestCase().assertRaises(d.DraftError):
			d.parse_draft(bad)


def test_parse_sua_gia_tri_lech():
	data = raw(1)
	data["steps"][0]["phase"] = "Lạ"
	data["steps"][0]["reference_minutes"] = -1
	data["steps"][0]["resources"] = [
		{"resource_type": "Lạ", "quantity": 1, "resource_text": "x", "uom": "cái"},
		{"resource_type": "Vật tư", "quantity": 1, "resource_text": "", "uom": "cái"},
		{"resource_type": "Vật tư", "quantity": 0, "resource_text": "x", "uom": "cái"},
		{"resource_type": "Nhân lực", "quantity": 10, "uom": "giờ", "headcount": 2, "resource_text": "BS"},
		"rác",
	]
	data["sections"] = {"overview": "rác"}
	dr = d.parse_draft(data)
	st = dr.steps[0]
	assert st["phase"] == "Thực hiện" and st["reference_minutes"] is None
	assert [r["resource_type"] for r in st["resources"]] == ["Khác", "Nhân lực"]
	assert st["resources"][1]["uom"] == "phút" and st["resources"][1]["headcount"] == 2
	assert len(dr.warnings) == 4
	assert dr.sections["overview"]["text"] == ""


def test_request_variables_va_html_rong():
	v = d.request_variables("yc", {"service_code": "X", "service_name": "Y", "extra": 1}, None)
	assert set(v) == {
		"doctor_request",
		"service",
		"current_procedure",
		"phases",
		"resource_types",
		"section_keys",
	}
	assert "extra" not in v["service"]
	assert d._html("") == ""
