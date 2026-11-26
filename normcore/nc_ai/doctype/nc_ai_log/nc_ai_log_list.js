// SCR-DSK-030: nhật ký AI, chỉ đọc (FEAT-023): màu theo trạng thái, luôn kèm chữ.
frappe.listview_settings["NC AI Log"] = {
	add_fields: ["status"],
	get_indicator(doc) {
		const color = { "Thành công": "green", "Lỗi": "red", "Quá hạn": "orange", "Bị chặn hạn mức": "red" }[doc.status] || "gray";
		return [doc.status, color, "status,=," + doc.status];
	},
};
