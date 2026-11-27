// SCR-DSK-025 (FEAT-026): đơn vị tham chiếu, lập phiếu khảo sát giá theo Phụ lục I (FR-BM-008).
frappe.ui.form.on("NC Benchmark Facility", {
	refresh(frm) {
		if (frm.is_new() || !frappe.model.can_create("NC Benchmark Price")) return;
		frm.add_custom_button(__("Price survey"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Price survey"),
				fields: [
					{ fieldname: "price_category", fieldtype: "Link", options: "NC Price Category", label: __("Price category"), reqd: 1 },
					{ fieldname: "specialty", fieldtype: "Link", options: "NC Specialty", label: __("Specialty") },
					{ fieldname: "services", fieldtype: "MultiSelectList", label: __("Services"), get_data: (txt) => frappe.db.get_link_options("NC Technical Service", txt) },
				],
				primary_action_label: __("Download"),
				primary_action(values) {
					const services = (values.services || []).map((s) => s.value || s);
					if (!values.specialty && !services.length) {
						frappe.msgprint(__("Choose a specialty or services"));
						return;
					}
					const params = new URLSearchParams({ facility: frm.doc.name, price_category: values.price_category });
					if (values.specialty) params.set("specialty", values.specialty);
					if (services.length) params.set("services", JSON.stringify(services));
					window.open("/api/method/normcore.api.benchmark.download_price_survey?" + params.toString());
					dialog.hide();
				},
			});
			dialog.show();
		});
	},
});
