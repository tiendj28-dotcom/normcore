// SCR-DSK-020 (FEAT-016): form lần nhập số liệu kế toán (UC-011).
const API = "normcore.api.accounting.";
const CATEGORIES = ["LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT"];
const CATEGORY_HELP = {
	LABOR: "Labor",
	DRUG_SUPPLY: "Drugs and supplies",
	DEPRECIATION: "Depreciation",
	UTILITY: "Utilities",
	MANAGEMENT: "Management",
	EXCLUDED: "Excluded from price",
};

function esc(v) {
	return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
}

function money(v) {
	return frappe.format(v || 0, { fieldtype: "Currency" });
}

function card(title, body) {
	return `<div class="col-sm-4"><div class="frappe-card" style="padding: var(--padding-md);"><div class="text-muted">${title}</div><div class="h4">${body}</div></div></div>`;
}

function totals_matrix(rows, title) {
	if (!rows || !rows.length) return "";
	const centers = [...new Set(rows.map((r) => r.cost_center))];
	const amount = (c, k) => rows.filter((r) => r.cost_center === c && r.cost_category === k).reduce((a, r) => a + Number(r.amount || 0), 0);
	const head = CATEGORIES.map((k) => `<th class="text-right">${esc(k)}</th>`).join("");
	const body = centers
		.map((c) => `<tr><td>${esc(c)}</td>${CATEGORIES.map((k) => `<td class="text-right">${money(amount(c, k))}</td>`).join("")}</tr>`)
		.join("");
	const foot = CATEGORIES.map((k) => `<td class="text-right"><b>${money(centers.reduce((a, c) => a + amount(c, k), 0))}</b></td>`).join("");
	return (
		`<div class="mt-3"><b>${title}</b></div><div class="table-responsive"><table class="table table-bordered">` +
		`<thead><tr><th>${__("Cost center")}</th>${head}</tr></thead><tbody>${body}</tbody>` +
		`<tfoot><tr><td><b>${__("Total")}</b></td>${foot}</tr></tfoot></table></div>`
	);
}

function render_summary(frm, s) {
	const errors = s.errors || [];
	const un = s.unassigned || [];
	const pill = (n, color, none) => (n > 0 ? `<span class="indicator-pill ${color}">${n}</span>` : `<span class="indicator-pill green">${none}</span>`);
	let html =
		`<div class="row">` +
		card(__("Lines / Total amount"), `${s.line_count} / ${money(s.total_amount)}`) +
		card(__("File errors"), pill(s.error_count, "red", __("None"))) +
		card(__("Lines without cost category"), pill(un.length, "orange", __("None"))) +
		`</div>`;
	if (errors.length) {
		const rows = errors.map((e) => `<tr><td>${esc(e.row)}</td><td>${esc(e.column)}</td><td>${esc(e.message)}</td></tr>`).join("");
		const more = s.error_count > errors.length ? `<div class="text-muted">${__("and {0} more errors", [s.error_count - errors.length])}</div>` : "";
		html +=
			`<div class="mt-3"><b>${__("Errors by line")}</b></div><table class="table table-bordered"><thead><tr><th>${__("Excel row")}</th><th>${__("Column")}</th><th>${__("Error")}</th></tr></thead><tbody>${rows}</tbody></table>${more}` +
			`<div class="text-muted">${__("Fix the file, attach it again in Source file and click Reload file, or create a new import.")}</div>`;
	}
	if (un.length) {
		const rows = un.map((u) => `<tr><td>${esc(u.idx)}</td><td>${esc(u.account_code)}</td><td>${esc(u.cost_center)}</td><td class="text-right">${money(u.amount)}</td></tr>`).join("");
		html += `<div class="mt-3"><b>${__("Lines without cost category")}</b></div><table class="table table-bordered"><thead><tr><th>${__("Line")}</th><th>${__("Account")}</th><th>${__("Cost center")}</th><th class="text-right">${__("Amount")}</th></tr></thead><tbody>${rows}</tbody></table>`;
	}
	html += totals_matrix(s.totals, s.status === "Đã chốt" ? __("Totals by cost center and category") : __("Preview: written on finalize"));
	frm.fields_dict.summary_html.$wrapper.html(html);
	frm.dashboard.clear_headline();
	if (s.status === "Đã chốt") {
		frm.dashboard.set_headline_alert(__("Finalized: the figures can be used in a costing run."), "green");
	} else if (s.error_count > 0) {
		frm.dashboard.set_headline_alert(__("The file has {0} error lines: fix the file and reload it. Cannot finalize yet.", [s.error_count]), "red");
	} else if (un.length) {
		frm.dashboard.set_headline_alert(__("{0} lines still have no cost category.", [un.length]), "orange");
	}
}

