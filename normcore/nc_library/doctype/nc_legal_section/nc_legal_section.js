// SCR-DSK-003 (FEAT-020), FR-LIB-011/012: mục cạnh trang gốc của tệp.
frappe.ui.form.on("NC Legal Section", {
	setup(frm) {
		// FR-SVC-006: chỉ chọn dịch vụ đang dùng cho lưới ánh xạ
		frm.set_query("technical_service", "service_mappings", () => ({ filters: { is_active: 1 } }));
	},
	refresh(frm) {
		const $w = frm.fields_dict.source_view_html.$wrapper;
		$w.empty();
		if (frm.is_new()) return;
		frappe.call({
			method: "normcore.api.library.get_source_view",
			args: { section: frm.doc.name },
			callback(r) {
				const v = r.message;
				if (!v) return;
				const url = frappe.utils.escape_html(v.file_url);
				if (v.file_kind === "pdf" && v.page_from) {
					const to = v.page_to || v.page_from;
					$w.html(
						`<p class="text-muted">${__("Pages {0}–{1} of {2}", [v.page_from, to, frappe.utils.escape_html(v.doc_number)])} ` +
							`<a class="btn btn-default btn-xs" target="_blank" rel="noopener" href="${url}">${__("Open file")}</a></p>` +
							`<iframe title="${__("Original page")}" src="${url}#page=${v.page_from}" ` +
							`style="width: 100%; height: 60vh; border: 0"></iframe>`
					);
				} else {
					$w.html(
						`<p class="text-muted">${__("Original pages are not available for DOCX files.")} ` +
							`<a class="btn btn-default btn-xs" href="${url}" download>${__("Download file")}</a></p>`
					);
				}
			},
			error() {
				$w.html(`<p class="text-muted">${__("Cannot load the original file")}</p>`);
			},
		});
	},
	plain_text(frm) {
		if (!frm.is_new() && !frm.fields_dict.plain_text.$wrapper.find(".nc-prev-note").length) {
			frm.fields_dict.plain_text.$wrapper.append(
				`<p class="text-muted small nc-prev-note">${__("The previous text is kept in the version history below.")}</p>`
			);
		}
	},
});
