"""FEAT-030 T02: ScopeRule.child và _doc_departments của core/permissions.py (cần frappe, chạy trong bench)."""

from unittest import TestCase, mock

from normcore.core import permissions as perm


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


class TestScopeChild(TestCase):
	def test_scope_rule_mac_dinh_khong_co_child(self):
		self.assertIsNone(perm.ScopeRule().child)
		self.assertEqual(
			perm.SCOPE_RULES["NC Price Proposal"].child, ("NC Price Proposal Item", "department")
		)
		self.assertIsNone(perm.SCOPE_RULES["NC Service Cost"].child)

	def test_doc_departments_tu_dong_con(self):
		rule = perm.SCOPE_RULES["NC Price Proposal"]
		items = [{"department": "K1"}, {"department": "K2"}, {"department": "K1"}, {"department": None}]
		with mock.patch.object(perm.frappe, "get_meta", lambda dt: _Meta()):
			doc = _Doc(doctype="NC Price Proposal", items=items)
			self.assertEqual(perm._doc_departments(rule, doc), {"K1", "K2"})
			self.assertEqual(perm._doc_departments(rule, _Doc(doctype="NC Price Proposal", items=[])), set())
