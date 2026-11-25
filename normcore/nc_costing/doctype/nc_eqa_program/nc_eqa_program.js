// SCR-DSK-034 (FEAT-032): form chương trình ngoại kiểm, tóm tắt số mẫu và tỷ lệ (FR-QC-003, 005).
const SUMMARY_API = "normcore.api.qc_plan.eqa_summary";

function payload(frm) {
	return {
		rounds_per_year: frm.doc.rounds_per_year,
		samples_per_round: frm.doc.samples_per_round,
		services: (frm.doc.services || []).map((r) => ({
			technical_service: r.technical_service,
			share_pct: r.share_pct,
		})),
	};
}

function render_summary(frm) {
	const wrapper = frm.fields_dict.summary_html.$wrapper;
	if (!(frm.doc.services || []).length) {
		wrapper.html(`<div class="text-muted">${__("No participating services yet")}</div>`);
		return;
	}
	wrapper.append(`<div class="text-muted">${__("Calculating…")}</div>`);
	frappe.call({
		method: SUMMARY_API,
		args: { program: payload(frm) },
		callback(r) {
			const m = r.message;
			if (!m) return;
			const esc = frappe.utils.escape_html;
			const n = (frm.doc.services || []).length;
			let how;
			if (m.mode === "equal") {
				how = __("Split equally across {0} services ({1}% each)", [n, format_number(100 / n, null, 2)]);
			} else if (m.mode === "custom") {
				how = __("Own shares, total {0}%", [format_number(m.total_pct, null, 2)]);
			} else {
				how = `<span class="indicator-pill orange"><span>${esc(m.message || "")}</span></span>`;
			}
			wrapper.html(
				`<div><b>${__("Samples per year")}:</b> ${format_number(m.samples_per_year, null, 0)}</div>` +
					`<div>${how}</div>`
			);
		},
		error() {
			wrapper.html(
				`<div class="text-muted">${__("Could not calculate the summary.")} ` +
					`<button class="btn btn-xs btn-default nc-eqa-retry">${__("Retry")}</button></div>`
			);
			wrapper.find(".nc-eqa-retry").on("click", () => render_summary(frm));
		},
	});
}

let timer = null;
function schedule(frm) {
	clearTimeout(timer);
	timer = setTimeout(() => render_summary(frm), 300);
}

frappe.ui.form.on("NC EQA Program", {
	setup(frm) {
		frm.set_query("technical_service", "services", () => ({ filters: { is_paraclinical: 1 } }));
	},
	refresh(frm) {
		render_summary(frm);
	},
	rounds_per_year: schedule,
	samples_per_round: schedule,
	services_remove: schedule,
});
frappe.ui.form.on("NC EQA Service", {
	technical_service: (frm) => schedule(frm),
	share_pct: (frm) => schedule(frm),
	services_add: (frm) => schedule(frm),
});
