// Loại giá (FR-RES-015): cấp phê duyệt bắt buộc, kiểm ở máy chủ; ở đây chỉ nhắc người dùng.
frappe.ui.form.on("NC Price Category", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(__("Choose the approval authority; it is required."), "blue");
		}
	},
});
