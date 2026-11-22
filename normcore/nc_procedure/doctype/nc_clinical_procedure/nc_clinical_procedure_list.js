// SCR-DSK-007: danh sách chuẩn của Desk, chỉ thêm chỉ báo trạng thái.
frappe.listview_settings["NC Clinical Procedure"] = {
	add_fields: ["workflow_state", "needs_review"],
	get_indicator(doc) {
		if (doc.workflow_state === "Đã ban hành") return [__(doc.workflow_state), "green", "workflow_state,=,Đã ban hành"];
		return [__(doc.workflow_state || "Nháp"), "gray", `workflow_state,=,${doc.workflow_state || "Nháp"}`];
	},
};
