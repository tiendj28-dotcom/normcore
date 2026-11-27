// FEAT-038 (FR-AI-016..018, UC-025; SCR-DSK-014, SCR-DSK-033): đề xuất định mức của AI từ tài liệu của hãng.
// Dùng chung cho form NC QC Plan và NC Norm Set. Chỉ gọi normcore.api.cls_norm_ai.*; quyền do máy chủ kiểm,
// ẩn hiện nút chỉ là tiện ích giao diện (can_edit, can_accept do máy chủ tính).
frappe.provide("normcore.cls_norm_ai");
(function () {
	const API = "normcore.api.cls_norm_ai.";
	const esc = (v) => frappe.utils.escape_html(v == null ? "" : String(v));
	const POLL_MS = 3000;
	const QUOTE_MAX = 200;
	const TYPE_ORDER = ["Lượng hóa chất mỗi test", "Tần suất chuẩn máy", "Tần suất nội kiểm", "Hạn dùng sau mở"];

	function call(method, args, callback, error) {
		frappe.call({
			method: API + method,
			args,
			freeze: false,
			silent: !!error,
			callback: (r) => r.message !== undefined && callback(r.message),
			error: error,
		});
	}

	function pill(color, text) {
		return `<span class="indicator-pill ${color} ellipsis"><span>${esc(text)}</span></span>`;
	}

	function status_pill(row) {
		if (row.status === "Đã chấp nhận") return pill("green", __(row.status));
		if (row.status === "Đã bỏ") return pill("darkgrey", __(row.status));
		return pill("purple", __("Suggested"));
	}

	function basis_cell(row) {
		if (row.relation !== "Theo hướng dẫn") return pill("red", __("No basis yet"));
		const quote = row.quote || "";
		const short = quote.length > QUOTE_MAX;
		const link = `<a href="/app/nc-legal-section/${encodeURIComponent(row.legal_section)}" target="_blank">${esc(row.doc_number || "")} – ${esc(__("section"))} ${esc(row.section_no)}</a>`;
		const text = short ? esc(quote.slice(0, QUOTE_MAX)) + "…" : esc(quote);
		const more = short
			? ` <a href="#" class="nc-more" data-full="${esc(quote)}">${esc(__("Show more"))}</a>`
			: "";
		return `${pill("green", __("Follows guideline"))} ${link}<blockquote class="text-muted small">${text}${more}</blockquote>`;
	}

	function target_cell(row) {
		if (row.not_in_catalog || !row.resource) {
			return `${esc(row.resource_text)} ${pill("orange", __("Not in catalog"))}`;
		}
		return `${esc(row.resource)} – ${esc(row.resource_label || row.resource_text)}`;
	}

	function target_name(row) {
		if (row.suggestion_type === "Lượng hóa chất mỗi test") return __("the draft norm set");
		if (row.suggestion_type === "Hạn dùng sau mở") return __("the item catalog");
		return __("the quality plan");
	}

	function actions_cell(row) {
		if (row.status !== "Đề xuất") return "";
		const name = esc(row.name);
		const out = [];
		if (row.not_in_catalog || !row.resource) {
			if (row.can_edit)
				out.push(`<button type="button" class="btn btn-default btn-xs" data-act="link" data-name="${name}" aria-label="${esc(__("Link") + " " + row.resource_text)}">${esc(__("Link"))}</button>`);
		} else if (row.can_accept) {
			out.push(`<button type="button" class="btn btn-primary btn-xs" data-act="accept" data-name="${name}" aria-label="${esc(__("Accept") + " " + row.resource_text)}">${esc(__("Accept"))}</button>`);
		}
		if (row.can_edit)
			out.push(`<button type="button" class="btn btn-default btn-xs" data-act="reject" data-name="${name}" aria-label="${esc(__("Reject") + " " + row.resource_text)}">${esc(__("Reject"))}</button>`);
		return out.join(" ");
	}

	function render_table(data) {
		if (!data.rows.length) return `<p class="text-muted">${esc(__("No pending AI suggestions."))}</p>`;
		const groups = TYPE_ORDER.map((t) => ({ type: t, rows: data.rows.filter((r) => r.suggestion_type === t) })).filter((g) => g.rows.length);
		const head = [__("Item or equipment"), __("Suggested value"), __("Basis"), __("Status"), __("Actions")]
			.map((h, i) => `<th${i === 1 ? ' class="text-right"' : ""}>${esc(h)}</th>`)
			.join("");
		const body = groups
			.map((g) => {
				const rows = g.rows
					.map(
						(r) =>
							`<tr${r.status === "Đề xuất" ? ' style="background: var(--highlight-color)"' : ""}>` +
							`<td>${target_cell(r)}</td>` +
							`<td class="text-right">${esc(format_number(r.value, null, 4))} ${esc(r.uom || "")}</td>` +
							`<td>${basis_cell(r)}</td><td>${status_pill(r)}</td><td>${actions_cell(r)}</td></tr>`
					)
					.join("");
				return `<tr><th colspan="5">${esc(__(g.type))}</th></tr>${rows}`;
			})
			.join("");
		return `<div style="max-height: 60vh; overflow-y: auto"><table class="table table-bordered"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
	}

	function link_dialog(row, done) {
		const d = new frappe.ui.Dialog({
			title: __("Link to catalog"),
			fields: [
				{ fieldname: "resource_doctype", label: __("Catalog"), fieldtype: "Select", options: "NC Item\nNC Equipment", default: "NC Item", reqd: 1 },
				{ fieldname: "resource", label: __("Item or equipment"), fieldtype: "Dynamic Link", options: "resource_doctype", reqd: 1 },
			],
			primary_action_label: __("Link"),
			primary_action(v) {
				call("link_cls_norm_suggestion", { name: row.name, resource_doctype: v.resource_doctype, resource: v.resource }, () => {
					d.hide();
					done();
				});
			},
		});
		d.show();
	}

	function open_dialog(frm, test_system) {
		const dialog = new frappe.ui.Dialog({
			title: __("AI norm suggestions"),
			size: "extra-large",
			fields: [
				{ fieldname: "scope", fieldtype: "Select", label: __("Show"), options: "Pending\nAll", default: "Pending" },
				{ fieldname: "table", fieldtype: "HTML" },
			],
		});
		const wrapper = () => dialog.fields_dict.table.$wrapper;
		function load() {
			wrapper().html(`<p class="text-muted">${esc(__("Loading…"))}</p>`);
			const status = dialog.get_value("scope") === "All" ? "all" : "Đề xuất";
			call(
				"list_cls_norm_suggestions",
				{ test_system, status },
				(data) => {
					wrapper().html(render_table(data));
					bind(data);
				},
				() => wrapper().html(`<p class="text-danger">${esc(__("Could not load the suggestions."))}</p>`)
			);
		}
		function after() {
			load();
			frm.reload_doc();
		}
		function bind(data) {
			wrapper().find("a.nc-more").on("click", function (e) {
				e.preventDefault();
				$(this).closest("blockquote").text($(this).data("full"));
			});
			wrapper().find("button[data-act]").on("click", function () {
				const row = data.rows.find((r) => r.name === this.dataset.name);
				if (!row) return;
				if (this.dataset.act === "accept") {
					frappe.confirm(
						__("Apply {0} = {1} {2} to {3}?", [__(row.suggestion_type), format_number(row.value, null, 4), row.uom || "", target_name(row)]),
						() =>
							call("accept_cls_norm_suggestion", { name: row.name }, () => {
								frappe.show_alert({ message: __("Suggestion applied"), indicator: "green" });
								after();
							})
					);
				} else if (this.dataset.act === "reject") {
					call("reject_cls_norm_suggestion", { name: row.name }, load);
				} else {
					link_dialog(row, load);
				}
			});
		}
		dialog.fields_dict.scope.df.onchange = load;
		dialog.show();
		load();
	}

	function watch(frm, test_system, job_id, btn) {
		const timer = setInterval(poll, POLL_MS);
		function stop() {
			clearInterval(timer);
			frappe.realtime.off("normcore_cls_norm_ai", on_rt);
			btn && btn.prop("disabled", false).text(__("AI norm suggestion"));
		}
		function poll() {
			call("get_cls_norm_suggestion_status", { job_id }, (st) => {
				if (st.status === "done") {
					stop();
					frappe.show_alert({
						message: __("{0} suggestions created ({1} without basis, {2} not in catalog)", [st.created || 0, st.unsupported || 0, st.not_in_catalog || 0]),
						indicator: "green",
					});
					frm.reload_doc();
					open_dialog(frm, test_system);
				} else if (st.status === "failed" || st.status === "unknown") {
					stop();
					frappe.msgprint({
						indicator: "red",
						title: __("AI suggestion failed"),
						message: esc(st.message || "") + "<br>" + esc(__("Your data is unchanged.")),
					});
				}
			});
		}
		function on_rt(msg) {
			if (msg && msg.job_id === job_id) poll();
		}
		frappe.realtime.on("normcore_cls_norm_ai", on_rt);
	}

	// Dải riêng, không dùng headline của form: FEAT-025 và FEAT-032 cũng đặt headline và ghi đè lẫn nhau.
	function draw_strip(frm, data, test_system) {
		$(frm.layout.wrapper).find(".nc-cls-ai-strip").remove();
		if (!data.pending) return;
		const $strip = $(
			`<div class="nc-cls-ai-strip alert alert-info" role="status">` +
				`${pill("purple", __("Suggested"))} ${esc(__("{0} AI suggestions not yet processed", [data.pending]))} ` +
				`<a href="#" class="nc-review">${esc(__("Review"))}</a></div>`
		);
		$strip.find(".nc-review").on("click", (e) => {
			e.preventDefault();
			open_dialog(frm, test_system);
		});
		$(frm.layout.wrapper).prepend($strip);
	}

	normcore.cls_norm_ai.attach = function (frm, test_system, opts) {
		opts = opts || {};
		if (frm.is_new() || !test_system) return;
		call(
			"list_cls_norm_suggestions",
			{ test_system },
			(data) => {
				draw_strip(frm, data, test_system);
				if (data.pending) {
					frm.add_custom_button(__("Review AI suggestions"), () => open_dialog(frm, test_system), __("AI"));
				}
				if (normcore.ai.enabled() && data.can_edit && (!opts.draft_only || frm.doc.status === "Nháp")) {
					frm.add_custom_button(
						__("AI norm suggestion"),
						() => {
							const btn = frm.custom_buttons[__("AI norm suggestion")] || $();
							btn.prop("disabled", true).text(__("Running…"));
							call(
								"start_cls_norm_suggestion",
								{ test_system },
								(r) => {
									if (r.job_id) return watch(frm, test_system, r.job_id, btn);
									btn.prop("disabled", false).text(__("AI norm suggestion"));
									frappe.msgprint(r.message);
								},
								() => btn.prop("disabled", false).text(__("AI norm suggestion"))
							);
						},
						__("AI")
					);
				}
			},
			() => {} // không có quyền đọc: không hiện dải, nút; không báo lỗi trên form
		);
	};
})();
