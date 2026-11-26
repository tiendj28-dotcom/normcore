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

// Bộ lọc "Tình trạng chuỗi" (FR-OUT-010, AMD-004); đọc nc_chain_stage, nc_department trên URL (liên kết từ trang chủ).
function normcore_chain_filter(listview) {
	const field = listview.page.add_field({
		fieldname: "nc_chain_stage",
		fieldtype: "Select",
		label: __("Chain status"),
		options: "",
		onchange() {
			apply();
		},
	});
	const dept_field = () => listview.page.fields_dict.department;
	function apply() {
		const stage = field.get_value();
		listview.filter_area.remove("name");
		if (!stage) return listview.filter_area.debounced_refresh_list_view();
		const department = dept_field() ? dept_field().get_value() : null;
		frappe
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
	frappe.xcall("normcore.api.home.get_home").then((data) => {
		const labels = (data.stages || []).filter((s) => !s.no_permission).map((s) => [s.stage, s.label]);
		field.df.options = [{ label: "", value: "" }].concat(labels.map((l) => ({ value: l[0], label: l[1] })));
		field.refresh();
		const params = new URLSearchParams(window.location.search);
		if (params.get("nc_department") && dept_field()) dept_field().set_value(params.get("nc_department"));
		if (params.get("nc_chain_stage")) field.set_value(params.get("nc_chain_stage"));
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
