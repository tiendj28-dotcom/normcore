// SCR-DSK-027 (FEAT-030): form phương án giá. Chuyển trạng thái qua normcore.api.price_proposal.apply_action
// (không qua apply_workflow của Desk). Quyền và điều kiện do máy chủ kiểm; nút chỉ là tiện ích giao diện.
const PP_API = "normcore.api.price_proposal.";
const PP_STATE_COLOR = {
	"Nháp": "gray",
	"Chờ khoa xác nhận": "orange",
	"Chờ phê duyệt": "orange",
	"Đã duyệt": "green",
	"Đã duyệt nội bộ, chờ trình": "blue",
	"Đã được cấp thẩm quyền duyệt": "green",
};
const PP_AUTHORITY_STATES = ["Đã duyệt nội bộ, chờ trình", "Đã được cấp thẩm quyền duyệt"];

function pp_esc(v) {
	return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
}

function pp_money(v) {
	return frappe.format(v || 0, { fieldtype: "Currency" });
}

function pp_pill(label, color) {
	return `<span class="indicator-pill ${pp_esc(color)}"><span>${pp_esc(label)}</span></span>`;
}

function pp_summary_html(data) {
	const s = data.summary;
	let html =
		`<div class="text-muted">${__("{0} services · {1} adjusted · {2} below full cost · {3} awaiting director acknowledgement", [s.count, s.adjusted, s.below_cost, s.unacked])}</div>`;
	if (s.below_cost) {
		html += `<div class="alert alert-warning" role="alert">${pp_esc(__("Some proposed prices are below full cost; the director must acknowledge each of these lines when approving"))}</div>`;
	}
	if (data.doc.workflow_state === "Đã duyệt") {
		html += `<div class="alert alert-success" role="status">${pp_esc(__("Approved prices recorded on services from {0}", [frappe.datetime.str_to_user(data.doc.apply_from)]))}</div>`;
	}
	if (data.doc.workflow_state === "Đã duyệt nội bộ, chờ trình") {
		html += `<div class="alert alert-info" role="status">${pp_esc(__("Approved internally, awaiting submission to the competent authority"))}</div>`;
	}
	return html;
}

function pp_confirm_html(data) {
	if (!data.confirmations.length) return `<div class="text-muted">${__("No department confirmation yet")}</div>`;
	const mine = data.my_departments || [];
	const rows = data.confirmations
		.map((c) => {
			const done = !!c.confirmed_by;
			const own = mine.includes(c.department) ? ' style="background:var(--control-bg)"' : "";
			return (
				`<tr${own}><td>${pp_esc(c.department_name || c.department)}</td>` +
				`<td>${done ? pp_pill(__("Confirmed"), "green") : pp_pill(__("Awaiting confirmation"), "orange")}</td>` +
				`<td>${pp_esc(c.user_name || c.confirmed_by || "")}</td>` +
				`<td>${c.confirmed_on ? pp_esc(frappe.datetime.str_to_user(c.confirmed_on)) : ""}</td>` +
				`<td>${pp_esc(c.note || "")}</td></tr>`
			);
		})
		.join("");
	return (
		`<div class="table-responsive"><table class="table table-bordered"><thead><tr>` +
		`<th scope="col">${__("Department")}</th><th scope="col">${__("Status")}</th><th scope="col">${__("Confirmed by")}</th>` +
		`<th scope="col">${__("Confirmed on")}</th><th scope="col">${__("Note")}</th></tr></thead><tbody>${rows}</tbody></table></div>`
	);
}

function pp_after(frm, r) {
	frappe.show_alert({ message: __("Moved to {0}", [__(r.message.workflow_state)]), indicator: "green" });
	return frm.reload_doc();
}

function pp_call(frm, args) {
	return frappe.call({ method: PP_API + "apply_action", args: { proposal: frm.doc.name, ...args } }).then((r) => pp_after(frm, r));
}

function pp_save_first(frm) {
	if (!frm.is_dirty()) return Promise.resolve();
	return frm.save();
}

function pp_confirm_dialog(frm, data) {
	const d = new frappe.ui.Dialog({
		title: __("Confirm"),
		fields: [
			...data.my_departments.map((dep) => ({ fieldtype: "Check", fieldname: "dep_" + dep, label: dep, default: 1 })),
			{ fieldtype: "Small Text", fieldname: "note", label: __("Note") },
		],
		primary_action_label: __("Confirm"),
		async primary_action(v) {
			d.hide();
			for (const dep of data.my_departments) {
				if (v["dep_" + dep]) await pp_call(frm, { action: "Xác nhận", department: dep, note: v.note });
			}
		},
	});
	d.show();
}

