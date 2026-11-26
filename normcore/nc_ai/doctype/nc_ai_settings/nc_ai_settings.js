// SCR-DSK-029a: cấu hình AI (FEAT-023). Form chuẩn Desk; khóa không bao giờ hiển thị lại (NFR-SEC-004).
frappe.ui.form.on("NC AI Settings", {
	refresh(frm) {
		frm.trigger("render_status");
		if (frm.doc.__islocal) return;
		if (frappe.model.can_write("NC AI Settings")) {
			frm.add_custom_button(__("Kiểm tra kết nối"), () => frm.trigger("test_connection"));
		}
		frm.add_custom_button(__("Xem nhật ký AI"), () => frappe.set_route("List", "NC AI Log"), __("Liên kết"));
		frm.add_custom_button(__("Mẫu lệnh AI"), () => frappe.set_route("List", "NC Prompt Template"), __("Liên kết"));
	},

	render_status(frm) {
		const field = frm.fields_dict.usage_html;
		if (field) field.$wrapper.html(`<span class="text-muted">${__("Đang tải…")}</span>`);
		frappe.call({
			method: "normcore.api.ai.get_ai_usage",
			callback: (r) => {
				const u = r.message || {};
				const fmt = (n) => format_number(n, null, 0);
				const text = u.budget
					? __("Đã dùng {0} / {1} token — tháng {2}", [fmt(u.used), fmt(u.budget), u.month])
					: __("Đã dùng {0} token — không giới hạn", [fmt(u.used)]);
				if (field) field.$wrapper.html(`<div>${frappe.utils.escape_html(text)}</div>`);
				frm.dashboard.clear_headline();
				if (u.blocked) {
					frm.dashboard.set_headline_alert(
						frappe.utils.escape_html(__("Vượt hạn mức") + ": " + text), "red");
					frm.page.set_indicator(__("Vượt hạn mức"), "red");
				} else if (frm.doc.enabled) {
					frm.dashboard.set_headline_alert(frappe.utils.escape_html(__("AI đang bật")), "green");
					frm.page.set_indicator(__("AI đang bật"), "green");
				} else {
					frm.dashboard.set_headline_alert(
						frappe.utils.escape_html(__("AI đang tắt") + ". " +
							__("Các nút gọi AI đang ẩn; mọi nghiệp vụ làm thủ công được.")), "gray");
					frm.page.set_indicator(__("AI đang tắt"), "gray");
				}
			},
			error: () => {
				if (field) field.$wrapper.html(`<span class="text-muted">${__("Không tải được số liệu sử dụng.")}</span>`);
			},
		});
	},

	test_connection(frm) {
		if (frm.is_dirty()) {
			frappe.msgprint(__("Lưu cấu hình trước khi kiểm tra kết nối."));
			return;
		}
		frappe.call({
			method: "normcore.api.ai.test_connection",
			freeze: true,
			freeze_message: __("Đang kiểm tra kết nối…"),
			callback: (r) => {
				const res = r.message || {};
				if (res.ok) {
					frappe.show_alert({
						message: __("Kết nối thành công ({0} ms)", [res.duration_ms]),
						indicator: "green",
					});
				} else {
					frappe.msgprint({
						title: __("Kiểm tra kết nối thất bại"),
						indicator: "red",
						message: frappe.utils.escape_html(res.message || ""),
					});
				}
			},
		});
	},

	validate(frm) {
		const was = frm.__enabled_before;
		if (was && !frm.doc.enabled && !frm.__confirmed_off) {
			frappe.confirm(
				__("Sau khi tắt, các nút gọi AI bị ẩn với mọi người dùng. Tiếp tục?"),
				() => {
					frm.__confirmed_off = true;
					frm.save();
				}
			);
			frappe.validated = false;
			return;
		}
		frm.__confirmed_off = false;
	},

	onload_post_render(frm) {
		frm.__enabled_before = frm.doc.enabled;
	},

	after_save(frm) {
		frm.__enabled_before = frm.doc.enabled;
		if (frm.doc.enabled) frappe.show_alert({ message: __("Đã bật AI"), indicator: "green" });
	},
});
