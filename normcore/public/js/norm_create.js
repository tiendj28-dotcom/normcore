// Khởi tạo bộ định mức (UC-021, SCR-DSK-013): hỏi create_options, hiện hộp chọn hệ thống xét nghiệm khi cần,
// rồi gọi create_norm_set. Dùng chung cho danh sách NC Norm Set và form quy trình. Chỉ gọi normcore.api.norm.*.
frappe.provide("normcore.norm");

(function () {
	const API = "normcore.api.norm.";

	function error_lines(r) {
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

	function open_set(result) {
		if (result.message) frappe.show_alert({ message: result.message, indicator: "blue" });
		if (result.link_job) frappe.route_options = { link_job: result.link_job }; // FEAT-025: lưới theo dõi tác vụ đề xuất
		frappe.set_route("norm-grid", result.name);
	}

	function create(procedure, test_system, on_error) {
		frappe.call({
			method: API + "create_norm_set",
			args: { procedure, test_system: test_system || null },
			freeze: true,
			silent: true,
			callback: (r) => r.message && open_set(r.message),
			error: (r) => on_error && on_error(error_lines(r).join(" ") || __("Could not complete the request. See the message from the server.")),
		});
	}

	normcore.norm.create = function (procedure) {
		frappe.call({
			method: API + "create_options",
			args: { procedure },
			freeze: true,
			callback(r) {
				const opt = r.message;
				if (!opt) return;
				if (!opt.required) return create(procedure, null, (msg) => frappe.msgprint(msg));
				const note = opt.template ? __("Will add the mandatory items of template {0}.", [opt.template]) : "";
				const dialog = new frappe.ui.Dialog({
					title: __("Choose test system"),
					fields: [
						{
							fieldname: "test_system",
							fieldtype: "Select",
							label: __("Test system"),
							reqd: 1,
							options: [""].concat(opt.test_systems.map((s) => s.name)),
						},
						{ fieldname: "note", fieldtype: "HTML", options: `<p class="text-muted">${frappe.utils.escape_html(note)}</p>` },
						{ fieldname: "errors", fieldtype: "HTML" },
					],
					primary_action_label: __("Create norm set"),
					primary_action(values) {
						create(procedure, values.test_system, (msg) => {
							dialog.fields_dict.errors.$wrapper.html(`<div class="text-danger" role="alert">${frappe.utils.escape_html(msg)}</div>`);
						});
					},
				});
				// Nhãn dạng "GLU-A · EQ_A"; hệ thống đã có bộ đang soạn có chú thích
				const field = dialog.fields_dict.test_system;
				field.$input.find("option").each(function () {
					const s = opt.test_systems.find((x) => x.name === this.value);
					if (s) this.textContent = `${s.name} · ${s.main_equipment || ""}` + (s.open_set ? " " + __("(norm set in progress)") : "");
				});
				dialog.show();
			},
		});
	};
})();
