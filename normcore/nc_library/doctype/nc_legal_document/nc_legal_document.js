// SCR-DSK-003 (FEAT-020): form văn bản, trạng thái lập chỉ mục và danh sách mục.
const VALIDITY_COLOR = { "Còn hiệu lực": "green", "Chưa hiệu lực": "blue", "Hết hiệu lực": "gray" };
const INDEX_COLOR = { "Chưa lập": "gray", "Đang lập": "orange", "Đã lập": "green", Lỗi: "red" };
const SECTION_PAGE = 100;
const POLL_MS = 10000;
const POLL_MAX = 30;

function pill(color, text) {
	return `<span class="indicator-pill ${color || "gray"} ellipsis"><span>${frappe.utils.escape_html(text || "")}</span></span>`;
}

function render_sections(frm, start, rows_so_far) {
	const $w = frm.fields_dict.sections_html.$wrapper;
	if (frm.is_new()) {
		$w.empty();
		return;
	}
	frappe.call({
		method: "normcore.api.library.get_sections",
		args: { legal_document: frm.doc.name, start: start, page_length: SECTION_PAGE },
		callback(r) {
			const res = r.message || { rows: [], total: 0 };
			if (!start) $w.empty();
			if (!res.total) {
				const waiting = ["Chưa lập", "Đang lập", "Lỗi"].includes(frm.doc.index_status);
				$w.html(`<p class="text-muted">${waiting ? __("No sections yet") : __("No sections found in the file")}</p>`);
				return;
			}
			if (!start) {
				$w.html(
					`<table class="table table-bordered"><thead><tr><th>${__("Section")}</th><th>${__("Heading")}</th>` +
						`<th>${__("Pages")}</th><th>${__("Validity")}</th><th></th></tr></thead><tbody></tbody></table>`
				);
			}
			const $body = $w.find("tbody");
			res.rows.forEach((s) => {
				const pages = s.page_from ? `${s.page_from}–${s.page_to || s.page_from}` : "—";
				const $tr = $(
					`<tr><td>${frappe.utils.escape_html(s.section_no)}</td><td>${frappe.utils.escape_html(s.heading || "")}</td>` +
						`<td>${pages}</td><td>${pill(VALIDITY_COLOR[s.validity_status], __(s.validity_status || ""))}</td>` +
						`<td><a href="#" class="nc-view">${__("View")}</a></td></tr>`
				);
				$tr.find(".nc-view").on("click", (e) => {
					e.preventDefault();
					frappe.set_route("Form", "NC Legal Section", s.name);
				});
				$body.append($tr);
			});
			const shown = rows_so_far + res.rows.length;
			$w.find(".nc-more").remove();
			if (shown < res.total) {
				const $more = $(`<button class="btn btn-default btn-sm nc-more">${__("More")}</button>`);
				$more.on("click", () => render_sections(frm, shown, shown));
				$w.append($more);
			}
		},
	});
}

// SCR-DSK-004 (FEAT-022): bảng ánh xạ hướng dẫn với dịch vụ trong form văn bản.
const MAP_PAGE = 100;
const MAP_STATUS_COLOR = { "Đề xuất": "gray", "Đã xác nhận": "green" };

function confidence_color(c) {
	return c >= 100 ? "green" : c >= 70 ? "blue" : "yellow";
}

function map_call(frm, method, args, done, opts) {
	frappe.call(Object.assign({ method: "normcore.api.library." + method, args: args, callback: done }, opts || {}));
}

function map_dialog(frm, title, section, row, after) {
	const d = new frappe.ui.Dialog({
		title: title,
		fields: [
			{
				fieldname: "technical_service",
				label: __("Technical service"),
				fieldtype: "Link",
				options: "NC Technical Service",
				reqd: 1,
				get_query: () => ({ filters: { is_active: 1 } }),
			},
			{ fieldtype: "HTML", options: `<p class="text-muted small">${__("Saving confirms the mapping.")}</p>` },
		],
		primary_action_label: __("Save"),
		primary_action(v) {
			map_call(
				frm,
				"save_mapping",
				{ section: section, technical_service: v.technical_service, row: row || null },
				() => {
					d.hide();
					frappe.show_alert({ message: __("Mapping saved"), indicator: "green" });
					after();
				}
			);
		},
	});
	d.show();
}

