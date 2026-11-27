// FEAT-026: danh sách chỉ số giá tiêu dùng, tháng hiện MM/YYYY (FR-BM-006).
frappe.listview_settings["NC CPI Index"] = {
	add_fields: ["month"],
	formatters: {
		month(value) {
			return value ? moment(value).format("MM/YYYY") : "";
		},
	},
};
