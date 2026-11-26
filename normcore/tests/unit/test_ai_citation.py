from normcore.ai import citation as c

SRC = [{"name": "LS-1", "plain_text": "Bệnh nhân nhịn ăn 6 giờ,\n trước khi  thực hiện."}]


def item(q, s="LS-1", t="a"):
    return {"target": t, "section": s, "quote": q, "relation": c.REL_FOLLOW}


def test_TC_AI_02_loai_trich_dan_khong_nguyen_van():
    r = c.check_citations([item("nhịn ăn 6 giờ"), item("nhịn ăn 8 giờ", t="b")], SRC)
    assert len(r.kept) == 1 and r.rejected[0][1] == "not_verbatim"
    labels = c.label_unsupported(["a", "b"], r.kept)
    assert labels == [{"target": "b", "relation": c.REL_NONE}]


def test_FR_AI_005_khac_khoang_trang_dau_cau_van_khop():
    assert c.quote_in_text("nhịn ăn 6 giờ trước khi thực hiện", SRC[0]["plain_text"])


def test_FR_AI_005_khac_mot_tu_khong_khop():
    assert not c.quote_in_text("nhịn ăn 6 tiếng", SRC[0]["plain_text"])


def test_FR_AI_005_missing_va_unknown_section():
    r = c.check_citations([item("  "), item("nhịn ăn", s="LS-9")], SRC)
    assert [x[1] for x in r.rejected] == ["missing_quote", "unknown_section"]
    assert c.check_citations(None, None).kept == []


def test_FR_AI_005_ranh_gioi_tu_va_nfc():
    assert not c.quote_in_text("a b", "xa by")
    assert c.quote_in_text("a b", "x a b y")
    nfd = "Việt Nam"
    import unicodedata
    assert c.quote_in_text(unicodedata.normalize("NFD", nfd), nfd)
