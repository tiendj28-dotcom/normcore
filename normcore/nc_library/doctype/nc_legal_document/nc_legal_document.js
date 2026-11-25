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

frappe.ui.form.on("NC Legal Document", {
	refresh(frm) {
		frm.set_intro("");
		if (frm.doc.validity_status) {
			frm.page.set_indicator(__(frm.doc.validity_status), VALIDITY_COLOR[frm.doc.validity_status] || "gray");
		}
		set_headline(frm);
		render_sections(frm, 0, 0);
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
