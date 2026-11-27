// SCR-DSK-027 (FEAT-030): danh sách phương án giá, nhãn trạng thái theo design.md mục 3.
frappe.listview_settings["NC Price Proposal"] = {
	add_fields: ["workflow_state"],
	get_indicator(doc) {
		const map = {
			"Nháp": [__("Draft proposal"), "gray"],
			"Chờ khoa xác nhận": [__("Awaiting department confirmation"), "orange"],
			"Chờ phê duyệt": [__("Awaiting approval"), "orange"],
			"Đã duyệt": [__("Approved"), "green"],
			"Đã duyệt nội bộ, chờ trình": [__("Approved internally, awaiting submission"), "blue"],
			"Đã được cấp thẩm quyền duyệt": [__("Approved by the authority"), "green"],
		};
		const [label, color] = map[doc.workflow_state] || [doc.workflow_state, "gray"];
		return [label, color, `workflow_state,=,${doc.workflow_state}`];
	},
};
