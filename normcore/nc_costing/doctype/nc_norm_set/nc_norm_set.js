// Form NC Norm Set (FEAT-012). Sửa dòng ở trang norm-grid; bảng dòng trên form chỉ đọc (ASM-012-16).
// Quyền do máy chủ kiểm; ẩn hiện nút chỉ là tiện ích giao diện.
frappe.ui.form.on("NC Norm Set", {
	refresh(frm) {
		frm.set_df_property("lines", "read_only", 1);
		if (frm.is_new()) return;
		// FEAT-008 (FR-WF-011): dải "Cần cập nhật" khi quy trình có phiên bản ban hành mới
		if (frm.doc.needs_update) {
			frm.dashboard.set_headline_alert(
				frappe.utils.escape_html(__("Needs update: the procedure has a new version - {0}.", [frm.doc.step_change_note || ""])),
				"yellow"
			);
			frappe.db.get_list("NC Clinical Procedure", {
				filters: { technical_service: frm.doc.technical_service, department: frm.doc.department, workflow_state: "Đã ban hành" },
				fields: ["name"],
				order_by: "version_no desc",
				limit: 1,
			}).then((rows) => {
				if (!rows.length) return;
				frm.add_custom_button(__("Compare versions"), () => {
					frappe.set_route("procedure-editor", frm.doc.procedure, "compare", rows[0].name);
				});
			});
		}
		const closed = ["Đã khóa", "Đã thay thế"].includes(frm.doc.status);
		if (closed) {
			frm.dashboard.set_headline(
				__("This record is {0} and cannot be edited. Create a new version in the norm grid.", [__(frm.doc.status)])
			);
		}
		frm.add_custom_button(__("Open norm grid"), () => frappe.set_route("norm-grid", frm.doc.name)).addClass(
			"btn-primary"
		);
		// FEAT-014, AMD-014-01: chỉ điều hướng tới báo cáo; mọi lệnh ghi đi qua normcore.api.time_study.
		if (frm.doc.status === "Nháp" && frappe.model.can_write("NC Norm Set")) {
			frm.add_custom_button(__("Apply time study result"), () =>
				frappe.set_route("query-report", "NC Time Study Result", {
					technical_service: frm.doc.technical_service,
					department: frm.doc.department,
					procedure: frm.doc.procedure,
					norm_set: frm.doc.name,
				})
			);
		}
		if (frm.doc.status === "Đã xác nhận chuyên môn" && frappe.user.has_role("NC Finance")) {
			frm.add_custom_button(__("Lock"), () => {
				frappe.confirm(__("After locking, the norm set can no longer be edited."), () => {
					frappe.call({
						method: "run_doc_method",
						args: { method: "lock", dt: frm.doctype, dn: frm.doc.name },
						freeze: true,
						callback: () => frm.reload_doc(),
					});
				});
			});
		}
	},
});