function pp_approve_dialog(frm, data) {
	const below = data.items.filter((i) => i.below_cost);
	if (!below.length) {
		frappe.confirm(__("Approve this price proposal?"), () => pp_call(frm, { action: "Phê duyệt" }));
		return;
	}
	const d = new frappe.ui.Dialog({
		title: __("Approve"),
		fields: [
			{ fieldtype: "HTML", fieldname: "info", options: `<div class="alert alert-warning" role="alert">${pp_esc(__("Some proposed prices are below full cost; the director must acknowledge each of these lines when approving"))}</div>` },
			...below.map((i) => ({
				fieldtype: "Check",
				fieldname: "ack_" + i.name,
				label: `${i.technical_service} — ${__("Proposed price")} ${pp_money(i.proposed_price)} < ${__("Full cost")} ${pp_money(i.full_cost)}: ${__("I acknowledge this line")}`,
			})),
		],
		primary_action_label: __("Approve"),
		primary_action(v) {
			const acked = below.filter((i) => v["ack_" + i.name]).map((i) => i.name);
			if (acked.length < below.length) {
				frappe.msgprint({ title: __("Cannot approve yet"), message: __("Tick every below-cost line to acknowledge it"), indicator: "red" });
				return;
			}
			d.hide();
			pp_call(frm, { action: "Phê duyệt", acknowledged: JSON.stringify(acked) });
		},
	});
	d.show();
}

function pp_reject(frm) {
	frappe.prompt(
		[{ fieldtype: "Small Text", fieldname: "reason", label: __("Reason"), reqd: 1 }],
		(v) => pp_call(frm, { action: "Từ chối", reason: v.reason }),
		__("Reject"),
		__("Reject")
	);
}

function pp_record_dialog(frm, data) {
	const d = new frappe.ui.Dialog({
		title: __("Record authority decision"),
		size: "large",
		fields: [
			{ fieldtype: "Data", fieldname: "doc_no", label: __("Decision number"), reqd: 1 },
			{ fieldtype: "Date", fieldname: "doc_date", label: __("Decision date"), reqd: 1 },
			{ fieldtype: "Date", fieldname: "apply_from", label: __("Apply from"), default: data.doc.apply_from },
			...data.items.flatMap((i) => [
				{ fieldtype: "Section Break", fieldname: "sb_" + i.name },
				{ fieldtype: "HTML", fieldname: "h_" + i.name, options: `<div><b>${pp_esc(i.technical_service)}</b> — ${__("Submitted price")}: ${pp_money(i.proposed_price)}</div>` },
				{ fieldtype: "Currency", fieldname: "p_" + i.name, label: __("Approved price"), reqd: 1, default: i.proposed_price },
			]),
		],
		primary_action_label: __("Record"),
		primary_action(v) {
			const prices = {};
			data.items.forEach((i) => (prices[i.name] = v["p_" + i.name]));
			d.hide();
			frappe
				.call({
					method: PP_API + "record_authority_result",
					args: { proposal: frm.doc.name, authority_doc_no: v.doc_no, authority_doc_date: v.doc_date, apply_from: v.apply_from, prices: JSON.stringify(prices) },
				})
				.then((r) => pp_after(frm, r));
		},
	});
	d.show();
}

function pp_add_buttons(frm, data) {
	const has = (a) => data.actions.includes(a);
	const guard = (fn) => () => pp_save_first(frm).then(fn);
	if (has("Gửi duyệt")) frm.add_custom_button(__("Submit for review"), guard(() => pp_call(frm, { action: "Gửi duyệt" }).catch(() => {}))).addClass("btn-primary");
	if (has("Xác nhận")) frm.add_custom_button(__("Confirm"), () => pp_confirm_dialog(frm, data)).addClass("btn-primary");
	if (has("Phê duyệt")) frm.add_custom_button(__("Approve"), () => pp_approve_dialog(frm, data)).addClass("btn-primary");
	if (has("Từ chối")) frm.add_custom_button(__("Reject"), () => pp_reject(frm)).addClass("btn-danger");
	if (has("Ghi kết quả phê duyệt")) frm.add_custom_button(__("Record authority decision"), () => pp_record_dialog(frm, data)).addClass("btn-primary");
	frm.add_custom_button(__("Export price comparison"), () => open_url_post("/api/method/" + PP_API + "export_price_comparison", { proposal: frm.doc.name }), __("Export"));
	frm.add_custom_button(__("Open price comparison"), () => frappe.set_route("price-compare", { run: frm.doc.costing_run }), __("View"));
}

