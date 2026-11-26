import { createApp } from "vue";
import ProcedureEditor from "./ProcedureEditor.vue";
import ProcedureCompare from "./ProcedureCompare.vue";

frappe.provide("normcore");

// Gắn ứng dụng Vue vào trang Desk. Trình duyệt chỉ gọi API whitelisted, không ghi thẳng DocType (ADR-010).
normcore.ProcedureEditor = class {
	constructor(page, name) {
		this.page = page;
		const mount = $('<div class="nc-procedure-editor"></div>').appendTo(page.main);
		this.app = createApp(ProcedureEditor, { initialName: name || "" });
		this.app.component("ProcedureCompare", ProcedureCompare); // đăng ký toàn cục: ProcedureEditor.vue không import (harness Node chạy khối script)
		SetVueGlobals(this.app); // cung cấp __() cho template, như các ứng dụng Vue của Frappe
		this.vm = this.app.mount(mount[0]);
	}
	show(name, target) {
		return this.vm.show(name, target);
	}
	load(name) {
		this.vm.load(name);
	}
};
