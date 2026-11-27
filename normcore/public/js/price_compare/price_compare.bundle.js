import { createApp } from "vue";
import PriceCompare from "./PriceCompare.vue";

frappe.provide("normcore");

// Gắn ứng dụng Vue vào trang Desk. Trình duyệt chỉ gọi normcore.api.price_compare (FEAT-028).
normcore.PriceCompare = class {
	constructor(page, run) {
		this.page = page;
		const mount = $('<div class="nc-pc"></div>').appendTo(page.main);
		this.app = createApp(PriceCompare, { initialRun: run || "" });
		SetVueGlobals(this.app);
		this.vm = this.app.mount(mount[0]);
	}
	load(run) {
		this.vm.load(run);
	}
};
