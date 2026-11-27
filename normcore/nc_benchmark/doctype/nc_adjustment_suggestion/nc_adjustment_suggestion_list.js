// SCR-DSK-026 (FEAT-028): danh sách gợi ý điều chỉnh giá.
frappe.listview_settings["NC Adjustment Suggestion"] = {
	add_fields: ["status", "direction"],
	get_indicator(doc) {
		const map = {
			"Mới": [__("New"), "blue"],
			"Chấp nhận": [__("Accepted"), "green"],
			"Từ chối": [__("Rejected"), "gray"],
			"Đã chuyển yêu cầu sửa quy trình": [__("Sent to procedure change"), "purple"],
		};
		const [label, color] = map[doc.status] || [doc.status, "gray"];
		return [label, color, `status,=,${doc.status}`];
	},
};
