// Nút tạm "Khóa" của skeleton FEAT-000 (luồng xác nhận chuyên môn là FEAT-012).
frappe.ui.form.on("NC Norm Set", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.status !== "Nháp" || !frappe.user.has_role("NC Finance")) return;
		frm.add_custom_button(__("Lock"), () => {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Save the form first."));
				return;
			}
			frappe.confirm(__("After locking, the norm set can no longer be edited."), () => {
				frappe.call({
					method: "run_doc_method",
					args: { method: "lock", dt: frm.doctype, dn: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				});
			});
		}).addClass("btn-primary");
	},
});
