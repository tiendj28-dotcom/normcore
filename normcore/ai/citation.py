"""Kiểm trích dẫn do AI trả về (FR-AI-005, DI-08). Module thuần, không phụ thuộc framework."""
import unicodedata
from collections import namedtuple

REL_FOLLOW = "Theo hướng dẫn"
REL_DEVIATION = "Khác biệt"
REL_NONE = "Chưa có căn cứ"

CheckResult = namedtuple("CheckResult", ["kept", "rejected"])


def normalize(text):
    """NFC, dấu câu → khoảng trắng, gộp khoảng trắng. Giữ hoa/thường và dấu tiếng Việt."""
    text = unicodedata.normalize("NFC", text or "")
    text = "".join(" " if unicodedata.category(c).startswith("P") else c for c in text)
    return " ".join(text.split())


def quote_in_text(quote, text):
    q = normalize(quote)
    if not q:
        return False
    return f" {q} " in f" {normalize(text)} "


def check_citations(items, sources):
    by_name = {s.get("name"): s.get("plain_text") or "" for s in sources or []}
    kept, rejected = [], []
    for item in items or []:
        if not normalize(item.get("quote")):
            rejected.append((item, "missing_quote"))
        elif item.get("section") not in by_name:
            rejected.append((item, "unknown_section"))
        elif not quote_in_text(item["quote"], by_name[item["section"]]):
            rejected.append((item, "not_verbatim"))
        else:
            kept.append(item)
    return CheckResult(kept, rejected)


def label_unsupported(targets, kept):
    covered = {k.get("target") for k in kept or []}
    return [{"target": t, "relation": REL_NONE} for t in targets if t not in covered]
