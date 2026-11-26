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
			frm.dashboard.add_comment(__("Create a version from the new procedure in the norm grid."), "yellow", true);
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
		normcore.norm_link.setup(frm);
	},
});

// FEAT-025, AMD-025-02: đề xuất liên kết của AI (FR-AI-007). Chỉ gọi normcore.api.norm_link.*; quyền do máy chủ kiểm.
frappe.provide("normcore.norm_link");
(function () {
	const API = "normcore.api.norm_link.";
	const esc = (v) => frappe.utils.escape_html(v == null ? "" : String(v));

	function call(method, args, callback) {
		frappe.call({ method: API + method, args, freeze: false, callback: (r) => r.message !== undefined && callback(r.message) });
	}

	function watch(frm, job_id) {
		frm.dashboard.set_headline(__("AI is suggesting catalog links…"));
		const timer = setInterval(poll, 3000);
		function done() {
			clearInterval(timer);
			frappe.realtime.off("normcore_ai_link", on_rt);
		}
		function poll() {
			call("get_link_suggestion_status", { job_id }, (st) => {
				if (st.status === "done") {
					done();
					frappe.show_alert({ message: __("{0} suggestions added", [st.suggested || 0]), indicator: "green" });
					frm.reload_doc();
				} else if (st.status === "failed" || st.status === "unknown") {
					done();
					frm.dashboard.set_headline(
						esc(__("AI could not suggest links: {0}. You can link lines manually.", [st.message || ""]))
					);
				}
			});
		}
		function on_rt(msg) {
			if (msg && msg.job_id === job_id) poll();
		}
		frappe.realtime.on("normcore_ai_link", on_rt);
	}

	function open_dialog(frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Link suggestions"),
			size: "extra-large",
			fields: [{ fieldname: "table", fieldtype: "HTML" }],
		});
		function render(data) {
			const rows = data.lines
				.map((l) => {
					const buttons = data.can_edit
						? `<button type="button" class="btn btn-default btn-xs" data-act="accept" data-line="${esc(l.line_id)}" aria-label="${esc(__("Accept") + " " + l.line_id)}">${esc(__("Accept"))}</button> ` +
						  `<button type="button" class="btn btn-default btn-xs" data-act="reject" data-line="${esc(l.line_id)}" aria-label="${esc(__("Remove") + " " + l.line_id)}">${esc(__("Remove"))}</button>`
						: "";
					return (
						`<tr><td>${esc(l.line_id)}</td><td>${esc(l.step_id)}</td><td>${esc(l.resource_text)}</td>` +
						`<td>${esc(l.resource_label)} <span class="indicator-pill purple">${esc(__("Suggested"))}</span></td>` +
						`<td>${esc(l.component)}</td><td title="${esc(__("Suggestion confidence {0}%", [l.ai_confidence]))}">${esc(l.ai_confidence)}%</td><td>${buttons}</td></tr>`
					);
				})
				.join("");
			const head = [__("Line"), __("Step"), __("Name in procedure"), __("Suggested resource"), __("Component"), __("Confidence")]
				.map((h) => `<th>${esc(h)}</th>`)
				.join("");
			const all =
				data.can_edit && data.lines.length
					? `<button type="button" class="btn btn-default btn-sm" data-act="all">${esc(__("Accept all"))}</button>`
					: "";
			const body = data.lines.length
				? `<table class="table table-bordered"><thead><tr>${head}<th></th></tr></thead><tbody>${rows}</tbody></table>${all}`
				: `<p class="text-muted">${esc(__("No AI link suggestions to review"))}</p>`;
			const wrapper = dialog.fields_dict.table.$wrapper;
			wrapper.html(body);
			wrapper.find("button[data-act]").on("click", function () {
				const act = this.dataset.act;
				const after = (d) => {
					render(d);
					frm.reload_doc();
				};
				if (act === "accept") call("accept_link_suggestions", { norm_set: frm.doc.name, line_ids: [this.dataset.line] }, after);
				else if (act === "reject") call("reject_link_suggestion", { norm_set: frm.doc.name, line_id: this.dataset.line }, after);
				else
					frappe.confirm(__("Accept all {0} AI suggestions?", [data.lines.length]), () =>
						call("accept_link_suggestions", { norm_set: frm.doc.name, all: 1 }, after)
					);
			});
		}
		call("list_link_suggestions", { norm_set: frm.doc.name }, (data) => {
			render(data);
			dialog.show();
		});
	}

	normcore.norm_link.setup = function (frm) {
		if (frm.is_new()) return;
		const pending = (frm.doc.lines || []).filter((l) => l.ai_suggested).length;
		if (pending) {
			frm.dashboard.set_headline(esc(__("{0} lines have AI link suggestions to review", [pending])));
			frm.add_custom_button(__("View link suggestions"), () => open_dialog(frm));
		}
		if (frm.doc.status === "Nháp" && frappe.model.can_write("NC Norm Set") && normcore.ai.enabled()) {
			frm.add_custom_button(__("Suggest links"), () =>
				call("start_link_suggestion", { norm_set: frm.doc.name }, (r) => {
					if (r.job_id) watch(frm, r.job_id);
					else frappe.show_alert({ message: r.message, indicator: "blue" });
				})
			);
		}
	};
})();
