"""FEAT-030 T02: sổ phạm vi khoa đọc khóa `child` (ASM-030-06), thuần, không cần frappe. Phần `core/permissions.py` ở normcore/core/test_scope_child.py."""

import json

from normcore.core import scope_registry as reg


def test_doc_dang_child_doc_tu_tep():
	rules = reg.load_scope_rules()
	assert rules["NC Price Proposal"]["child"] == ("NC Price Proposal Item", "department")
	assert "child" not in rules["NC Service Cost"]
	assert "child" not in rules["NC Clinical Procedure"]


def test_child_trong_tep_tam(tmp_path):
	(tmp_path / "nc_x.json").write_text(
		json.dumps({"doctype": "NC X", "child": ["NC X Item", "khoa"]}), encoding="utf-8"
	)
	assert reg.load_scope_rules(tmp_path)["NC X"]["child"] == ("NC X Item", "khoa")
