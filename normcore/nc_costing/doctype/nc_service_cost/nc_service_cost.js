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

function num(v, digits) {
	return Number(v || 0).toLocaleString("vi-VN", { minimumFractionDigits: digits || 0, maximumFractionDigits: digits || 0 });
}

function line_name(l) {
	const id = l.norm_line_id || "";
	if (id === "EQ-P") return __("Parts per result");
	if (id === "EQ-E") return __("Equipment electricity");
	if (id === "EQA") return __("External quality assessment");
	if (id.startsWith("QC-N")) return __("Internal QC material");
	if (id.startsWith("QC-C")) return __("Calibrator");
	return id;
}

function source_pill(text) {
	if (!text) return "";
	return text === "Ước tính từ kế hoạch" ? `<span class="indicator-pill orange">${esc(text)}</span>` : esc(text);
}

function render_systems(p) {
	const rows = p.systems
		.map((s) => {
			const warn = s.low_volume_warning ? `<span class="indicator-pill yellow">${__("Low volume")}</span>` : "";
			const est = s.k_estimated ? ` <span class="indicator-pill orange">${__("Estimated from plan")}</span>` : "";
			return (
				`<tr><td>${esc(s.test_system)}</td><td>${esc(s.equipment || "")}</td><td class="text-right">${num(s.patient_results)}</td>` +
				`<td class="text-right">${num(s.share_pct, 2)}%</td><td>${esc(s.share_source)}</td><td class="text-right">${num(s.k_factor, 6)}${est}</td>` +
				`<td class="text-right">${money(s.direct_cost)}</td><td>${warn}</td></tr>`
			);
		})
		.join("");
	const foot = (label, value, bold) =>
		`<tr><td colspan="6" class="text-right">${bold ? "<b>" : ""}${label}${bold ? "</b>" : ""}</td><td class="text-right">${bold ? "<b>" : ""}${money(value)}${bold ? "</b>" : ""}</td><td></td></tr>`;
	return (
		`<div class="mt-3"><b>${__("Direct cost by test system")}</b></div><div class="table-responsive"><table class="table table-bordered"><thead><tr>` +
		`<th>${__("Test system")}</th><th>${__("Equipment")}</th><th class="text-right">${__("Patient results")}</th><th class="text-right">${__("Share")}</th>` +
		`<th>${__("Share source")}</th><th class="text-right">${__("k factor")}</th><th class="text-right">${__("Cost per result")}</th><th>${__("Warning")}</th></tr></thead><tbody>${rows}` +
		foot(__("Weighted average"), p.weighted_direct) +
		foot(__("External quality assessment per result"), p.eqa_cost) +
		foot(__("Direct cost of the service"), p.direct_total, true) +
		`</tbody></table></div>`
	);
}

function render_k_cards(p) {
	return p.systems
		.map((s, i) => {
			const est = s.k_estimated ? ` <span class="indicator-pill orange">${__("Estimated from plan")}</span>` : "";
			const item = (label, v) => `<tr><td>${label}</td><td class="text-right">${num(v)}</td></tr>`;
			return (
				`<details${i === 0 ? " open" : ""} class="mt-2"><summary><b>${__("How k is calculated")}: ${esc(s.test_system)}</b>${est}</summary>` +
				`<div class="text-muted">k = (Qbn + Qnk + Qchuẩn + Qlại + Qngk) ÷ ((1 − h) × Qbn)</div>` +
				`<table class="table table-bordered" style="max-width:480px"><tbody>` +
				item("Qbn", s.patient_results) +
				item("Qnk", s.q_iqc) +
				item("Qchuẩn", s.q_calibration) +
				item("Qlại", s.q_rerun) +
				item("Qngk", s.q_eqa) +
				item(__("Total tests"), s.total_tests) +
				`<tr><td>h (%)</td><td class="text-right">${num(s.wastage_rate, 2)}</td></tr>` +
				`<tr><td><b>k</b></td><td class="text-right"><b>${num(s.k_factor, 6)}</b></td></tr></tbody></table></details>`
			);
		})
		.join("");
}

