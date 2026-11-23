// SCR-DSK-032 (FEAT-031): danh sách hệ thống xét nghiệm.
frappe.listview_settings["NC Test System"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const color = doc.status === "Đang dùng" ? "green" : "gray";
		return [doc.status, color, `status,=,${doc.status}`];
	},
	onload(listview) {
		if (frappe.model.can_create("NC Test System")) {
			listview.page.add_inner_button(__("Import from Excel"), () => {
				frappe.set_route("import-excel", { import_set: "nc_test_system" });
			});
		}
	},
};
