// SCR-DSK-037 (FEAT-035): form sản lượng cận lâm sàng; báo các cột test phụ để trống (FR-QC-006).
const AUX_LABELS = {
	iqc_tests: "IQC tests",
	calibration_tests: "Calibration tests",
	rerun_tests: "Rerun tests",
	eqa_tests: "EQA tests",
};

frappe.ui.form.on("NC Test System Volume", {
	refresh(frm) {
		frm.dashboard.clear_headline();
		const blank = Object.keys(AUX_LABELS).filter((f) => frm.doc[f] === null || frm.doc[f] === undefined || frm.doc[f] === "");
		if (!frm.is_new() && blank.length) {
			const names = blank.map((f) => __(AUX_LABELS[f])).join(", ");
			frm.dashboard.set_headline_alert(
				frappe.utils.escape_html(
					__("Blank columns will be estimated from the quality plan when costing: {0}.", [names])
				),
				"orange"
			);
		}
	},
});