function load_summary(frm) {
	const wrapper = frm.fields_dict.summary_html.$wrapper;
	wrapper.html(`<div class="text-muted">${__("Loading summary…")}</div>`);
	frappe.call({
		method: API + "get_import_summary",
		args: { name: frm.doc.name },
		callback(r) {
			render_summary(frm, r.message || {});
		},
		error() {
			wrapper.html(`<div class="text-danger">${__("Cannot load the import summary.")} <a class="nc-retry">${__("Retry")}</a></div>`);
			wrapper.find(".nc-retry").on("click", () => load_summary(frm));
		},
	});
}

function call(frm, method, args, done) {
	frappe.call({
		method: API + method,
		args: { name: frm.doc.name, ...args },
		freeze: true,
		callback(r) {
			if (done) done(r.message || {});
			frm.reload_doc();
		},
	});
}

function edit_line_dialog(frm, row) {
	const d = new frappe.ui.Dialog({
		title: __("Edit cost category: line {0}, account {1}", [row.idx, esc(row.account_code)]),
		fields: [
			{ fieldname: "cost_category", fieldtype: "Select", label: __("Cost category"), options: ["", ...CATEGORIES].join("\n"), default: row.cost_category },
			{ fieldname: "is_excluded", fieldtype: "Check", label: __("Excluded"), default: row.is_excluded },
			{ fieldname: "change_reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 },
			{ fieldtype: "HTML", options: `<div class="text-muted">${Object.entries(CATEGORY_HELP).map(([k, v]) => `${k}: ${__(v)}`).join("; ")}</div>` },
		],
		primary_action_label: __("Save"),
		primary_action(values) {
			frappe.call({
				method: API + "update_line",
				args: { name: frm.doc.name, row: row.name, ...values },
				callback() {
					d.hide();
					frm.reload_doc();
				},
			});
		},
	});
	d.show();
}

frappe.ui.form.on("NC Accounting Import", {
	setup(frm) {
		frm.set_query("cost_center", "lines", () => ({}));
	},
	refresh(frm) {
		if (frm.is_new()) {
			frm.set_intro(__("Upload an Excel file by the template (Account code, Account name, Cost center code, Amount) then click Save."));
			return;
		}
		const draft = frm.doc.status === "Nháp";
		frm.fields_dict.lines.grid.cannot_add_rows = true;
		frm.fields_dict.lines.grid.cannot_delete_rows = true;
		frm.fields_dict.lines.grid.update_docfield_property("account_code", "read_only", 1);
		load_summary(frm);
		frm.add_custom_button(__("Download template"), () => window.open(frappe.urllib.get_full_url("/api/method/" + API + "download_template")), __("Actions"));
		if (!draft || !frm.perm[0].write) return;
		frm.page.set_primary_action(__("Finalize"), () => {
			frappe.confirm(__("After finalizing, lines are locked and cannot be reopened. Finalize this import?"), () => call(frm, "finalize"));
		});
		frm.add_custom_button(__("Reapply account mapping"), () =>
			call(frm, "reapply_mapping", {}, (m) => frappe.show_alert({ message: __("Reapplied {0} lines; manual edits are kept", [m.changed]), indicator: "green" })), __("Actions"));
		frm.add_custom_button(__("Reload file"), () =>
			frappe.confirm(__("Reloading replaces all lines and drops manual edits. Continue?"), () => call(frm, "reload_file")), __("Actions"));
		frm.add_custom_button(__("Edit cost category of a line"), () => {
			const sel = frm.fields_dict.lines.grid.get_selected_children() || [];
			if (sel.length === 0) return frappe.msgprint(__("Select one line in the Lines table first."));
			if (sel.length > 1) return frappe.msgprint(__("Select only one line to edit."));
			edit_line_dialog(frm, sel[0]);
		}, __("Actions"));
	},
});
