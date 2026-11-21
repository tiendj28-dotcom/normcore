frappe.pages["procedure-editor"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Procedure editor"),
		single_column: true,
	});
	frappe.require("procedure_editor.bundle.js").then(() => {
		wrapper.procedure_editor = new normcore.ProcedureEditor(page, frappe.get_route()[1]);
	});
};

frappe.pages["procedure-editor"].on_page_show = function (wrapper) {
	const name = frappe.get_route()[1];
	if (wrapper.procedure_editor && name) wrapper.procedure_editor.load(name);
};
