// SCR-DSK-024 (FEAT-017): danh sách dòng đối soát. Dòng do hệ thống tạo khi tính giá, không tạo tay.
frappe.listview_settings["NC Reconciliation Line"] = {
	add_fields: ["over_tolerance", "explanation", "variance_pct"],
	get_indicator(doc) {
		if (!doc.over_tolerance) return [__("Watch"), "gray", "over_tolerance,=,0"];
		return doc.explanation
			? [__("Over tolerance · explained"), "green", "over_tolerance,=,1"]
			: [__("Over tolerance · needs explanation"), "red", "over_tolerance,=,1"];
	},
	onload(listview) {
		listview.page.set_title(__("Reconciliation lines"));
	},
	can_create: false,
};
