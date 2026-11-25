// SCR-DSK-021 (FEAT-016): danh sách NC Cost Center Driver, nút nhập từ Excel.
frappe.listview_settings["NC Cost Center Driver"] = {
	onload(listview) {
		if (!frappe.model.can_create("NC Cost Center Driver")) return;
		listview.page.add_inner_button(__("Import from Excel"), () => {
			frappe.set_route("import-excel", { import_set: "nc_cost_center_driver" });
		});
	},
};
