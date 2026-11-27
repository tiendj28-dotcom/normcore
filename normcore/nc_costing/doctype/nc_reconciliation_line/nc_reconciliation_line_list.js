// SCR-DSK-024 (FEAT-017): danh sách dòng đối soát. Dòng do hệ thống tạo khi tính giá, không tạo tay.
frappe.listview_settings["NC Reconciliation Line"] = {
	add_fields: ["over_tolerance", "explanation", "variance_pct", "recon_type", "recon_status"],
	get_indicator(doc) {
		if (doc.recon_type === "Sản lượng") {
			return doc.over_tolerance ? [__("Volume deviation warning"), "yellow", "over_tolerance,=,1"] : [__("Watch"), "gray", "over_tolerance,=,0"];
		}
		if (doc.recon_status === "Chưa đối soát") {
			return doc.explanation ? [__("Not reconciled · confirmed"), "green", "recon_status,=,Chưa đối soát"] : [__("Not reconciled · needs explanation"), "red", "recon_status,=,Chưa đối soát"];
		}
		if (!doc.over_tolerance) return [__("Watch"), "gray", "over_tolerance,=,0"];
		return doc.explanation
			? [__("Over tolerance · explained"), "green", "over_tolerance,=,1"]
			: [__("Over tolerance · needs explanation"), "red", "over_tolerance,=,1"];
	},
	onload(listview) {
		listview.page.set_title(__("Reconciliation lines"));
	},
	can_create: false,
};
