"""Rà soát quy trình khi văn bản hết hiệu lực (FR-LIB-009): hàm thuần."""

from datetime import date

from normcore.procedure import review as r

SECS = [("LS-1", "LD-1"), ("LS-2", "LD-1"), ("LS-3", "LD-2")]


def idx():
	return r.build_index(SECS)


def test_resolve_theo_link_muc_va_van_ban():
	i = idx()
	assert r.resolve({"legal_section": "LS-2"}, i) == ("LD-1", "LS-2")
	# mục quyết định văn bản, bỏ qua legal_document lệch
	assert r.resolve({"legal_document": "LD-9", "legal_section": "LS-3"}, i) == ("LD-2", "LS-3")
	assert r.resolve({"legal_document": "LD-1", "legal_section": ""}, i) == ("LD-1", None)
	# mục ngoài chỉ mục liên quan: rơi về cấp văn bản nếu có
	assert r.resolve({"legal_document": "LD-7", "legal_section": "LS-X"}, i) == ("LD-7", None)
	# không có Link nào (trích dẫn cũ không chuyển được)
	assert r.resolve({"legal_document": "", "legal_section": ""}, i) is None
	assert r.resolve({"legal_section": "LS-X"}, i) is None
	assert r.resolve({}, i) is None


def test_affected_ly_do():
	i = idx()
	cites = [
		{"legal_document": "LD-1", "legal_section": "LS-1"},
		{"legal_document": "LD-1", "legal_section": "LS-2"},
		{"legal_document": "LD-2"},
		{"legal_document": "", "legal_section": ""},
	]
	out = r.affected(cites, i, {"LD-2"}, {"LS-1"})
	assert [(o["legal_document_name"], o["legal_section_name"], o["reason"]) for o in out] == [
		("LD-1", "LS-1", r.REASON_SECTION),
		("LD-2", None, r.REASON_DOC),
	]
	assert r.affected([{"legal_document": "LD-1", "legal_section": "LS-1"}], i, set(), set()) == []
	# văn bản hết: mục thuộc văn bản đó cũng bị ảnh hưởng, lý do là văn bản
	out = r.affected([{"legal_document": "LD-1", "legal_section": "LS-1"}], i, {"LD-1"}, set())
	assert out[0]["reason"] == r.REASON_DOC


def test_to_flag_chi_da_ban_hanh():
	i = idx()
	c = [{"legal_document": "LD-1", "legal_section": "LS-1"}]
	procs = [
		{"name": "P1", "workflow_state": "Đã ban hành", "citations": c},
		{"name": "P2", "workflow_state": "Nháp", "citations": c},
		{
			"name": "P3",
			"workflow_state": "Đã ban hành",
			"citations": [{"legal_document": "LD-1", "legal_section": "LS-2"}],
		},
		{"name": "P4", "workflow_state": "Đã ban hành"},
	]
	out = r.to_flag(procs, i, set(), {"LS-1"})
	assert [n for n, _ in out] == ["P1"]


def test_notify_subject():
	refs = [
		{
			"doc_number": "123/QĐ",
			"section_no": "2",
			"legal_section_name": "LS-1",
			"legal_document_name": "LD-1",
		},
		{
			"doc_number": "123/QĐ",
			"section_no": "2",
			"legal_section_name": "LS-1",
			"legal_document_name": "LD-1",
		},
		{"legal_document_name": "LD-2", "legal_document": "9/TT", "legal_section_name": None},
	]
	s = r.notify_subject("QT-1", refs, date(2026, 7, 1))
	assert s == "Cần rà soát quy trình QT-1: 123/QĐ mục 2; LD-2 hết hiệu lực từ 01/07/2026"
	assert r.notify_subject("QT-1", [{"legal_document": "9/TT"}], "2026-07-01").endswith("2026-07-01")
	assert r.notify_subject("QT-1", [{"legal_document": "9/TT"}], date(2026, 7, 1)).startswith(
		"Cần rà soát quy trình QT-1: 9/TT"
	)


def test_dismiss_errors():
	assert r.dismiss_errors("Đã ban hành", 1, "lý do") == []
	assert r.dismiss_errors("Nháp", 0, "  ") == [
		"Chỉ rà soát quy trình đã ban hành",
		"Quy trình không có cờ Cần rà soát",
		"Cần nhập lý do không cần sửa",
	]
