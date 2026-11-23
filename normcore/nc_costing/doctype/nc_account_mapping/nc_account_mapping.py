import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import accounting


class NCAccountMapping(Document):
	def validate(self):
		# FR-ACCT-009, ASM-120: tiền tố chuẩn hóa, duy nhất theo (chế độ, tiền tố)
		self.account_prefix = accounting.normalize_account(self.account_prefix)
		if not self.account_prefix:
			frappe.throw(_("Tiền tố tài khoản không được để trống"))
		dup = frappe.db.exists(
			"NC Account Mapping",
			{
				"accounting_regime": self.accounting_regime,
				"account_prefix": self.account_prefix,
				"name": ("!=", self.name),
			},
		)
		if dup:
			frappe.throw(
				_("Tiền tố {0} của chế độ {1} đã có").format(self.account_prefix, self.accounting_regime)
			)


def on_doctype_update():
	frappe.db.add_unique("NC Account Mapping", ["accounting_regime", "account_prefix"])


def mapping_for(regime) -> dict:
	"""{tiền tố: loại chi phí} của một chế độ kế toán."""
	rows = frappe.get_all(
		"NC Account Mapping", {"accounting_regime": regime}, ["account_prefix", "cost_category"]
	)
	return {r.account_prefix: r.cost_category for r in rows}
