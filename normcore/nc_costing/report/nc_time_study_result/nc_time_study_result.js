// SCR-DSK-016 (FEAT-014): kết quả bấm giờ và nút "Áp vào bộ định mức". Mọi lệnh ghi qua normcore.api.time_study.
function nc_ts_apply(report, normSet, confirm) {
	frappe.call({
		method: "normcore.api.time_study.apply_to_norm_set",
		args: { norm_set: normSet, confirm: confirm ? 1 : 0 },
		freeze: true,
		callback: (r) => {
			const res = r.message;
			if (!res) return;
			if (res.needs_confirm) {
				frappe.confirm(
					__(
						"Only {0} cases, fewer than the minimum {1}. Apply the medians to the norm set anyway? The minutes of matching lines will be replaced and the basis set to time study.",
						[res.n_cases, res.min_cases]
					),
					() => nc_ts_apply(report, normSet, true)
				);
				return;
			}
			frappe.show_alert({ message: __("Updated {0} lines.", [res.updated.length]), indicator: "green" });
			if (res.unmatched.length) {
				const list = res.unmatched.map((u) => frappe.utils.escape_html(u.step_id + " · " + u.resource)).join("; ");
				frappe.msgprint({
					title: __("No matching norm line"),
					message: __("No matching norm line: {0}", [list]),
					primary_action: {
						label: __("Open norm grid"),
						action: () => frappe.set_route("norm-grid", normSet),
					},
				});
			}
		},
	});
}

function nc_ts_open_dialog(report) {
	const f = report.get_filter_values();
	const dialog = new frappe.ui.Dialog({
		title: __("Apply to norm set"),
		fields: [
			{
				fieldname: "norm_set",
				fieldtype: "Link",
				options: "NC Norm Set",
				label: __("Norm set"),
				reqd: 1,
				default: f.norm_set || "",
				get_query: () => ({
					filters: {
						technical_service: f.technical_service,
						department: f.department,
						...(f.procedure ? { procedure: f.procedure } : {}),
						status: "Nháp",
					},
				}),
			},
			{ fieldname: "none_hint", fieldtype: "HTML", options: "" },
		],
		primary_action_label: __("Apply"),
		primary_action(values) {
			dialog.hide();
			nc_ts_apply(report, values.norm_set, false);
		},
	});
	frappe.db
		.count("NC Norm Set", {
			filters: { technical_service: f.technical_service, department: f.department, status: "Nháp" },
		})
		.then((n) => {
			if (!n) {
				dialog.fields_dict.none_hint.$wrapper.html(
					'<p class="text-muted">' +
						__("There is no draft norm set for this procedure.") +
						' <a href="/app/nc-norm-set">' +
						__("Norm set list") +
						"</a></p>"
				);
			}
		});
	dialog.show();
}

frappe.query_reports["NC Time Study Result"] = {
	filters: [
		{ fieldname: "technical_service", label: __("Service"), fieldtype: "Link", options: "NC Technical Service", reqd: 1 },
		{ fieldname: "department", label: __("Department"), fieldtype: "Link", options: "NC Department", reqd: 1 },
		{
			fieldname: "procedure",
			label: __("Procedure version"),
			fieldtype: "Link",
			options: "NC Clinical Procedure",
			get_query: () => {
				const f = frappe.query_report.get_filter_values();
				return { filters: { technical_service: f.technical_service, department: f.department } };
			},
		},
		{ fieldname: "norm_set", label: __("Norm set"), fieldtype: "Link", options: "NC Norm Set", hidden: 1 },
	],
	onload(report) {
		if (frappe.model.can_write("NC Norm Set")) {
			report.page.add_inner_button(__("Apply to norm set"), () => nc_ts_open_dialog(report)).addClass("btn-primary");
		}
		report.page.add_inner_button(__("Record new study"), () => {
			const f = report.get_filter_values();
			frappe.new_doc("NC Time Study", { technical_service: f.technical_service, department: f.department });
		});
	},
};
