frappe.listview_settings["NC Item Price"] = {
	add_fields: ["verification_status"],
	get_indicator(doc) {
		if (doc.verification_status === "Đã xác minh") return [__("Verified"), "green", "verification_status,=,Đã xác minh"];
		return [__("Unverified"), "orange", "verification_status,=,Chưa xác minh"];
	},
};
