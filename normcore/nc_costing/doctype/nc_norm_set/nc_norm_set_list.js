// SCR-DSK-013: danh sách bộ định mức (FEAT-012). Cột tên hiện chữ thường; nút "Mở lưới" ở mỗi dòng mở trang norm-grid.
frappe.listview_settings["NC Norm Set"] = {
	add_fields: ["status", "needs_update", "test_system"],
	hide_name_column: false,
	get_indicator(doc) {
		const color = { "Nháp": "gray", "Đã xác nhận chuyên môn": "blue", "Đã khóa": "green", "Đã thay thế": "darkgrey" };
		return [__(doc.status), color[doc.status] || "gray", "status,=," + doc.status];
	},
	button: {
		show: () => true,
		get_label: () => __("Open norm grid"),
		get_description: (doc) => __("Open norm grid") + " " + doc.name,
		action: (doc) => frappe.set_route("norm-grid", doc.name),
	},
	formatters: {
		needs_update(value) {
			return value ? '<span class="indicator-pill yellow">' + __("Needs update") + "</span>" : "";
		},
	},
	onload(listview) {
		if (!frappe.model.can_create("NC Norm Set")) return;
		listview.page.add_inner_button(__("Create norm set"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Create norm set"),
				fields: [
					{
						fieldname: "procedure",
						fieldtype: "Link",
						options: "NC Clinical Procedure",
						label: __("Published procedure"),
						reqd: 1,
						get_query: () => ({ filters: { workflow_state: "Đã ban hành" } }),
					},
				],
				primary_action_label: __("Create norm set"),
				primary_action(values) {
					dialog.hide();
					// UC-021: dịch vụ có hệ thống xét nghiệm thì hỏi chọn hệ thống (create_options)
					frappe.require("/assets/normcore/js/norm_create.js", () => normcore.norm.create(values.procedure));
				},
			});
			dialog.show();
		});
	},
};
