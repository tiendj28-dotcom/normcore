// Chạy hành vi thật của ProcedureEditor.vue (khối <script>) trong Node, không cần Vue hay trình duyệt.
// frappe.call giả lập trả về đối tượng kiểu jQuery Deferred: có then/catch nhưng KHÔNG có finally.
// Dùng: node procedure_editor_harness.js <ProcedureEditor.vue> <kịch bản>  → in JSON kết quả.
const fs = require("fs");

const src = fs.readFileSync(process.argv[2], "utf8");
const scenario = process.argv[3];
const script = src.match(/<script>([\s\S]*?)<\/script>/)[1].replace("export default", "return");
const component = new Function(script)();

const consoleErrors = [];
console.error = (...a) => consoleErrors.push(a.map(String).join(" "));
process.on("unhandledRejection", (e) => consoleErrors.push("unhandledRejection: " + e));

function deferred(p) {
	return {
		then: (a, b) => deferred(p.then(a, b)),
		catch: (f) => deferred(p.catch(f)),
		done: (f) => deferred(p.then(f)),
		fail: (f) => deferred(p.catch(f)),
	};
}

const steps = (ids) => ids.map((id) => ({ step_id: id, step_title: id, phase: "Thực hiện", description: "d" }));
const state = { order: ["S1", "S2", "S3"], calls: [], failMethod: "" };
const procDoc = () => ({ name: "QT-1", can_edit: true, sections: [], steps: steps(state.order), resources: [] });

globalThis.__ = (s) => s;
globalThis.frappe = {
	call(opts) {
		const m = opts.method.split(".").pop();
		state.calls.push(m);
		const p = new Promise((resolve, reject) => {
			setTimeout(() => {
				if (m === state.failMethod) {
					const r = { _server_messages: JSON.stringify([JSON.stringify({ message: "Lỗi máy chủ" })]) };
					if (opts.error) opts.error(r);
					return reject({ responseJSON: r });
				}
				if (m === "reorder_steps") state.order = opts.args.order;
				const out = { get_procedure: procDoc(), list_procedures: [], create_procedure: { name: "QT-1" }, copy_procedure: { name: "QT-1" }, find_existing: { draft: "QT-9" } }[m];
				resolve({ message: out === undefined ? {} : out });
			}, 0);
		});
		return deferred(p);
	},
	confirm: () => {},
	model: { can_create: () => true },
};

// vm tối giản: dữ liệu + phương thức, $el giả lập các nút Lên/Xuống theo thứ tự hiện tại.
function makeVm() {
	const vm = Object.assign({}, component.data.call({ initialName: "" }));
	for (const [k, f] of Object.entries(component.methods)) vm[k] = f.bind(vm);
	vm.doc = procDoc();
	vm.focused = null;
	vm.$nextTick = (f) => Promise.resolve().then(f);
	const buttons = () =>
		vm.doc.steps.flatMap((s, i, all) => [
			{ key: s.step_id + ":up", disabled: i === 0 || vm.busy },
			{ key: s.step_id + ":down", disabled: i === all.length - 1 || vm.busy },
		]);
	vm.$el = {
		querySelector(sel) {
			const exact = sel.match(/^\[data-move="(.+)"\]:not\(\[disabled\]\)$/);
			const prefix = sel.match(/^\[data-move\^="(.+)"\]:not\(\[disabled\]\)$/);
			const hit = buttons().find((b) => !b.disabled && (exact ? b.key === exact[1] : prefix && b.key.startsWith(prefix[1])));
			return hit ? { focus: () => (vm.focused = hit.key) } : null;
		},
	};
	return vm;
}

async function main() {
	const vm = makeVm();
	const r = {};
	if (scenario === "step_ok" || scenario === "step_error") {
		vm.form = { kind: "step", row: null, phase: "Thực hiện", step_title: "x", description: "y" };
		if (scenario === "step_error") state.failMethod = "add_step";
		await vm.submitStep();
	} else if (scenario === "create_ok" || scenario === "copy_ok") {
		vm.form = { kind: scenario === "create_ok" ? "create" : "copy", service: "DV1", department: "KH1" };
		await vm.submitProcedureForm();
	} else if (scenario.startsWith("move_")) {
		const [, id, dir] = scenario.split("_");
		const i = state.order.indexOf(id);
		await vm.move(i, dir === "up" ? -1 : 1, { currentTarget: { dataset: { move: `${id}:${dir}` } } });
		r.focused = vm.focused;
		r.order = state.order;
	}
	await new Promise((res) => setTimeout(res, 5));
	Object.assign(r, { busy: vm.busy, loading: vm.loading, error: vm.error, existing: vm.existing, calls: state.calls, consoleErrors });
	console.log(JSON.stringify(r));
}
main().catch((e) => {
	console.log(JSON.stringify({ crash: String(e), consoleErrors }));
});
