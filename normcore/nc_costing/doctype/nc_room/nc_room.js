// SCR-DSK-018 (FEAT-010): form phòng, đơn giá giờ phòng tạm tính (FR-RES-008, BR-COST-005).
frappe.ui.form.on("NC Room", {
	refresh(frm) {
		if (frm.is_new()) return;
		frappe.call({
			method: "normcore.api.equipment.get_room_rate",
			args: { room: frm.doc.name },
			callback(r) {
				const rate = (r.message || {}).hourly_rate;
				frm.dashboard.set_headline(
					`${__("Room hourly rate")}: <b>${frappe.format(rate, { fieldtype: "Float", precision: 4 })}</b>`
				);
			},
		});
	},
});
