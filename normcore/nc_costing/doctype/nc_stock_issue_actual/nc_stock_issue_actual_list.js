// SCR-DSK-037 (FEAT-035): danh sách xuất kho thực tế; nút nhập từ Excel.
frappe.listview_settings["NC Stock Issue Actual"] = {
	onload(listview) {
		if (!frappe.model.can_create("NC Stock Issue Actual")) return;
		listview.page.add_inner_button(__("Import from Excel"), () => {
			frappe.set_route("import-excel", { import_set: "nc_stock_issue_actual" });
		});
	},
};
