// SCR-DSK-022 (FEAT-015): form lần tính giá (UC-012).
const API = "normcore.api.costing.";
const PROGRESS_EVENT = "normcore_costing_progress";
const RESULT_COLOR = { "Thành công": "green", "Cảnh báo": "yellow", "Lỗi": "red" };

function esc(v) {
	return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
}

function money(v) {
	return frappe.format(v || 0, { fieldtype: "Currency" });
}

function can_write(frm) {
	return Boolean(frm.perm[0] && frm.perm[0].write);
}

function finish(frm) {
	frm.reload_doc().then(() => {
		if (frm.doc.status === "Đã tính") {
			frappe.show_alert({ message: __("Costing completed."), indicator: "green" });
		} else if (frm.doc.status === "Tính lỗi") {
			frappe.show_alert({ message: __("Costing failed."), indicator: "red" });
		}
	});
}

function poll_progress(frm) {
	if (frm.__costing_timer) clearTimeout(frm.__costing_timer);
	if (frm.doc.status !== "Đang tính") return;
	frm.__costing_timer = setTimeout(() => {
		frappe.call({
			method: API + "get_progress",
			args: { run: frm.doc.name },
			callback(r) {
				const m = r.message || {};
				if (m.status === "Đang tính") {
					frm.dashboard.show_progress(__("Costing progress"), m.progress || 0, __("Costing… {0}%", [m.progress || 0]));
					poll_progress(frm);
				} else {
					finish(frm);
				}
			},
		});
	}, 5000);
}

function render_progress(frm) {
	frm.dashboard.hide_progress();
	if (frm.doc.status !== "Đang tính") return;
	const pct = frm.doc.progress || 0;
	frm.dashboard.show_progress(__("Costing progress"), pct, __("Costing… {0}%", [pct]));
	frm.dashboard.set_headline_alert(__("Costing… {0}%", [pct]), "orange");
	poll_progress(frm);
}

function render_status_banner(frm) {
	frm.dashboard.clear_headline();
	if (frm.doc.status === "Tính lỗi") {
		frm.dashboard.set_headline_alert(__("The costing run failed. See Error Log or run it again."), "red");
	} else if (frm.doc.status === "Đã tính") {
		frm.dashboard.set_headline_alert(__("To change the inputs, duplicate the costing run."), "blue");
	} else if (frm.doc.status === "Đã khóa") {
		frm.dashboard.set_headline_alert(__("This record is locked and cannot be edited."), "green");
	}
}

function render_results(frm) {
	if (!["Đã tính", "Tính lỗi", "Đã khóa"].includes(frm.doc.status)) return;
	const section = frm.dashboard.add_section(`<div class="text-muted">${__("Loading results…")}</div>`, __("Costing results"));
	frappe.call({
		method: API + "get_run_results",
		args: { run: frm.doc.name },
		callback(r) {
			const data = r.message || { results: [], counts: {} };
			const rows = data.results;
			if (!rows.length) {
				section.html(`<div class="text-muted">${__("No results yet.")}</div>`);
				return;
			}
			const counts = Object.keys(RESULT_COLOR)
				.filter((k) => data.counts[k])
				.map((k) => `<span class="indicator-pill ${RESULT_COLOR[k]}">${esc(k)}: ${data.counts[k]}</span>`)
				.join(" ");
			const warn = rows.some((x) => !x.has_allocation && x.calc_status !== "Lỗi")
				? `<div class="alert alert-warning" role="alert">${__("No shared allocation yet: the shared cost allocation is added by FEAT-017.")}</div>`
				: "";
			const body = rows
				.map((x) => {
					const msg = x.calc_message || "";
					return (
						`<tr data-name="${esc(x.name)}" tabindex="0" style="cursor:pointer">` +
						`<td>${esc(x.service)}</td><td>${esc(x.service_name)}</td><td>${esc(x.department_name || x.department)}</td>` +
						`<td><span class="indicator-pill ${RESULT_COLOR[x.calc_status] || "gray"}">${esc(x.calc_status)}</span></td>` +
						`<td title="${esc(msg)}">${esc(msg.length > 80 ? msg.slice(0, 80) + "…" : msg)}</td>` +
						`<td class="text-right">${money(x.full_cost)}</td><td class="text-right">${money(x.calculated_price)}</td>` +
						`<td class="text-right"><b>${money(x.rounded_price)}</b></td></tr>`
					);
				})
				.join("");
			section.html(
				`<div>${__("{0} services", [rows.length])} · ${counts}</div>${warn}` +
					`<div class="table-responsive"><table class="table table-bordered"><thead><tr>` +
					`<th>${__("Service code")}</th><th>${__("Service")}</th><th>${__("Department")}</th><th>${__("Result")}</th><th>${__("Message")}</th>` +
					`<th class="text-right">${__("Full cost")}</th><th class="text-right">${__("Calculated price")}</th><th class="text-right">${__("Rounded price")}</th>` +
					`</tr></thead><tbody>${body}</tbody></table></div>`
			);
			section.find("tr[data-name]").on("click keydown", function (e) {
				if (e.type === "keydown" && e.key !== "Enter") return;
				frappe.set_route("Form", "NC Service Cost", $(this).attr("data-name"));
			});
		},
	});
}

