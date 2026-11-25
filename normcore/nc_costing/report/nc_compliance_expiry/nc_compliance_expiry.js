// SCR-DSK-036 (FEAT-033): báo cáo hạn hồ sơ tuân thủ.
frappe.query_reports["NC Compliance Expiry"] = {
	filters: [
		{ fieldname: "as_of", label: __("As of date"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
		{ fieldname: "department", label: __("Department"), fieldtype: "Link", options: "NC Department" },
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Hết hạn", "Sắp hết hạn", "Thiếu hồ sơ còn hạn"],
		},
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "status" && data) {
			const colors = { "Hết hạn": "red", "Sắp hết hạn": "orange", "Thiếu hồ sơ còn hạn": "red" };
			const color = colors[data.status] || "gray";
			value = `<span class="indicator-pill ${color} filterable no-indicator-dot">${value}</span>`;
		}
		return value;
	},
};
