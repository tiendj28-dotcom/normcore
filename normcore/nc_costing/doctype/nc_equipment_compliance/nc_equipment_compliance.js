// SCR-DSK-035 (FEAT-033): form hồ sơ tuân thủ thiết bị.
const STATUS_COLOR = { "Còn hạn": "green", "Sắp hết hạn": "orange", "Hết hạn": "red" };

function suggest_expiry(frm) {
	// ASM-102: chỉ gợi ý khi ngày hết hạn trống; người dùng sửa được
	if (frm.doc.expiry_date || !frm.doc.performed_on || !(frm.doc.cycle_months > 0)) return;
	frm.set_value("expiry_date", frappe.datetime.add_months(frm.doc.performed_on, frm.doc.cycle_months));
}

frappe.ui.form.on("NC Equipment Compliance", {
	refresh(frm) {
		frm.dashboard.clear_headline();
		if (frm.is_new() || !frm.doc.status) return;
		const days = frappe.datetime.get_diff(frm.doc.expiry_date, frappe.datetime.get_today());
		const note =
			days >= 0 ? __("Expires in {0} days", [days]) : __("Expired {0} days ago", [-days]);
		frm.dashboard.set_headline_alert(
			`${frappe.utils.escape_html(frm.doc.status)} — ${note}`,
			STATUS_COLOR[frm.doc.status] || "gray"
		);
	},
	performed_on: suggest_expiry,
	cycle_months: suggest_expiry,
});
