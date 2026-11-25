// Thư ký hội đồng: máy chủ kiểm vai trò NC Council Member khi lưu (AMD-007-01, FR-WF-004).
frappe.ui.form.on("NC Settings", {
	setup(frm) {
		frm.set_query("council_secretary", () => ({
			query: "frappe.core.doctype.user.user.user_query",
			filters: { ignore_user_type: 1 },
		}));
	},
});