function pp_style_grid(frm, data) {
	const by_name = Object.fromEntries(data.items.map((i) => [i.name, i]));
	const grid = frm.fields_dict.items.grid;
	const editable = frm.doc.workflow_state === "Nháp" && frappe.user.has_role("NC Finance");
	grid.cannot_add_rows = true;
	grid.cannot_delete_rows = true;
	const ro = !editable;
	["proposed_price", "adjustment_basis"].forEach((f) => grid.update_docfield_property(f, "read_only", ro ? 1 : 0));
	["authority_price", "director_ack"].forEach((f) => grid.update_docfield_property(f, "hidden", 0));
	grid.update_docfield_property("authority_price", "hidden", PP_AUTHORITY_STATES.includes(frm.doc.workflow_state) ? 0 : 1);
	grid.update_docfield_property("director_ack", "hidden", ["Chờ phê duyệt", "Đã duyệt", "Đã duyệt nội bộ, chờ trình", "Đã được cấp thẩm quyền duyệt"].includes(frm.doc.workflow_state) ? 0 : 1);
	grid.refresh();
	(frm.doc.items || []).forEach((row) => {
		const g = grid.grid_rows_by_docname && grid.grid_rows_by_docname[row.name];
		if (!g) return;
		const info = by_name[row.name] || {};
		const below = flt(row.proposed_price) < flt(row.full_cost);
		const needs_basis = flt(row.proposed_price) !== flt(row.rounded_price) && !(row.adjustment_basis || "").trim();
		const price_cell = g.columns && g.columns.proposed_price;
		const basis_cell = g.columns && g.columns.adjustment_basis;
		if (price_cell) price_cell.find(".nc-pp-pill").remove();
		if (basis_cell) basis_cell.find(".nc-pp-pill").remove();
		if (price_cell && (below || info.below_cost)) price_cell.append(` <span class="nc-pp-pill">${pp_pill(__("Below cost"), "red")}</span>`);
		if (basis_cell && needs_basis) basis_cell.append(` <span class="nc-pp-pill">${pp_pill(__("Basis required"), "orange")}</span>`);
	});
}

frappe.ui.form.on("NC Price Proposal", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.page.set_indicator(frm.doc.workflow_state, PP_STATE_COLOR[frm.doc.workflow_state] || "gray");
		frm.fields_dict.summary_html.$wrapper.attr("aria-busy", "true").html(`<div class="text-muted">${__("Loading…")}</div>`);
		frappe.call({ method: PP_API + "get_proposal", args: { proposal: frm.doc.name } }).then((r) => {
			const data = r.message;
			if (!data || data.doc.name !== frm.doc.name) return;
			frm.nc_proposal = data;
			frm.fields_dict.summary_html.$wrapper.attr("aria-busy", "false").html(pp_summary_html(data));
			frm.set_df_property("confirm_section", "hidden", data.confirmations.length ? 0 : 1);
			frm.fields_dict.department_confirmations.$wrapper.hide();
			let host = frm.fields_dict.confirm_section.wrapper.find(".nc-pp-confirm");
			if (!host.length) host = $('<div class="nc-pp-confirm"></div>').appendTo(frm.fields_dict.confirm_section.wrapper);
			host.html(pp_confirm_html(data));
			pp_add_buttons(frm, data);
			pp_style_grid(frm, data);
		});
	},
	// Nút Hành động của Workflow: dùng hộp thoại của ta, gọi apply_action; từ chối promise để Desk không gọi apply_workflow.
	before_workflow_action(frm) {
		const data = frm.nc_proposal;
		const action = frm.selected_workflow_action;
		if (action === "Xác nhận" && data) pp_confirm_dialog(frm, data);
		else if (action === "Phê duyệt" && data) pp_approve_dialog(frm, data);
		else if (action === "Từ chối") pp_reject(frm);
		else if (action === "Ghi kết quả phê duyệt" && data) pp_record_dialog(frm, data);
		else pp_save_first(frm).then(() => pp_call(frm, { action }));
		return Promise.reject();
	},
	items_on_form_rendered(frm) {
		if (frm.nc_proposal) pp_style_grid(frm, frm.nc_proposal);
	},
});

frappe.ui.form.on("NC Price Proposal Item", {
	proposed_price(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "below_cost", flt(row.proposed_price) < flt(row.full_cost) ? 1 : 0);
		if (frm.nc_proposal) pp_style_grid(frm, frm.nc_proposal);
	},
	adjustment_basis(frm) {
		if (frm.nc_proposal) pp_style_grid(frm, frm.nc_proposal);
	},
});
