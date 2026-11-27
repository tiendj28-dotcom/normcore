// NORM-75: chạy nc_technical_service_list.js thật trong Node với frappe giả. Dùng: node harness.js <list.js> <kịch bản>
// Giả lập ô Link "Khoa thực hiện": gõ tay rồi Tab chỉ phát sự kiện DOM change/blur, không chạy df.onchange.
const fs = require("fs");
const vm = require("vm");

const [file, scenario] = process.argv.slice(2);
const calls = [];
const filters = {};
let refreshes = 0;

function make_input() {
	const handlers = {};
	return {
		on(events, fn) {
			events.split(" ").forEach((e) => (handlers[e] = (handlers[e] || []).concat(fn)));
			return this;
		},
		trigger(e) {
			(handlers[e] || []).forEach((fn) => fn());
		},
	};
}
function make_field(df) {
	return {
		df,
		$input: make_input(),
		text: "",
		refresh() {},
		get_value() { return this.text; }, // như Frappe: đọc thẳng từ ô nhập
		set_value(v) {
			const changed = this.text !== v;
			this.text = v;
			if (changed && this.df.onchange) return this.df.onchange();
			return Promise.resolve();
		},
	};
}
const fields_dict = {};
const filter_area = {
	get_standard_filters: () => [],
	remove(k) { delete filters[k]; },
	add(list) { list.forEach((f) => (filters[f[1]] = f[3])); refreshes++; },
	debounced_refresh_list_view() { refreshes++; },
};
const listview = {
	doctype: "NC Technical Service",
	filter_area,
	before_refresh() {},
	data: [],
	page: {
		fields_dict,
		add_field(df) { const f = make_field(df); fields_dict[df.fieldname] = f; return f; },
		add_inner_button() {},
	},
};
const SERVICES = { K01: ["A", "B"], "THU-K02": ["X", "Y", "Z"] };
const frappe = {
	listview_settings: {},
	route_options: {},
	model: { can_create: () => false },
	show_alert() {},
	xcall(method, args) {
		calls.push([method, args]);
		if (method.endsWith("get_home")) return Promise.resolve({ stages: [{ stage: "A", label: "Chưa có quy trình" }] });
		if (method.endsWith("services_in_stage")) return Promise.resolve(SERVICES[args.department] || []);
		return Promise.resolve({});
	},
};
const sandbox = {
	frappe, __: (s) => s, console, setTimeout, Promise,
	URLSearchParams,
	window: { location: { search: "", pathname: "/app/nc-technical-service", hash: "" }, history: { state: null, replaceState() {} } },
	$: () => ({ find: () => ({ each() {} }) }),
};
sandbox.window.history = sandbox.window.history;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(file, "utf8"), sandbox);
sandbox.history = sandbox.window.history;

const tick = (ms = 20) => new Promise((r) => setTimeout(r, ms));

async function main() {
	listview_settings = frappe.listview_settings["NC Technical Service"];
	listview_settings.onload(listview);
	await tick();
	const dept = fields_dict.department;
	const stage = fields_dict.nc_chain_stage;
	await stage.set_value("A");
	await tick();
	// chọn từ gợi ý: onchange chạy
	await dept.set_value("K01");
	await tick();
	const after_pick = filters.name;
	// gõ tay rồi Tab: chỉ sự kiện DOM
	dept.text = "THU-K02";
	dept.$input.trigger("change");
	dept.$input.trigger("blur");
	await tick(400);
	return { after_pick, after_typed: filters.name, calls: calls.filter((c) => c[0].endsWith("services_in_stage")).length };
}
let listview_settings;
main().then((r) => console.log(JSON.stringify(r))).catch((e) => { console.log(JSON.stringify({ crash: String(e && e.stack) })); });
