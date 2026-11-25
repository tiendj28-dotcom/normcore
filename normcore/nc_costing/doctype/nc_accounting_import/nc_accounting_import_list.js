// SCR-DSK-020 (FEAT-016): danh sách lần nhập số liệu kế toán.
frappe.listview_settings["NC Accounting Import"] = {
	add_fields: ["status", "error_count"],
	get_indicator(doc) {
		if (doc.status === "Đã chốt") return [doc.status, "green", "status,=,Đã chốt"];
		if (doc.error_count > 0) return [__("Has error lines"), "red", "error_count,>,0"];
		return [doc.status, "orange", "status,=,Nháp"];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Download template"), () =>
			window.open(frappe.urllib.get_full_url("/api/method/normcore.api.accounting.download_template"))
		);
	},
};
