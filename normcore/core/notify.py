"""Thông báo và việc chờ xử lý dùng chung (FR-NOTI-001..003, FEAT-002).

Email (FR-NOTI-002): Frappe bỏ qua email cho Notification Log loại "Alert" (hook notification_skip_email_types),
nên `notify` tự gọi `send_notification_email` của Frappe (cùng mẫu thư, cùng liên kết bản ghi) khi người nhận
chưa tắt email trong Notification Settings. Không có Email Account gửi đi thì chỉ ghi log lỗi, thông báo
trong ứng dụng vẫn có (ASM-002-14).
"""

import frappe

SKIP_USERS = ("Administrator", "Guest")
HOOK = "normcore_pending_sources"


def notify(users, subject, ref_doctype, ref_name, from_user=None):
	"""Notification Log (Alert) cho từng người; bỏ người trống, Administrator, Guest, user tắt; gộp trùng;
	không tạo nếu đã có cùng (người nhận, DocType, bản ghi, tiêu đề). Trả số thông báo đã tạo."""
	created = 0
	for user in dict.fromkeys(users or []):
		if not user or user in SKIP_USERS or not frappe.db.get_value("User", user, "enabled"):
			continue
		if frappe.db.exists(
			"Notification Log",
			{"for_user": user, "document_type": ref_doctype, "document_name": ref_name, "subject": subject},
		):
			continue
		log = frappe.get_doc(
			{
				"doctype": "Notification Log",
				"type": "Alert",
				"document_type": ref_doctype,
				"document_name": ref_name,
				"subject": subject,
				"for_user": user,
				"from_user": from_user or frappe.session.user,
			}
		).insert(ignore_permissions=True)
		_email(log)
		created += 1
	return created


def _email(log):
	from frappe.desk.doctype.notification_log.notification_log import send_notification_email
	from frappe.desk.doctype.notification_settings.notification_settings import is_email_notifications_enabled

	if not is_email_notifications_enabled(log.for_user):
		return
	try:
		send_notification_email(log)
	except Exception:
		frappe.log_error(title="Không gửi được email thông báo")


def register_pending_sources():
	"""Hàm nguồn việc chờ đăng ký ở hook `normcore_pending_sources`; đường dẫn lỗi bị bỏ và ghi log."""
	sources = []
	for path in frappe.get_hooks(HOOK) or []:
		try:
			sources.append(frappe.get_attr(path))
		except Exception:
			frappe.log_error(title=f"Nguồn việc chờ lỗi: {path}")
	return sources


def pending_for(user=None):
	"""Gộp việc chờ của `user` từ mọi nguồn, việc chờ lâu nhất lên đầu. Nguồn lỗi không làm hỏng nguồn khác."""
	user = user or frappe.session.user
	items = []
	for source in register_pending_sources():
		try:
			items.extend(source(user) or [])
		except Exception:
			frappe.log_error(title=f"Nguồn việc chờ lỗi: {getattr(source, '__name__', source)}")
	return sorted(items, key=lambda i: i.get("since") or "")
