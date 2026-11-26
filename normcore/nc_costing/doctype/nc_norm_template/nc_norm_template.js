// SCR-DSK-041 (FEAT-034): form mẫu định mức. Quyền và ràng buộc do máy chủ kiểm; đây chỉ là tiện ích giao diện.
const NC_DEFAULT_TEMPLATES = ["MDM-HOA-SINH", "MDM-MIEN-DICH"];

frappe.ui.form.on("NC Norm Template", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (NC_DEFAULT_TEMPLATES.includes(frm.doc.name) && !frm.doc.is_active) {
			frm.dashboard.set_headline(
				__("Preset template, not in use. Review the items, then turn on Active."),
				"blue"
			);
		}
	},
});
