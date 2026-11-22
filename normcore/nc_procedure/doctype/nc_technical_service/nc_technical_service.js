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
			let body = "";
			if (item.state === "no_permission") {
				body = pill(item.message, "gray");
			} else if (item.key === "price") {
				body = `<a href="#nc-chain-price" class="nc-chain-price-link">${esc(item.message)}</a>`;
			} else if (item.state === "empty" && !(item.rows || []).length) {
				body = pill(item.message || __("None yet"), "gray");
			} else {
				body = item.rows
					.map((row) => {
						const dept = `<div class="text-muted">${esc(row.department_name || row.department)}</div>`;
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

frappe.ui.form.on("NC Technical Service", {
	refresh(frm) {
		load_chain(frm);
	},
	after_save(frm) {
		load_chain(frm);
	},
});
