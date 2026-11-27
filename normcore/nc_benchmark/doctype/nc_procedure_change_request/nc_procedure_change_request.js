// SCR-DSK-026 (FEAT-029): yêu cầu sửa đổi quy trình từ Bàn so sánh giá. Mọi trường chỉ đọc; nút theo quyền máy chủ.
const SCENARIO_API = "normcore.api.scenario.";

function act(frm, action, reason) {
	return frappe.call({
		method: SCENARIO_API + "act_on_change_request",
		args: { name: frm.doc.name, action, reason },
		freeze: true,
	});
}

frappe.ui.form.on("NC Procedure Change Request", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(__("Open procedure"), () => frappe.set_route("Form", "NC Clinical Procedure", frm.doc.procedure));
		if (frm.doc.source_suggestion) {
			frm.add_custom_button(__("Open suggestion"), () => frappe.set_route("Form", "NC Adjustment Suggestion", frm.doc.source_suggestion));
		}
		frappe.call({ method: SCENARIO_API + "change_request_actions", args: { name: frm.doc.name } }).then((r) => {
			const actions = r.message || [];
			if (actions.includes("Tiếp nhận")) {
				frm.add_custom_button(__("Accept and open revision"), () =>
					act(frm, "Tiếp nhận").then((res) => frappe.set_route("procedure-editor", res.message.revision))
				).addClass("btn-primary");
			}
			if (actions.includes("Từ chối")) {
				frm.add_custom_button(__("Reject"), () =>
					frappe.prompt(
						[{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 }],
						(v) => act(frm, "Từ chối", v.reason).then(() => frm.reload_doc()),
						__("Reject"),
						__("Reject")
					)
				);
			}
			if (actions.includes("Đã thực hiện")) {
				frm.add_custom_button(__("Mark as done"), () => act(frm, "Đã thực hiện").then(() => frm.reload_doc()));
			}
		});
	},
});
