// NORM-31: chạy import_excel.js thật trong Node với frappe giả. Dùng: node harness.js <import_excel.js> <kịch bản>
const fs = require("fs");
const vm = require("vm");

const [file, scenario] = process.argv.slice(2);
const SETS = [
	{ key: "nc_account_mapping", label: "Ánh xạ tài khoản" },
	{ key: "nc_service_volume", label: "Sản lượng dịch vụ" },
	{ key: "nc_cost_center_driver", label: "Tiêu chí trung tâm" },
];
const consoleErrors = [];
const msgprint_calls = [];
const state = { texts: {}, disabled: {} };
const pendingCalls = [];

function node(sel) {
	return {
		text(v) { if (v !== undefined) state.texts[sel] = v; return this; },
		html(v) { if (v !== undefined) state.texts[sel] = v; return this; },
		empty() { if (sel === ".nc-import-result") state.texts[sel] = ""; return this; },
		prop(k, v) { state.disabled[sel] = v; return this; },
		find(s) { return node(s); },
	};
}
function button(name) {
	return { prop(k, v) { state.disabled[name] = v; return this; } };
}

function make_field(df) {
	const f = {
		df,
		value: undefined,
		refresh() {},
		get_value() { return this.value; },
		set_value(v) {
			const changed = this.value !== v;
			this.value = v;
			if (changed && df.change) df.change();
		},
	};
	return f;
}

const frappe = {
	pages: {},
	route_options: null,
	provide() {},
	ui: {
		make_app_page() {
			return {
				add_field(df) { return make_field(df); },
				set_secondary_action() {},
				add_inner_button(label) { return button(label); },
				main: node(""),
			};
		},
		FileUploader: function () {},
	},
	call(opts) { pendingCalls.push(opts); },
	msgprint(m) { msgprint_calls.push(m); },
	throw(m) { msgprint_calls.push("throw:" + m); },
	utils: { escape_html: (s) => String(s) },
	urllib: { get_full_url: (u) => u },
};
const sandbox = {
	frappe, normcore: {}, __: (s) => s, window: { open() {} }, $: () => node(""),
	console: { error: (...a) => consoleErrors.push(a.join(" ")), log() {} },
};
sandbox.window.frappe = frappe;
vm.createContext(sandbox);
frappe.pages["import-excel"] = {};

function resolve(sets) {
	const c = pendingCalls.shift();
	c.callback({ message: sets });
}
function snapshot(wrapper) {
	const ie = wrapper.import_excel;
	return {
		value: ie.set_field.get_value(),
		set_name: state.texts[".nc-import-set"],
		file_url: ie.file_url,
		btn_check_disabled: state.disabled["Check"],
		message: state.texts[".nc-import-result"],
		route_options: frappe.route_options,
		msgprint_calls,
		consoleErrors,
	};
}
function load(wrapper) {
	frappe.pages["import-excel"].on_page_load(wrapper);
	if (frappe.pages["import-excel"].on_page_show) frappe.pages["import-excel"].on_page_show(wrapper);
}
function show(wrapper) {
	if (frappe.pages["import-excel"].on_page_show) frappe.pages["import-excel"].on_page_show(wrapper);
}

try {
	vm.runInContext(fs.readFileSync(file, "utf8"), sandbox);
	const wrapper = {};
	let out;
	if (scenario === "route_ok") {
		frappe.route_options = { import_set: "nc_service_volume" };
		load(wrapper); resolve(SETS); out = snapshot(wrapper);
	} else if (scenario === "route_before_load") {
		// on_page_show chạy sau khi danh sách đã tải xong
		frappe.pages["import-excel"].on_page_load(wrapper); resolve(SETS);
		frappe.route_options = { import_set: "nc_cost_center_driver" };
		show(wrapper); out = snapshot(wrapper);
	} else if (scenario === "route_bad") {
		frappe.route_options = { import_set: "khong_co" };
		load(wrapper); resolve(SETS); out = snapshot(wrapper);
	} else if (scenario === "no_route") {
		load(wrapper); resolve(SETS); out = snapshot(wrapper);
	} else if (scenario === "reopen_other") {
		frappe.route_options = { import_set: "nc_account_mapping" };
		load(wrapper); resolve(SETS);
		wrapper.import_excel.file_url = "/private/files/a.xlsx"; wrapper.import_excel.refresh_buttons();
		frappe.route_options = { import_set: "nc_service_volume" };
		show(wrapper); out = snapshot(wrapper);
	} else if (scenario === "consumed") {
		frappe.route_options = { import_set: "nc_service_volume" };
		load(wrapper); resolve(SETS);
		wrapper.import_excel.set_field.set_value("nc_cost_center_driver");
		show(wrapper); out = snapshot(wrapper);
	} else if (scenario === "empty_sets") {
		frappe.route_options = { import_set: "nc_service_volume" };
		load(wrapper); resolve([]); out = snapshot(wrapper);
	} else {
		throw new Error("kịch bản lạ: " + scenario);
	}
	console.log(JSON.stringify(out));
} catch (e) {
	console.log(JSON.stringify({ crash: String(e && e.stack || e) }));
}
