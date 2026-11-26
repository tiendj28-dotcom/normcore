// FEAT-008 (FR-WF-011): thêm nhãn "Cần cập nhật" cạnh chỉ báo trạng thái trong danh sách.
frappe.listview_settings["NC Norm Set"] = {
	add_fields: ["status", "needs_update"],
	get_indicator(doc) {
		const colors = { "Nháp": "gray", "Đã xác nhận chuyên môn": "blue", "Đã khóa": "green", "Đã thay thế": "orange" };
		if (doc.needs_update) return [__("Needs update"), "yellow", "needs_update,=,1"];
		return [__(doc.status), colors[doc.status] || "gray", "status,=," + doc.status];
	},
};
