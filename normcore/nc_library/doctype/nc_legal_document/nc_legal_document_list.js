// SCR-DSK-002 (FEAT-020): danh sách văn bản và tìm trong nội dung.
const VALIDITY_COLOR = { "Còn hiệu lực": "green", "Chưa hiệu lực": "blue", "Hết hiệu lực": "gray" };
const INDEX_COLOR = { "Chưa lập": "gray", "Đang lập": "orange", "Đã lập": "green", Lỗi: "red" };
function mode_label(mode) {
	const labels = { text: __("content"), doc_number: __("document number"), service: __("service code") };
	return labels[mode] || mode;
}

function pill(color, text) {
	const label = frappe.utils.escape_html(text || "");
	return `<span class="indicator-pill ${color || "gray"} ellipsis"><span>${label}</span></span>`;
}

function highlight(snippet, query) {
	const esc = frappe.utils.escape_html(snippet || "");
	const q = frappe.utils.escape_html((query || "").trim());
	if (!q) return esc;
	const re = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
	return esc.replace(re, (m) => `<mark>${m}</mark>`);
}

function open_search_dialog() {
	const PAGE = 20;
	let start = 0;
	let rows_shown = 0;
	const d = new frappe.ui.Dialog({
		title: __("Search in content"),
		size: "extra-large",
		fields: [
			{
				fieldname: "query",
				fieldtype: "Data",
				label: __("Query"),
				reqd: 1,
				description: __("Keyword, phrase, document number or service code"),
			},
			{
				fieldname: "doc_type",
				fieldtype: "Select",
				label: __("Type"),
				options: ["", "Luật", "Nghị định", "Thông tư", "Quyết định", "Công văn", "Tài liệu nội bộ"].join("\n"),
			},
			{
				fieldname: "validity_status",
				fieldtype: "Select",
				label: __("Validity"),
				options: ["", "Còn hiệu lực", "Chưa hiệu lực", "Hết hiệu lực"].join("\n"),
			},
			{ fieldname: "results", fieldtype: "HTML" },
		],
		primary_action_label: __("Search"),
		primary_action() {
			start = 0;
			rows_shown = 0;
			run(false);
		},
	});

	function render(rows, append, res, values) {
		const $res = d.fields_dict.results.$wrapper;
		if (!append) $res.empty();
		if (!append && !rows.length) {
			$res.html(`<p class="text-muted">${__("No matching sections")}</p>`);
			return;
		}
		if (!append) {
			$res.append(
				`<p class="text-muted nc-search-head">${__("{0} results — searched by {1}", [
					res.total,
					mode_label(res.mode),
				])}</p>` +
					`<div style="max-height: 60vh; overflow-y: auto"><table class="table table-bordered">` +
					`<thead><tr><th>${__("Document number")}</th><th>${__("Section")}</th><th>${__("Heading")}</th>` +
					`<th>${__("Pages")}</th><th>${__("Validity")}</th><th>${__("Matched by")}</th>` +
					`<th>${__("Snippet")}</th></tr></thead><tbody></tbody></table></div>`
			);
		}
		const $body = $res.find("tbody");
		rows.forEach((r) => {
			const pages = r.page_from ? `${r.page_from}–${r.page_to || r.page_from}` : "—";
			const $tr = $(
				`<tr><td>${frappe.utils.escape_html(r.doc_number)}</td>` +
					`<td><a href="#" class="nc-open">${frappe.utils.escape_html(r.section_no)}</a></td>` +
					`<td>${frappe.utils.escape_html(r.heading || "")}</td><td>${pages}</td>` +
					`<td>${pill(VALIDITY_COLOR[r.validity_status], r.validity_status)}</td>` +
					`<td>${frappe.utils.escape_html(r.match || "")}</td>` +
					`<td style="white-space: normal">${highlight(r.snippet, res.mode === "text" ? values.query : "")}</td></tr>`
			);
			$tr.find(".nc-open").on("click", (e) => {
				e.preventDefault();
				d.hide();
				frappe.set_route("Form", "NC Legal Section", r.section);
			});
			$body.append($tr);
		});
		$res.find(".nc-more").remove();
		if (rows_shown < res.total) {
			const $more = $(`<button class="btn btn-default btn-sm nc-more">${__("More")}</button>`);
			$more.on("click", () => run(true));
			$res.append($more);
		}
	}

	function run(append) {
		const values = d.get_values();
		if (!values) return;
		d.get_primary_btn().prop("disabled", true).text(__("Searching…"));
		frappe.call({
			method: "normcore.api.library.search_sections",
			args: {
				query: values.query,
				mode: "auto",
				doc_type: values.doc_type || null,
				validity_status: values.validity_status || null,
				start: start,
				page_length: PAGE,
			},
			callback(r) {
				const res = r.message || { rows: [], total: 0 };
				rows_shown += res.rows.length;
				start = rows_shown;
				render(res.rows, append, res, values);
			},
			always() {
				d.get_primary_btn().prop("disabled", false).text(__("Search"));
			},
		});
	}

	d.show();
	d.$wrapper.find("[data-fieldname='query'] input").on("keydown", (e) => {
		if (e.key === "Enter") {
			e.preventDefault();
			d.get_primary_btn().trigger("click");
		}
	});
}

frappe.listview_settings["NC Legal Document"] = {
	add_fields: ["validity_status", "index_status"],
	get_indicator(doc) {
		return [
			__(doc.validity_status || ""),
			VALIDITY_COLOR[doc.validity_status] || "gray",
			`validity_status,=,${doc.validity_status}`,
		];
	},
	formatters: {
		index_status(value) {
			return pill(INDEX_COLOR[value], __(value || ""));
		},
	},
	onload(listview) {
		if (!frappe.model.can_read("NC Legal Section")) return;
		listview.page.add_inner_button(__("Search in content"), open_search_dialog);
		frappe.ui.keys.add_shortcut({
			shortcut: "ctrl+shift+f",
			action: open_search_dialog,
			page: listview.page,
			description: __("Search in content"),
		});
	},
};
