// Form Desk quy trình. Quyền do máy chủ kiểm; ẩn hiện nút chỉ là tiện ích giao diện.
// Chuyển trạng thái đi qua api.procedure_workflow.apply_action (ASM-007-13), không qua apply_workflow của Desk.
const NC_WF = "normcore.api.procedure_workflow.";
const NC_CLOSED = ["Đã ban hành", "Đã thay thế", "Đã thu hồi"];

function nc_error_lines(r) {
	try {
		return JSON.parse(r._server_messages)
			.map((m) => (typeof m === "string" && m.startsWith("{") ? JSON.parse(m).message : m))
			.flatMap((m) => String(m).split(/<br\s*\/?>/i))
			.map((m) => m.replace(/<[^>]*>/g, "").trim())
			.filter(Boolean);
	} catch (e) {
		return [];
	}
}

// Hộp thoại theo hành động; trả promise hoàn tất khi máy chủ đã chuyển trạng thái.
function nc_apply_action(frm, action) {
	return new Promise((resolve, reject) => {
		const fields = [];
		if (action === "Từ chối") fields.push({ fieldname: "reason", fieldtype: "Small Text", label: __("Rejection reason"), reqd: 1 });
		if (action === "Ban hành") {
			fields.push({ fieldname: "decision_no", fieldtype: "Data", label: __("Decision number"), reqd: 1, default: frm.doc.decision_no });
			fields.push({ fieldname: "effective_date", fieldtype: "Date", label: __("Effective date"), reqd: 1, default: frm.doc.effective_date || frappe.datetime.get_today() });
			fields.push({ fieldname: "note", fieldtype: "HTML", options: "<p>" + frappe.utils.escape_html(__("After issuing, the content of this version cannot be edited.")) + "</p>" });
		}
		if (action === "Gửi duyệt") {
			fields.push({ fieldname: "note", fieldtype: "HTML", options: "<p>" + frappe.utils.escape_html(__("After submitting, the procedure cannot be edited until it is returned.")) + "</p>" });
		}
		fields.push({ fieldname: "errors", fieldtype: "HTML" });
		const dialog = new frappe.ui.Dialog({
			title: __(action),
			fields,
			primary_action_label: __(action),
			primary_action(values) {
				frappe.call({
					method: NC_WF + "apply_action",
					args: { procedure: frm.doc.name, action, ...values },
					freeze: true,
					silent: true,
					callback: (r) => {
						dialog.hide();
						frappe.show_alert({ message: __("Moved to") + " " + __(r.message.workflow_state), indicator: "green" });
						frm.reload_doc();
						resolve(r.message);
					},
					error: (r) => {
						const lines = nc_error_lines(r || {});
						const items = (lines.length ? lines : [__("Could not complete this action")]).map((l) => "<li>" + frappe.utils.escape_html(l) + "</li>");
						dialog.fields_dict.errors.$wrapper.html('<div role="alert"><ul>' + items.join("") + "</ul></div>");
					},
				});
			},
		});
		dialog.onhide = () => reject();
		dialog.show();
	});
}

function nc_download(frm, method) {
	window.open("/api/method/" + NC_WF + method + "?procedure=" + encodeURIComponent(frm.doc.name));
}

frappe.ui.form.on("NC Clinical Procedure", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Open editor"), () => {
			frappe.set_route("procedure-editor", frm.doc.name);
		});
		frm.add_custom_button(__("Print PDF"), () => nc_download(frm, "download_pdf"), __("Export"));
		frm.add_custom_button(__("Download DOCX"), () => nc_download(frm, "download_docx"), __("Export"));

		if (frm.doc.workflow_state !== "Nháp") {
			frm.dashboard.set_headline(
				NC_CLOSED.includes(frm.doc.workflow_state)
					? __("This procedure is issued or closed and cannot be edited. Create a new version in the revision function.")
					: __("This procedure is awaiting approval and cannot be edited.")
			);
		}

		if (frm.doc.workflow_state === "Chờ ban hành" && frappe.user.has_role("NC Director")) {
			frm.add_custom_button(__("Publish"), () => {
				if (frm.is_dirty()) {
					frappe.msgprint(__("Save the form first."));
					return;
				}
				nc_apply_action(frm, "Ban hành").catch(() => {});
			}).addClass("btn-primary");
		}

		if (frm.doc.workflow_state === "Đã ban hành" && frappe.model.can_create("NC Norm Set")) {
			frm.add_custom_button(__("Create norm set"), () => {
				frappe.call({
					method: "normcore.nc_costing.doctype.nc_norm_set.nc_norm_set.make_norm_set",
					args: { procedure: frm.doc.name },
					freeze: true,
					callback: (r) => {
						if (r.message) frappe.set_route("Form", "NC Norm Set", r.message);
					},
				});
			}).addClass("btn-primary");
		}
	},

	// Nút Hành động của Workflow: dùng hộp thoại của ta, gọi apply_action; từ chối promise để Desk không gọi apply_workflow.
	before_workflow_action(frm) {
		const action = frm.selected_workflow_action;
		return nc_apply_action(frm, action).then(
			() => Promise.reject(),
			() => Promise.reject()
		);
	},
});