function render_mappings(frm, start) {
	const $w = frm.fields_dict.mapping_html.$wrapper;
	if (frm.is_new() || !frm.doc.is_procedure_guideline) {
		$w.empty();
		return;
	}
	if (frm.doc.index_status !== "Đã lập") {
		$w.html(`<p class="text-muted">${__("Mappings are available after indexing finishes.")}</p>`);
		return;
	}
	const can_write = !!(frm.perm[0] && frm.perm[0].write);
	if (frm._nc_unconf === undefined) frm._nc_unconf = 1;
	const reload = () => render_mappings(frm, 0);
	map_call(
		frm,
		"get_mappings",
		{ legal_document: frm.doc.name, unconfirmed_only: frm._nc_unconf, start: start, page_length: MAP_PAGE },
		(r) => {
			const res = r.message || { rows: [], total: 0, pending_exact: 0 };
			if (!start) {
				$w.html(
					`<div class="nc-map-bar form-inline" style="gap: var(--margin-md); margin-bottom: var(--margin-md)"></div>` +
						`<div class="table-responsive"><table class="table table-bordered nc-map-table"><thead><tr>` +
						(can_write ? `<th></th>` : "") +
						`<th>${__("Section")}</th><th>${__("Heading")}</th><th>${__("Technical service")}</th>` +
						`<th>${__("Confidence")}</th><th>${__("Status")}</th>` +
						(can_write ? `<th>${__("Actions")}</th>` : "") +
						`</tr></thead><tbody></tbody></table></div><div class="nc-map-foot"></div>`
				);
				const $bar = $w.find(".nc-map-bar");
				const $chk = $(
					`<label class="checkbox"><input type="checkbox" class="nc-map-filter" ${frm._nc_unconf ? "checked" : ""}> ` +
						`${__("Unconfirmed only")}</label>`
				);
				$chk.find("input").on("change", (e) => {
					frm._nc_unconf = e.target.checked ? 1 : 0;
					reload();
				});
				$bar.append($chk);
				if (can_write) {
					if (res.pending_exact) {
						const $b = $(`<button class="btn btn-primary btn-sm">${__("Confirm all 100% ({0})", [res.pending_exact])}</button>`);
						$b.on("click", () =>
							frappe.confirm(__("Confirm {0} suggestions with 100% confidence?", [res.pending_exact]), () =>
								map_call(frm, "confirm_exact", { legal_document: frm.doc.name }, (x) => {
									frappe.show_alert({ message: __("Confirmed {0} mapping(s)", [x.message.confirmed]), indicator: "green" });
									reload();
								}, { freeze: true })
							)
						);
						$bar.append($b);
					}
					const $sel = $(`<button class="btn btn-default btn-sm nc-map-sel" disabled>${__("Confirm selected")}</button>`);
					$sel.on("click", () => {
						const rows = $w.find(".nc-map-pick:checked").map((i, e) => $(e).data("row")).get();
						map_call(frm, "confirm_mappings", { legal_document: frm.doc.name, rows: rows }, (x) => {
							frappe.show_alert({ message: __("Confirmed {0} mapping(s)", [x.message.confirmed]), indicator: "green" });
							reload();
						}, { freeze: true });
					});
					const $again = $(`<button class="btn btn-default btn-sm">${__("Suggest again")}</button>`);
					$again.on("click", () =>
						frappe.confirm(
							__("Recalculate suggestions? Confirmed mappings are kept; current suggestions are replaced."),
							() => map_call(frm, "suggest_mappings", { legal_document: frm.doc.name }, (x) => {
								frappe.show_alert({ message: __("{0} suggestions created", [x.message.suggested]), indicator: "green" });
								reload();
							}, { freeze: true })
						)
					);
					$bar.append($sel, $again);
				}
			}
			const $body = $w.find("tbody");
			if (!start && !res.rows.length) {
				$w.find(".nc-map-table").hide();
				$w.find(".nc-map-foot").html(
					`<p class="text-muted">${frm._nc_unconf ? __("All sections are confirmed.") : __("No suggestions found. Use + Add service on each section or Suggest again.")}</p>`
				);
				return;
			}
			res.rows.forEach((sec) => {
				const rows = sec.mappings.length ? sec.mappings : [null];
				rows.forEach((m, i) => {
					const $tr = $("<tr></tr>");
					if (can_write) {
						$tr.append(
							m && m.mapping_status === "Đề xuất"
								? $(`<td><input type="checkbox" class="nc-map-pick" aria-label="${__("Select")}"></td>`).find("input").data("row", m.row).end()
								: "<td></td>"
						);
					}
					if (i === 0) {
						$tr.append(
							$(`<td rowspan="${rows.length}"><a href="#" class="nc-map-sec">${frappe.utils.escape_html(sec.section_no)}</a></td>`),
							`<td rowspan="${rows.length}">${frappe.utils.escape_html(sec.heading || "")}</td>`
						);
						$tr.find(".nc-map-sec").on("click", (e) => {
							e.preventDefault();
							frappe.set_route("Form", "NC Legal Section", sec.section);
						});
					}
					if (m) {
						const conf = m.confidence
							? `<span class="indicator-pill ${confidence_color(m.confidence)} ellipsis"><span>${m.confidence}%</span></span>`
							: __("Manual");
						let st = `<span class="indicator-pill ${MAP_STATUS_COLOR[m.mapping_status] || "gray"} ellipsis"><span>${__(m.mapping_status)}</span></span>`;
						if (m.mapping_status === "Đã xác nhận" && m.confirmed_by) {
							st += `<div class="text-muted small">${frappe.utils.escape_html(frappe.user.full_name(m.confirmed_by))}, ${frappe.datetime.str_to_user(m.confirmed_on)}</div>`;
						}
						$tr.append(
							`<td><a href="/app/nc-technical-service/${encodeURIComponent(m.technical_service)}">${frappe.utils.escape_html(m.technical_service)}</a> — ${frappe.utils.escape_html(m.service_name || "")}</td>`,
							`<td>${conf}</td>`,
							`<td>${st}</td>`
						);
					} else {
						$tr.append("<td>—</td><td></td><td></td>");
					}
					if (can_write) {
						const $act = $("<td></td>");
						if (m && m.mapping_status === "Đề xuất") {
							const $c = $(`<button class="btn btn-default btn-xs">${__("Confirm")}</button>`);
							$c.on("click", () => map_call(frm, "confirm_mappings", { legal_document: frm.doc.name, rows: [m.row] }, (x) => {
								frappe.show_alert({ message: __("Confirmed {0} mapping(s)", [x.message.confirmed]), indicator: "green" });
								reload();
							}));
							$act.append($c, " ");
						}
						if (m) {
							const $e = $(`<button class="btn btn-default btn-xs">${__("Change")}</button>`);
							$e.on("click", () => map_dialog(frm, __("Change service"), sec.section, m.row, reload));
							const $r = $(`<button class="btn btn-default btn-xs">${__("Remove")}</button>`);
							$r.on("click", () =>
								frappe.confirm(__("Remove this mapping?"), () =>
									map_call(frm, "remove_mapping", { row: m.row }, () => {
										frappe.show_alert({ message: __("Mapping removed"), indicator: "green" });
										reload();
									})
								)
							);
							$act.append($e, " ", $r, " ");
						}
						if (i === rows.length - 1) {
							const $a = $(`<button class="btn btn-default btn-xs">${__("+ Add service")}</button>`);
							$a.on("click", () => map_dialog(frm, __("Add service"), sec.section, null, reload));
							$act.append($a);
						}
						$tr.append($act);
					}
					$body.append($tr);
				});
			});
			$w.find(".nc-map-pick").off("change").on("change", () => {
				$w.find(".nc-map-sel").prop("disabled", !$w.find(".nc-map-pick:checked").length);
			});
			const shown = start + res.rows.length;
			$w.find(".nc-map-more").remove();
			if (shown < res.total) {
				const $more = $(`<button class="btn btn-default btn-sm nc-map-more">${__("More")}</button>`);
				$more.on("click", () => render_mappings(frm, shown));
				$w.append($more);
			}
		}
	);
}

