import { createApp } from "vue";
import ProcedureEditor from "./ProcedureEditor.vue";

frappe.provide("normcore");

// Gắn ứng dụng Vue vào trang Desk. Trình duyệt chỉ gọi API whitelisted, không ghi thẳng DocType (ADR-010).
normcore.ProcedureEditor = class {
	constructor(page, name) {
		this.page = page;
		const mount = $('<div class="nc-procedure-editor"></div>').appendTo(page.main);
		this.app = createApp(ProcedureEditor, { initialName: name || "" });
		this.vm = this.app.mount(mount[0]);
	}
	load(name) {
		this.vm.load(name);
	}
};
