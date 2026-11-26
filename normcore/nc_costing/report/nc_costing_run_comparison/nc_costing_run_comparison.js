// SCR-DSK-022 (FEAT-018): so sánh hai lần tính giá. Dữ liệu và quyền do normcore.api.costing quyết định.
frappe.query_reports["NC Costing Run Comparison"] = {
	filters: [
		{ fieldname: "base_run", label: __("Base run"), fieldtype: "Link", options: "NC Costing Run", reqd: 1, default: (frappe.route_options || {}).base_run },
		{ fieldname: "other_run", label: __("Compared run"), fieldtype: "Link", options: "NC Costing Run", reqd: 1, default: (frappe.route_options || {}).other_run },
		{ fieldname: "only_changed", label: __("Only services with a difference"), fieldtype: "Check", default: 1 },
		{ fieldname: "technical_service", label: __("Service"), fieldtype: "Link", options: "NC Technical Service" },
	],
	tree: true,
	name_field: "node",
	parent_field: "parent_node",
	initial_depth: 0,
	formatter(value, row, column, data, default_formatter) {
		const out = default_formatter(value, row, column, data);
		if (!data) return out;
		if (column.fieldname === "diff" && value) return `<b>${(value > 0 ? "+" : "") + out.replace("-", "−")}</b>`;
		if (column.fieldname === "note" && data.is_service && data.diff) {
			return `<span class="indicator-pill red filterable no-indicator-dot">${__("Different")}</span> ${out}`;
		}
		return out;
	},
};
