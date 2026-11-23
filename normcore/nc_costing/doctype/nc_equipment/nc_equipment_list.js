// SCR-DSK-018 (FEAT-010): danh sách thiết bị.
frappe.listview_settings["NC Equipment"] = {
	add_fields: ["acquisition_mode", "allocation_basis"],
	get_indicator(doc) {
		const colors = {
			"Mua": "green",
			"Thuê": "blue",
			"Đặt theo hóa chất": "orange",
			"Liên doanh, liên kết": "purple",
		};
		return [doc.acquisition_mode, colors[doc.acquisition_mode] || "gray", `acquisition_mode,=,${doc.acquisition_mode}`];
	},
};
