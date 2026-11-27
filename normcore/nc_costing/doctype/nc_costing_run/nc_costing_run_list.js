// SCR-DSK-022 (FEAT-015): danh sách lần tính giá.
frappe.listview_settings["NC Costing Run"] = {
	add_fields: ["status", "progress", "fiscal_year", "costing_date", "price_category", "based_on_run"],
	get_indicator(doc) {
		const color = {
			"Nháp": "gray",
			"Đang tính": "orange",
			"Đã tính": "blue",
			"Tính lỗi": "red",
			"Đã khóa": "green",
		}[doc.status];
		let label = doc.status === "Đang tính" ? `${doc.status} ${doc.progress || 0}%` : doc.status;
		if (doc.based_on_run) label = `${label} · ${__("Scenario")}`; // FEAT-029
		return [label, doc.based_on_run ? "purple" : color || "gray", `status,=,${doc.status}`];
	},
	onload(listview) {
		listview.page.set_title(__("Costing runs"));
	},
	// Danh sách rỗng: hướng dẫn tạo lần tính đầu tiên (chỉ khi có quyền tạo).
	get_no_result_message() {
		return frappe.model.can_create("NC Costing Run") ? __("No costing runs yet. Create the first costing run.") : __("No costing runs yet.");
	},
};
