// Thư ký hội đồng: máy chủ kiểm vai trò NC Council Member khi lưu (AMD-007-01, FR-WF-004).
frappe.ui.form.on("NC Settings", {
	setup(frm) {
		frm.set_query("council_secretary", () => ({
			query: "frappe.core.doctype.user.user.user_query",
			filters: { ignore_user_type: 1 },
		}));
	},
	refresh(frm) {
		if (frappe.model.can_read("NC AI Settings")) {
			frm.set_intro(
				`${__("New values apply to the next operation, no restart needed.")} ${__("AI call timeout is set in AI settings.")} <a href="/app/nc-ai-settings">${__("AI settings")}</a>`,
				"blue"
			);
		}
	},
	after_save() {
		frappe.show_alert({
			message: __("Saved. New values apply to the next operation."),
			indicator: "green",
		});
	},
});