function set_headline(frm) {
	frm.dashboard.clear_headline();
	if (frm.is_new()) return;
	const st = frm.doc.index_status;
	if (st === "Chưa lập" || st === "Đang lập") {
		frm.dashboard.set_headline_alert(__("Indexing in progress. Sections will appear when it finishes."), "orange");
	} else if (st === "Lỗi") {
		frm.dashboard.set_headline_alert(
			__("Indexing failed: {0}", [frappe.utils.escape_html(frm.doc.index_error || "")]) +
				" " + __("Replace the file or click Re-index."),
			"red"
		);
	}
}

// SCR-DSK-003 (FEAT-021): khai báo thay thế và khối "Bị thay thế bởi" (FR-LIB-007, FR-LIB-008).
function user_date(d) {
	return frappe.datetime.str_to_user(d);
}

function render_superseded_by(frm) {
	const $w = frm.fields_dict.superseded_by_html.$wrapper;
	$w.empty();
	if (frm.is_new()) return;
	frappe.call({
		method: "normcore.api.library.get_supersessions",
		args: { legal_document: frm.doc.name },
		callback(r) {
			const rows = (r.message || {}).superseded_by || [];
			if (!rows.length) return;
			const esc = frappe.utils.escape_html;
			const items = rows
				.map((x) => {
					const scope = x.scope === "Một phần" ? `${__("Sections")}: ${esc(x.sections)}` : __("Whole document");
					return (
						`<li><a href="/app/nc-legal-document/${encodeURIComponent(x.document)}">${esc(x.doc_number || x.document)}</a>` +
						` — ${esc(x.title || "")}, ${scope}, ${__("from")} ${user_date(x.from_date)}</li>`
					);
				})
				.join("");
			$w.html(`<p class="text-muted">${__("Superseded by")}</p><ul>${items}</ul>`);
		},
	});
}

