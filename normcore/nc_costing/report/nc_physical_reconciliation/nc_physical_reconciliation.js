// SCR-DSK-038 (FEAT-037): đối soát vật chất và sản lượng. Dữ liệu và quyền do normcore.api.costing quyết định.
const API = "normcore.api.costing.";
const STATE_COLOR = {
	"Trong ngưỡng": "gray",
	"Vượt ngưỡng · cần giải trình": "red",
	"Vượt ngưỡng · đã giải trình": "green",
	"Chưa đối soát · cần giải trình": "red",
	"Chưa đối soát · đã xác nhận": "green",
	"Cảnh báo lệch sản lượng": "yellow",
};

function esc(v) {
	return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
}

function qty(v, uom) {
	if (v === null || v === undefined) return "—";
	const n = frappe.format(v, { fieldtype: "Float", precision: 2 });
	return uom ? `${n} ${esc(uom)}` : n;
}

function pct(v, note) {
	if (v === null || v === undefined) return `<span title="${esc(note || "")}">—</span>`;
	return `${frappe.format(v, { fieldtype: "Float", precision: 2 }).replace("-", "−")}%`;
}

function banner(color, html) {
	return `<div class="alert alert-${color}" role="alert">${html}</div>`;
}

function show_explain_dialog(report, line, table) {
	const unreconciled = line.recon_status === "Chưa đối soát";
	const title = unreconciled
		? __("Confirm not reconciled: {0}", [line.department])
		: __("Explanation: {0}", [`${line.department} · ${line.item || line.technical_service || ""}`]);
	const must = table === "Vật chất" ? 1 : 0;
	const d = new frappe.ui.Dialog({
		title,
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "figures",
				options:
					`<div>${__("Calculated quantity")}: ${qty(line.calculated_qty, line.norm_uom)}</div>` +
					`<div>${__("Actual stock issue")}: ${qty(line.actual_qty, line.norm_uom)}</div>` +
					`<div>${__("Variance (%)")}: ${pct(line.variance_pct)}</div>`,
			},
			{ fieldtype: "Small Text", fieldname: "explanation", label: unreconciled ? __("Reason") : __("Explanation"), default: line.explanation || "", reqd: must && (line.over_tolerance || unreconciled) ? 1 : 0 },
		],
		primary_action_label: __("Save"),
		primary_action(values) {
			if (must && (line.over_tolerance || unreconciled) && !(values.explanation || "").trim()) {
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
	const $box = report.__phys_box || (report.__phys_box = $('<div class="nc-phys-header"></div>').insertBefore(report.$report));
	report.page.clear_primary_action();
	if (!run) {
		$box.html(`<div class="text-muted">${__("Select a costing run to see the material and volume reconciliation.")}</div>`);
		return;
	}
	frappe.call({
		method: API + "get_physical_reconciliation",
		args: { run },
		callback(r) {
			const m = r.message;
			if (!m) return;
			report.__phys = m;
			const parts = [`<div><b>${esc(m.run)}</b> · ${esc(m.status)} · ${__("Material tolerance")} ${esc(m.material_tolerance)}% · ${__("Volume tolerance")} ${esc(m.volume_tolerance)}%</div>`];
			if (!["Đã tính", "Đã khóa"].includes(m.status)) {
				parts.push(`<div class="text-muted">${__("This costing run has no reconciliation results yet. Run costing first.")}</div>`);
			}
			if (!m.available) {
				parts.push(`<div class="text-muted">${__("Material and volume reconciliation is only prepared for the Actual 12 months scenario. This costing run uses the scenario {0}.", [esc(m.scenario)])}</div>`);
			} else if (!m.material.length && !m.volume.length && ["Đã tính", "Đã khóa"].includes(m.status)) {
				parts.push(`<div class="text-muted">${__("This costing run has no paraclinical service to reconcile.")}</div>`);
			}
			if (m.blocked) {
				parts.push(banner("danger", __("{0} lines over tolerance or not reconciled have no explanation. The costing run cannot be locked yet.", [m.blocked])));
			}
			const un = m.material.filter((x) => x.recon_status === "Chưa đối soát" && !x.item);
			if (un.length) {
				const names = un.map((x) => esc(x.department)).join(", ");
				const open = un.some((x) => x.needs_explanation);
				parts.push(banner(open ? "danger" : "success", `<b>${__("Material reconciliation pending")}</b>: ${names} — ${__("no stock issue data for the fiscal year. NC Finance confirms with a reason to lock.")}`));
			}
			const warn = m.volume.filter((x) => x.over_tolerance).length;
			if (warn) parts.push(banner("warning", __("{0} services deviate in volume beyond the tolerance. Warning only; it does not block locking.", [warn])));
			if (m.status === "Đã khóa") parts.push(`<div class="text-muted">${__("This record is locked and cannot be edited.")}</div>`);
			parts.push(`<div class="text-muted small">${__("Calculated quantity = norm quantity × k × results (plus per-tube, per-batch, per-day, per-period and internal quality control lines). Stock issue is converted to the norm unit.")}</div>`);
			$box.html(parts.join(""));
			if (m.can_lock) report.page.set_primary_action(__("Lock costing run"), () => lock(report, m.run));
			report.page.add_inner_button(__("Reconciliation table"), () => {
				frappe.route_options = { costing_run: m.run };
				frappe.set_route("query-report", "NC Reconciliation");
			});
			report.page.add_inner_button(__("Open costing run"), () => frappe.set_route("Form", "NC Costing Run", m.run));
		},
	});
}

frappe.query_reports["NC Physical Reconciliation"] = {
	filters: [
		{
			fieldname: "costing_run",
			label: __("Costing run"),
			fieldtype: "Link",
			options: "NC Costing Run",
			reqd: 1,
			default: (frappe.route_options || {}).costing_run,
		},
		{ fieldname: "table", label: __("Table"), fieldtype: "Select", options: "Vật chất\nSản lượng", default: "Vật chất" },
		{ fieldname: "department", label: __("Department"), fieldtype: "Link", options: "NC Department" },
		{ fieldname: "only_attention", label: __("Only lines needing attention"), fieldtype: "Check" },
	],
	onload(report) {
		report.page.wrapper.on("click", ".nc-phys-explain", function () {
			const name = $(this).attr("data-name");
			const line = (report.data || []).find((x) => x.name === name);
			if (line) show_explain_dialog(report, line, report.get_filter_value("table"));
		});
	},
	refresh(report) {
		render_header(report);
	},
	formatter(value, row, column, data, default_formatter) {
		if (!data) return default_formatter(value, row, column, data);
		const info = (frappe.query_report && frappe.query_report.__phys) || {};
		if (column.fieldname === "variance_pct") return pct(data.variance_pct, __("Missing data"));
		if (["calculated_qty", "actual_qty", "diff_qty"].includes(column.fieldname)) {
			const v = data[column.fieldname];
			return `<span class="text-right" style="display:block;font-variant-numeric:tabular-nums">${qty(v, data.norm_uom)}</span>`;
		}
		if (column.fieldname === "state") {
			return `<span class="indicator-pill ${STATE_COLOR[data.state] || "gray"} filterable no-indicator-dot">${esc(data.state)}</span>`;
		}
		if (column.fieldname === "explanation") {
			const text = data.explanation || "";
			const shown = text.length > 60 ? text.slice(0, 60) + "…" : text;
			const label = data.recon_status === "Chưa đối soát" || data.needs_explanation ? (text ? __("Edit explanation") : __("Explain")) : __("Note");
			const btn = info.can_explain ? ` <button class="btn btn-xs btn-default nc-phys-explain" data-name="${esc(data.name)}">${label}</button>` : "";
			return `<span title="${esc(text)}">${esc(shown)}</span>${btn}`;
		}
		return default_formatter(value, row, column, data);
	},
};