function start(frm, confirm) {
	frappe.call({
		method: API + "start_costing",
		args: { run: frm.doc.name, confirm_ineligible: confirm ? 1 : 0 },
		freeze: true,
		freeze_message: __("Costing…"),
		callback(r) {
			if (r.message && r.message.enqueued) {
				frappe.show_alert({ message: __("The costing run is running in the background."), indicator: "orange" });
				frm.reload_doc();
			} else {
				finish(frm);
			}
		},
	});
}

function ask_to_run(frm) {
	frappe.call({
		method: API + "check_scope",
		args: { run: frm.doc.name },
		callback(r) {
			const s = r.message || { eligible: [], ineligible: [] };
			const n = s.eligible.length;
			const rerun = frm.doc.status === "Đã tính" ? ` ${__("The old results of this run will be replaced.")}` : "";
			if (!s.ineligible.length) {
				if (!n) {
					frappe.msgprint(__("No service is eligible to be costed."));
					return;
				}
				const bg = s.background ? ` ${__("The run will go to the background and show progress.")}` : "";
				frappe.confirm(`${__("Cost {0} services?", [n])}${bg}${rerun}`, () => start(frm, false));
				return;
			}
			const list = s.ineligible
				.map((x) => `<li>${esc(x.service)} — ${esc(x.service_name || "")} · ${esc(x.department_name || x.department || "")}</li>`)
				.join("");
			const d = new frappe.ui.Dialog({
				title: __("{0} services have no locked norm set", [s.ineligible.length]),
				fields: [
					{
						fieldtype: "HTML",
						fieldname: "list",
						options:
							`<ul style="max-height:240px;overflow:auto">${list}</ul>` +
							`<div>${n ? __("Only {0} eligible services will be costed.", [n]) : __("No service is eligible to be costed.")}${rerun}</div>`,
					},
				],
				primary_action_label: __("Cost eligible services only"),
				primary_action() {
					d.hide();
					start(frm, true);
				},
				secondary_action_label: __("Cancel"),
				secondary_action() {
					d.hide();
				},
			});
			if (!n) d.get_primary_btn().hide();
			d.show();
		},
	});
}

frappe.ui.form.on("NC Costing Run", {
	setup(frm) {
		frm.set_query("accounting_import", () => ({ filters: { status: "Đã chốt" } }));
		frappe.realtime.on(PROGRESS_EVENT, (data) => {
			if (data && data.run === frm.doc.name) {
				frm.dashboard.show_progress(__("Costing progress"), data.progress, __("Costing… {0}%", [data.progress]));
				if (data.progress >= 100) finish(frm);
			}
		});
	},
	refresh(frm) {
		frm.toggle_display("progress", frm.doc.status === "Đang tính");
		if (frm.is_new()) return;
		render_status_banner(frm);
		render_progress(frm);

		if (["Nháp", "Tính lỗi", "Đã tính"].includes(frm.doc.status) && can_write(frm)) {
			frm.add_custom_button(__("Run costing"), () => {
				if (frm.is_dirty()) {
					frappe.msgprint(__("Save the form first."));
					return;
				}
				ask_to_run(frm);
			}).addClass("btn-primary");
		}

		if (frm.doc.status === "Đã tính") {
			frm.add_custom_button(__("View costing results"), () => {
				frappe.set_route("List", "NC Service Cost", { costing_run: frm.doc.name });
			});
		}
		render_results(frm);
	},
});
