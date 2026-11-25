// SCR-DSK-007: danh sách chuẩn của Desk, chỉ thêm chỉ báo trạng thái (màu theo design.md mục 3).
const NC_STATE_COLOR = {
	"Nháp": "gray",
	"Chờ trưởng khoa duyệt": "orange",
	"Chờ hội đồng thẩm định": "orange",
	"Chờ ban hành": "orange",
	"Đã ban hành": "green",
	"Đã thay thế": "darkgrey",
	"Đã thu hồi": "red",
};
frappe.listview_settings["NC Clinical Procedure"] = {
	add_fields: ["workflow_state", "needs_review"],
	get_indicator(doc) {
		const state = doc.workflow_state || "Nháp";
		return [__(state), NC_STATE_COLOR[state] || "gray", `workflow_state,=,${state}`];
	},
};
