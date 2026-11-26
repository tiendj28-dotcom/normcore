// Form NC Norm Set (FEAT-012). Sửa dòng ở trang norm-grid; bảng dòng trên form chỉ đọc (ASM-012-16).
// Quyền do máy chủ kiểm; ẩn hiện nút chỉ là tiện ích giao diện.
frappe.ui.form.on("NC Norm Set", {
	refresh(frm) {
		frm.set_df_property("lines", "read_only", 1);
		if (frm.is_new()) return;
		const closed = ["Đã khóa", "Đã thay thế"].includes(frm.doc.status);
		if (closed) {
			frm.dashboard.set_headline(
				__("This record is {0} and cannot be edited. Create a new version in the norm grid.", [__(frm.doc.status)])
			);
		}
		frm.add_custom_button(__("Open norm grid"), () => frappe.set_route("norm-grid", frm.doc.name)).addClass(
			"btn-primary"
		);
		if (frm.doc.status === "Đã xác nhận chuyên môn" && frappe.user.has_role("NC Finance")) {
			frm.add_custom_button(__("Lock"), () => {
				frappe.confirm(__("After locking, the norm set can no longer be edited."), () => {
					frappe.call({
						method: "run_doc_method",
						args: { method: "lock", dt: frm.doctype, dn: frm.doc.name },
						freeze: true,
						callback: () => frm.reload_doc(),
					});
				});
			});
		}
	},
});
