"""NORM-65 (ASM-046): bộ khớp giá trị Data cũ của NC Procedure Citation sang tên bản ghi Link."""

from normcore.procedure.citation_link import LEGACY_PREFIX, convert_row, match_document, match_section

DOCS = {"LD-00001": "43/2013/TT-BYT", "LD-00002": "15/2023/QH15"}
SECS = {"LS-0000001": ("LD-00001", "5"), "LS-0000002": ("LD-00001", "6"), "LS-0000003": ("LD-00002", "7")}


class TestMatchDocument:
	def test_ten_ban_ghi(self):
		assert match_document("LD-00002", DOCS) == "LD-00002"

	def test_so_hieu_chuan_hoa(self):
		assert match_document("43 / 2013 / tt-byt", DOCS) == "LD-00001"

	def test_so_hieu_nam_trong_gia_tri(self):
		assert match_document("Thông tư 43/2013/TT-BYT", DOCS) == "LD-00001"

	def test_khong_khop_hoac_mo_ho(self):
		assert match_document("Thông tư 99/2020/TT-BYT", DOCS) is None
		assert match_document("", DOCS) is None
		assert match_document("43/2013/TT-BYT và 15/2023/QH15", DOCS) is None  # chứa hai số hiệu: mơ hồ


class TestMatchSection:
	def test_ten_ban_ghi_lay_van_ban_tu_muc(self):
		assert match_section("LS-0000003", None, SECS) == ("LS-0000003", "LD-00002")

	def test_ma_muc_chuan_hoa_trong_van_ban(self):
		assert match_section("Điều 5", "LD-00001", SECS) == ("LS-0000001", "LD-00001")
		assert match_section("6", "LD-00001", SECS) == ("LS-0000002", "LD-00001")

	def test_ma_muc_cua_van_ban_khac_khong_khop(self):
		assert match_section("Điều 7", "LD-00001", SECS) == (None, None)

	def test_khong_co_van_ban_thi_khong_khop_theo_ma(self):
		assert match_section("Điều 5", None, SECS) == (None, None)


class TestConvertRow:
	def test_khop_ca_hai(self):
		assert convert_row("Thông tư 43/2013/TT-BYT", "Điều 5", "q", DOCS, SECS) == (
			"LD-00001",
			"LS-0000001",
			"q",
		)

	def test_chi_van_ban(self):
		assert convert_row("43/2013/TT-BYT", "", "q", DOCS, SECS) == ("LD-00001", None, "q")

	def test_da_la_ten_thi_giu_nguyen_chay_lai(self):
		assert convert_row("LD-00001", "LS-0000001", "q", DOCS, SECS) == ("LD-00001", "LS-0000001", "q")

	def test_khong_khop_van_ban_ghi_vao_quote_va_de_trong(self):
		d, s, q = convert_row("Thông tư 99/2020/TT-BYT", "Điều 5", "đoạn trích", DOCS, SECS)
		assert (d, s) == (None, None)
		assert q == f"{LEGACY_PREFIX}Thông tư 99/2020/TT-BYT — Điều 5] đoạn trích"

	def test_khop_van_ban_khong_khop_muc_giu_link_van_ban(self):
		d, s, q = convert_row("43/2013/TT-BYT", "Phụ lục A", None, DOCS, SECS)
		assert (d, s) == ("LD-00001", None)
		assert q == f"{LEGACY_PREFIX}Phụ lục A]"

	def test_quote_trong_thi_chi_co_ghi_chu(self):
		assert convert_row("x", None, "", DOCS, SECS)[2] == f"{LEGACY_PREFIX}x]"

	def test_khong_co_gi_thi_khong_doi(self):
		assert convert_row(None, "", "q", DOCS, SECS) == (None, None, "q")
