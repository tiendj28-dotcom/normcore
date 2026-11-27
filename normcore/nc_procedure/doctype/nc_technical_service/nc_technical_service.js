// SCR-DSK-006: form chuẩn + thẻ tình trạng chuỗi (FR-SVC-004). Dữ liệu và quyền do máy chủ quyết định.
const CHAIN_API = "normcore.api.service.get_chain_status";

function chain_html(items) {
	const esc = frappe.utils.escape_html;
	const cards = items
		.map((item) => {
			const pill = (label, indicator) =>
				`<span class="indicator-pill ${esc(indicator || "gray")}"><span>${esc(label)}</span></span>`;
			const head = `<div class="nc-chain-title"><b>${esc(item.label)}</b></div>`;
			const badges = (item.badges || []).map((b) => pill(b.label, b.indicator)).join(" ");
			const rows_html = (item.rows || [])
				.map((row) => {
					const dept = `<div class="text-muted">${esc(row.department_name || row.department)}</div>`;
					if (row.state === "no_permission") return `<div class="nc-chain-row">${dept}${pill(__("No permission to view"), "gray")}</div>`;
					if (row.state !== "ok") return `<div class="nc-chain-row">${dept}${pill(row.status, "gray")}</div>`;
					const date = row.date ? frappe.datetime.str_to_user(row.date) : "";
					const extra = (row.badges || []).map((b) => pill(b.label, b.indicator)).join(" ");
					return (
						`<div class="nc-chain-row">${dept}` +
						`<a href="${esc(row.route)}">${esc(row.name)}</a> ` +
						`${pill(row.status, row.indicator)} ${extra} <span class="text-muted">${esc(date)}</span></div>`
					);
				})
				.join("");
			let body = "";
			if (item.key === "price") {
				body = `<a href="#nc-chain-price" class="nc-chain-price-link">${esc(item.message)}</a>`;
			} else if (item.state === "ok") {
				body = rows_html;
			} else {
				// empty hoặc no_permission: nhãn của mục (ASM-047: "Chưa có trong phạm vi khoa của bạn"), rồi các dòng khoa nếu có
				body = pill(item.message || __("None yet"), "gray") + rows_html;
			}
			const attrs = item.key === "price" ? ' id="nc-chain-price" tabindex="-1"' : "";
			return `<div class="nc-chain-card"${attrs}>${head}${badges}${body}</div>`;
		})
		.join("");
	const style =
		"<style>.nc-chain{display:flex;flex-wrap:nowrap;border:1px solid var(--border-color);border-radius:var(--border-radius-md)}" +
		".nc-chain-card{flex:1 1 0;min-width:0;padding:var(--padding-md);border-right:1px solid var(--border-color)}" +
		".nc-chain-card:last-child{border-right:0}.nc-chain-card:focus{outline:2px solid var(--primary)}" +
		".nc-chain-row{margin-top:var(--margin-sm)}" +
		"@media (max-width:768px){.nc-chain{flex-direction:column}.nc-chain-card{border-right:0;border-bottom:1px solid var(--border-color)}}</style>";
	return `${style}<div class="nc-chain">${cards}</div>`;
}

function load_chain(frm) {
	const wrapper = frm.fields_dict.chain_status_html.$wrapper;
	if (frm.is_new()) {
		frm.set_df_property("chain_section", "hidden", 1);
		return;
	}
	frm.set_df_property("chain_section", "hidden", 0);
	const service = frm.doc.name;
	wrapper.html(`<div class="text-muted">${__("Loading chain status…")}</div>`);
	frappe.call({
		method: CHAIN_API,
		args: { service },
		callback(r) {
			if (frm.doc.name !== service || !r.message || r.message.service !== frm.doc.name) return;
			wrapper.html(chain_html(r.message.items));
			wrapper.find(".nc-chain-price-link").on("click", (e) => {
				e.preventDefault();
				e.stopPropagation(); // Frappe gắn handler trên body cho mọi thẻ a href="#..." và gọi set_route
				const el = wrapper.find("#nc-chain-price").get(0);
				el.scrollIntoView({ block: "nearest" });
				el.focus();
			});
		},
		error() {
			if (frm.doc.name !== service) return;
			wrapper.html(
				`<div class="text-muted">${__("Could not load chain status.")} ` +
					`<button class="btn btn-xs btn-default nc-chain-retry">${__("Retry")}</button></div>`
			);
			wrapper.find(".nc-chain-retry").on("click", () => load_chain(frm));
		},
	});
}

// FEAT-031: khối "Cận lâm sàng" — danh sách hệ thống xét nghiệm của dịch vụ (FR-CLS-002).
const SYSTEMS_API = "normcore.api.test_system.get_service_systems";

