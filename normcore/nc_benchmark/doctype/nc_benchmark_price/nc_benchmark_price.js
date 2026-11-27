// SCR-DSK-025 (FEAT-026): form giá tham chiếu. Trạng thái chỉ đổi bằng nút để luôn qua API xác nhận.
const API = "normcore.api.benchmark.";

frappe.ui.form.on("NC Benchmark Price", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.trigger("render_headline");
		frm.trigger("render_adjusted");
		if (!frm.perm[0] || !frm.perm[0].write) return;
		const call = (method, args) =>
			frappe.call({ method: API + method, args, freeze: true, callback: () => frm.reload_doc() });
		if (frm.doc.status === "Đề xuất") {
			frm.add_custom_button(__("Confirm"), () => {
				const go = () => call("confirm_prices", { names: [frm.doc.name], technical_service: frm.doc.technical_service });
				frm.is_dirty() ? frm.save().then(go) : go();
			}).addClass("btn-primary");
			frm.add_custom_button(__("Reject"), () => call("reject_prices", { names: [frm.doc.name] }));
		} else {
			frm.add_custom_button(__("Reopen"), () => call("reopen_prices", { names: [frm.doc.name] }), __("Actions"));
		}
	},
	render_headline(frm) {
		if (frm.doc.status !== "Đề xuất") return;
		const msg = frm.doc.technical_service
			? __("Proposed match: {0}. Check and confirm.", [frappe.utils.escape_html(frm.doc.technical_service)])
			: __("No matching service found. Choose a service, then confirm.");
		frm.dashboard.set_headline_alert(msg, "alert-warning");
	},
	render_adjusted(frm) {
		const field = frm.get_field("adjusted_html");
		if (!field) return;
		frappe.call({
			method: API + "get_adjusted_price",
			args: { name: frm.doc.name },
			callback(r) {
				const m = r.message || {};
				let text;
				if (m.adjusted_price === null || m.adjusted_price === undefined) {
					const months = (m.missing || []).map((d) => String(d).slice(0, 7)).join(", ");
					text = __("No CPI for month {0}; price not adjusted", [months]);
				} else {
					text = __("Adjusted to {0}: {1} (index {2} → {3})", [
						String(m.target_month).slice(0, 7),
						format_currency(m.adjusted_price),
						m.index_effective,
						m.index_target,
					]);
				}
				field.$wrapper.html(`<p class="text-muted">${frappe.utils.escape_html(text)}</p>`);
			},
		});
	},
});
