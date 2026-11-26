// Nút tạm "Khóa" của skeleton FEAT-000 (luồng xác nhận chuyên môn là FEAT-012).
frappe.ui.form.on("NC Norm Set", {
	refresh(frm) {
		// FEAT-008 (FR-WF-011): dải "Cần cập nhật" khi quy trình có phiên bản ban hành mới
		if (!frm.is_new() && frm.doc.needs_update) {
			frm.dashboard.set_headline_alert(
				frappe.utils.escape_html(__("Needs update: the procedure has a new version - {0}.", [frm.doc.step_change_note || ""])),
				"yellow"
			);
			frappe.db.get_list("NC Clinical Procedure", {
				filters: { technical_service: frm.doc.technical_service, department: frm.doc.department, workflow_state: "Đã ban hành" },
				fields: ["name"],
				order_by: "version_no desc",
				limit: 1,
			}).then((rows) => {
				if (!rows.length) return;
				frm.add_custom_button(__("Compare versions"), () => {
					frappe.set_route("procedure-editor", frm.doc.procedure, "compare", rows[0].name);
				});
			});
		}
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
