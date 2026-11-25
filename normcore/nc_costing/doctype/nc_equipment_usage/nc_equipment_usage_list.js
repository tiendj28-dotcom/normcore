// SCR-DSK-037 (FEAT-035): danh sách phút khai thác thiết bị; nút nhập từ Excel, kịch bản mặc định.
frappe.listview_settings["NC Equipment Usage"] = {
	filters: [["scenario", "=", "Thực tế 12 tháng"]],
	onload(listview) {
		if (!frappe.model.can_create("NC Equipment Usage")) return;
		listview.page.add_inner_button(__("Import from Excel"), () => {
			frappe.set_route("import-excel", { import_set: "nc_equipment_usage" });
		});
	},
};