function supersession_dialog(frm) {
	const state = { indexed: true };
	const note = (d) => {
		const v = d.get_values(true) || {};
		const $n = d.fields_dict.note.$wrapper;
		if (!v.superseded_document || !v.from_date) {
			$n.html("");
			return;
		}
		const exp = frappe.datetime.add_days(v.from_date, -1);
		$n.html(
			`<p class="text-muted small">${__("{0} will expire from {1} (expiry date {2})", [
				frappe.utils.escape_html(v.superseded_document),
				user_date(v.from_date),
				user_date(exp),
			])}</p>`
		);
	};
	const load_sections = (d) => {
		const b = d.get_value("superseded_document");
		const f = d.fields_dict.sections;
		if (!b) {
			f.df.options = [];
			f.refresh();
			return;
		}
		frappe.call({
			method: "normcore.api.library.get_sections",
			args: { legal_document: b, start: 0, page_length: 500 },
			callback(r) {
				const rows = (r.message || {}).rows || [];
				state.indexed = rows.length > 0;
				f.df.options = rows.map((x) => ({ label: `${x.section_no} — ${x.heading || ""}`, value: x.section_no }));
				f.refresh();
				d.fields_dict.no_index.$wrapper.html(
					state.indexed ? "" : `<p class="text-muted">${__("Document has no sections indexed, sections cannot be chosen")}</p>`
				);
				toggle(d);
			},
		});
	};
	const toggle = (d) => {
		const part = d.get_value("scope") === "Một phần";
		d.set_df_property("sections", "hidden", part && state.indexed ? 0 : 1);
		d.fields_dict.no_index.$wrapper.toggle(part && !state.indexed);
	};
	const d = new frappe.ui.Dialog({
		title: __("Declare supersession"),
		fields: [
			{
				fieldname: "superseded_document",
				label: __("Superseded document"),
				fieldtype: "Link",
				options: "NC Legal Document",
				reqd: 1,
				get_query: () => ({ filters: { name: ["!=", frm.doc.name] } }),
				onchange() {
					load_sections(d);
					note(d);
				},
			},
			{
				fieldname: "scope",
				label: __("Scope"),
				fieldtype: "Select",
				options: ["Toàn bộ", "Một phần"],
				default: "Toàn bộ",
				reqd: 1,
				onchange() {
					toggle(d);
				},
			},
			{ fieldname: "no_index", fieldtype: "HTML" },
			{ fieldname: "sections", label: __("Superseded sections"), fieldtype: "MultiCheck", options: [], hidden: 1, columns: 2 },
			{
				fieldname: "from_date",
				label: __("From date"),
				fieldtype: "Date",
				reqd: 1,
				onchange() {
					note(d);
				},
			},
			{ fieldname: "note", fieldtype: "HTML" },
		],
		primary_action_label: __("Declare"),
		primary_action(v) {
			const part = v.scope === "Một phần";
			const sections = part ? d.fields_dict.sections.get_checked_options() : [];
			if (part && !sections.length) {
				frappe.msgprint(__("Choose at least one section"));
				return;
			}
			frappe.confirm(
				__(
					"After declaring, {0} (or the chosen sections) will expire from {1}; issued procedures that cite it will be flagged for review.",
					[frappe.utils.escape_html(v.superseded_document), user_date(v.from_date)]
				),
				() => {
					d.disable_primary_action();
					frappe.call({
						method: "normcore.api.library.declare_supersession",
						args: {
							legal_document: frm.doc.name,
							superseded_document: v.superseded_document,
							scope: v.scope,
							from_date: v.from_date,
							sections: sections,
						},
						freeze: true,
						callback() {
							d.hide();
							frappe.show_alert({ message: __("Supersession declared"), indicator: "green" });
							frm.reload_doc();
						},
						error() {
							d.enable_primary_action();
						},
					});
				}
			);
		},
	});
	d.show();
}

