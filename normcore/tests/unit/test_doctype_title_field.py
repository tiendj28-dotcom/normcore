"""NORM-87: title_field của DocType phải là trường thật (không phải "name"),
nếu không ListView Desk lỗi `reading 'fieldname'` và danh sách trống."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FILES = sorted(ROOT.glob("nc_*/doctype/*/*.json"))


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.parent.name)
def test_title_field_la_truong_that(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    title = data.get("title_field")
    if not title:
        return
    names = {f["fieldname"] for f in data.get("fields", [])}
    assert title in names, f"{path.parent.name}: title_field {title!r} không phải trường"
