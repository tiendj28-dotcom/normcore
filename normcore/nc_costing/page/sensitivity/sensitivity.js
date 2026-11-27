frappe.pages["sensitivity"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Sensitivity analysis"),
		single_column: true,
	});
	frappe.require("sensitivity.bundle.js").then(() => {
		wrapper.sensitivity = new normcore.Sensitivity(page, (frappe.route_options || {}).service_cost || frappe.get_route()[1]);
	});
};

frappe.pages["sensitivity"].on_page_show = function (wrapper) {
	const name = (frappe.route_options || {}).service_cost || frappe.get_route()[1];
	if (wrapper.sensitivity && name) wrapper.sensitivity.load(name);
};
