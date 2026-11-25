// SCR-DSK-037 (FEAT-035): danh sách sản lượng cận lâm sàng; nút nhập từ Excel, kịch bản mặc định.
const AUX_FIELDS = ["iqc_tests", "calibration_tests", "rerun_tests", "eqa_tests"];

frappe.listview_settings["NC Test System Volume"] = {
	add_fields: AUX_FIELDS,
	filters: [["scenario", "=", "Thực tế 12 tháng"]],
	get_indicator(doc) {
		const blank = AUX_FIELDS.some((f) => doc[f] === null || doc[f] === undefined);
		return blank
			? [__("Will be estimated from the plan"), "orange", "iqc_tests,is,not set"]
			: [__("Actual figures"), "green", "iqc_tests,is,set"];
	},
	onload(listview) {
		if (!frappe.model.can_create("NC Test System Volume")) return;
		listview.page.add_inner_button(__("Import from Excel"), () => {
			frappe.set_route("import-excel", { import_set: "nc_test_system_volume" });
		});
	},
};
