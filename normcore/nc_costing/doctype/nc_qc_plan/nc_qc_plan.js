// SCR-DSK-033 (FEAT-032): form kế hoạch chất lượng, số test ước tính, cảnh báo thiếu nội kiểm (FR-QC-001, 002, 007).
const ESTIMATE_API = "normcore.api.qc_plan.estimate_tests";
const WARNING_API = "normcore.api.qc_plan.missing_iqc_warning";
const FIELDS = ["levels", "runs_per_day", "points", "replicates", "calibrations_per_year"];

function plan_payload(frm) {
	const pick = (rows, keys) => (rows || []).map((r) => Object.fromEntries(keys.map((k) => [k, r[k]])));
	return {
		run_days_per_year: frm.doc.run_days_per_year,
		iqc_lines: pick(frm.doc.iqc_lines, ["levels", "runs_per_day"]),
		calibration_lines: pick(frm.doc.calibration_lines, ["points", "replicates", "calibrations_per_year"]),
	};
}

function render_estimate(frm) {
	const wrapper = frm.fields_dict.estimate_html.$wrapper;
	wrapper.find(".nc-qp-state").remove();
	wrapper.append(`<div class="text-muted nc-qp-state">${__("Calculating…")}</div>`);
	frappe.call({
		method: ESTIMATE_API,
		args: { plan: plan_payload(frm) },
		callback(r) {
			if (!r.message) return;
			const fmt = (n) => format_number(n, null, 0);
			const note = r.message.complete
				? ""
				: `<div class="text-muted">${__("Some lines are missing figures")}</div>`;
			wrapper.html(
				`<div><b>${__("Internal QC")}:</b> ${fmt(r.message.iqc_tests)} ${__("tests")}</div>` +
					`<div><b>${__("Calibration")}:</b> ${fmt(r.message.calibration_tests)} ${__("tests")}</div>` +
					note +
					`<div class="text-muted">${__("Used when volumes have no actual internal QC or calibration test counts (FR-QC-006)")}</div>`
			);
		},
		error() {
			wrapper.html(
				`<div class="text-muted">${__("Could not calculate the estimated tests.")} ` +
					`<button class="btn btn-xs btn-default nc-qp-retry">${__("Retry")}</button></div>`
			);
			wrapper.find(".nc-qp-retry").on("click", () => render_estimate(frm));
		},
	});
}

let timer = null;
function schedule_estimate(frm) {
	clearTimeout(timer);
	timer = setTimeout(() => render_estimate(frm), 300);
}

function show_system_info(frm) {
	if (!frm.doc.test_system) return;
	frappe.db
		.get_value("NC Test System", frm.doc.test_system, ["technical_service", "department"])
		.then((r) => {
			const s = r.message;
			if (!s || !s.technical_service) return;
			frappe.db.get_value("NC Technical Service", s.technical_service, "cls_group").then((g) => {
				const group = (g.message && g.message.cls_group) || "";
				frm.set_df_property(
					"test_system",
					"description",
					__("Service {0} — department {1} — group {2}", [s.technical_service, s.department, group])
				);
			});
		});
}

function show_warning(frm) {
	frm.dashboard.clear_headline();
	if (frm.is_new() || !frm.doc.test_system) return;
	frappe.call({
		method: WARNING_API,
		args: { test_system: frm.doc.test_system },
		callback(r) {
			if (r.message && r.message.warning) {
				frm.dashboard.set_headline_alert(frappe.utils.escape_html(r.message.message), "orange");
			}
		},
	});
}

const table_events = {};
FIELDS.forEach((f) => (table_events[f] = (frm) => schedule_estimate(frm)));

frappe.ui.form.on("NC QC Plan", {
	refresh(frm) {
		render_estimate(frm);
		show_system_info(frm);
		show_warning(frm);
	},
	test_system(frm) {
		show_system_info(frm);
	},
	run_days_per_year(frm) {
		schedule_estimate(frm);
	},
	iqc_lines_remove(frm) {
		schedule_estimate(frm);
	},
	calibration_lines_remove(frm) {
		schedule_estimate(frm);
	},
});
frappe.ui.form.on("NC QC IQC Line", { ...table_events, iqc_lines_add: (frm) => schedule_estimate(frm) });
frappe.ui.form.on("NC QC Calibration Line", table_events);
