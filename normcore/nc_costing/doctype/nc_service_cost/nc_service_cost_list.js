// SCR-DSK-023 (FEAT-015): danh sách kết quả giá theo dịch vụ.
frappe.listview_settings["NC Service Cost"] = {
	add_fields: ["calc_status", "full_cost", "rounded_price"],
	get_indicator(doc) {
		const color = { "Thành công": "green", "Cảnh báo": "yellow", "Lỗi": "red" }[doc.calc_status];
		return [doc.calc_status, color || "gray", `calc_status,=,${doc.calc_status}`];
	},
};
