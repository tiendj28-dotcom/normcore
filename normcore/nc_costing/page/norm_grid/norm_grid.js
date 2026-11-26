frappe.pages["norm-grid"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Norm grid"),
		single_column: true,
	});
	frappe.require("norm_grid.bundle.js").then(() => {
		wrapper.norm_grid = new normcore.NormGrid(page, frappe.get_route()[1]);
	});
};

frappe.pages["norm-grid"].on_page_show = function (wrapper) {
	const name = frappe.get_route()[1];
	if (wrapper.norm_grid && name) wrapper.norm_grid.load(name);
};
