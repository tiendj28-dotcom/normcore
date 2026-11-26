// SCR-DSK-012 (FEAT-021): hàng đợi rà soát quy trình khi văn bản hoặc mục hết hiệu lực (FR-LIB-009, UC-002 bước 6–7).
frappe.pages["review-queue"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Review queue"),
		single_column: true,
	});
	wrapper.review_queue = new normcore.ReviewQueue(page);
};

frappe.pages["review-queue"].on_page_show = function (wrapper) {
	if (wrapper.review_queue) wrapper.review_queue.load(0);
};

frappe.provide("normcore");

normcore.ReviewQueue = class ReviewQueue {
	constructor(page) {
		this.page = page;
		this.page_length = 50;
		this.rows = [];
		this.total = 0;
		this.department = this.page.add_field({
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "NC Department",
			change: () => this.load(0),
		});
		const $main = $(this.page.main);
		$main.html(
			`<p class="text-muted small">${__("Issued · Needs review")}</p>` +
				`<p class="nc-rq-summary"></p><div class="nc-rq-list"></div><div class="nc-rq-more"></div>`
		);
		this.$summary = $main.find(".nc-rq-summary");
		this.$list = $main.find(".nc-rq-list");
		this.$more = $main.find(".nc-rq-more");
	}

	load(start) {
		if (!start) {
			this.rows = [];
			this.$list.html(`<p class="text-muted">${__("Loading...")}</p>`);
		}
		this.$more.empty();
		frappe.call({
			method: "normcore.api.review.get_review_queue",
			args: { department: this.department.get_value() || null, start: start, page_length: this.page_length },
			callback: (r) => {
				const res = r.message || { rows: [], total: 0 };
				this.total = res.total;
				this.rows = start ? this.rows.concat(res.rows) : res.rows;
				this.render();
			},
			error: (r) => this.show_error(r),
		});
	}

	show_error(r) {
		const denied = r && r.exc_type === "PermissionError";
		const msg = denied
			? __("You do not have permission to view procedures")
			: __("Could not load the review queue");
		this.$summary.empty();
		this.$list.html(`<div class="alert alert-danger">${frappe.utils.escape_html(msg)}</div>`);
		if (!denied) {
			const $retry = $(`<button class="btn btn-default btn-sm">${__("Retry")}</button>`);
			$retry.on("click", () => this.load(0));
			this.$list.append($retry);
		}
	}

	render() {
		this.$summary.text(__("{0} procedures need review", [this.total]));
		this.$list.empty();
		if (!this.rows.length) {
			const $empty = $(
				`<div class="text-muted"><p>${__("No procedures need review. A procedure is flagged when a cited legal document or section expires.")}</p>` +
					`<button class="btn btn-default btn-sm">${__("Open procedure list")}</button></div>`
			);
			$empty.find("button").on("click", () => frappe.set_route("List", "NC Clinical Procedure"));
			this.$list.append($empty);
		}
		this.rows.forEach((row) => this.$list.append(this.card(row)));
		this.$more.empty();
		if (this.rows.length < this.total) {
			const $more = $(`<button class="btn btn-default btn-sm">${__("More")}</button>`);
			$more.on("click", () => this.load(this.rows.length));
			this.$more.append($more);
		}
	}

	card(row) {
		const esc = frappe.utils.escape_html;
		const date = (d) => (d ? frappe.datetime.str_to_user(d) : "");
		const $c = $(`<div class="frappe-card" style="margin-bottom: var(--margin-md)"></div>`);
		$c.append(
			`<div class="flex justify-between"><div>` +
				`<a href="/app/nc-clinical-procedure/${encodeURIComponent(row.name)}"><b>${esc(row.name)}</b></a> ` +
				`${esc(row.service_name || "")} · ${esc(row.department)} · v${row.version_no} ` +
				`<span class="indicator-pill green ellipsis"><span>${"Đã ban hành"}</span></span> ` +
				`<span class="indicator-pill yellow ellipsis"><span>${"Cần rà soát"}</span></span></div>` +
				`<div class="text-muted small">${esc(row.decision_no || "")} ${date(row.effective_date)}</div></div>`
		);
		if (row.pending_revision) {
			$c.append(
				`<p class="text-muted small">${__("Revision in progress: {0}", [
					`<a href="/app/procedure-editor/${encodeURIComponent(row.pending_revision)}">${esc(row.pending_revision)}</a>`,
				])}</p>`
			);
		}
		if (!row.citations.length) {
			$c.append(`<p class="text-muted">${__("Affected citations could not be identified")}</p>`);
		} else {
			$c.append(this.citations_table(row));
		}
		if (row.can_act) $c.append(this.actions(row));
		return $c;
	}

	citations_table(row) {
		const esc = frappe.utils.escape_html;
		const date = (d) => frappe.datetime.str_to_user(d);
		const body = row.citations
			.map((c) => {
				const where = c.target_section ? esc(c.target_section) : `${__("Step")} ${esc(c.target_step_id || "")}`;
				const doc = `<a href="/app/nc-legal-document/${encodeURIComponent(c.legal_document)}">${esc(c.doc_number || c.legal_document)}</a>`;
				const sec = c.section_no ? ` ${__("section")} ${esc(c.section_no)} — ${esc(c.heading || "")}` : ` ${__("(whole document)")}`;
				const quote = (c.quote || "").length > 160 ? c.quote.slice(0, 160) + "…" : c.quote || "";
				const repl = (c.replacements || []).length
					? c.replacements
							.map((x) => {
								const scope = x.scope === "Một phần" ? `${__("sections")}: ${esc(x.sections)}` : __("whole");
								return `<div><a href="/app/nc-legal-document/${encodeURIComponent(x.document)}">${esc(x.doc_number)}</a> — ${esc(x.title || "")}, ${scope}, ${__("from")} ${date(x.from_date)}</div>`;
							})
							.join("")
					: "—";
				return (
					`<tr><td>${where}</td><td>${doc}${sec}</td>` +
					`<td><span class="indicator-pill darkgrey ellipsis"><span>${"Hết hiệu lực"}</span></span> ${c.expiry_date ? __("from") + " " + date(frappe.datetime.add_days(c.expiry_date, 1)) : ""}</td>` +
					`<td>${esc(c.reason)}</td><td title="${esc(c.quote || "")}">${esc(quote)}</td><td>${repl}</td></tr>`
				);
			})
			.join("");
		return $(
			`<div class="table-responsive"><table class="table table-bordered"><thead><tr><th>${__("Location in procedure")}</th>` +
				`<th>${__("Document, section")}</th><th>${__("Validity")}</th><th>${__("Reason")}</th><th>${__("Quote")}</th>` +
				`<th>${__("Replacing document")}</th></tr></thead><tbody>${body}</tbody></table></div>`
		);
	}

	actions(row) {
		const $a = $(
			`<div><button class="btn btn-primary btn-sm nc-rq-revise">${__("Revise")}</button> ` +
				`<button class="btn btn-default btn-sm nc-rq-dismiss">${__("No change needed")}</button></div>`
		);
		$a.find(".nc-rq-revise").on("click", () => {
			frappe.call({
				method: "normcore.api.procedure.create_revision",
				args: { procedure: row.name },
				freeze: true,
				callback: (r) => {
					const res = r.message || {};
					if (res.existing) frappe.show_alert({ message: __("A revision is already being drafted"), indicator: "orange" });
					frappe.set_route("procedure-editor", res.name);
				},
			});
		});
		$a.find(".nc-rq-dismiss").on("click", () => this.dismiss(row));
		return $a;
	}

	dismiss(row) {
		const d = new frappe.ui.Dialog({
			title: __("No change needed"),
			fields: [
				{ fieldname: "reason", label: __("Reason"), fieldtype: "Small Text", reqd: 1 },
				{
					fieldtype: "HTML",
					options: `<p class="text-muted small">${__("The review flag will be removed; the reason is recorded in the procedure history.")}</p>`,
				},
			],
			primary_action_label: __("Confirm"),
			primary_action: (v) => {
				d.disable_primary_action();
				frappe.call({
					method: "normcore.api.review.dismiss_review",
					args: { procedure: row.name, reason: v.reason },
					callback: () => {
						d.hide();
						frappe.show_alert({ message: __("Review flag removed"), indicator: "green" });
						this.rows = this.rows.filter((x) => x.name !== row.name);
						this.total = Math.max(0, this.total - 1);
						this.render();
					},
					error: () => d.enable_primary_action(),
				});
			},
		});
		d.show();
	}
};
