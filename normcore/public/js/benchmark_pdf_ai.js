// FEAT-027 (FR-BM-003, FR-AI-008, FR-AI-015, UC-013 2a, 2c; SCR-DSK-025): trích bảng giá PDF bằng AI.
// Chỉ gọi normcore.api.benchmark_ai.*; quyền do máy chủ kiểm, ẩn hiện nút chỉ là tiện ích giao diện.
// Tệp riêng, không sửa JS của FEAT-026 (ASM-027-10); nạp qua hook_registry/FEAT-027.json.
frappe.provide("normcore.benchmark_pdf_ai");
(function () {
	const API = "normcore.api.benchmark_ai.";
	const esc = (v) => frappe.utils.escape_html(v == null ? "" : String(v));
	const POLL_MS = 3000;

	function call(method, args, callback, error) {
		frappe.call({
			method: API + method,
			args,
			freeze: false,
			callback: (r) => r.message !== undefined && callback(r.message),
			error: error,
		});
	}

	function reasons_table(title, rows) {
		if (!rows || !rows.length) return "";
		const body = rows
			.map((r) => `<tr><td>${esc(r.service_name)}</td><td>${esc(r.reason || r.message)}</td></tr>`)
			.join("");
		return `<p><b>${esc(title)}</b></p><table class="table table-bordered"><thead><tr><th>${esc(__("Service name"))}</th><th>${esc(__("Reason"))}</th></tr></thead><tbody>${body}</tbody></table>`;
	}

	function show_result(frm, st) {
		const created = st.created || 0;
		const not_in_file = st.not_in_file || 0;
		if (created) {
			frm.dashboard.set_headline_alert(esc(__("{0} reference prices created as Proposed.", [created])), "alert-success");
			frm.add_custom_button(
				__("Review rows"),
				() => frappe.set_route("List", "NC Benchmark Price", { ai_log: st.log }),
				__("Review rows")
			);
		} else {
			frm.dashboard.set_headline_alert(esc(__("No price rows found in the file.")), "alert-warning");
		}
		const skipped = (st.skipped || []).concat(st.duplicates || []);
		if (skipped.length || not_in_file) {
			let html = reasons_table(__("Some rows were not created"), skipped);
			if (not_in_file) html += `<p>${esc(__("{0} rows were not found in the file and were dropped.", [not_in_file]))}</p>`;
			frappe.msgprint({ title: __("Some rows were not created"), message: html, wide: true });
		}
	}

	function show_failure(frm, st) {
		frm.dashboard.set_headline_alert(esc(st.message || __("AI extraction failed")), "alert-danger");
		frm.add_custom_button(__("Enter manually"), () => frappe.new_doc("NC Benchmark Price", { facility: frm.doc.name }), __("Price list"));
		frm.add_custom_button(__("Import from Excel"), () => frappe.set_route("import-excel", { import_set: "nc_benchmark_price" }), __("Price list"));
	}

	function watch(frm, job_id) {
		const timer = setInterval(poll, POLL_MS);
		function stop() {
			clearInterval(timer);
			frappe.realtime.off("normcore_price_list_ai", on_rt);
		}
		function poll() {
			if (cur_frm !== frm) return stop();
			call("get_price_list_extraction_status", { job_id }, (st) => {
				if (st.status === "done") {
					stop();
					show_result(frm, st);
				} else if (st.status === "failed" || st.status === "unknown") {
					stop();
					show_failure(frm, st);
				}
			});
		}
		function on_rt(msg) {
			if (msg && msg.job_id === job_id) poll();
		}
		frappe.realtime.on("normcore_price_list_ai", on_rt);
	}

	function open_dialog(frm) {
		const dialog = new frappe.ui.Dialog({
			title: __("Extract price list from PDF"),
			fields: [
				{
					fieldname: "pdf_file",
					fieldtype: "Attach",
					label: __("PDF file"),
					reqd: 1,
					options: { restrictions: { allowed_file_types: [".pdf"] } },
				},
				{ fieldname: "price_category", fieldtype: "Link", options: "NC Price Category", label: __("Price category"), reqd: 1 },
				{ fieldname: "source_doc_no", fieldtype: "Data", label: __("Source document no.") },
				{
					fieldname: "default_effective_date",
					fieldtype: "Date",
					label: __("Default effective date"),
					description: __("Used for rows without a date in the file"),
				},
				{
					fieldname: "note",
					fieldtype: "HTML",
					options: `<p class="text-muted">${esc(__("AI reads the file; every row is created as Proposed and must be checked against the original page before it is used for comparison."))}</p>`,
				},
			],
			primary_action_label: __("Extract"),
			primary_action(values) {
				call(
					"start_price_list_extraction",
					{
						facility: frm.doc.name,
						price_category: values.price_category,
						file_url: values.pdf_file,
						source_doc_no: values.source_doc_no,
						default_effective_date: values.default_effective_date,
					},
					(r) => {
						dialog.hide();
						frm.dashboard.set_headline_alert(esc(__("Extracting price list… You can keep working; the result will appear here.")), "alert-info");
						watch(frm, r.job_id);
					}
				);
			},
		});
		dialog.show();
	}

	frappe.ui.form.on("NC Benchmark Facility", {
		refresh(frm) {
			if (normcore.ai.enabled() && !frm.is_new() && frappe.model.can_create("NC Benchmark Price")) {
				frm.add_custom_button(__("Extract price list from PDF (AI)"), () => open_dialog(frm), __("Price list"));
			}
		},
	});

	frappe.ui.form.on("NC Benchmark Price", {
		refresh(frm) {
			if (frm.doc.ai_log) {
				frm.dashboard.add_comment(
					__("Extracted by AI from the source file. Check against the original page before confirming."),
					"blue",
					true
				);
			}
			const url = frm.doc.source_url || frm.doc.source_file;
			if (frm.doc.ai_log && url) {
				frm.add_custom_button(__("Open original page"), () => window.open(url), __("Source"));
			}
		},
	});
})();
