// SCR-DSK-028 (FEAT-019): hộp thoại "Xuất hồ sơ" dùng chung. Gọi: normcore.export.open({run | service_cost | norm_set, run?}).
// Quyền và trạng thái do máy chủ kiểm; nút mờ chỉ là tiện ích giao diện.
frappe.provide("normcore.export");

(function () {
	const API = "normcore.api.export.";
	const ANNEX = ["annex_ii", "annex_iii", "annex_iv", "annex_v"];
	const esc = (v) => frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));

	function download(args, btn) {
		const label = btn && btn.text();
		if (btn) btn.prop("disabled", true).text(__("Creating file…"));
		// open_url_post gửi tham số bằng POST, không đặt lên URL; lỗi máy chủ do trình duyệt hiện
		open_url_post("/api/method/" + API + "export_file", args);
		if (btn) setTimeout(() => btn.prop("disabled", false).text(label), 2000);
	}

	function pick(obj, keys) {
		const out = {};
		keys.forEach((k) => obj[k] && (out[k] = obj[k]));
		return out;
	}

	function source_html(o) {
		const s = o.source;
		const parts = [];
		if (s.run) parts.push(`${__("Costing run")} <b>${esc(s.run)}</b>`);
		else parts.push(`${__("Norm set")} <b>${esc(s.norm_set)}</b> · ${__("No costing run attached")}`);
		if (s.service_cost) parts.push(esc(s.service_cost));
		const locked = o.options.every((x) => x.enabled) || (!s.run && s.norm_set);
		if (s.run) parts.push(`<span class="indicator-pill ${locked ? "green" : "yellow"}">${esc(locked ? __("Locked") : __("Not locked"))}</span>`);
		return `<div>${parts.join(" · ")}</div>`;
	}

	// Chọn giá trị cho ô Select: set_value của Frappe có thể chạy khi <option> chưa dựng nên selectedIndex = -1;
	// nên ghi thẳng vào DOM và vào value của control (luôn là chuỗi).
	function select_value(f, v) {
		if (v === null || v === undefined || v === "") return;
		v = String(v);
		f.value = v;
		if (f.$input) f.$input.val(v);
		f.set_value(v);
		if (f.$input && f.$input.val() !== v) f.$input.val(v);
	}

	function render(d, o, state) {
		const opt = {};
		o.options.forEach((x) => (opt[x.file_type] = x));
		const blocked = o.options.find((x) => !x.enabled && x.reason && state.run);
		const f = d.fields_dict;
		f.source.$wrapper.html(source_html(o) + (blocked ? `<div class="alert alert-warning" role="alert">${esc(blocked.reason)}</div>` : ""));
		if (state.run) {
			const rows = ANNEX.map(
				(t) =>
					`<div class="nc-exp-row" style="display:flex;justify-content:space-between;margin:4px 0"><span>${esc(opt[t].label)}</span>` +
					`<button type="button" class="btn btn-default btn-xs" data-type="${t}" ${opt[t].enabled ? "" : `disabled title="${esc(opt[t].reason)}"`}>${__("Download")}</button></div>`
			).join("");
			f.annex.$wrapper.html(
				rows +
					`<div class="text-muted small"><span class="indicator-pill yellow">${__("Assumption - pending confirmation")}</span> ${__("Column layout follows a provisional template, pending the official template of Circular 21/2024/TT-BYT (TBD-01).")}</div>`
			);
			f.annex.$wrapper.find("button[data-type]").on("click", function () {
				download({ file_type: $(this).attr("data-type"), run: state.run }, $(this));
			});
		}
		const costs = (o.service_costs || []).filter((x) => x.calc_status !== "Lỗi");
		f.service_cost.df.options = costs.map((x) => ({ value: x.name, label: `${x.service_code} — ${x.service_name || ""} · ${x.department}` }));
		f.service_cost.refresh();
		// Select chỉ có một lựa chọn thì tự chọn (ô không được để trống)
		const only_cost = costs.length === 1 ? costs[0].name : null;
		if (state.service_cost || only_cost) select_value(f.service_cost, state.service_cost || only_cost);
		f.norm_set.df.options = (o.norm_sets || []).map((x) => ({ value: x.name, label: `${x.name} · ${x.service_code}` }));
		if (state.norm_set && !(o.norm_sets || []).some((x) => x.name === state.norm_set)) f.norm_set.df.options.push({ value: state.norm_set, label: state.norm_set });
		f.norm_set.refresh();
		const only_norm = (o.norm_sets || []).length === 1 ? o.norm_sets[0].name : null;
		if (state.norm_set || only_norm) select_value(f.norm_set, state.norm_set || only_norm);
		f.cost_empty.$wrapper.toggle(!costs.length && !!state.run).html(`<div class="text-muted">${__("No successfully costed service in this run")}</div>`);
		f.norm_empty.$wrapper.toggle(!(o.norm_sets || []).length && !state.norm_set).html(`<div class="text-muted">${__("This run has no norm set attached")}</div>`);
		f.bundle_info.$wrapper.html(
			(o.bundle ? `<a href="${esc(o.bundle.file_url)}">${__("Latest archive")} (${esc(frappe.datetime.str_to_user(o.bundle.creation))})</a>` : "")
		);
	}

	function bundle_banner(d, kind, text) {
		const w = d.fields_dict.bundle_status.$wrapper;
		const role = kind === "red" ? 'role="alert"' : 'aria-live="polite"';
		w.html(`<div class="alert alert-${kind === "red" ? "danger" : kind === "green" ? "success" : "info"}" ${role}>${text}</div>`);
	}

	normcore.export.open = function (source) {
		const state = {
			run: source.run || null,
			service_cost: source.service_cost || null,
			norm_set: source.norm_set || null,
		};
		frappe
			.call({ method: API + "get_export_options", args: pick(source, ["run", "service_cost", "norm_set"]) })
			.then((r) => {
				const o = r.message;
				state.run = state.run || o.source.run;
				const d = new frappe.ui.Dialog({
					title: __("Export documents"),
					size: "large",
					fields: [
						{ fieldtype: "HTML", fieldname: "source" },
						{ fieldtype: "Section Break", fieldname: "sb_annex", label: __("Circular 21 forms"), depends_on: "eval:" + !!state.run },
						{ fieldtype: "HTML", fieldname: "annex" },
						{ fieldtype: "Section Break", fieldname: "sb_expl", label: __("Cost explanation (PDF)") },
						{ fieldtype: "Select", fieldname: "service_cost", label: __("Service"), read_only: state.service_cost ? 1 : 0 },
						{ fieldtype: "HTML", fieldname: "cost_empty" },
						{ fieldtype: "Button", fieldname: "get_expl", label: __("Download PDF") },
						{ fieldtype: "Section Break", fieldname: "sb_norm", label: __("Norm set") },
						{ fieldtype: "Select", fieldname: "norm_set", label: __("Norm set") },
						{ fieldtype: "HTML", fieldname: "norm_empty" },
						{ fieldtype: "Button", fieldname: "get_norm_xlsx", label: __("Download Excel") },
						{ fieldtype: "Button", fieldname: "get_norm_pdf", label: __("Download PDF") },
						{ fieldtype: "Section Break", fieldname: "sb_bundle", label: __("Whole file set"), depends_on: "eval:" + !!state.run },
						{ fieldtype: "HTML", fieldname: "bundle_help", options: `<div class="text-muted">${__("Packs Annexes II-V, every explanation and every norm set into one archive. Runs in the background; you will be notified when done.")}</div>` },
						{ fieldtype: "HTML", fieldname: "bundle_status" },
						{ fieldtype: "HTML", fieldname: "bundle_info" },
						{ fieldtype: "Section Break", fieldname: "sb_foot" },
						{ fieldtype: "HTML", fieldname: "foot", options: `<div class="text-muted">${__("Each file records the costing run, parameter set, time and exporter; the export is written to the audit log.")}</div>` },
					],
					primary_action_label: __("Pack documents"),
					primary_action() {
						pack(d, state);
					},
				});
				d.fields_dict.get_expl.input.onclick = () => {
					const sc = d.get_value("service_cost");
					if (!sc) return frappe.msgprint({ title: __("Export error"), message: __("Select a service to export"), indicator: "red" });
					download({ file_type: "explanation_pdf", service_cost: sc }, $(d.fields_dict.get_expl.input));
				};
				const norm = (type) => () => {
					const ns = d.get_value("norm_set");
					if (!ns) return frappe.msgprint({ title: __("Export error"), message: __("Select a norm set to export"), indicator: "red" });
					const a = { file_type: type, norm_set: ns };
					if (state.run) a.run = state.run;
					download(a, $(type === "norm_set_pdf" ? d.fields_dict.get_norm_pdf.input : d.fields_dict.get_norm_xlsx.input));
				};
				d.fields_dict.get_norm_xlsx.input.onclick = norm("norm_set_xlsx");
				d.fields_dict.get_norm_pdf.input.onclick = norm("norm_set_pdf");
				if (!state.run) {
					d.get_primary_btn().hide();
				} else if (!o.options.every((x) => x.enabled)) {
					d.get_primary_btn().prop("disabled", true);
				}
				frappe.realtime.on("nc_export_bundle", (m) => {
					if (m.run !== state.run) return;
					d.get_primary_btn().prop("disabled", false);
					if (m.status === "done") {
						bundle_banner(d, "green", `${__("Documents packed.")} <a href="${esc(m.file_url)}">${__("Download archive")}</a>`);
						frappe.show_alert({ message: __("Documents packed."), indicator: "green" });
					} else {
						bundle_banner(d, "red", `${__("Packing error")}: ${esc(m.message)}. ${__("See the error log for details.")}`);
					}
				});
				render(d, o, state);
				d.show();
				// dựng lại sau khi hiện để chắc chắn ô Select đã có option
				render(d, o, state);
			});
	};

	function pack(d, state) {
		frappe.call({ method: API + "export_bundle", args: { run: state.run } }).then((r) => {
			const m = r.message || {};
			d.get_primary_btn().prop("disabled", true);
			bundle_banner(d, "blue", m.running ? __("This run is already being packed.") : __("Packing documents… You can close this dialog; you will be notified when done."));
		});
	}
})();
