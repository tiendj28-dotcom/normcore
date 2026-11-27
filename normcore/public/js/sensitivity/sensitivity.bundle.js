import { createApp } from "vue";
import Sensitivity from "./Sensitivity.vue";

frappe.provide("normcore");

// Gắn ứng dụng Vue vào trang Desk. Trình duyệt chỉ gọi get_sensitivity_base, run_sensitivity của normcore.api.costing:
// trang không ghi dữ liệu (ADR-010 [1.1], FR-COST-030).
normcore.Sensitivity = class {
	constructor(page, name) {
		this.page = page;
		const mount = $('<div class="nc-sens"></div>').appendTo(page.main);
		this.app = createApp(Sensitivity, { initialName: name || "" });
		SetVueGlobals(this.app);
		this.vm = this.app.mount(mount[0]);
	}
	load(name) {
		this.vm.load(name);
	}
};
