import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from normcore.benchmark import reference as ref

DUP_FIELDS = [
	"name",
	"facility",
	"price_category",
	"effective_date",
	"technical_service",
	"service_name_raw",
	"status",
]


class NCBenchmarkPrice(Document):
	"""Giá tham chiếu (FR-BM-002, 004, 007). Logic quyết định nằm ở `normcore/benchmark/reference.py`."""

	def before_insert(self):
		# FR-BM-004, ASM-026-02, 03: đề xuất dịch vụ khớp; trạng thái ban đầu
		user_service = bool(self.technical_service)
		if not user_service and self.service_name_raw:
			services = frappe.get_all(
				"NC Technical Service", filters={"is_active": 1}, fields=["name", "service_name"]
			)
			self.technical_service = ref.suggest_service(self.service_name_raw, services)
		self.status = ref.initial_status(user_service, bool(self.ai_log), bool(self.flags.get("keep_status")))

	def validate(self):
		if not self.technical_service and not self.service_name_raw:
			frappe.throw(_("Cần mã dịch vụ hoặc tên dịch vụ gốc"))
		if not self.service_name_raw:  # ASM-026-04
			self.service_name_raw = frappe.db.get_value(
				"NC Technical Service", self.technical_service, "service_name"
			)
		if not (self.source_doc_no or self.source_url or self.source_file):  # ASM-026-05
			frappe.throw(_("Cần nguồn: số văn bản, đường dẫn hoặc tệp nguồn"))
		if self.price is None or self.price <= 0:
			frappe.throw(_("Giá phải lớn hơn 0"))
		if self.status == ref.STATUS_CONFIRMED and not self.technical_service:
			frappe.throw(_("Chưa gắn mã dịch vụ, chưa xác nhận được"))
		self._check_duplicate()
		self._stamp_verification()

	def _check_duplicate(self):
		"""FR-BM-007, ASM-026-06: trùng đơn vị, dịch vụ, loại giá, ngày hiệu lực."""
		if self.status == ref.STATUS_REJECTED:
			return
		dup = find_saved_duplicate(self.as_dict())
		if dup:
			frappe.throw(
				_("Trùng giá tham chiếu {0}: cùng đơn vị, dịch vụ, loại giá, ngày hiệu lực").format(dup),
				frappe.ValidationError,
			)

	def _stamp_verification(self):
		was = self.get_doc_before_save()
		if self.status != ref.STATUS_CONFIRMED:
			self.verified_by = None
			self.verified_on = None
		elif not was or was.status != ref.STATUS_CONFIRMED:
			self.verified_by = frappe.session.user
			self.verified_on = now_datetime()


def find_saved_duplicate(row):
	"""Tên dòng đã lưu trùng với `row` (dict có facility, price_category, effective_date, dịch vụ); không có: None."""
	candidates = frappe.get_all(
		"NC Benchmark Price",
		filters={
			"facility": row.get("facility"),
			"price_category": row.get("price_category"),
			"effective_date": row.get("effective_date"),
			"status": ["!=", ref.STATUS_REJECTED],
			"name": ["!=", row.get("name") or ""],
		},
		fields=DUP_FIELDS,
	)
	return ref.find_duplicate(row, candidates)