function systems_html(data) {
	const esc = frappe.utils.escape_html;
	const pill = (label, indicator) =>
		`<span class="indicator-pill ${esc(indicator)}"><span>${esc(label)}</span></span>`;
	let html = "";
	(data.departments || []).forEach((d) => {
		const warn = d.warning ? " " + pill(__("Total share differs from 100%"), "orange") : "";
		const rows = d.systems
			.map(
				(s) =>
					`<tr><td><a href="${esc(frappe.utils.get_form_link("NC Test System", s.name))}">${esc(s.name)}</a></td>` +
					`<td>${esc(s.equipment_name || s.main_equipment)}</td>` +
					`<td>${frappe.format(s.volume_share_pct, { fieldtype: "Float", precision: 2 })}</td>` +
					`<td>${pill(s.status, s.status === "Đang dùng" ? "green" : "gray")}</td></tr>`
			)
			.join("");
		html +=
			`<div class="nc-cls-dept"><b>${__("Department")} ${esc(d.department_name || d.department)}` +
			` — ${__("total share")} ${frappe.format(d.total_share, { fieldtype: "Float", precision: 2 })}%</b>${warn}` +
			`<div class="table-responsive"><table class="table table-bordered"><thead><tr>` +
			`<th>${__("Code")}</th><th>${__("Main equipment")}</th><th>${__("Share (%)")}</th><th>${__("Status")}</th>` +
			`</tr></thead><tbody>${rows}</tbody></table></div></div>`;
	});
	if (!html) html = `<div class="text-muted">${__("No test system yet")}</div>`;
	return html;
}

function load_systems(frm) {
	// Phần hiện/ẩn theo is_paraclinical do depends_on của trường quyết định
	const wrapper = frm.fields_dict.cls_systems_html.$wrapper;
	if (frm.is_new()) {
		wrapper.html(`<div class="text-muted">${__("Save to add test systems")}</div>`);
		return;
	}
	if (!frm.doc.is_paraclinical) return;
	const service = frm.doc.name;
	wrapper.html(`<div class="text-muted">${__("Loading test systems…")}</div>`);
	frappe.call({
		method: SYSTEMS_API,
		args: { service },
		callback(r) {
			if (frm.doc.name !== service || !r.message) return;
			wrapper.html(systems_html(r.message));
			if (r.message.can_create) {
				const btn = $(`<button class="btn btn-xs btn-default">${__("Add test system")}</button>`);
				btn.on("click", () => frappe.new_doc("NC Test System", { technical_service: service }));
				wrapper.append(btn);
			}
		},
		error() {
			if (frm.doc.name !== service) return;
			wrapper.html(
				`<div class="text-muted">${__("Could not load test systems.")} ` +
					`<button class="btn btn-xs btn-default nc-cls-retry">${__("Retry")}</button></div>`
			);
			wrapper.find(".nc-cls-retry").on("click", () => load_systems(frm));
		},
	});
}

// FEAT-024: SCR-DSK-006 nút "Soạn quy trình" (UC-004). AI tắt → tạo bản nháp trống (1a), không có chữ AI.
function add_draft_button(frm) {
	if (frm.is_new() || !frappe.model.can_create("NC Clinical Procedure")) return;
	frm.add_custom_button(__("Draft procedure"), () => {
		if (normcore.ai.enabled()) {
			normcore.procedure.open_ai_draft_dialog({
				technical_service: frm.doc.name,
				service_name: frm.doc.service_name,
			});
			return;
		}
		frappe.prompt(
			[{ fieldname: "department", fieldtype: "Link", options: "NC Department", label: __("Department"), reqd: 1 }],
			(values) =>
				frappe.call({
					method: "normcore.api.procedure.create_procedure",
					args: { technical_service: frm.doc.name, department: values.department },
					callback(r) {
						frappe.set_route("procedure-editor", { name: r.message.name });
					},
					error() {
						const existing = frappe.last_response && frappe.last_response.existing_procedure;
						if (existing) {
							frm.add_custom_button(__("Open existing procedure"), () =>
								frappe.set_route("procedure-editor", { name: existing })
							);
						}
					},
				}),
			__("Draft procedure"),
			__("Create")
		);
	});
}

// FEAT-030: section "Giá đã duyệt" chỉ đọc, ngày áp dụng giảm dần, không thêm/xóa dòng
function show_approved_prices(frm) {
	const grid = frm.fields_dict.approved_prices && frm.fields_dict.approved_prices.grid;
	if (!grid) return;
	grid.cannot_add_rows = true;
	grid.cannot_delete_rows = true;
	frm.set_df_property("prices_section", "collapsible", 1);
	grid.refresh();
	if (!(frm.doc.approved_prices || []).length) frm.fields_dict.approved_prices.$wrapper.append(`<div class="text-muted nc-no-price">${__("No approved price yet")}</div>`);
}

frappe.ui.form.on("NC Technical Service", {
	refresh(frm) {
		show_approved_prices(frm);
		load_chain(frm);
		load_systems(frm);
		add_draft_button(frm);
	},
	is_paraclinical(frm) {
		load_systems(frm);
	},
});
