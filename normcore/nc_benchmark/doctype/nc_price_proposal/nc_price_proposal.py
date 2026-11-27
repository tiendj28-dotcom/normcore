import frappe
from frappe import _
from frappe.model.document import Document

from normcore.benchmark import proposal

RUN = "NC Costing Run"
LOCKED = "Đã khóa"
_DATA_FIELDS = ("title", "apply_from", "price_category", "costing_run")
# Trường dòng chỉ máy chủ ghi (read_only trên form): chặn sửa trực tiếp qua REST/`frappe.client.save` (FR-PRICE-002..004)
_SERVER_ITEM_FIELDS = (
	"technical_service",
	"department",
	"full_cost",
	"calculated_price",
	"rounded_price",
	"benchmark_median",
	"benchmark_count",
	"director_ack",
	"authority_price",
)
_COST_FIELDS = ("department", "full_cost", "calculated_price", "rounded_price")
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


def _norm(value):
	"""So sánh giá trị trường dòng: số làm tròn 2 chữ số, chuỗi trống = None."""
	if value in (None, ""):
		return None
	if isinstance(value, (int, float)) or hasattr(value, "as_tuple"):
		return round(float(value), 2)
	return str(value)


def _snapshot(doc):
	rows = [
		tuple(str(r.get(f) if r.get(f) is not None else "") for f in _ITEM_FIELDS) for r in doc.items or []
	]
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
		self.check_run()
		self.check_server_fields()
		self.mark_below_cost()

	def check_run(self):
		status, category = frappe.db.get_value(RUN, self.costing_run, ["status", "price_category"])
		if status != LOCKED:
			frappe.throw(_("Chỉ lập phương án từ lần tính giá đã khóa"))
		self.price_category = category  # ASM-030-02

	def check_server_fields(self):
		"""FR-PRICE-002..004: ở "Nháp", trường dòng chỉ máy chủ ghi không đổi được bằng save trực tiếp (REST,
		`frappe.client.save`). Phương án mới: dòng phải khớp NC Service Cost của lần tính; phương án đã lưu: khớp
		bản đã lưu, không thêm/xóa dòng. API đặt `flags.proposal_action` nên không qua kiểm này."""
		if self.flags.proposal_action:
			return
		prev = self.get_doc_before_save()
		if prev is None:
			self.check_new_rows()
			return
		if prev.workflow_state != proposal.DRAFT:
			return  # đã có check_content_lock
		old = {r.name: r for r in prev.items or []}
		names = {r.name for r in self.items or []}
		if names != set(old):
			frappe.throw(
				_("Không thêm hoặc xóa dòng của phương án giá; dòng do lần tính giá quyết định"),
				title=_("Dòng chỉ đọc"),
			)
		for row in self.items or []:
			before = old[row.name]
			for f in _SERVER_ITEM_FIELDS:
				if _norm(row.get(f)) != _norm(before.get(f)):
					frappe.throw(
						_("Dòng {0}: trường {1} do hệ thống ghi, không sửa trực tiếp").format(
							before.technical_service, _(frappe.get_meta(row.doctype).get_label(f))
						),
						title=_("Dòng chỉ đọc"),
					)

	def check_new_rows(self):
		costs = {
			c.technical_service: c
			for c in frappe.get_all(
				"NC Service Cost",
				{"costing_run": self.costing_run, "calc_status": ["!=", "Lỗi"]},
				["technical_service", *_COST_FIELDS],
			)
		}
		seen = set()
		for row in self.items or []:
			cost = costs.get(row.technical_service)
			if cost is None or row.technical_service in seen:
				frappe.throw(
					_("Dòng {0} không thuộc lần tính giá {1} hoặc bị lặp").format(
						row.technical_service, self.costing_run
					),
					title=_("Dòng chỉ đọc"),
				)
			seen.add(row.technical_service)
			for f in _COST_FIELDS:
				if _norm(row.get(f)) != _norm(cost.get(f)):
					frappe.throw(
						_("Dòng {0}: trường {1} phải bằng kết quả tính giá").format(
							row.technical_service, _(frappe.get_meta(row.doctype).get_label(f))
						),
						title=_("Dòng chỉ đọc"),
					)
			row.director_ack, row.authority_price = 0, None

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
			frappe.throw(_("Phương án đang duyệt hoặc đã duyệt, không sửa được"), title=_("Bản ghi đã khóa"))

	def on_trash(self):
		if self.workflow_state != proposal.DRAFT:  # DI-07
			frappe.throw(_("Chỉ xóa được phương án ở trạng thái Nháp."), title=_("Bản ghi đã khóa"))
