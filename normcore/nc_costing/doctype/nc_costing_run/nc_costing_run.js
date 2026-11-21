// Nút tạm "Chạy tính giá" của skeleton FEAT-000 (FEAT-015 sẽ thay).
frappe.ui.form.on("NC Costing Run", {
	refresh(frm) {
		if (frm.is_new()) return;

		if (["Nháp", "Tính lỗi"].includes(frm.doc.status) && frm.perm[0] && frm.perm[0].write) {
			frm.add_custom_button(__("Run costing"), () => {
				if (frm.is_dirty()) {
					frappe.msgprint(__("Save the form first."));
					return;
				}
				frappe.call({
					method: "run_doc_method",
					args: { method: "run_costing", dt: frm.doctype, dn: frm.doc.name },
					freeze: true,
					callback: () => {
						frm.reload_doc().then(() => {
							if (frm.doc.status === "Đã tính") {
								frappe.show_alert({ message: __("Costing completed."), indicator: "green" });
							} else if (frm.doc.status === "Tính lỗi") {
								frappe.show_alert({ message: __("Costing failed."), indicator: "red" });
							}
						});
					},
				});
			}).addClass("btn-primary");
		}

		if (frm.doc.status === "Đã tính") {
			frm.add_custom_button(__("View costing results"), () => {
				frappe.set_route("List", "NC Service Cost", { costing_run: frm.doc.name });
			});
		}
	},
});
