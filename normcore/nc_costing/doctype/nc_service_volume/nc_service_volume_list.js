// SCR-DSK-021 (FEAT-016): danh sách NC Service Volume, nút nhập từ Excel.
frappe.listview_settings["NC Service Volume"] = {
	onload(listview) {
		if (frappe.model.can_read("NC Test System Volume")) {
			// SCR-DSK-037 (FEAT-035)
			listview.page.add_inner_button(__("Clinical volume and stock issues"), () => {
				frappe.set_route("List", "NC Test System Volume");
			});
		}
		if (!frappe.model.can_create("NC Service Volume")) return;
		listview.page.add_inner_button(__("Import from Excel"), () => {
			frappe.set_route("import-excel", { import_set: "nc_service_volume" });
		});
	},
};
