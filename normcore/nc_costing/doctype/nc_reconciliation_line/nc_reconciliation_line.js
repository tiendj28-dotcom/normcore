// SCR-DSK-024 (FEAT-017): form dòng đối soát. Chỉ giải trình sửa được, và chỉ khi lần tính "Đã tính".
frappe.ui.form.on("NC Reconciliation Line", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Open reconciliation table"), () => {
			frappe.route_options = { costing_run: frm.doc.costing_run };
			frappe.set_route("query-report", "NC Reconciliation");
		});
		frappe.db.get_value("NC Costing Run", frm.doc.costing_run, "status").then((r) => {
			const open = (r.message || {}).status === "Đã tính";
			frm.set_df_property("explanation", "read_only", open ? 0 : 1);
			if (!open) frm.dashboard.set_headline_alert(__("This record is locked and cannot be edited."), "green");
		});
	},
});