function setup_supersession(frm) {
	render_superseded_by(frm);
	if (!frm.is_new() && frm.perm[0] && frm.perm[0].write) {
		frm.add_custom_button(__("Declare supersession"), () => supersession_dialog(frm));
	}
}

frappe.ui.form.on("NC Legal Document", {
	refresh(frm) {
		frm.set_intro("");
		if (frm.doc.validity_status) {
			frm.page.set_indicator(__(frm.doc.validity_status), VALIDITY_COLOR[frm.doc.validity_status] || "gray");
		}
		set_headline(frm);
		render_sections(frm, 0, 0);
		render_mappings(frm, 0);
		setup_supersession(frm);
		if (!frm.is_new() && frm.perm[0] && frm.perm[0].write && frm.doc.index_status !== "Đang lập") {
			frm.add_custom_button(
				__("Re-index"),
				() => {
					frappe.confirm(
						__("Re-index this document? Manual edits to section text will be overwritten (kept in version history)."),
						() => {
							frappe.call({
								method: "normcore.api.library.reindex",
								args: { legal_document: frm.doc.name },
								freeze: true,
								callback() {
									frm.reload_doc();
								},
							});
						}
					);
				},
				__("Actions")
			);
		}
		// tự làm mới khi còn đang lập chỉ mục (tối đa 30 lần, mỗi 10 giây)
		clearTimeout(frm._nc_poll);
		if (!frm.is_new() && ["Chưa lập", "Đang lập"].includes(frm.doc.index_status)) {
			frm._nc_polls = (frm._nc_polls || 0) + 1;
			if (frm._nc_polls <= POLL_MAX) {
				frm._nc_poll = setTimeout(() => {
					if (cur_frm && cur_frm.doc && cur_frm.doc.name === frm.doc.name) frm.reload_doc();
				}, POLL_MS);
			}
		} else {
			frm._nc_polls = 0;
		}
	},
	before_unload(frm) {
		clearTimeout(frm._nc_poll);
	},
});
