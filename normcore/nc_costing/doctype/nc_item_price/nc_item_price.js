// SCR-DSK-017: đơn giá có chứng từ. Nút "Xác minh" (FR-RES-016), nhãn trạng thái xác minh (FR-RES-017).
frappe.ui.form.on("NC Item Price", {
	refresh(frm) {
		if (frm.is_new()) return;
		const verified = frm.doc.verification_status === "Đã xác minh";
		frm.dashboard.clear_headline();
		frm.dashboard.set_headline_alert(
			verified ? __("Verified") : __("Unverified"),
			verified ? "green" : "orange"
		);
		if (!verified && frappe.model.can_write("NC Item Price") && !frm.is_dirty()) {
			frm.add_custom_button(__("Verify"), () => {
				frappe.call({
					method: "normcore.api.item.verify_price",
					args: { name: frm.doc.name },
					freeze: true,
					callback: () => frm.reload_doc(),
				});
			});
		}
	},
});
