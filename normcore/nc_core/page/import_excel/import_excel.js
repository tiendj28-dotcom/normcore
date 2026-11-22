frappe.pages["import-excel"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Import data from Excel"),
		single_column: true,
	});
	wrapper.import_excel = new normcore.ImportExcel(page);
};

frappe.provide("normcore");

normcore.ImportExcel = class ImportExcel {
	constructor(page) {
		this.page = page;
		this.file_url = null;
		this.checked = false;
		this.api = "normcore.api.importer.";
		this.make();
		this.load_sets();
	}

	make() {
		this.set_field = this.page.add_field({
			fieldname: "import_set",
			label: __("Catalog"),
			fieldtype: "Select",
			change: () => this.reset(),
		});
		this.page.set_secondary_action(__("Download template"), () => this.download());
		this.btn_upload = this.page.add_inner_button(__("Upload file"), () => this.upload());
		this.btn_check = this.page.add_inner_button(__("Check"), () => this.run("thu"));
		this.btn_write = this.page.add_inner_button(__("Confirm import"), () => this.run("ghi"));
		this.page.main.html(
			`<div class="nc-import-file text-muted" style="margin: var(--margin-md) 0"></div>
			<div class="nc-import-result"></div>`
		);
		this.reset();
	}

	load_sets() {
		frappe.call({
			method: this.api + "list_import_sets",
			callback: (r) => {
				const sets = r.message || [];
				this.set_field.df.options = sets.map((s) => ({ value: s.key, label: s.label }));
				this.set_field.refresh();
				if (sets.length) this.set_field.set_value(sets[0].key);
				else this.show_message(__("You do not have permission to import data."));
			},
		});
	}

	reset() {
		this.file_url = null;
		this.checked = false;
		this.page.main.find(".nc-import-file").text(__("No file chosen"));
		this.page.main.find(".nc-import-result").empty();
		this.refresh_buttons();
	}

	refresh_buttons() {
		const has_file = !!this.file_url;
		this.btn_check.prop("disabled", !has_file);
		this.btn_write.prop("disabled", !(has_file && this.checked));
	}

	download() {
		const key = this.set_field.get_value();
		if (!key) return;
		window.open(
			frappe.urllib.get_full_url(
				"/api/method/" + this.api + "download_template?import_set=" + encodeURIComponent(key)
			)
		);
	}

	upload() {
		new frappe.ui.FileUploader({
			doctype: null,
			make_attachments_public: false,
			disable_file_browser: true,
			restrictions: { allowed_file_types: [".xlsx"] },
			on_success: (file) => {
				this.file_url = file.file_url;
				this.checked = false;
				this.page.main.find(".nc-import-file").text(file.file_name);
				this.page.main.find(".nc-import-result").empty();
				this.refresh_buttons();
			},
		});
	}

	run(mode) {
		const url = this.file_url;
		frappe.call({
			method: this.api + "import_file",
			args: { import_set: this.set_field.get_value(), file_url: url, mode: mode },
			freeze: true,
			callback: (r) => {
				if (url !== this.file_url) return;
				this.checked = mode === "thu";
				this.render(r.message, mode);
				this.refresh_buttons();
			},
		});
	}

	show_message(text) {
		this.page.main.find(".nc-import-result").text(text);
	}

	render(res, mode) {
		const title = mode === "thu" ? __("Check result (nothing saved yet)") : __("Import result");
		const rows = (res.errors || [])
			.map(
				(e) =>
					`<tr><td>${e.row == null ? "" : e.row}</td><td>${frappe.utils.escape_html(
						e.column || ""
					)}</td><td>${frappe.utils.escape_html(e.message)}</td></tr>`
			)
			.join("");
		const table = rows
			? `<table class="table table-bordered"><thead><tr><th>${__("Row", null, "Import Excel")}</th><th>${__("Column", null, "Import Excel")}</th><th>${__("Message", null, "Import Excel")}</th></tr></thead><tbody>${rows}</tbody></table>`
			: "";
		const warn = (res.warnings || [])
			.map((w) => `<div class="text-muted">${frappe.utils.escape_html(w)}</div>`)
			.join("");
		this.page.main.find(".nc-import-result").html(
			`<h5>${title}</h5>
			<p>${__("Created", null, "Import Excel")}: <b>${res.created}</b> · ${__("Updated", null, "Import Excel")}: <b>${res.updated}</b> ·
			${__("Unchanged", null, "Import Excel")}: <b>${res.unchanged}</b> · ${__("Errors", null, "Import Excel")}: <b>${res.error_count}</b></p>
			${warn}${table}`
		);
	}
};
