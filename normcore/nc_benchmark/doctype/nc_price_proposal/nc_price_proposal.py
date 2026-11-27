import frappe
from frappe import _
from frappe.model.document import Document

from normcore.benchmark import proposal

RUN = "NC Costing Run"
LOCKED = "Đã khóa"
_DATA_FIELDS = ("title", "apply_from", "price_category", "costing_run")
_ITEM_FIELDS = (
	"technical_service",
	"department",
	"full_cost",
	"calculated_price",
	"rounded_price",
	"benchmark_median",
	"benchmark_count",
	"proposed_price",
	"adjustment_basis",
	"below_cost",
	"director_ack",
	"authority_price",
)


def _snapshot(doc):
	rows = [tuple(str(r.get(f) if r.get(f) is not None else "") for f in _ITEM_FIELDS) for r in doc.items or []]
	return tuple(str(doc.get(f) or "") for f in _DATA_FIELDS), tuple(rows)


class NCPriceProposal(Document):
	"""Phương án giá (FR-PRICE-001..010). Trạng thái và nội dung đổi qua api.price_proposal (flags.proposal_action)."""

	def before_insert(self):
		self.check_run()

	def validate(self):
		if not self.workflow_state:
			self.workflow_state = proposal.DRAFT
		if self.is_new() and self.workflow_state != proposal.DRAFT:
			frappe.throw(_("Phương án mới phải ở trạng thái Nháp"))
		self.check_state_transition()
		self.check_content_lock()
		if self.is_new() or not self.price_category:
			self.check_run()
		self.mark_below_cost()

	def check_run(self):
		status, category = frappe.db.get_value(RUN, self.costing_run, ["status", "price_category"])
		if status != LOCKED:
			frappe.throw(_("Chỉ lập phương án từ lần tính giá đã khóa"))
		self.price_category = category  # ASM-030-02

	def check_state_transition(self):
		prev = self.get_doc_before_save()
		before = prev.workflow_state if prev else proposal.DRAFT
		if self.workflow_state != before and not self.flags.proposal_action:
			frappe.throw(_("Chỉ đổi trạng thái bằng các nút của luồng duyệt"))

	def mark_below_cost(self):
		for row in self.items or []:
			if row.proposed_price is None or row.proposed_price <= 0:
				frappe.throw(_("Dòng {0}: giá đề xuất phải lớn hơn 0").format(row.technical_service))
			row.below_cost = 1 if proposal.is_below_cost(row.proposed_price, row.full_cost) else 0

	def check_content_lock(self):
		"""DI-07: ngoài "Nháp" không sửa nội dung (trừ API)."""
		prev = self.get_doc_before_save()
		if not prev or prev.workflow_state == proposal.DRAFT or self.flags.proposal_action:
			return
		if _snapshot(prev) != _snapshot(self):
			frappe.throw(
				_("Phương án đang duyệt hoặc đã duyệt, không sửa được"), title=_("Bản ghi đã khóa")
			)

	def on_trash(self):
		if self.workflow_state != proposal.DRAFT:  # DI-07
			frappe.throw(_("Chỉ xóa được phương án ở trạng thái Nháp."), title=_("Bản ghi đã khóa"))
