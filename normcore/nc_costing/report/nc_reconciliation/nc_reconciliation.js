// SCR-DSK-024 (FEAT-017): bảng đối soát. Dữ liệu và quyền do normcore.api.costing quyết định.
const API = "normcore.api.costing.";
const STATE_COLOR = { "Vượt ngưỡng · cần giải trình": "red", "Vượt ngưỡng · đã giải trình": "green", "Theo dõi": "gray" };

function esc(v) {
	return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
}

function money(v) {
	return frappe.format(v || 0, { fieldtype: "Currency" });
}

function pct(v) {
	if (v === null || v === undefined) return `<span title="${esc(__("Accounting amount is 0"))}">—</span>`;
	return `${frappe.format(v, { fieldtype: "Float", precision: 2 }).replace("-", "−")}%`;
}

function banner(color, html) {
	return `<div class="alert alert-${color}" role="alert">${html}</div>`;
}

function show_explain_dialog(report, line) {
	const d = new frappe.ui.Dialog({
		title: __("Explanation: {0}", [`${line.cost_center} · ${line.category_label}`]),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "figures",
				options:
					`<div>${__("Costed amount")}: ${money(line.costed_amount)}</div>` +
					`<div>${__("Accounting amount (incl. level 1)")}: ${money(line.accounting_amount)}</div>` +
					`<div>${__("Variance (%)")}: ${pct(line.variance_pct)}</div>`,
			},
			{ fieldtype: "Small Text", fieldname: "explanation", label: __("Explanation"), default: line.explanation || "", reqd: line.over_tolerance ? 1 : 0 },
		],
		primary_action_label: __("Save"),
		primary_action(values) {
			if (line.over_tolerance && !(values.explanation || "").trim()) {
				frappe.msgprint(__("Enter the explanation."));
				return;
			}
			frappe.call({
				method: API + "save_explanation",
				args: { line: line.name, explanation: values.explanation || "" },
				callback() {
					d.hide();
					frappe.show_alert({ message: __("Explanation saved."), indicator: "green" });
					report.refresh();
				},
			});
		},
	});
	d.show();
}

function lock(report, run) {
	frappe.confirm(__("Lock costing run {0}? It cannot be recalculated and explanations cannot be edited afterwards.", [run]), () => {
		frappe.call({
			method: API + "lock_run",
			args: { run },
			freeze: true,
			callback() {
				frappe.show_alert({ message: __("Locked."), indicator: "green" });
				report.refresh();
			},
		});
	});
}

function render_header(report) {
	const run = report.get_filter_value("costing_run");
	const $box = report.__recon_box || (report.__recon_box = $('<div class="nc-recon-header"></div>').insertBefore(report.$report));
	report.page.clear_primary_action();
	if (!run) {
		$box.html(`<div class="text-muted">${__("Select a costing run to see the reconciliation table.")}</div>`);
		return;
	}
	frappe.call({
		method: API + "get_reconciliation",
		args: { run },
		callback(r) {
			const m = r.message;
			if (!m) return;
			report.__recon = m;
			const parts = [`<div><b>${esc(m.run)}</b> · ${esc(m.status)} · ${__("Reconciliation tolerance")} ${esc(m.tolerance)}%</div>`];
			if (!["Đã tính", "Đã khóa"].includes(m.status)) {
				parts.push(`<div class="text-muted">${__("This costing run has no reconciliation results yet. Run costing first.")}</div>`);
			}
			if (m.blocked) {
				parts.push(banner("danger", __("{0} lines over tolerance have no explanation. The costing run cannot be locked yet.", [m.blocked])));
			} else if (m.lines.some((x) => x.over_tolerance)) {
				parts.push(banner("success", __("Every line over tolerance has an explanation.")));
			}
			if (m.warnings.length) {
				const items = m.warnings.map((w) => `<li>${esc(w)}</li>`).join("");
				parts.push(banner("warning", `<b>${__("Allocation warnings")}</b><ul>${items}</ul>`));
			}
			if (m.partial_scope) parts.push(`<div class="text-muted">${__("Partial scope: the remainder of a cost center is shared only among the services in this costing run.")}</div>`);
			if (!m.include_depreciation) parts.push(`<div class="text-muted">${__("This price category has no depreciation: depreciation is neither allocated nor reconciled.")}</div>`);
			if (m.status === "Đã khóa") parts.push(`<div class="text-muted">${__("This record is locked and cannot be edited.")}</div>`);
			$box.html(parts.join(""));
			if (m.can_lock) report.page.set_primary_action(__("Lock costing run"), () => lock(report, m.run));
			report.page.add_inner_button(__("Open costing run"), () => frappe.set_route("Form", "NC Costing Run", m.run));
		},
	});
}

frappe.query_reports["NC Reconciliation"] = {
	filters: [
		{
			fieldname: "costing_run",
			label: __("Costing run"),
			fieldtype: "Link",
			options: "NC Costing Run",
			reqd: 1,
			default: (frappe.route_options || {}).costing_run,
		},
		{ fieldname: "cost_center", label: __("Cost center"), fieldtype: "Link", options: "NC Cost Center" },
		{ fieldname: "only_over", label: __("Only lines over tolerance"), fieldtype: "Check" },
	],
	onload(report) {
		report.page.add_inner_message(__("Reconciliation note: costed amounts of labor, depreciation and utility below the accounting amount are normal (the indirect part is allocated at level 2). Management is not reconciled."));
		report.page.wrapper.on("click", ".nc-recon-explain", function () {
			const name = $(this).attr("data-name");
			const line = (report.data || []).find((x) => x.name === name);
			if (line) show_explain_dialog(report, line);
		});
	},
	refresh(report) {
		render_header(report);
	},
	formatter(value, row, column, data, default_formatter) {
		if (!data) return default_formatter(value, row, column, data);
		if (column.fieldname === "variance_pct") return pct(data.variance_pct);
		if (column.fieldname === "state") {
			return `<span class="indicator-pill ${STATE_COLOR[data.state] || "gray"} filterable no-indicator-dot">${esc(data.state)}</span>`;
		}
		if (column.fieldname === "explanation") {
			const text = data.explanation || "";
			const shown = text.length > 60 ? text.slice(0, 60) + "…" : text;
			const info = (frappe.query_report && frappe.query_report.__recon) || {};
			const can = info.can_explain;
			const btn = can
				? ` <button class="btn btn-xs btn-default nc-recon-explain" data-name="${esc(data.name)}">${data.over_tolerance ? (text ? __("Edit explanation") : __("Explain")) : __("Note")}</button>`
				: "";
			return `<span title="${esc(text)}">${esc(shown)}</span>${btn}`;
		}
		return default_formatter(value, row, column, data);
	},
};
