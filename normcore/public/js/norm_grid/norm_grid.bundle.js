import { createApp } from "vue";
import NormGrid from "./NormGrid.vue";

frappe.provide("normcore");

// Gắn ứng dụng Vue vào trang Desk. Trình duyệt chỉ gọi API whitelisted normcore.api.norm.*, không ghi thẳng DocType (ADR-010).
normcore.NormGrid = class {
	constructor(page, name) {
		this.page = page;
		const mount = $('<div class="nc-norm-grid"></div>').appendTo(page.main);
		this.app = createApp(NormGrid, { initialName: name || "" });
		SetVueGlobals(this.app);
		this.vm = this.app.mount(mount[0]);
	}
	load(name) {
		this.vm.load(name);
	}
};
