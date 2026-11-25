// SCR-DSK-037 (FEAT-035): form xuất kho thực tế; hiện đơn vị mua của mặt hàng (chỉ hiển thị, không lưu).
function show_uom(frm) {
	if (!frm.doc.item) {
		frm.set_df_property("issued_qty", "description", "");
		return;
	}
	frappe.db.get_value("NC Item", frm.doc.item, "uom").then((r) => {
		const uom = r.message && r.message.uom;
		frm.set_df_property("issued_qty", "description", uom ? __("Unit: {0}", [uom]) : "");
	});
}

frappe.ui.form.on("NC Stock Issue Actual", {
	refresh: show_uom,
	item: show_uom,
});
