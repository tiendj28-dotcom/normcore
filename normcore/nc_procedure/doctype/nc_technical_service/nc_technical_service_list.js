// SCR-DSK-005: danh sách chuẩn của Desk; thêm bộ lọc khoa thực hiện và hai nút nhập (FEAT-005, AMD-004).
frappe.listview_settings["NC Technical Service"] = {
	add_fields: ["is_active"],
	get_indicator(doc) {
		return doc.is_active
			? [__("Active", null, "NC Technical Service"), "green", "is_active,=,1"]
			: [__("Inactive", null, "NC Technical Service"), "darkgrey", "is_active,=,0"];
	},
	onload(listview) {
		listview.page.add_field({
			fieldname: "department",
			doctype: "NC Service Department",
			fieldtype: "Link",
			options: "NC Department",
			condition: "=",
			label: __("Performing department"),
			onchange() {
				listview.filter_area.debounced_refresh_list_view();
			},
		});
		normcore_chain_filter(listview);
		listview.page.add_inner_button(__("Download template"), () => {
			window.open(
				"/api/method/normcore.api.importer.download_template?import_set=nc_technical_service"
			);
		});
		if (frappe.model.can_create("NC Technical Service")) {
			listview.page.add_inner_button(__("Import from Excel"), () => {
				frappe.set_route("import-excel");
			});
		}
	},
	refresh(listview) {
		normcore_chain_dots(listview);
	},
};

const NC_MAX_FILTER = 2000;
const NC_ROUTE_PARAMS = ["nc_chain_stage", "nc_department"];

// Lấy nc_chain_stage, nc_department khỏi frappe.route_options và URL trước khi list view dựng truy vấn
// (Frappe coi chúng là trường lọc của DocType và trả 417); trả về giá trị đã đọc (NORM-57).
function normcore_take_route_params() {
	const taken = {};
	const params = new URLSearchParams(window.location.search);
	NC_ROUTE_PARAMS.forEach((key) => {
		const value = (frappe.route_options && frappe.route_options[key]) || params.get(key);
		if (value) taken[key] = value;
		if (frappe.route_options) delete frappe.route_options[key];
		params.delete(key);
	});
	const query = params.toString();
	window.history.replaceState(
		window.history.state,
		"",
		window.location.pathname + (query ? "?" + query : "") + window.location.hash
	);
	return taken;
}

// Bộ lọc "Tình trạng chuỗi" (FR-OUT-010, AMD-004); đọc nc_chain_stage, nc_department trên URL (liên kết từ trang chủ).
function normcore_chain_filter(listview) {
	let options_ready = false;
	let pending = null; // mức chờ đặt khi danh sách mức chưa nạp xong
	const field = listview.page.add_field({
		fieldname: "nc_chain_stage",
		fieldtype: "Select",
		label: __("Chain status"),
		options: "",
		onchange() {
			if (!silent) apply();
		},
	});
	let silent = false; // đặt mức từ liên kết: tự gọi apply() một lần sau khi khoa đã ghi xong
	// nc_chain_stage không phải trường của DocType: không để Frappe đưa nó vào bộ lọc/URL (NORM-57).
	const standard_filters = listview.filter_area.get_standard_filters.bind(listview.filter_area);
	listview.filter_area.get_standard_filters = () =>
		standard_filters().filter((f) => f[1] !== "nc_chain_stage");
	const dept_field = () => listview.page.fields_dict.department;
	function apply() {
		const stage = field.get_value();
		listview.filter_area.remove("name");
		if (!stage) return Promise.resolve(listview.filter_area.debounced_refresh_list_view());
		const department = dept_field() ? dept_field().get_value() : null;
		return frappe
			.xcall("normcore.api.home.services_in_stage", { stage, department: department || null })
			.then((names) => {
				if (names.length > NC_MAX_FILTER) {
					frappe.show_alert({
						message: __("Too many services, filter by department first"),
						indicator: "orange",
					});
					return;
				}
				listview.filter_area.add([[listview.doctype, "name", "in", names.length ? names : ["__none__"]]]);
			});
	}
	// Đặt mức theo liên kết và luôn tính lại bộ lọc `name`, kể cả khi giá trị mức không đổi
	// (Frappe bỏ qua set_value cùng giá trị nên onchange không chạy).
	function set_stage(stage) {
		if (!options_ready) {
			pending = stage || "";
			return Promise.resolve();
		}
		silent = true;
		return Promise.resolve(field.set_value(stage || "", true))
			.then(() => {
				silent = false;
				return apply();
			})
			.catch((e) => {
				silent = false;
				throw e;
			});
	}
	// Frappe giữ list view trong cache (onload chỉ chạy một lần): đọc và gỡ tham số ở MỖI lần list hiện ra,
	// trước khi before_refresh gốc đọc URL/route_options. Có tham số thì đặt khoa (chờ ghi xong, vì trường
	// Link kiểm tra qua mạng) rồi mới đặt mức, để apply() đọc đúng khoa mới.
	const before_refresh = listview.before_refresh.bind(listview);
	listview.before_refresh = function () {
		const taken = normcore_take_route_params();
		if (!taken.nc_chain_stage && !taken.nc_department) return before_refresh();
		const dept = dept_field();
		return Promise.resolve(dept && dept.set_value(taken.nc_department || ""))
			.then(() => set_stage(taken.nc_chain_stage))
			.then(() => before_refresh());
	};
	frappe.xcall("normcore.api.home.get_home").then((data) => {
		const labels = (data.stages || []).filter((s) => !s.no_permission).map((s) => [s.stage, s.label]);
		field.df.options = [{ label: "", value: "" }].concat(labels.map((l) => ({ value: l[0], label: l[1] })));
		field.refresh();
		options_ready = true;
		if (pending !== null) {
			const stage = pending;
			pending = null;
			return set_stage(stage);
		}
	});
}

// Cột "Tình trạng chuỗi": thẻ bốn chấm cuối mỗi dòng (không chặn danh sách khi lỗi).
function normcore_chain_dots(listview) {
	const names = (listview.data || []).map((d) => d.name);
	if (!names.length || !window.normcore || !normcore.chain_dots) return;
	frappe
		.xcall("normcore.api.home.get_service_stages", { services: JSON.stringify(names.slice(0, 500)) })
		.then((stages) => {
			listview.$result.find(".list-row-container").each(function () {
				const row = $(this);
				const name = row.find("[data-name]").first().attr("data-name");
				if (!name || !stages[name] || row.find(".nc-chain-dots").length) return;
				row.find(".list-row-col").last().append(normcore.chain_dots.render(stages[name].dots));
			});
		})
		.catch(() => {});
}