function render_cls_lines(p) {
	const head =
		`<thead><tr><th>${__("Line")}</th><th>${__("Line origin")}</th><th>${__("Cost level")}</th><th>${__("Resource")}</th>` +
		`<th class="text-right">${__("Applied quantity")}</th><th class="text-right">${__("Unit rate")}</th><th class="text-right">k</th>` +
		`<th>${__("Divisor")}</th><th>${__("Divisor source")}</th><th class="text-right">${__("Amount")}</th><th>${__("Warning")}</th></tr></thead>`;
	const row = (l) =>
		`<tr><td>${esc(line_name(l))}</td><td>${esc(l.line_origin)}</td><td>${esc(l.cost_level_label)}</td><td>${esc(l.resource_label)}<div class="text-muted">${esc(l.rate_source)}</div></td>` +
		`<td class="text-right">${qty(l.applied_qty)}</td><td class="text-right">${qty(l.unit_rate)}</td><td class="text-right">${l.k_factor ? num(l.k_factor, 6) : ""}</td>` +
		`<td>${esc(l.divisor_label)}: ${num(l.divisor_value, Number.isInteger(l.divisor_value) ? 0 : 4)}</td><td>${source_pill(l.divisor_source)}</td>` +
		`<td class="text-right">${money(l.amount)}</td><td>${warning_pill(l.warning)}</td></tr>`;
	let html = "";
	p.systems.forEach((s) => {
		const lines = [];
		s.groups.forEach((g) => g.steps.forEach((st) => st.lines.forEach((l) => lines.push(l))));
		html +=
			`<div class="mt-3"><b>${esc(s.test_system)} · ${__("one result of the system")} · ${money(s.direct_cost)}</b></div>` +
			`<div class="table-responsive"><table class="table table-bordered">${head}<tbody>${lines.map(row).join("")}</tbody></table></div>`;
	});
	if (p.service_lines.length) {
		html +=
			`<div class="mt-3"><b>${__("Service level")}</b></div><div class="table-responsive"><table class="table table-bordered">${head}<tbody>${p.service_lines.map(row).join("")}</tbody></table></div>`;
	}
	return html + `<div class="text-muted">${__("Each amount is the cost of one result of the system. The direct cost of the service is the weighted average by share plus external quality assessment.")}</div>`;
}

function render_header(h) {
	const errors = h.calc_status === "Lỗi" ? (h.calc_message || "").split("; ").filter(Boolean) : [];
	const msg = errors.length
		? `<div class="alert alert-danger" role="alert"><ul style="margin:0 0 0 16px">${errors.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`
		: h.calc_message
			? `<div class="alert alert-warning" role="status">${esc(h.calc_message)}</div>`
			: "";
	return (
		`<div><b>${esc(h.service)} — ${esc(h.service_name || "")}</b> · ${esc(h.department)} · ` +
		`<a href="/app/nc-costing-run/${encodeURIComponent(h.costing_run)}">${esc(h.costing_run)}</a> · ${esc(h.price_category || "")} ` +
		`<span class="indicator-pill ${RESULT_COLOR[h.calc_status] || "gray"}">${esc(h.calc_status)}</span>${h.is_paraclinical ? ` <span class="indicator-pill blue">${__("Paraclinical")}</span>` : ""}</div>${msg}`
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
		if (e.paraclinical) {
			html += render_prices(h) + render_systems(e.paraclinical) + render_k_cards(e.paraclinical) + render_cls_lines(e.paraclinical) + render_allocation(e.allocation_lines);
		} else {
			html += render_prices(h) + render_structure(e.structure) + render_direct(e.direct_groups) + render_allocation(e.allocation_lines);
		}
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
		frm.set_df_property("test_system_costs", "hidden", 1);
		if (frm.is_new()) return;
		frappe.db.get_value("NC Costing Run", frm.doc.costing_run, "status").then((r) => {
			if (((r.message || {}).status) === "Đã khóa") {
				frm.add_custom_button(__("Export explanation PDF"), () => normcore.export.open({ service_cost: frm.doc.name }));
			}
		});
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
