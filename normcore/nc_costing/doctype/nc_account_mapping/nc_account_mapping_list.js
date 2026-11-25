// SCR-DSK-021 (FEAT-016): danh sách NC Account Mapping, nút nhập từ Excel.
frappe.listview_settings["NC Account Mapping"] = {
	add_fields: ["note"],
	formatters: {
		note(value) {
			return (value || "").includes("Giả định — chờ xác nhận")
				? `<span class="indicator-pill gray">${__("Assumption")}</span>`
				: frappe.utils.escape_html(value || "");
		},
	},
	onload(listview) {
		if (!frappe.model.can_create("NC Account Mapping")) return;
		listview.page.add_inner_button(__("Import from Excel"), () => {
			frappe.set_route("import-excel", { import_set: "nc_account_mapping" });
		});
	},
};
