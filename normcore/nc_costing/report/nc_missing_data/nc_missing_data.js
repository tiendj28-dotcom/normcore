// SCR-DSK-039 (FEAT-037): báo cáo thiếu dữ liệu của một phạm vi tính giá. Chỉ đọc; chạy được trước khi có lần tính.
const KIND_COLOR = {
	"Thiếu đơn giá": "red",
	"Thiếu sản lượng": "red",
	"Thiếu bấm giờ": "orange",
	"Thiếu kế hoạch chất lượng": "orange",
	"Thiếu hồ sơ tuân thủ": "orange",
};

function esc(v) {
	return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
}

frappe.query_reports["NC Missing Data"] = {
	filters: [
		{ fieldname: "fiscal_year", label: __("Fiscal year"), fieldtype: "Int", reqd: 1, default: new Date().getFullYear() },
		{ fieldname: "volume_scenario", label: __("Volume scenario"), fieldtype: "Select", options: "Thực tế 12 tháng\nKế hoạch\nCông suất", default: "Thực tế 12 tháng" },
		{ fieldname: "costing_date", label: __("Costing date"), fieldtype: "Date", default: frappe.datetime.get_today() },
		{ fieldname: "parameter_set", label: __("Parameter set"), fieldtype: "Link", options: "NC Costing Parameter Set", reqd: 1 },
		{ fieldname: "price_category", label: __("Price category"), fieldtype: "Link", options: "NC Price Category", reqd: 1 },
		{ fieldname: "department", label: __("Department"), fieldtype: "Link", options: "NC Department" },
		{ fieldname: "technical_service", label: __("Service"), fieldtype: "Link", options: "NC Technical Service" },
		{
			fieldname: "kind",
			label: __("Missing"),
			fieldtype: "Select",
			options: "\nThiếu đơn giá\nThiếu sản lượng\nThiếu bấm giờ\nThiếu kế hoạch chất lượng\nThiếu hồ sơ tuân thủ",
		},
	],
	formatter(value, row, column, data, default_formatter) {
		if (data && column.fieldname === "kind") {
			return `<span class="indicator-pill ${KIND_COLOR[data.kind] || "gray"} filterable no-indicator-dot">${esc(data.kind)}</span>`;
		}
		return default_formatter(value, row, column, data);
	},
};
