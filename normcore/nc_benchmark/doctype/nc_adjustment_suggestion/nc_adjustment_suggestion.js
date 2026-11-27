// SCR-DSK-026 (FEAT-028): form chỉ đọc; lối sang Bàn so sánh giá.
frappe.ui.form.on("NC Adjustment Suggestion", {
	refresh(frm) {
		if (frm.is_new() || !frm.doc.service_cost) return;
		frm.add_custom_button(__("Open in price comparison"), () => {
			frappe.db.get_value("NC Service Cost", frm.doc.service_cost, "costing_run").then((r) => {
				frappe.set_route("price-compare", { run: r.message.costing_run });
			});
		});
	},
});
