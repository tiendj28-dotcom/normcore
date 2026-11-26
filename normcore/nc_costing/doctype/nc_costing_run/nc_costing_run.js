// SCR-DSK-022 (FEAT-015): form lần tính giá (UC-012).
const API = "normcore.api.costing.";
const PROGRESS_EVENT = "normcore_costing_progress";
const LOCK_METHOD = "normcore.api.costing.lock_run"; // FEAT-017: khoa sau khi đối soát
const RECON_REPORT = "NC Reconciliation";
const PHYSICAL_REPORT = "NC Physical Reconciliation"; // FEAT-037
const MISSING_REPORT = "NC Missing Data"; // FEAT-037
const DUPLICATE_METHOD = "normcore.api.costing.duplicate_run"; // FEAT-018
const VERIFY_METHOD = "normcore.api.costing.verify_snapshot";
const COMPARE_REPORT = "NC Costing Run Comparison";
const RESULT_COLOR = { "Thành công": "green", "Cảnh báo": "yellow", "Lỗi": "red" };

function esc(v) {
	return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
}

function money(v) {
	return frappe.format(v || 0, { fieldtype: "Currency" });
}

function num(v, digits) {
	return Number(v || 0).toLocaleString("vi-VN", { minimumFractionDigits: digits || 0, maximumFractionDigits: digits || 0 });
}

function render_run_warnings(section, data) {
	const items = (data.run && data.run.run_warnings) || [];
	if (!items.length) return "";
	const li = items.map((w, i) => `<li${i >= 5 ? ' class="nc-more" style="display:none"' : ""}>${esc(w)}</li>`).join("");
	const more = items.length > 5 ? ` <a href="#" class="nc-show-more">${__("Show more")}</a>` : "";
	return (
		`<div class="alert alert-warning" role="status"><b>${__("The costing run has {0} warnings and was still costed", [items.length])}</b>` +
		`<ul style="margin:4px 0 0 16px">${li}</ul>${more}</div>`
	);
}

function render_systems(rows) {
	const cls = rows.filter((x) => x.is_paraclinical && x.test_systems && x.test_systems.length);
	if (!cls.length) return "";
	let body = "";
	cls.forEach((x) => {
		body += `<tr class="active"><td colspan="7"><b>${esc(x.service)} — ${esc(x.service_name || "")} · ${esc(x.department_name || x.department)}</b> ${__("Weighted average + external quality assessment = direct cost of the service")}: ${money(x.eqa_cost)}</td></tr>`;
		x.test_systems.forEach((t) => {
			const est = t.k_estimated ? ` <span class="indicator-pill orange">${__("Estimated from plan")}</span>` : "";
			const low = t.low_volume_warning ? `<span class="indicator-pill yellow">${__("Low volume")}</span>` : "";
			body +=
				`<tr data-name="${esc(x.name)}" tabindex="0" style="cursor:pointer"><td>${esc(t.test_system)}</td>` +
				`<td><a href="/app/nc-norm-set/${encodeURIComponent(t.norm_set || "")}">${esc(t.norm_set || "")}</a></td>` +
				`<td class="text-right">${num(t.patient_results)}</td><td class="text-right">${num(t.share_pct, 2)}%</td>` +
				`<td class="text-right">${num(t.k_factor, 6)}${est}</td><td class="text-right">${money(t.direct_cost)}</td><td>${low}</td></tr>`;
		});
	});
	return (
		`<details open class="mt-3"><summary><b>${__("Results by test system")}</b></summary>` +
		`<div class="table-responsive"><table class="table table-bordered"><thead><tr>` +
		`<th>${__("Test system")}</th><th>${__("Norm set")}</th><th class="text-right">${__("Patient results")}</th><th class="text-right">${__("Share")}</th>` +
		`<th class="text-right">${__("k factor")}</th><th class="text-right">${__("Direct cost per result")}</th><th>${__("Warning")}</th></tr></thead><tbody>${body}</tbody></table></div></details>`
	);
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
		const h = frm.doc.snapshot_hash;
		const msg = h
			? __("Locked · snapshot {0}. It cannot be recalculated or edited; duplicate it to create a new costing run.", [h.slice(0, 12)])
			: __("Locked (no input snapshot). It cannot be recalculated or edited; duplicate it to create a new costing run.");
		frm.dashboard.set_headline_alert(msg, "green");
	}
}

function render_allocation_warnings(frm) {
	frm.toggle_display("allocation_warnings", false);
	const lines = (frm.doc.allocation_warnings || "").split("\n").filter((x) => x.trim());
	if (!lines.length || !["Đã tính", "Đã khóa"].includes(frm.doc.status)) return;
	const items = lines.map((x) => `<li>${esc(x)}</li>`).join("");
	frm.dashboard.add_section(
		`<div class="alert alert-warning" role="alert"><b>${__("Allocation warnings")}</b><ul>${items}</ul></div>`,
		__("Allocation warnings")
	);
}

function open_reconciliation(frm) {
	frappe.route_options = { costing_run: frm.doc.name };
	frappe.set_route("query-report", RECON_REPORT);
}

