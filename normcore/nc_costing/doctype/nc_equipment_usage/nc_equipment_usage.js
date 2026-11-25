// SCR-DSK-037 (FEAT-035): form phút khai thác; chỉ thiết bị chia chi phí theo Phút chiếm máy.
frappe.ui.form.on("NC Equipment Usage", {
	refresh(frm) {
		frm.set_df_property("equipment", "description", __("Only equipment allocated by machine minutes"));
	},
});
