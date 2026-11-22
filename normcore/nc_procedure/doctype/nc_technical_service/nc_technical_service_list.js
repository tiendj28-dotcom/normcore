// SCR-DSK-005: danh sách chuẩn của Desk; thêm bộ lọc khoa thực hiện và hai nút nhập (FEAT-005, AMD-004).
frappe.listview_settings["NC Technical Service"] = {
	add_fields: ["is_active"],
	get_indicator(doc) {
		return doc.is_active
			? [__("Active"), "green", "is_active,=,1"]
			: [__("Inactive"), "darkgrey", "is_active,=,0"];
	},
	onload(listview) {
		listview.page.add_field({
			fieldname: "department",
			doctype: "NC Service Department",
			fieldtype: "Link",
			options: "NC Department",
			condition: "=",
			label: __("Performing department"),
			onchange() {
				listview.filter_area.debounced_refresh_list_view();
			},
		});
		listview.page.add_inner_button(__("Download template"), () => {
			window.open(
				"/api/method/normcore.api.importer.download_template?import_set=nc_technical_service"
			);
		});
		if (frappe.model.can_create("NC Technical Service")) {
			listview.page.add_inner_button(__("Import from Excel"), () => {
				frappe.set_route("import-excel");
			});
		}
	},
};
