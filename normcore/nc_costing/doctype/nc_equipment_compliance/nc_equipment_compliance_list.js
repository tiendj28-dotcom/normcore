// SCR-DSK-035 (FEAT-033): danh sách hồ sơ tuân thủ thiết bị.
frappe.listview_settings["NC Equipment Compliance"] = {
	add_fields: ["status", "expiry_date"],
	get_indicator(doc) {
		const colors = { "Còn hạn": "green", "Sắp hết hạn": "orange", "Hết hạn": "red" };
		return [doc.status, colors[doc.status] || "gray", `status,=,${doc.status}`];
	},
	onload(listview) {
		if (frappe.model.can_write("NC Equipment Compliance")) {
			listview.page.add_inner_button(__("Check expiry now"), () => {
				frappe.call({
					method: "normcore.api.compliance.run_compliance_check",
					freeze: true,
					callback(r) {
						const m = r.message || {};
						frappe.show_alert({
							message: __("Updated {0} records, sent {1} notifications", [m.updated, m.notified]),
							indicator: "green",
						});
						listview.refresh();
					},
				});
			});
		}
		if (frappe.model.can_create("NC Equipment Compliance")) {
			listview.page.add_inner_button(__("Import from Excel"), () => {
				frappe.set_route("import-excel");
			});
		}
	},
};
