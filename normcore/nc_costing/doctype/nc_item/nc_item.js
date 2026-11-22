// SCR-DSK-017: mặt hàng. Thẻ đơn giá đang dùng tại hôm nay (FR-RES-004) và lịch sử đơn giá có chứng từ.
const PRICE_API = "normcore.api.item.get_effective_price";

function pill(label, indicator) {
	return `<span class="indicator-pill ${frappe.utils.escape_html(indicator)}"><span>${frappe.utils.escape_html(label)}</span></span>`;
}

function render_prices(frm, rows, effective) {
	const esc = frappe.utils.escape_html;
	const wrapper = frm.fields_dict.price_history_html.$wrapper;
	let head = `<div class="text-muted">${__("No price yet")}</div>`;
	if (effective && effective.price) {
		const warns = (effective.warnings || []).map((w) => pill(w, "orange")).join(" ");
		head =
			`<div><b>${__("Price in use today")}:</b> ${esc(format_number(effective.price.unit_price, null, 4))} ` +
			`(${esc(effective.price.price_source)}) ${warns}</div>`;
		if (frm.doc.norm_units_per_purchase_unit > 1 || frm.doc.norm_uom) {
			head += `<div>${__("Price per norm unit")}: ${esc(format_number(effective.norm_unit_price, null, 4))} / ${esc(effective.norm_uom || frm.doc.uom)}</div>`;
		}
	}
	const body = (rows || [])
		.map((r) => {
			const ok = r.verification_status === "Đã xác minh";
			return (
				`<tr><td><a href="/app/nc-item-price/${encodeURIComponent(r.name)}">${esc(r.name)}</a></td>` +
				`<td>${esc(r.price_source)}</td><td class="text-right">${esc(format_number(r.unit_price, null, 4))}</td>` +
				`<td>${esc(r.document_no)}</td><td>${esc(frappe.datetime.str_to_user(r.valid_from))}</td>` +
				`<td>${esc(r.valid_to ? frappe.datetime.str_to_user(r.valid_to) : "")}</td>` +
				`<td>${ok ? pill(__("Verified"), "green") : pill(__("Unverified"), "orange")}</td></tr>`
			);
		})
		.join("");
	const table = rows && rows.length
		? `<table class="table table-bordered"><thead><tr><th>${__("Price")}</th><th>${__("Source")}</th><th>${__("Unit price")}</th><th>${__("Document no.")}</th><th>${__("Valid from")}</th><th>${__("Valid to")}</th><th>${__("Verification")}</th></tr></thead><tbody>${body}</tbody></table>`
		: "";
	wrapper.html(head + table);
}

frappe.ui.form.on("NC Item", {
	refresh(frm) {
		frm.toggle_display("price_section", !frm.is_new());
		if (frm.is_new()) return;
		if (frappe.model.can_create("NC Item Price")) {
			frm.add_custom_button(__("Add price"), () =>
				frappe.new_doc("NC Item Price", { item: frm.doc.name })
			);
		}
		Promise.all([
			frappe.db.get_list("NC Item Price", {
				filters: { item: frm.doc.name },
				fields: ["name", "price_source", "unit_price", "document_no", "valid_from", "valid_to", "verification_status"],
				order_by: "valid_from desc",
				limit: 100,
			}),
			frappe.xcall(PRICE_API, { item: frm.doc.name }),
		]).then(([rows, effective]) => render_prices(frm, rows, effective));
	},
});
