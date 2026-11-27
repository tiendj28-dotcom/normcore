// SCR-DSK-025 (FEAT-026): danh sách giá tham chiếu, rà soát dòng "Đề xuất", nhập tệp.
const API = "normcore.api.benchmark.";

frappe.listview_settings["NC Benchmark Price"] = {
	add_fields: ["status", "technical_service"],
	get_indicator(doc) {
		if (doc.status === "Đã xác nhận") return [__("Confirmed"), "green", "status,=,Đã xác nhận"];
		if (doc.status === "Loại bỏ") return [__("Rejected"), "gray", "status,=,Loại bỏ"];
		if (doc.technical_service) return [__("Proposed"), "purple", "status,=,Đề xuất"];
		return [__("No service code"), "orange", "status,=,Đề xuất"];
	},
	onload(listview) {
		listview.page.add_inner_button(__("Needs review"), () => {
			listview.filter_area.clear().then(() => listview.filter_area.add([["NC Benchmark Price", "status", "=", "Đề xuất"]]));
		});
		listview.page.add_inner_button(__("No service code"), () => {
			listview.filter_area.clear().then(() =>
				listview.filter_area.add([
					["NC Benchmark Price", "status", "=", "Đề xuất"],
					["NC Benchmark Price", "technical_service", "is", "not set"],
				])
			);
		});
		if (!frappe.model.can_create("NC Benchmark Price")) return;
		listview.page.add_inner_button(__("Download template"), () => {
			window.open("/api/method/normcore.api.importer.download_template?import_set=nc_benchmark_price");
		});
		listview.page.add_inner_button(__("Import from Excel"), () => {
			frappe.set_route("import-excel", { import_set: "nc_benchmark_price" });
		});
		if (!frappe.model.can_write("NC Benchmark Price")) return;
		const bulk = (label, method, key) =>
			listview.page.add_actions_menu_item(__(label, null, "NC Benchmark Price"), () => {
				const names = listview.get_checked_items(true);
				if (!names.length) return;
				const run = () =>
					frappe.call({
						method: API + method,
						args: { names },
						freeze: true,
						callback(r) {
							const done = (r.message && r.message[key]) || [];
							const errors = (r.message && r.message.errors) || [];
							frappe.show_alert({ message: __("{0} rows updated", [done.length]), indicator: "green" });
							if (errors.length) {
								const rows = errors.map((e) => `<tr><td>${frappe.utils.escape_html(e.name)}</td><td>${frappe.utils.escape_html(e.message)}</td></tr>`);
								frappe.msgprint({ title: __("Some rows were not updated"), message: `<table class="table table-bordered">${rows.join("")}</table>` });
							}
							listview.refresh();
						},
					});
				if (method === "confirm_prices") {
					frappe.confirm(__("Confirm {0} reference prices?", [names.length]), run);
				} else {
					run();
				}
			});
		bulk("Confirm", "confirm_prices", "confirmed");
		bulk("Reject", "reject_prices", "rejected");
		bulk("Reopen", "reopen_prices", "reopened");
	},
};
