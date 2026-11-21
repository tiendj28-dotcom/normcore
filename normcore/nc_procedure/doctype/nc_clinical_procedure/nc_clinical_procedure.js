// Nút tạm của skeleton FEAT-000. Quyền do máy chủ kiểm; ẩn hiện nút chỉ là tiện ích giao diện.
frappe.ui.form.on("NC Clinical Procedure", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Open editor"), () => {
			frappe.set_route("procedure-editor", frm.doc.name);
		});

		if (frm.doc.workflow_state === "Nháp" && frappe.user.has_role("NC Director")) {
			frm.add_custom_button(__("Publish"), () => {
				if (frm.is_dirty()) {
					frappe.msgprint(__("Save the form first."));
					return;
				}
				frappe.confirm(__("After publishing, this version's content can no longer be edited."), () => {
					frappe.call({
						method: "run_doc_method",
						args: { method: "publish", dt: frm.doctype, dn: frm.doc.name },
						freeze: true,
						callback: () => frm.reload_doc(),
					});
				});
			}).addClass("btn-primary");
		}

		if (frm.doc.workflow_state === "Đã ban hành" && frappe.model.can_create("NC Norm Set")) {
			frm.add_custom_button(__("Create norm set"), () => {
				frappe.call({
					method: "normcore.nc_costing.doctype.nc_norm_set.nc_norm_set.make_norm_set",
					args: { procedure: frm.doc.name },
					freeze: true,
					callback: (r) => {
						if (r.message) frappe.set_route("Form", "NC Norm Set", r.message);
					},
				});
			}).addClass("btn-primary");
		}
	},
});
