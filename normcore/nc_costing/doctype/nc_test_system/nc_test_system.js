// SCR-DSK-032 (FEAT-031): form hệ thống xét nghiệm, khối tình trạng, ngừng dùng / dùng lại (FR-CLS-005, 006, 007).
const STATUS_API = "normcore.api.test_system.get_status";

function render_status(frm) {
	const wrapper = frm.fields_dict.status_html.$wrapper;
	if (frm.is_new()) {
		frm.dashboard.clear_headline();
		wrapper.html(`<div class="text-muted">${__("Save to see the status")}</div>`);
		return;
	}
	const name = frm.doc.name;
	wrapper.html(`<div class="text-muted">${__("Loading status…")}</div>`);
	frappe.call({
		method: STATUS_API,
		args: { test_system: name },
		callback(r) {
			if (frm.doc.name !== name || !r.message) return;
			const esc = frappe.utils.escape_html;
			const cards = r.message.items
				.map(
					(i) =>
						`<div class="nc-ts-card"><b>${esc(i.label)}</b><div>` +
						`<span class="indicator-pill gray"><span>${esc(i.message)}</span></span></div></div>`
				)
				.join("");
			const style =
				"<style>.nc-ts{display:flex;flex-wrap:nowrap;border:1px solid var(--border-color);border-radius:var(--border-radius-md)}" +
				".nc-ts-card{flex:1 1 0;min-width:0;padding:var(--padding-md);border-right:1px solid var(--border-color)}" +
				".nc-ts-card:last-child{border-right:0}" +
				"@media (max-width:768px){.nc-ts{flex-direction:column}.nc-ts-card{border-right:0;border-bottom:1px solid var(--border-color)}}</style>";
			wrapper.html(`${style}<div class="nc-ts">${cards}</div>`);
			frm.dashboard.clear_headline();
			r.message.warnings.forEach((w) => {
				frm.dashboard.set_headline_alert(esc(w.message), w.code === "inactive" ? "gray" : "orange");
			});
		},
		error() {
			if (frm.doc.name !== name) return;
			wrapper.html(
				`<div class="text-muted">${__("Could not load the status.")} ` +
					`<button class="btn btn-xs btn-default nc-ts-retry">${__("Retry")}</button></div>`
			);
			wrapper.find(".nc-ts-retry").on("click", () => render_status(frm));
		},
	});
}

function toggle_minutes(frm) {
	if (!frm.doc.main_equipment) {
		frm.toggle_reqd("machine_minutes_per_case", false);
		return;
	}
	frappe.db.get_value("NC Equipment", frm.doc.main_equipment, "allocation_basis").then((r) => {
		const minute = r.message && r.message.allocation_basis === "Phút chiếm máy";
		frm.toggle_reqd("machine_minutes_per_case", !!minute);
		frm.set_df_property(
			"machine_minutes_per_case",
			"description",
			minute ? __("Equipment is allocated by machine minutes") : ""
		);
	});
}

function change_status(frm, status) {
	if (frm.is_dirty()) {
		frappe.msgprint(__("Save your changes first"));
		return;
	}
	const apply = () => {
		frm.set_value("status", status);
		frm.save();
	};
	if (status === "Ngừng dùng") {
		frappe.confirm(
			__(
				"Deactivate test system {0}? It will not enter new costing runs; existing runs stay unchanged.",
				[frm.doc.name]
			),
			apply
		);
	} else {
		apply();
	}
}

frappe.ui.form.on("NC Test System", {
	refresh(frm) {
		render_status(frm);
		toggle_minutes(frm);
		if (!frm.is_new() && frm.perm[0] && frm.perm[0].write) {
			if (frm.doc.status === "Đang dùng") {
				frm.add_custom_button(__("Deactivate"), () => change_status(frm, "Ngừng dùng"));
			} else {
				frm.add_custom_button(__("Reactivate"), () => change_status(frm, "Đang dùng"));
			}
		}
	},
	main_equipment(frm) {
		toggle_minutes(frm);
	},
});
