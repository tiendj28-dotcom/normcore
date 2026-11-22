// SCR-DSK-019: bộ tham số tính giá. Bộ đã được lần tính giá khóa sử dụng thì chỉ đọc, cho nhân bản (FR-RES-011).
frappe.ui.form.on("NC Costing Parameter Set", {
	refresh(frm) {
		if (frm.is_new()) return;
		const in_use = !!(frm.doc.__onload && frm.doc.__onload.in_use);
		if (in_use) {
			frm.set_intro(
				__("This parameter set is used by a locked costing run and is read-only. Use Duplicate to create an editable copy."),
				"red"
			);
			frm.disable_form();
		}
		if (frm.perm[0] && frm.perm[0].create) {
			const btn = frm.add_custom_button(__("Duplicate"), () => {
				frappe.call({
					method: "run_doc_method",
					args: { method: "duplicate", dt: frm.doctype, dn: frm.doc.name },
					freeze: true,
					callback: (r) => {
						if (r.message) frappe.set_route("Form", frm.doctype, r.message);
					},
				});
			});
			if (in_use) btn.addClass("btn-primary");
		}
	},
});
