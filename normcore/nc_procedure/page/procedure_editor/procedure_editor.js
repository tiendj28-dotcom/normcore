frappe.pages["procedure-editor"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Procedure editor"),
		single_column: true,
	});
	frappe.require("procedure_editor.bundle.js").then(() => {
		wrapper.procedure_editor = new normcore.ProcedureEditor(page, frappe.get_route()[1]);
		const route = frappe.get_route();
		if (route[2] === "compare") wrapper.procedure_editor.show(route[1], route[3]);
	});
};

frappe.pages["procedure-editor"].on_page_show = function (wrapper) {
	const route = frappe.get_route();
	const name = route[1];
	if (wrapper.procedure_editor && name) wrapper.procedure_editor.show(name, route[2] === "compare" ? route[3] : null);
};
