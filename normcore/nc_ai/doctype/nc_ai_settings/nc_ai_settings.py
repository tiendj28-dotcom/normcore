import frappe
from frappe import _
from frappe.model.document import Document

from normcore.ai import gateway


def _int(value, default):
	return default if value in (None, "") else int(value)


class NCAISettings(Document):
	def validate(self):
		self.timeout_seconds = _int(self.timeout_seconds, 180)
		if not 1 <= self.timeout_seconds <= 600:
			frappe.throw(_("Thời hạn phải từ 1 đến 600 giây"))
		self.max_output_tokens = _int(self.max_output_tokens, 4096)
		if self.max_output_tokens <= 0:
			frappe.throw(_("Số token trả về tối đa phải lớn hơn 0"))
		self.monthly_token_budget = _int(self.monthly_token_budget, 0)
		if self.monthly_token_budget < 0:
			frappe.throw(_("Hạn mức token tháng không được âm"))
		self.base_url = (self.base_url or "").strip().rstrip("/")
		if self.base_url and not self.base_url.startswith(("http://", "https://")):
			frappe.throw(_("Địa chỉ phải bắt đầu bằng http:// hoặc https://"))
		if self.protocol == gateway.PROTO_OPENAI and not self.base_url:
			frappe.throw(_("Giao thức OpenAI-compatible cần địa chỉ"))
		if self.enabled and not self.model:
			frappe.throw(_("Cần nhập mô hình để bật AI"))
		# UC-017 4c: bật AI (0 -> 1) phải kiểm tra kết nối; thất bại thì không lưu trạng thái "đang bật"
		was_enabled = int(frappe.db.get_single_value(gateway.SETTINGS, "enabled") or 0)
		if self.enabled and not was_enabled:
			res = gateway.ping(gateway.settings_from_doc(self))
			if not res.ok:
				frappe.throw(
					_("Kiểm tra kết nối thất bại: {0}. AI chưa được bật.").format(res.error),
					title=_("Cấu hình AI"),
				)
