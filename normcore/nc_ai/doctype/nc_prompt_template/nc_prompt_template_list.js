// SCR-DSK-029b: danh sách mẫu lệnh AI (FEAT-023).
frappe.listview_settings["NC Prompt Template"] = {
	add_fields: ["is_active", "version"],
	get_indicator(doc) {
		return doc.is_active
			? [__("Đang dùng"), "green", "is_active,=,1"]
			: [__("Ngừng dùng"), "darkgrey", "is_active,=,0"];
	},
};
