// SCR-DSK-023 (FEAT-015): bảng giải trình của một dịch vụ (chế độ xem, toàn bộ chỉ đọc).
const API = "normcore.api.costing.";
const RESULT_COLOR = { "Thành công": "green", "Cảnh báo": "yellow", "Lỗi": "red" };
const BAR_COLOR = {
	LABOR: "--blue-500",
	DRUG: "--green-500",
	SUPPLY: "--teal-500",
	EQUIPMENT: "--orange-500",
	INFRA: "--purple-500",
	UTILITY: "--yellow-500",
};

function esc(v) {
	return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
}

function money(v) {
	return frappe.format(v || 0, { fieldtype: "Currency" });
}

function qty(v) {
	return v === null || v === undefined ? "" : frappe.format(v, { fieldtype: "Float", precision: Number.isInteger(v) ? 0 : 4 });
}

function warning_pill(text) {
	if (!text) return "";
	return text
		.split("; ")
		.map((w) => `<span class="indicator-pill ${w.startsWith("Khấu hao bị loại") ? "gray" : "yellow"}">${esc(w)}</span>`)
		.join(" ");
}

function render_header(h) {
	const msg = h.calc_message ? `<div class="alert alert-${h.calc_status === "Lỗi" ? "danger" : "warning"}" role="alert">${esc(h.calc_message)}</div>` : "";
	return (
		`<div><b>${esc(h.service)} — ${esc(h.service_name || "")}</b> · ${esc(h.department)} · ` +
		`<a href="/app/nc-costing-run/${encodeURIComponent(h.costing_run)}">${esc(h.costing_run)}</a> · ${esc(h.price_category || "")} ` +
		`<span class="indicator-pill ${RESULT_COLOR[h.calc_status] || "gray"}">${esc(h.calc_status)}</span></div>${msg}`
	);
}

function render_notes(notes) {
	return (notes || []).map((n) => `<div class="alert alert-warning" role="alert">${esc(n)}</div>`).join("");
}

function render_prices(h) {
	const cell = (label, value, bold) => `<div class="col-sm"><div class="text-muted">${label}</div><div class="text-right">${bold ? "<b>" : ""}${money(value)}${bold ? "</b>" : ""}</div></div>`;
	return (
		`<div class="row mt-3">` +
		cell(__("Direct cost"), h.direct_total) +
		cell(__("Allocation"), h.alloc_total) +
		cell(__("Full cost"), h.full_cost) +
		cell(__("Accumulation"), h.accumulation) +
		cell(__("Financial obligation"), h.obligation) +
		cell(__("Calculated price"), h.calculated_price) +
		cell(__("Rounded price"), h.rounded_price, true) +
		`</div>`
	);
}

function render_structure(items) {
	if (!items || !items.length) return "";
	const segs = items
		.map((s) => `<div title="${esc(s.label)}" style="width:${s.share_pct}%;background:var(${BAR_COLOR[s.component] || "--gray-500"});height:16px"></div>`)
		.join("");
	const legend = items
		.map((s) => `<span style="margin-right:12px"><span style="display:inline-block;width:10px;height:10px;background:var(${BAR_COLOR[s.component] || "--gray-500"})"></span> ${esc(s.label)}: ${money(s.amount)} (${s.share_pct}%)</span>`)
		.join("");
	return `<div class="mt-3"><b>${__("Price structure")}</b><div style="display:flex;margin:6px 0">${segs}</div><div class="text-muted">${legend}</div></div>`;
}

function render_direct(groups) {
	if (!groups || !groups.length) return "";
	const head =
		`<thead><tr><th>${__("Step")}</th><th>${__("Norm line")}</th><th>${__("Resource")}</th><th class="text-right">${__("Applied quantity")}</th>` +
		`<th class="text-right">${__("Unit rate")}</th><th class="text-right">${__("Amount")}</th><th>${__("Rate source")}</th><th>${__("Warning")}</th></tr></thead>`;
	let body = "";
	groups.forEach((g, gi) => {
		body += `<tr class="active" data-group="${gi}" tabindex="0" style="cursor:pointer"><td colspan="5"><b>${esc(g.label)}</b></td><td class="text-right"><b>${money(g.total)}</b></td><td colspan="2"></td></tr>`;
		g.steps.forEach((s) => {
			s.lines.forEach((l) => {
				const excluded = (l.rate_source || "").startsWith("Loại trừ");
				body +=
					`<tr data-in-group="${gi}"${excluded ? ' class="text-muted"' : ""}><td>${esc(l.step_label)}</td><td>${esc(l.norm_line_id)}</td><td>${esc(l.resource_label)}</td>` +
					`<td class="text-right">${qty(l.applied_qty)}</td><td class="text-right">${qty(l.unit_rate)}</td><td class="text-right">${money(l.amount)}</td>` +
					`<td>${esc(l.rate_source)}</td><td>${warning_pill(l.warning)}</td></tr>`;
			});
		});
	});
	return `<div class="mt-3"><b>${__("Direct costs")}</b></div><div class="table-responsive"><table class="table table-bordered">${head}<tbody>${body}</tbody></table></div>`;
}

function render_allocation(lines) {
	if (!lines || !lines.length) return "";
	const body = lines
		.map(
			(l) =>
				`<tr><td>${esc(l.component)}</td><td>${l.allocation_rule ? `<a href="/app/nc-allocation-rule/${encodeURIComponent(l.allocation_rule)}">${esc(l.allocation_rule)}</a>` : ""}</td>` +
				`<td class="text-right">${qty(l.driver_value)}</td><td class="text-right">${qty(l.driver_total)}</td><td class="text-right">${money(l.pool_amount)}</td><td class="text-right">${money(l.amount)}</td></tr>`
		)
		.join("");
	return (
		`<div class="mt-3"><b>${__("Allocation")}</b></div><div class="table-responsive"><table class="table table-bordered"><thead><tr>` +
		`<th>${__("Cost type")}</th><th>${__("Allocation rule")}</th><th class="text-right">${__("Driver of the service")}</th><th class="text-right">${__("Total driver")}</th>` +
		`<th class="text-right">${__("Cost pool")}</th><th class="text-right">${__("Allocated amount")}</th></tr></thead><tbody>${body}</tbody></table></div>`
	);
}

function render(section, e) {
	const h = e.header;
	let html = render_header(h) + render_notes(e.notes);
	if (h.calc_status !== "Lỗi") {
		html += render_prices(h) + render_structure(e.structure) + render_direct(e.direct_groups) + render_allocation(e.allocation_lines);
	}
	section.html(html);
	section.find("tr[data-group]").on("click keydown", function (ev) {
		if (ev.type === "keydown" && ev.key !== "Enter") return;
		section.find(`tr[data-in-group="${$(this).attr("data-group")}"]`).toggle();
	});
}

frappe.ui.form.on("NC Service Cost", {
	refresh(frm) {
		frm.disable_save();
		frm.set_df_property("lines", "hidden", 1);
		if (frm.is_new()) return;
		const loading = frm.dashboard.add_section(`<div class="text-muted">${__("Loading explanation…")}</div>`, __("Cost explanation"));
		frappe.call({
			method: API + "get_explanation",
			args: { service_cost: frm.doc.name },
			callback(r) {
				if (r.message) render(loading, r.message);
			},
		});
	},
});
