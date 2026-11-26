// SCR-DSK-015: phiếu bấm giờ (FEAT-014). Bảng ghi theo bước vẽ vào entry_panel; ghi dữ liệu bằng lưu form chuẩn.
// Quyền do máy chủ kiểm; ẩn hiện nút chỉ là tiện ích giao diện.
frappe.dom.set_style(`
.nc-ts-step { border-bottom: 1px solid var(--border-color); padding: 8px 0; }
.nc-ts-head { margin-bottom: 8px; }
.nc-ts-row { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 8px; margin-bottom: 8px; }
.nc-ts-label { flex: 1 1 100%; }
.nc-ts-cell { display: flex; flex-direction: column; margin: 0; }
.nc-ts-input { min-height: 44px; min-width: 88px; max-width: 100%; }
.nc-ts-panel .btn { min-height: 44px; min-width: 44px; }
@media (max-width: 1199px) { .form-layout [data-fieldname="lines"] { display: none; } }
`);

function nc_ts_render(frm, data) {
	const wrap = frm.fields_dict.entry_panel.$wrapper.empty();
	const canWrite = data.can_write;
	if (!canWrite) {
		frm.dashboard.set_headline(__("You can only view this study."));
	}
	const root = $('<div class="nc-ts-panel"></div>').appendTo(wrap);
	data.steps.forEach((step) => {
		const lines = data.lines.filter((l) => l.step_id === step.step_id);
		const idle = lines.every((l) => !(l.labor_minutes > 0) && !(l.machine_minutes > 0));
		const block = $('<section class="nc-ts-step"></section>').appendTo(root);
		const head = $('<div class="nc-ts-head"></div>').appendTo(block);
		$("<strong></strong>").text(step.step_id + " · " + step.step_title).appendTo(head);
		$('<span class="text-muted small"></span>').text(" " + __(step.phase)).appendTo(head);
		if (idle) {
			$('<span class="indicator-pill gray"></span>').text(__("Not performed")).appendTo(head);
		}
		lines.forEach((l) => {
			const row = $('<div class="nc-ts-row"></div>').appendTo(block);
			const label = l.job_title ? l.job_title_label : l.equipment ? l.equipment_label : __("No resource selected");
			$('<div class="nc-ts-label"></div>').text(label).appendTo(row);
			const fields = l.job_title ? ["headcount", "labor_minutes"] : ["machine_minutes"];
			fields.forEach((f) => {
				const caption = { headcount: __("Headcount"), labor_minutes: __("Minutes"), machine_minutes: __("Machine minutes") }[f];
				const cell = $('<label class="nc-ts-cell"></label>').appendTo(row);
				$('<span class="small text-muted"></span>').text(caption).appendTo(cell);
				const input = $('<input class="form-control nc-ts-input" type="number" inputmode="decimal" min="0" step="any">')
					.attr("data-field", f)
					.attr("aria-label", label + " — " + caption)
					.val(l[f] || "")
					.prop("disabled", !canWrite)
					.appendTo(cell);
				input.on("change", () => {
					frappe.model.set_value("NC Time Study Line", l.name, f, parseFloat(input.val()) || 0);
				});
				input.on("focus", () => input[0].scrollIntoView({ block: "center" }));
				input.on("keydown", (e) => {
					if (e.key !== "Enter") return;
					e.preventDefault();
					const all = root.find("input.nc-ts-input").toArray();
					const next = all[all.indexOf(input[0]) + 1];
					if (next) next.focus();
				});
			});
		});
	});
}

function nc_ts_load(frm) {
	const wrap = frm.fields_dict.entry_panel.$wrapper.empty();
	$('<div role="status" class="text-muted"></div>').text(__("Loading...")).appendTo(wrap);
	frappe.call({
		method: "normcore.api.time_study.get_entry",
		args: { name: frm.doc.name },
		callback: (r) => r.message && nc_ts_render(frm, r.message),
		error: () => {
			wrap.empty();
			const alertBox = $('<div role="alert" class="text-danger"></div>').text(__("Could not load the study.")).appendTo(wrap);
			$('<button class="btn btn-default btn-sm"></button>')
				.text(__("Retry"))
				.on("click", () => nc_ts_load(frm))
				.appendTo(alertBox);
		},
	});
}

frappe.ui.form.on("NC Time Study", {
	setup(frm) {
		frm.set_query("procedure", () => ({
			filters: {
				workflow_state: "Đã ban hành",
				technical_service: frm.doc.technical_service,
				department: frm.doc.department,
			},
		}));
	},
	refresh(frm) {
		const panel = frm.fields_dict.entry_panel.$wrapper.empty();
		if (frm.is_new()) {
			const msg = frm.doc.technical_service && frm.doc.department
				? __("Save to load the steps of the procedure.")
				: __("Choose a service and department to load the steps of the published procedure.");
			$("<div class='text-muted'></div>").text(msg).appendTo(panel);
			return;
		}
		nc_ts_load(frm);
		frm.add_custom_button(__("View time study result"), () =>
			frappe.set_route("query-report", "NC Time Study Result", {
				technical_service: frm.doc.technical_service,
				department: frm.doc.department,
				procedure: frm.doc.procedure,
			})
		);
		frm.add_custom_button(__("Record new study"), () =>
			frappe.new_doc("NC Time Study", {
				technical_service: frm.doc.technical_service,
				department: frm.doc.department,
			})
		);
	},
	after_save(frm) {
		nc_ts_load(frm);
	},
});
