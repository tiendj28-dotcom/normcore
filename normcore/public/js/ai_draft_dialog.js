// SCR-DSK-008: hộp thoại ba bước soạn dự thảo quy trình bằng AI (FEAT-024, UC-004).
// Dữ liệu, quyền, điều kiện do máy chủ quyết định; hộp thoại chỉ gọi API và hiện kết quả.
frappe.provide("normcore.procedure");

(function () {
	const API = "normcore.api.procedure.";
	const MAX_REQUEST = 5000;
	const MAX_EXTRA = 20;
	const POLL_MS = 3000;
	const esc = (s) => frappe.utils.escape_html(s == null ? "" : String(s));
	const editor_route = (name) => `/app/procedure-editor?name=${encodeURIComponent(name)}`;

	function first_department() {
		const perms = (frappe.defaults.get_user_permissions() || {})["NC Department"] || [];
		return perms.length ? perms[0].doc : "";
	}

	normcore.procedure.open_ai_draft_dialog = function (opts) {
		const state = {
			step: 1,
			prepared: null,
			extra: [],
			job: null,
			timer: null,
			confirm_no_source: 0,
		};
		const title = __("Draft procedure with AI — {0}", [`${opts.technical_service} · ${opts.service_name || ""}`]);
		const d = new frappe.ui.Dialog({
			title,
			size: "large",
			fields: [
				{ fieldname: "steps_html", fieldtype: "HTML" },
				{ fieldname: "department", fieldtype: "Link", options: "NC Department", label: __("Department"), reqd: 1, default: first_department() },
				{ fieldname: "sources_html", fieldtype: "HTML" },
				{ fieldname: "confirm_no_source", fieldtype: "Check", label: __("I understand and want to continue"), hidden: 1 },
				{
					fieldname: "doctor_request",
					fieldtype: "Small Text",
					label: __("Request"),
					reqd: 1,
					hidden: 1,
					description: __(
						"Department conditions, equipment, drugs, supplies, technique variants. Where you differ from the guideline, say so here; it becomes the deviation reason."
					),
				},
				{ fieldname: "counter_html", fieldtype: "HTML", hidden: 1 },
				{ fieldname: "extra_query", fieldtype: "Data", label: __("Additional sections (optional)"), hidden: 1 },
				{ fieldname: "extra_html", fieldtype: "HTML", hidden: 1 },
				{ fieldname: "progress_html", fieldtype: "HTML", hidden: 1 },
			],
			primary_action_label: __("Next"),
			primary_action() {
				if (state.step === 1) return go(2);
				if (state.step === 2) return start();
			},
			secondary_action_label: __("Back"),
			secondary_action() {
				if (state.step === 2) go(1);
				else if (state.step === 3) go(2);
			},
		});

		function show(fields, on) {
			fields.forEach((f) => d.set_df_property(f, "hidden", on ? 0 : 1));
		}

		function stepper() {
			const labels = [__("1. Sources"), __("2. Request"), __("3. Drafting")];
			d.fields_dict.steps_html.$wrapper.html(
				labels
					.map((l, i) => (i + 1 === state.step ? `<b aria-current="step">${esc(l)}</b>` : esc(l)))
					.join(" · ")
			);
		}

		function go(step) {
			state.step = step;
			stepper();
			show(["department", "sources_html"], step === 1);
			show(["confirm_no_source"], step === 1 && !!state.prepared && state.prepared.no_sources);
			show(["doctor_request", "counter_html", "extra_query", "extra_html"], step === 2);
			show(["progress_html"], step === 3);
			d.get_secondary_btn().toggle(step > 1);
			d.get_primary_btn().toggle(step < 3).text(step === 1 ? __("Next") : __("Draft"));
			if (step === 1) refresh_next();
			if (step === 2) refresh_draft_button();
		}

		function refresh_next() {
			const p = state.prepared;
			const ok = p && !p.existing && (!p.no_sources || d.get_value("confirm_no_source"));
			d.get_primary_btn().prop("disabled", !ok);
		}

		function refresh_draft_button() {
			const text = d.get_value("doctor_request") || "";
			d.fields_dict.counter_html.$wrapper.html(`<div class="text-muted">${text.length}/${MAX_REQUEST}</div>`);
			d.get_primary_btn().prop("disabled", !text.trim() || text.length > MAX_REQUEST);
		}

		function load_sources() {
			const department = d.get_value("department");
			if (!department) return;
			const w = d.fields_dict.sources_html.$wrapper;
			w.html(`<div class="text-muted" role="status">${__("Loading sources…")}</div>`);
			frappe.call({
				method: API + "prepare_ai_draft",
				args: { technical_service: opts.technical_service, department },
				callback(r) {
					const p = (state.prepared = r.message);
					let html = "";
					if (p.existing) {
						html += `<div class="alert alert-warning">${__("This service already has a {0} procedure for this department: {1}", [
							esc(p.existing_state),
							`<a href="${editor_route(p.existing)}">${esc(p.existing)}</a>`,
						])}</div>`;
					}
					if (p.no_sources) {
						html += `<div class="alert alert-warning">${__(
							"This service has no confirmed guideline section in effect. The draft will be marked 'Unsupported' wherever there is no source."
						)}</div>`;
					} else {
						html += `<p>${__("{0} confirmed guideline sections in effect", [p.sources.length])}</p>`;
						html +=
							`<table class="table table-bordered"><thead><tr><th>${__("Document")}</th><th>${__("Section no.")}</th><th>${__("Heading")}</th><th></th></tr></thead><tbody>` +
							p.sources
								.map(
									(s) =>
										`<tr><td>${esc(s.doc_number)}</td><td>${esc(s.section_no)}</td><td>${esc(s.heading)}</td>` +
										`<td><a href="#" class="nc-src-view" data-name="${esc(s.name)}">${__("View")}</a></td></tr>`
								)
								.join("") +
							"</tbody></table>";
					}
					if (p.current_procedure) {
						html += `<p>${__("Current hospital procedure: {0} (v{1}) will also be sent", [esc(p.current_procedure.name), p.current_procedure.version_no])}</p>`;
					}
					w.html(html);
					w.find(".nc-src-view").on("click", (e) => {
						e.preventDefault();
						view_source($(e.currentTarget).data("name"));
					});
					show(["confirm_no_source"], state.step === 1 && p.no_sources);
					refresh_next();
				},
			});
		}

		function view_source(name) {
			frappe.call({
				method: "normcore.api.library.get_source_view",
				args: { section: name },
				callback(r) {
					const v = r.message || {};
					frappe.msgprint({ title: __("View"), message: `<pre style="white-space:pre-wrap">${esc(v.plain_text || v.text || JSON.stringify(v))}</pre>` });
				},
			});
		}

		function render_extra() {
			const w = d.fields_dict.extra_html.$wrapper;
			const chips = state.extra
				.map(
					(s) =>
						`<span class="indicator-pill gray">${esc(s.doc_number)} ${esc(s.section_no)} ` +
						`<a href="#" class="nc-extra-del" data-name="${esc(s.name)}" aria-label="${__("Remove {0}", [esc(s.section_no)])}">×</a></span> `
				)
				.join("");
			w.find(".nc-extra-chips").remove();
			w.prepend(`<div class="nc-extra-chips">${chips}${state.extra.length >= MAX_EXTRA ? `<div class="text-muted">${__("Up to 20 sections")}</div>` : ""}</div>`);
			w.find(".nc-extra-del").on("click", (e) => {
				e.preventDefault();
				const n = $(e.currentTarget).data("name");
				state.extra = state.extra.filter((s) => s.name !== n);
				render_extra();
			});
		}

		let search_timer = null;
		function search_extra() {
			const q = (d.get_value("extra_query") || "").trim();
			const w = d.fields_dict.extra_html.$wrapper;
			if (q.length < 2) return;
			frappe.call({
				method: API + "search_extra_sources",
				args: { query: q, technical_service: opts.technical_service },
				callback(r) {
					w.find(".nc-extra-results").remove();
					const rows = (r.message || []).filter((s) => !state.extra.some((x) => x.name === s.name));
					const html = rows
						.map(
							(s) =>
								`<div>${esc(s.doc_number)} · ${esc(s.section_no)} · ${esc(s.heading)} ` +
								`<button class="btn btn-xs btn-default nc-extra-add" data-name="${esc(s.name)}" ${state.extra.length >= MAX_EXTRA ? "disabled" : ""}>${__("Add")}</button></div>`
						)
						.join("");
					w.append(`<div class="nc-extra-results">${html}</div>`);
					w.find(".nc-extra-add").on("click", (e) => {
						const s = rows.find((x) => x.name === $(e.currentTarget).data("name"));
						if (s && state.extra.length < MAX_EXTRA) state.extra.push(s);
						render_extra();
						search_extra();
					});
				},
			});
		}

		function show_progress(html) {
			d.fields_dict.progress_html.$wrapper.html(html);
		}

		function start() {
			go(3);
			d.get_secondary_btn().hide();
			show_progress(
				`<div class="progress"><div class="progress-bar progress-bar-striped active" style="width:100%"></div></div>` +
					`<p role="status" aria-live="polite">${__("AI is drafting… This can take a few minutes.")}</p>`
			);
			frappe.call({
				method: API + "start_ai_draft",
				args: {
					technical_service: opts.technical_service,
					department: d.get_value("department"),
					doctor_request: d.get_value("doctor_request"),
					extra_sections: JSON.stringify(state.extra.map((s) => s.name)),
					confirm_no_source: d.get_value("confirm_no_source") ? 1 : 0,
				},
				callback(r) {
					state.job = r.message.job_id;
					frappe.realtime.on("normcore_ai_draft", (data) => {
						if (data.job_id === state.job) poll();
					});
					state.timer = setInterval(poll, POLL_MS);
					poll();
				},
				error(r) {
					const existing = frappe.last_response && frappe.last_response.existing_procedure;
					fail(existing ? __("Open existing procedure") : null, existing);
					go(existing ? 1 : 2);
					if (existing) load_sources();
				},
			});
		}

		function stop() {
			if (state.timer) clearInterval(state.timer);
			state.timer = null;
		}

		function poll() {
			if (!state.job) return;
			frappe.call({
				method: API + "get_ai_draft_status",
				args: { job_id: state.job },
				callback(r) {
					const st = r.message || {};
					if (st.status === "done") {
						stop();
						d.hide();
						const extra = st.rejected > 0 ? " " + __("{0} citation(s) removed for not matching the source.", [st.rejected]) : "";
						frappe.show_alert({ message: __("Draft {0} created.", [st.procedure]) + extra, indicator: "green" });
						frappe.set_route(editor_route(st.procedure).replace("/app/", ""));
					} else if (st.status === "failed") {
						stop();
						failed(st);
					} else if (st.status === "unknown") {
						stop();
						show_progress(
							`<div class="alert alert-warning">${__("The drafting job can no longer be tracked. Check the procedure list.")}</div>` + retry_buttons(false)
						);
						bind_retry();
					}
				},
			});
		}

		function retry_buttons(manual) {
			return (
				`<button class="btn btn-sm btn-primary nc-retry">${__("Retry")}</button> ` +
				(manual ? `<button class="btn btn-sm btn-default nc-manual">${__("Draft manually")}</button> ` : "") +
				`<button class="btn btn-sm btn-default nc-close">${__("Close")}</button>`
			);
		}

		function failed(st) {
			const existing = st.existing_procedure;
			show_progress(
				`<div class="alert alert-danger" role="alert">${esc(st.error)}</div>` +
					(existing ? `<a href="${editor_route(existing)}" class="btn btn-sm btn-default">${__("Open existing procedure")}</a> ` : "") +
					retry_buttons(true)
			);
			bind_retry();
		}

		function fail() {
			/* thông báo lỗi đồng bộ đã do máy chủ hiện qua msgprint */
		}

		function bind_retry() {
			const w = d.fields_dict.progress_html.$wrapper;
			w.find(".nc-retry").on("click", () => start());
			w.find(".nc-close").on("click", () => d.hide());
			w.find(".nc-manual").on("click", () => {
				frappe.call({
					method: API + "create_procedure",
					args: {
						technical_service: opts.technical_service,
						department: d.get_value("department"),
						doctor_request: d.get_value("doctor_request"),
					},
					callback(r) {
						d.hide();
						frappe.set_route(editor_route(r.message.name).replace("/app/", ""));
					},
				});
			});
		}

		d.fields_dict.department.df.onchange = () => load_sources();
		d.fields_dict.confirm_no_source.df.onchange = () => refresh_next();
		d.fields_dict.doctor_request.df.onchange = () => refresh_draft_button();
		d.fields_dict.doctor_request.$wrapper.on("input", "textarea", () => {
			d.fields_dict.doctor_request.df.value = d.fields_dict.doctor_request.get_input_value();
			const text = d.fields_dict.doctor_request.get_input_value() || "";
			d.fields_dict.counter_html.$wrapper.html(`<div class="text-muted">${text.length}/${MAX_REQUEST}</div>`);
			d.get_primary_btn().prop("disabled", !text.trim() || text.length > MAX_REQUEST);
		});
		d.fields_dict.extra_query.$wrapper.on("input", "input", () => {
			clearTimeout(search_timer);
			search_timer = setTimeout(search_extra, 300);
		});
		d.onhide = stop;
		d.show();
		go(1);
		render_extra();
		load_sources();
		return d;
	};
})();