function open_physical(frm) {
	frappe.route_options = { costing_run: frm.doc.name };
	frappe.set_route("query-report", PHYSICAL_REPORT);
}

function open_missing(frm) {
	const one = (rows, field) => (rows && rows.length === 1 ? rows[0][field] : undefined);
	frappe.route_options = {
		fiscal_year: frm.doc.fiscal_year,
		costing_date: frm.doc.costing_date,
		parameter_set: frm.doc.parameter_set,
		price_category: frm.doc.price_category,
		volume_scenario: frm.doc.volume_scenario,
		department: one(frm.doc.scope_departments, "department"),
		technical_service: one(frm.doc.scope_services, "technical_service"),
	};
	frappe.set_route("query-report", MISSING_REPORT);
}

function render_physical_banner(section, data) {
	const n = data.physical_unreconciled || 0;
	if (!n) return "";
	return (
		`<div class="alert alert-danger" role="alert"><b>${__("Material reconciliation pending")}</b>: ` +
		`${__("{0} departments have no stock issue data. NC Finance must confirm with a reason before the costing run can be locked.", [n])} ` +
		`<a href="#" class="nc-open-physical">${__("Material and volume reconciliation")}</a></div>`
	);
}

function lock_run(frm) {
	frappe.call({
		method: API + "get_run_results",
		args: { run: frm.doc.name },
		callback(r) {
			const n = (r.message || {}).recon_blocked || 0;
			if (n) {
				frappe.msgprint({
					title: __("Cannot lock"),
					indicator: "red",
					message:
						`${__("{0} reconciliation lines are over tolerance or not reconciled and have no explanation.", [n])} ` +
						`<a href="#" class="open-recon">${__("Reconciliation table")}</a> · <a href="#" class="open-physical">${__("Material and volume reconciliation")}</a>`,
				});
				$(".msgprint .open-recon").on("click", (e) => {
					e.preventDefault();
					open_reconciliation(frm);
				});
				$(".msgprint .open-physical").on("click", (e) => {
					e.preventDefault();
					open_physical(frm);
				});
				return;
			}
			frappe.confirm(
				`${__("Lock costing run {0}? It cannot be recalculated and explanations cannot be edited afterwards.", [frm.doc.name])} ${__("The system will recalculate from the current data to check, then save the input snapshot.")}`,
				() => {
					frappe.call({
						method: LOCK_METHOD,
						args: { run: frm.doc.name },
						freeze: true,
						freeze_message: __("Saving the input snapshot…"),
						callback() {
							frappe.show_alert({ message: __("Locked."), indicator: "green" });
							frm.reload_doc();
						},
						error() {
							frappe.msgprint({ title: __("Cannot lock"), indicator: "red", message: __("The lock was refused. If the inputs changed after the run, run costing again, then lock.") });
						},
					});
				}
			);
		},
	});
}

function duplicate_run(frm) {
	frappe.confirm(__("Create a new costing run in Draft with the same inputs and scope? Results, reconciliation and the snapshot are not copied."), () => {
		frappe.call({
			method: DUPLICATE_METHOD,
			args: { run: frm.doc.name },
			freeze: true,
			callback(r) {
				const name = (r.message || {}).name;
				if (!name) return;
				frappe.show_alert({ message: __("Created {0}", [name]), indicator: "green" });
				frappe.set_route("Form", "NC Costing Run", name);
			},
		});
	});
}

function verify_snapshot(frm) {
	frappe.call({
		method: VERIFY_METHOD,
		args: { run: frm.doc.name },
		freeze: true,
		freeze_message: __("Recalculating from the snapshot…"),
		callback(r) {
			const m = r.message || {};
			if (m.ok) {
				frappe.msgprint({
					title: __("Reproduction matches"),
					indicator: "green",
					message: __("Recalculating from the snapshot (schema {0}) matches the locked results in every field: {1} services, {2} explanation lines, {3} reconciliation lines.", [m.version, m.services, m.lines, m.recon_lines]),
				});
				return;
			}
			const items = (m.diffs || []).map((x) => `<li>${esc(x)}</li>`).join("");
			frappe.msgprint({
				title: __("Reproduction does not match"),
				indicator: "red",
				message: `<div role="alert"><div style="max-height:50vh;overflow:auto"><ul>${items}</ul></div><b>${__("Total {0} differences", [m.diff_count || 0])}</b></div>`,
			});
		},
	});
}

function compare_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Compare with another costing run"),
		fields: [
			{
				fieldtype: "Link",
				fieldname: "other_run",
				label: __("Costing run to compare"),
				options: "NC Costing Run",
				reqd: 1,
				get_query: () => ({ filters: { status: ["in", ["Đã tính", "Đã khóa"]], name: ["!=", frm.doc.name] }, order_by: "modified desc" }),
			},
		],
		primary_action_label: __("Compare"),
		primary_action(values) {
			d.hide();
			frappe.set_route("query-report", COMPARE_REPORT, { base_run: frm.doc.name, other_run: values.other_run });
		},
	});
	d.show();
}

