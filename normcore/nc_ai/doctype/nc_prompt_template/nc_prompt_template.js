// SCR-DSK-029b: mẫu lệnh AI có phiên bản (FEAT-023, FR-AI-014). Bản đã tạo không sửa được.
const NC_PROMPT_LOCKED = ["template_code", "system_prompt", "user_prompt", "output_schema"];

frappe.ui.form.on("NC Prompt Template", {
	refresh(frm) {
		if (frm.doc.__islocal) {
			frm.set_df_property("version", "read_only", 1);
			return;
		}
		NC_PROMPT_LOCKED.forEach((f) => frm.set_df_property(f, "read_only", 1));
		frm.set_df_property("version", "read_only", 1);
		frm.dashboard.set_headline_alert(
			frappe.utils.escape_html(__("Mẫu lệnh đã tạo không sửa được. Chọn \"Tạo phiên bản mới\" để sửa.")),
			"blue"
		);
		if (frappe.model.can_create("NC Prompt Template")) {
			frm.add_custom_button(__("Tạo phiên bản mới"), () => frm.trigger("new_version"));
		}
		frm.add_custom_button(__("Xem nhật ký dùng mẫu này"), () =>
			frappe.set_route("List", "NC AI Log", { prompt_template: frm.doc.name })
		);
	},

	is_active(frm) {
		if (!frm.doc.__islocal && frm.doc.is_active) {
			frappe.show_alert({
				message: __("Các phiên bản khác của {0} sẽ thôi dùng.", [frm.doc.template_code]),
				indicator: "orange",
			});
		}
	},

	new_version(frm) {
		const d = new frappe.ui.Dialog({
			title: __("Phiên bản mới của {0}", [frm.doc.template_code]),
			size: "large",
			fields: [
				{ fieldtype: "HTML", options: `<p class="text-muted">${frappe.utils.escape_html(
					__("Bản mới sẽ được dùng ngay; bản v{0} được giữ lại và thôi dùng.", [frm.doc.version]))}</p>` },
				{ fieldname: "system_prompt", label: __("Lệnh hệ thống"), fieldtype: "Long Text", reqd: 1, default: frm.doc.system_prompt },
				{ fieldname: "user_prompt", label: __("Lệnh người dùng (Jinja)"), fieldtype: "Long Text", reqd: 1, default: frm.doc.user_prompt },
				{ fieldname: "output_schema", label: __("Lược đồ JSON đầu ra"), fieldtype: "Code", options: "JSON", reqd: 1, default: frm.doc.output_schema },
			],
			primary_action_label: __("Tạo phiên bản"),
			primary_action(values) {
				frappe.call({
					method: "normcore.api.ai.new_prompt_version",
					args: { template_code: frm.doc.template_code, ...values },
					callback: (r) => {
						if (!r.message) return;
						d.hide();
						frappe.show_alert({ message: __("Đã tạo phiên bản v{0}", [r.message.version]), indicator: "green" });
						frappe.set_route("Form", "NC Prompt Template", r.message.name);
					},
				});
			},
		});
		d.show();
	},
});
