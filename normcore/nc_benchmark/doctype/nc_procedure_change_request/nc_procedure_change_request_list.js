// SCR-DSK-026 (FEAT-029): danh sách yêu cầu sửa đổi quy trình từ Bàn so sánh giá.
frappe.listview_settings["NC Procedure Change Request"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const map = {
			"Mới": [__("New"), "blue"],
			"Đã tiếp nhận": [__("Received"), "orange"],
			"Từ chối": [__("Rejected"), "gray"],
			"Đã thực hiện": [__("Done"), "green"],
		};
		const [label, color] = map[doc.status] || [doc.status, "gray"];
		return [label, color, `status,=,${doc.status}`];
	},
};