function add_lock_buttons(frm) {
	if (frm.doc.status !== "Đang tính") {
		frappe.call({
			method: API + "get_run_results",
			args: { run: frm.doc.name },
			callback(r) {
				if (!(r.message || {}).can_duplicate) return;
				frm.add_custom_button(__("Duplicate"), () => duplicate_run(frm)).addClass(frm.doc.status === "Đã khóa" ? "btn-primary" : "btn-default");
			},
		});
	}
	if (frm.doc.status === "Đã khóa" && frm.doc.snapshot_file) {
		frm.add_custom_button(__("Check reproduction"), () => verify_snapshot(frm));
	}
	if (["Đã tính", "Đã khóa"].includes(frm.doc.status)) {
		frm.add_custom_button(__("Compare with another run"), () => compare_dialog(frm));
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
			frm.toggle_display("run_warnings", Boolean(frm.doc.run_warnings));
			if (!rows.length) {
				section.html(`<div class="text-muted">${__("No results yet.")}</div>`);
				return;
			}
			const counts = Object.keys(RESULT_COLOR)
				.filter((k) => data.counts[k])
				.map((k) => `<span class="indicator-pill ${RESULT_COLOR[k]}">${esc(k)}: ${data.counts[k]}</span>`)
				.join(" ");
			const blocked = data.recon_blocked || 0;
			const blocked_pill = blocked
				? ` <span class="indicator-pill red">${__("{0} reconciliation lines need an explanation", [blocked])}</span>`
				: "";
			const btn = frm.custom_buttons && frm.custom_buttons[__("Reconciliation table")];
			if (btn && blocked) btn.text(`${__("Reconciliation table")} (${blocked})`);
			const warn = !rows.some((x) => x.has_allocation)
				? `<div class="alert alert-warning" role="alert">${__("No shared allocation yet: the shared cost allocation is added by FEAT-017.")}</div>`
				: "";
			const body = rows
				.map((x) => {
					const msg = x.calc_message || "";
					const tag = x.is_paraclinical ? ` <span class="indicator-pill blue">${__("Paraclinical")}</span>` : "";
					return (
						`<tr data-name="${esc(x.name)}" tabindex="0" style="cursor:pointer">` +
						`<td>${esc(x.service)}</td><td>${esc(x.service_name)}${tag}</td><td>${esc(x.department_name || x.department)}</td>` +
						`<td><span class="indicator-pill ${RESULT_COLOR[x.calc_status] || "gray"}">${esc(x.calc_status)}</span>` +
						`${x.has_volume_warning ? ` <span class="indicator-pill yellow">${__("Volume 0")}</span>` : ""}</td>` +
						`<td title="${esc(msg)}">${esc(msg.length > 80 ? msg.slice(0, 80) + "…" : msg)}</td>` +
						`<td class="text-right">${money(x.full_cost)}</td><td class="text-right">${money(x.calculated_price)}</td>` +
						`<td class="text-right"><b>${money(x.rounded_price)}</b></td></tr>`
					);
				})
				.join("");
			section.html(
				render_run_warnings(section, data) +
				render_physical_banner(section, data) +
				`<div>${__("{0} services", [rows.length])} · ${counts}${blocked_pill}</div>${warn}` +
					`<div class="table-responsive"><table class="table table-bordered"><thead><tr>` +
					`<th>${__("Service code")}</th><th>${__("Service")}</th><th>${__("Department")}</th><th>${__("Result")}</th><th>${__("Message")}</th>` +
					`<th class="text-right">${__("Full cost")}</th><th class="text-right">${__("Calculated price")}</th><th class="text-right">${__("Rounded price")}</th>` +
					`</tr></thead><tbody>${body}</tbody></table></div>` +
					render_systems(rows)
			);
			section.find(".nc-open-physical").on("click", (e) => {
				e.preventDefault();
				open_physical(frm);
			});
			section.find(".nc-show-more").on("click", function (e) {
				e.preventDefault();
				section.find(".nc-more").show();
				$(this).hide();
			});
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
			const rerun =
				frm.doc.status === "Đã tính"
					? ` ${__("The old results of this run will be replaced.")} ${__("Existing reconciliation lines and explanations will be replaced.")}`
					: "";
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
			}).addClass(frm.doc.status === "Đã tính" ? "btn-default" : "btn-primary");
		}

		if (["Đã tính", "Đã khóa"].includes(frm.doc.status)) {
			frm.add_custom_button(__("View costing results"), () => {
				frappe.set_route("List", "NC Service Cost", { costing_run: frm.doc.name });
			});
			frm.add_custom_button(__("Reconciliation table"), () => open_reconciliation(frm));
			frm.add_custom_button(__("Material and volume reconciliation"), () => open_physical(frm));
		}
		frm.add_custom_button(__("Missing data report"), () => open_missing(frm));
		if (frm.doc.status === "Đã tính" && can_write(frm)) {
			frm.add_custom_button(__("Lock"), () => lock_run(frm)).addClass("btn-primary");
		}
		add_lock_buttons(frm);
		if (frm.doc.status === "Đã khóa") frm.disable_form();
		render_allocation_warnings(frm);
		render_results(frm);
	},
});
