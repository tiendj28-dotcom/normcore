frappe.listview_settings["NC Item Price"] = {
	add_fields: ["verification_status"],
	get_indicator(doc) {
		if (doc.verification_status === "Đã xác minh") return [__("Verified", null, "NC Item Price"), "green", "verification_status,=,Đã xác minh"];
		return [__("Unverified", null, "NC Item Price"), "orange", "verification_status,=,Chưa xác minh"];
	},
};
