// NORM-31: chạy nc_accounting_import.js thật trong Node. Dùng: node harness.js <js> <kịch bản>
const fs = require("fs");
const vm = require("vm");

const [file, scenario] = process.argv.slice(2);
const consoleErrors = [];
const msgprint_calls = [];
const dialogs = [];
let handlers = null;
const buttons = {};

const fmt = (s, args) => String(s).replace(/\{(\d+)\}/g, (_, i) => (args && args[i] !== undefined ? args[i] : ""));
const frappe = {
	ui: {
		form: { on(dt, h) { handlers = h; } },
		Dialog: function (opts) {
			dialogs.push({ title: opts.title, fields: opts.fields });
			this.show = () => {};
			this.hide = () => {};
		},
	},
	utils: { escape_html: (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;") },
	msgprint(m) { msgprint_calls.push(m); },
	call() {},
	format: (v) => String(v),
	urllib: { get_full_url: (u) => u },
	confirm() {},
	show_alert() {},
};
const sandbox = {
	frappe, __: (s, args) => fmt(s, args), window: { open() {} }, $: () => ({ html() {}, empty() {} }),
	console: { error: (...a) => consoleErrors.push(a.join(" ")), log() {} },
};
vm.createContext(sandbox);

const LINES = [
	{ name: "r1", idx: 1, account_code: "6411", cost_category: "LABOR", is_excluded: 0 },
	{ name: "r2", idx: 2, account_code: "6412", cost_category: "UTILITY", is_excluded: 0 },
	{ name: "r3", idx: 3, account_code: "6421", cost_category: "MANAGEMENT", is_excluded: 0 },
];

try {
	vm.runInContext(fs.readFileSync(file, "utf8"), sandbox);
	let selected;
	if (scenario === "none") selected = [];
	else if (scenario === "one") selected = [LINES[2]];
	else if (scenario === "many") selected = [LINES[0], LINES[2]];
	else if (scenario === "html") selected = [{ ...LINES[2], account_code: "<b>6421</b>" }];
	else throw new Error("kịch bản lạ: " + scenario);
	const noop = { html() {}, empty() {}, append() {} };
	const frm = {
		doc: { name: "ACI-1", status: "Nháp", lines: LINES },
		perm: [{ write: 1 }],
		is_new: () => false,
		set_intro() {},
		page: { set_primary_action() {} },
		fields_dict: {
			lines: { grid: { get_selected_children: () => selected, update_docfield_property() {} } },
			summary_html: { $wrapper: noop },
		},
		add_custom_button(label, fn) { buttons[label] = fn; },
		dashboard: { clear_headline() {}, set_headline() {}, add_section() {} },
		reload_doc() {},
	};
	handlers.refresh(frm);
	const fn = buttons["Edit cost category of a line"];
	if (!fn) throw new Error("không có nút sửa dòng: " + Object.keys(buttons));
	fn();
	console.log(JSON.stringify({ dialogs, msgprint_calls, consoleErrors }));
} catch (e) {
	console.log(JSON.stringify({ crash: String((e && e.stack) || e) }));
}
