"""FEAT-030 T02: phạm vi khoa theo bảng con (khóa `child`, ASM-030-06). Tương thích ngược với rule cũ."""

import json

from normcore.core import permissions as perm
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


def test_scope_rule_mac_dinh_khong_co_child():
	assert perm.ScopeRule().child is None
	assert perm.SCOPE_RULES["NC Price Proposal"].child == ("NC Price Proposal Item", "department")
	assert perm.SCOPE_RULES["NC Service Cost"].child is None


class _Doc(dict):
	@property
	def doctype(self):
		return self["doctype"]


class _Field:
	def __init__(self, fieldname, options):
		self.fieldname, self.options = fieldname, options


class _Meta:
	def get_table_fields(self):
		return [_Field("confirmations", "NC Khac"), _Field("items", "NC Price Proposal Item")]


def test_doc_departments_tu_dong_con(monkeypatch):
	monkeypatch.setattr(perm.frappe, "get_meta", lambda dt: _Meta())
	rule = perm.SCOPE_RULES["NC Price Proposal"]
	doc = _Doc(doctype="NC Price Proposal", items=[{"department": "K1"}, {"department": "K2"}, {"department": "K1"}, {"department": None}])
	assert perm._doc_departments(rule, doc) == {"K1", "K2"}
	assert perm._doc_departments(rule, _Doc(doctype="NC Price Proposal", items=[])) == set()
