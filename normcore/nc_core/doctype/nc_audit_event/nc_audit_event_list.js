// SCR-DSK-030: sổ sự kiện, danh sách chuẩn của Desk, chỉ đọc (FEAT-003, ASM-065).
frappe.listview_settings["NC Audit Event"] = {
	add_fields: ["event_type"],
	get_indicator(doc) {
		const color = { "Khóa": "orange", "Xuất tệp": "blue" }[doc.event_type] || "gray";
		return [doc.event_type, color, "event_type,=," + doc.event_type];
	},
};
