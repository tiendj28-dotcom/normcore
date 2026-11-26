// SCR-DSK-041 (FEAT-034): danh sách mẫu định mức. Nút "Mới" hiện theo DocPerm (NC Finance, NC Admin).
frappe.listview_settings["NC Norm Template"] = {
	add_fields: ["is_active", "cls_group"],
	get_indicator(doc) {
		return doc.is_active
			? [__("Active"), "green", "is_active,=,1"]
			: [__("Not in use"), "gray", "is_active,=,0"];
	},
};
