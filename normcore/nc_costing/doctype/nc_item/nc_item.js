// SCR-DSK-017: mặt hàng. Thẻ đơn giá đang dùng tại hôm nay (FR-RES-004) và lịch sử đơn giá có chứng từ.
const PRICE_API = "normcore.api.item.get_effective_price";

function pill(label, indicator) {
	return `<span class="indicator-pill ${frappe.utils.escape_html(indicator)}"><span>${frappe.utils.escape_html(label)}</span></span>`;
}

function render_prices(frm, rows, effective) {
	const esc = frappe.utils.escape_html;
	const wrapper = frm.fields_dict.price_history_html.$wrapper;
	let head = `<div class="text-muted">${__("No price yet", null, "NC Item")}</div>`;
	if (effective && effective.price) {
		const warns = (effective.warnings || []).map((w) => pill(w, "orange")).join(" ");
		head =
			`<div><b>${__("Price in use today", null, "NC Item")}:</b> ${esc(format_number(effective.price.unit_price, null, 4))} ` +
			`(${esc(effective.price.price_source)}) ${warns}</div>`;
		if (frm.doc.norm_units_per_purchase_unit > 1 || frm.doc.norm_uom) {
			head += `<div>${__("Price per norm unit", null, "NC Item")}: ${esc(format_number(effective.norm_unit_price, null, 4))} / ${esc(effective.norm_uom || frm.doc.uom)}</div>`;
		}
	}
	const body = (rows || [])
		.map((r) => {
			const ok = r.verification_status === "Đã xác minh";
			return (
				`<tr><td><a href="/app/nc-item-price/${encodeURIComponent(r.name)}">${esc(r.price_code || r.name)}</a></td>` +
				`<td>${esc(r.price_source)}</td><td class="text-right">${esc(format_number(r.unit_price, null, 4))}</td>` +
				`<td>${esc(r.document_no)}</td><td>${esc(frappe.datetime.str_to_user(r.valid_from))}</td>` +
				`<td>${esc(r.valid_to ? frappe.datetime.str_to_user(r.valid_to) : "")}</td>` +
				`<td>${ok ? pill(__("Verified", null, "NC Item"), "green") : pill(__("Unverified", null, "NC Item"), "orange")}</td></tr>`
			);
		})
		.join("");
	const table = rows && rows.length
		? `<div style="overflow-x:auto"><table class="table table-bordered"><thead><tr><th>${__("Price code", null, "NC Item")}</th><th>${__("Source", null, "NC Item")}</th><th>${__("Unit price", null, "NC Item")}</th><th>${__("Document no.", null, "NC Item")}</th><th>${__("Valid from", null, "NC Item")}</th><th>${__("Valid to", null, "NC Item")}</th><th>${__("Verification", null, "NC Item")}</th></tr></thead><tbody>${body}</tbody></table></div>`
		: "";
	wrapper.html(head + table);
}

frappe.ui.form.on("NC Item", {
	refresh(frm) {
		frm.toggle_display("price_section", !frm.is_new());
		if (frm.is_new()) return;
		if (frappe.model.can_create("NC Item Price")) {
			frm.add_custom_button(__("Add price", null, "NC Item"), () =>
				frappe.new_doc("NC Item Price", { item: frm.doc.name })
			);
		}
		Promise.all([
			frappe.db.get_list("NC Item Price", {
				filters: { item: frm.doc.name },
				fields: ["name", "price_code", "price_source", "unit_price", "document_no", "valid_from", "valid_to", "verification_status"],
				order_by: "valid_from desc",
				limit: 100,
			}),
			frappe.xcall(PRICE_API, { item: frm.doc.name }),
		]).then(([rows, effective]) => render_prices(frm, rows, effective));
	},
});
