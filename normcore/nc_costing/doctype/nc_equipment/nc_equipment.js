// SCR-DSK-018 (FEAT-010): form thiết bị, giá trị tạm tính theo ngày hiện tại (FR-RES-006, 007).
const RATE_API = "normcore.api.equipment.get_indicative_rate";

function money(value) {
	return frappe.format(value || 0, { fieldtype: "Currency" });
}

function render_indicative(frm) {
	const wrapper = frm.fields_dict.indicative_html.$wrapper;
	if (frm.is_new()) {
		wrapper.html(`<div class="text-muted">${__("Save to see the indicative values.")}</div>`);
		return;
	}
	wrapper.html(`<div class="text-muted">${__("Loading…")}</div>`);
	frappe.call({
		method: RATE_API,
		args: { equipment: frm.doc.name },
		callback(r) {
			const v = r.message || {};
			const pill = v.expired
				? `<span class="indicator-pill orange">${__("Past useful life")} (${frappe.utils.escape_html(v.expired_mode)})</span>`
				: "";
			const rate =
				v.hourly_rate === null || v.hourly_rate === undefined
					? `<div class="text-muted">${__("Rate per result or minute is computed in the costing run.")}</div>`
					: `<div>${__("Machine hourly rate")}: <b>${frappe.format(v.hourly_rate, { fieldtype: "Float", precision: 4 })}</b></div>`;
			wrapper.html(
				`<div class="text-muted">${__("As of today")} ${frappe.utils.escape_html(v.on || "")}</div>` +
					`<div>${__("Annual depreciation")}: <b>${money(v.annual_depreciation)}</b> ${pill}</div>` +
					`<div>${__("Annual machine cost")}: <b>${money(v.annual_machine_cost)}</b></div>` +
					`<div>${__("Annual equipment cost")}: <b>${money(v.annual_equipment_cost)}</b></div>${rate}`
			);
		},
		error() {
			wrapper.html(`<div class="text-danger">${__("Cannot load the indicative values.")}</div>`);
		},
	});
}

frappe.ui.form.on("NC Equipment", {
	refresh(frm) {
		render_indicative(frm);
	},
});
