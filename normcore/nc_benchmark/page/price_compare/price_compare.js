// SCR-DSK-026 (FEAT-028): Bàn so sánh giá. Trang chỉ gọi normcore.api.price_compare.
frappe.pages["price-compare"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Price comparison"),
		single_column: true,
	});
	frappe.require("price_compare.bundle.js").then(() => {
		wrapper.price_compare = new normcore.PriceCompare(page, runFromRoute());
	});
};

frappe.pages["price-compare"].on_page_show = function (wrapper) {
	const run = runFromRoute();
	if (wrapper.price_compare && run) wrapper.price_compare.load(run);
};

function runFromRoute() {
	return (frappe.route_options || {}).run || new URLSearchParams(window.location.search).get("run") || "";
}
