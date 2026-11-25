// SCR-DSK-021 (FEAT-016): quy tắc phân bổ; tiêu chí và trung tâm theo cấp (BR-COST-009).
const ALL_DRIVERS = ["LABOR_MIN", "MACHINE_MIN", "VOLUME", "DIRECT_COST", "REVENUE", "HEADCOUNT", "AREA"];
const LEVEL1_ONLY = ["REVENUE", "HEADCOUNT", "AREA"];

function apply_level(frm) {
	const level2 = frm.doc.level === "Cấp 2";
	const drivers = level2 ? ALL_DRIVERS.filter((d) => !LEVEL1_ONLY.includes(d)) : ALL_DRIVERS;
	frm.set_df_property("driver", "options", ["", ...drivers].join("\n"));
	if (frm.doc.driver && !drivers.includes(frm.doc.driver)) frm.set_value("driver", "");
	frm.set_query("cost_center", () => ({ filters: { center_type: level2 ? "Lâm sàng" : "Hỗ trợ" } }));
}

frappe.ui.form.on("NC Allocation Rule", {
	refresh: apply_level,
	level: apply_level,
});
