// SCR-DSK-031 (FEAT-001): NC Admin gán / bỏ gán người dùng vào khoa (FR-ACC-006, UC-017 bước 3).
frappe.ui.form.on("NC Department", {
	refresh(frm) {
		if (frm.is_new() || !frappe.user.has_role("NC Admin")) return;
		frm.add_custom_button(__("Assign user"), () => {
			frappe.prompt(
				{ fieldname: "user", fieldtype: "Link", options: "User", label: __("User"), reqd: 1 },
				(values) =>
					frappe.call({
						method: "normcore.api.access.assign_department",
						args: { user: values.user, department: frm.doc.name },
						freeze: true,
						callback: () => {
							frappe.show_alert({ message: __("User assigned to department."), indicator: "green" });
							frm.trigger("render_users");
						},
					}),
				__("Assign user"),
				__("Assign")
			);
		});
		frm.trigger("render_users");
	},

	render_users(frm) {
		frappe.call({
			method: "normcore.api.access.list_department_users",
			args: { department: frm.doc.name },
			callback: (r) => {
				const users = r.message || [];
				const rows = users.length
					? users
							.map(
								(u) =>
									`<div class="nc-dept-user">${frappe.utils.escape_html(u)} ` +
									`<a href="#" data-user="${frappe.utils.escape_html(u)}">${__("Unassign")}</a></div>`
							)
							.join("")
					: `<div class="text-muted">${__("No users assigned.")}</div>`;
				frm.dashboard.clear_headline();
				frm.dashboard.set_headline(`<b>${__("Assigned users")}</b>${rows}`);
				frm.dashboard.wrapper.find("a[data-user]").on("click", (e) => {
					e.preventDefault();
					frappe.call({
						method: "normcore.api.access.unassign_department",
						args: { user: $(e.currentTarget).data("user"), department: frm.doc.name },
						callback: () => frm.trigger("render_users"),
					});
				});
			},
		});
	},
});
