<template>
	<div class="nc-pe">
		<div class="nc-pe__bar">
			<label class="sr-only" for="nc-pe-select">{{ __("Select a procedure") }}</label>
			<select id="nc-pe-select" v-model="selected" class="form-control nc-pe__select" @change="load(selected)">
				<option value="">{{ __("Select a procedure") }}</option>
				<option v-for="p in procedures" :key="p.name" :value="p.name">
					{{ p.name }} ({{ p.workflow_state }})
				</option>
			</select>
			<button v-if="canCreate" class="btn btn-default btn-sm" type="button" @click="openForm('create')">
				{{ __("Create procedure") }}
			</button>
			<button v-if="doc && canCreate" class="btn btn-default btn-sm" type="button" @click="openForm('copy')">
				{{ __("Copy from this procedure") }}
			</button>
		</div>

		<form v-if="form.kind === 'create' || form.kind === 'copy'" class="nc-pe__form" @submit.prevent="submitProcedureForm" @keydown.esc="closeForm">
			<input v-model="form.service" class="form-control" :aria-label="__('Technical service')" :placeholder="__('Technical service')" required />
			<input v-model="form.department" class="form-control" :aria-label="__('Department')" :placeholder="__('Department')" required />
			<button type="submit" class="btn btn-primary btn-sm" :disabled="busy">
				{{ form.kind === "copy" ? __("Copy") : __("Create") }}
			</button>
			<button type="button" class="btn btn-default btn-sm" @click="closeForm">{{ __("Cancel") }}</button>
		</form>

		<div v-if="error" class="nc-pe__error" role="alert">
			{{ error }}
			<a v-if="existing" href="#" @click.prevent="load(existing)">{{ existing }}</a>
		</div>
		<div v-if="loading" class="text-muted" role="status">{{ __("Loading...") }}</div>

		<div v-if="!doc && !loading" class="nc-pe__empty text-muted">{{ __("Pick a procedure to see its steps.") }}</div>

		<template v-if="doc">
			<div class="nc-pe__title">
				<strong>{{ doc.name }}</strong>
				<span class="indicator-pill" :class="doc.workflow_state === published ? 'green' : 'gray'">{{ doc.workflow_state }}</span>
				<span v-if="doc.needs_review" class="indicator-pill orange">{{ __("Needs review") }}</span>
			</div>
			<div v-if="!doc.can_edit" class="nc-pe__notice" role="note">
				{{ doc.workflow_state === published ? __("This procedure is issued and read-only.") : __("You can only view this procedure.") }}
			</div>

			<div class="nc-pe__layout">
				<div class="nc-pe__main">
					<section v-for="s in doc.sections" :key="s.key" class="nc-pe__section">
						<h4 class="nc-pe__h" :class="{ 'nc-pe__h--sel': isSelected('section', s.label) }">
							<button type="button" class="nc-pe__link" @click="select('section', s.label)">{{ __(s.label) }}</button>
						</h4>

						<template v-if="s.key !== 'steps'">
							<textarea
								v-model="drafts[s.key]"
								class="form-control"
								rows="3"
								:readonly="!doc.can_edit"
								:aria-label="__(s.label)"
								@focus="select('section', s.label)"
							></textarea>
							<button v-if="doc.can_edit" type="button" class="btn btn-default btn-xs nc-pe__save" :disabled="busy" @click="saveSection(s.key)">
								{{ __("Save section") }}
							</button>
						</template>

						<template v-else>
							<div v-if="!doc.steps.length" class="text-muted">{{ __("No steps yet. Add the first step below.") }}</div>
							<article
								v-for="(st, i) in doc.steps"
								:key="st.step_id"
								class="nc-pe__card"
								:class="{ 'nc-pe__card--sel': isSelected('step', st.step_id) }"
							>
								<header class="nc-pe__cardhead">
									<button type="button" class="nc-pe__link" @click="select('step', st.step_id)">
										<strong>{{ st.step_id }}</strong> · {{ __(st.phase) }} · {{ st.step_title }}
									</button>
									<span v-if="doc.can_edit" class="nc-pe__actions">
										<button type="button" class="btn btn-default btn-xs" :disabled="i === 0 || busy" :aria-label="__('Move step up') + ' ' + st.step_id" :data-move="st.step_id + ':up'" @click="move(i, -1, $event)">{{ __("Up") }}</button>
										<button type="button" class="btn btn-default btn-xs" :disabled="i === doc.steps.length - 1 || busy" :aria-label="__('Move step down') + ' ' + st.step_id" :data-move="st.step_id + ':down'" @click="move(i, 1, $event)">{{ __("Down") }}</button>
										<button type="button" class="btn btn-default btn-xs" @click="openForm('step', st)">{{ __("Edit") }}</button>
										<button type="button" class="btn btn-default btn-xs" :disabled="busy" @click="deleteStep(st)">{{ __("Delete") }}</button>
									</span>
								</header>
								<p class="nc-pe__desc">{{ st.description }}</p>

								<table v-if="resourcesOf(st.step_id).length" class="nc-pe__table">
									<thead>
										<tr>
											<th>{{ __("Row ID") }}</th>
											<th>{{ __("Type") }}</th>
											<th>{{ __("Name") }}</th>
											<th>{{ __("Quantity") }}</th>
											<th>{{ __("Unit") }}</th>
											<th>{{ __("Headcount") }}</th>
											<th></th>
										</tr>
									</thead>
									<tbody>
										<tr v-for="r in resourcesOf(st.step_id)" :key="r.resource_row_id">
											<td>{{ r.resource_row_id }}</td>
											<td>{{ __(r.resource_type) }}</td>
											<td>{{ r.resource_text }}<span v-if="r.linked_name" class="text-muted"> ({{ r.linked_name }})</span></td>
											<td>{{ r.quantity }}</td>
											<td>{{ r.uom }}</td>
											<td>{{ r.headcount || "" }}</td>
											<td v-if="doc.can_edit">
												<button type="button" class="btn btn-default btn-xs" @click="openForm('resource', r)">{{ __("Edit") }}</button>
												<button type="button" class="btn btn-default btn-xs" :disabled="busy" @click="deleteResource(r)">{{ __("Delete") }}</button>
											</td>
										</tr>
									</tbody>
								</table>
								<button v-if="doc.can_edit" type="button" class="btn btn-default btn-xs" @click="openForm('resource', null, st.step_id)">
									{{ __("Add resource") }}
								</button>
							</article>

							<button v-if="doc.can_edit" type="button" class="btn btn-primary btn-sm" @click="openForm('step')">{{ __("Add step") }}</button>
						</template>
					</section>
				</div>

				<aside class="nc-pe__side" :aria-label="__('Citations')">
					<h4 class="nc-pe__h">{{ __("Citations") }}: {{ selection.key ? (selection.type === "step" ? selection.key : __(selection.key)) : __("Select a section or step") }}</h4>
					<div v-if="!citations.length" class="text-muted">{{ __("No citations for this selection.") }}</div>
					<div v-for="c in citations" :key="c.name" class="nc-pe__cite">
						<span class="nc-pe__rel" :class="relClass(c.relation)">{{ __(c.relation) }}</span>
						<div v-if="c.legal_document || c.legal_section" class="nc-pe__legal">{{ [c.legal_document, c.legal_section].filter(Boolean).join(" — ") }}</div>
						<blockquote v-if="c.quote" class="nc-pe__quote">{{ c.quote }}</blockquote>
						<div v-if="c.deviation_reason" class="text-muted">{{ __("Reason") }}: {{ c.deviation_reason }}</div>
						<span v-if="doc.can_edit">
							<button type="button" class="btn btn-default btn-xs" @click="openForm('citation', c)">{{ __("Edit") }}</button>
							<button type="button" class="btn btn-default btn-xs" :disabled="busy" @click="deleteCitation(c)">{{ __("Delete") }}</button>
						</span>
					</div>
					<button v-if="doc.can_edit && selection.key" type="button" class="btn btn-default btn-xs" @click="openForm('citation')">
						{{ __("Add citation") }}
					</button>
					<div class="text-muted nc-pe__hint">{{ __("Legal text links are provided by the document library.") }}</div>
				</aside>
			</div>

			<form v-if="form.kind === 'step'" class="nc-pe__form" @submit.prevent="submitStep" @keydown.esc="closeForm">
				<select v-model="form.phase" class="form-control" :aria-label="__('Phase')">
					<option v-for="p in phases" :key="p" :value="p">{{ __(p) }}</option>
				</select>
				<input v-model="form.step_title" class="form-control" :aria-label="__('Step title')" :placeholder="__('Step title')" required />
				<input v-model="form.description" class="form-control" :aria-label="__('Description')" :placeholder="__('Description')" required />
				<button type="submit" class="btn btn-primary btn-sm" :disabled="busy">{{ __("Save") }}</button>
				<button type="button" class="btn btn-default btn-sm" @click="closeForm">{{ __("Cancel") }}</button>
			</form>

			<form v-if="form.kind === 'resource'" class="nc-pe__form nc-pe__form--res" @submit.prevent="submitResource" @keydown.esc="closeForm">
				<select v-model="form.resource_type" class="form-control" :aria-label="__('Type')" :disabled="!!form.row" @change="onType">
					<option v-for="t in types" :key="t" :value="t">{{ __(t) }}</option>
				</select>
				<input v-model="form.resource_text" class="form-control" list="nc-pe-suggest" :aria-label="__('Name')" :placeholder="__('Name')" required @input="suggest" />
				<datalist id="nc-pe-suggest"><option v-for="s in suggestions" :key="s.name" :value="s.label">{{ s.name }}</option></datalist>
				<input v-model.number="form.quantity" type="number" min="0" step="any" class="form-control" :aria-label="isLabor ? __('Minutes per person') : __('Quantity')" :placeholder="isLabor ? __('Minutes per person') : __('Quantity')" required />
				<input v-model="form.uom" class="form-control" :aria-label="__('Unit')" :placeholder="__('Unit')" :readonly="isLabor" required />
				<input v-if="isLabor" v-model.number="form.headcount" type="number" min="1" class="form-control" :aria-label="__('Headcount')" :placeholder="__('Headcount')" />
				<button type="submit" class="btn btn-primary btn-sm" :disabled="busy">{{ __("Save") }}</button>
				<button type="button" class="btn btn-default btn-sm" @click="closeForm">{{ __("Cancel") }}</button>
			</form>

			<form v-if="form.kind === 'citation'" class="nc-pe__form nc-pe__form--cite" @submit.prevent="submitCitation" @keydown.esc="closeForm">
				<select v-model="form.relation" class="form-control" :aria-label="__('Relation')">
					<option v-for="r in relations" :key="r" :value="r">{{ __(r) }}</option>
				</select>
				<input v-model="form.legal_document" class="form-control" :aria-label="__('Legal document')" :placeholder="__('Legal document')" />
				<input v-model="form.legal_section" class="form-control" :aria-label="__('Legal section')" :placeholder="__('Legal section')" />
				<input v-model="form.quote" class="form-control" :aria-label="__('Quote')" :placeholder="__('Quote')" />
				<input v-model="form.deviation_reason" class="form-control" :aria-label="__('Reason')" :placeholder="__('Reason')" />
				<button type="submit" class="btn btn-primary btn-sm" :disabled="busy">{{ __("Save") }}</button>
				<button type="button" class="btn btn-default btn-sm" @click="closeForm">{{ __("Cancel") }}</button>
			</form>
		</template>
	</div>
</template>

<script>
const API = "normcore.api.procedure.";
export default {
	name: "ProcedureEditor",
	props: { initialName: { type: String, default: "" } },
	data() {
		return {
			procedures: [],
			selected: this.initialName,
			doc: null,
			drafts: {},
			citations: [],
			selection: { type: "", key: "" },
			error: "",
			existing: "",
			busy: false,
			loading: false,
			published: "Đã ban hành",
			laborUom: "phút",
			phases: ["Chuẩn bị", "Thực hiện", "Theo dõi", "Kết thúc"],
			types: ["Nhân lực", "Thuốc", "Hóa chất", "Dịch truyền", "Vật tư", "Thiết bị", "Phòng", "Khác"],
			relations: ["Theo hướng dẫn", "Khác biệt", "Chưa có căn cứ"],
			suggestions: [],
			form: { kind: "" },
		};
	},
	computed: {
		canCreate() {
			// G1: NC Auditor không thấy nút tạo/sao chép (máy chủ vẫn từ chối)
			return frappe.model.can_create("NC Clinical Procedure");
		},
		isLabor() {
			return this.form.resource_type === "Nhân lực";
		},
	},
	mounted() {
		this.refreshList();
		if (this.selected) this.load(this.selected);
	},
	methods: {
		call(method, args) {
			this.error = "";
			this.existing = "";
			return frappe
				.call({ method: API + method, args, freeze: false, error() {} })
				.then((r) => r.message)
				.catch((e) => {
					this.error = __("Could not complete the request. See the message from the server.");
					throw e;
				});
		},
		refreshList() {
			return this.call("list_procedures").then((r) => (this.procedures = r || [])).catch(() => {});
		},
		resourcesOf(stepId) {
			return this.doc.resources.filter((r) => r.step_id === stepId);
		},
		relClass(rel) {
			return { "Theo hướng dẫn": "nc-pe__rel--ok", "Khác biệt": "nc-pe__rel--warn", "Chưa có căn cứ": "nc-pe__rel--none" }[rel];
		},
		isSelected(type, key) {
			return this.selection.type === type && this.selection.key === key;
		},
		select(type, key) {
			this.selection = { type, key };
			return this.loadCitations();
		},
		loadCitations() {
			const args = { name: this.doc.name };
			if (this.selection.type === "step") args.step_id = this.selection.key;
			else if (this.selection.type === "section") args.section = this.selection.key;
			else return Promise.resolve();
			return this.call("get_procedure", args)
				.then((d) => (this.citations = d.citations))
				.catch(() => {});
		},
		load(name) {
			this.closeForm();
			if (!name) {
				this.doc = null;
				return Promise.resolve();
			}
			this.selected = name;
			this.loading = true;
			return this.call("get_procedure", { name })
				.then((doc) => {
					this.doc = doc;
					this.drafts = Object.fromEntries(doc.sections.filter((s) => s.key !== "steps").map((s) => [s.key, s.value || ""]));
					this.citations = this.selection.key ? this.citations : [];
					return this.selection.key ? this.loadCitations() : null;
				})
				.catch(() => {})
				.finally(() => (this.loading = false));
		},
		reload() {
			return this.load(this.doc.name);
		},
		// --- biểu mẫu ---
		openForm(kind, row, stepId) {
			this.error = "";
			if (kind === "create" || kind === "copy") this.form = { kind, service: "", department: "" };
			else if (kind === "step")
				this.form = { kind, row, phase: row ? row.phase : "Thực hiện", step_title: row ? row.step_title : "", description: row ? row.description : "" };
			else if (kind === "resource")
				this.form = {
					kind,
					row,
					step_id: row ? row.step_id : stepId,
					resource_type: row ? row.resource_type : "Nhân lực",
					resource_text: row ? row.resource_text : "",
					quantity: row ? row.quantity : null,
					uom: row ? row.uom : this.laborUom,
					headcount: row ? row.headcount : 1,
					linked_name: row ? row.linked_name : "",
				};
			else
				this.form = {
					kind,
					row,
					relation: row ? row.relation : "Chưa có căn cứ",
					legal_document: row ? row.legal_document : "",
					legal_section: row ? row.legal_section : "",
					quote: row ? row.quote : "",
					deviation_reason: row ? row.deviation_reason : "",
				};
			this.suggestions = [];
		},
		closeForm() {
			this.form = { kind: "" };
		},
		run(fn) {
			this.busy = true;
			return fn()
				.catch(() => {})
				.finally(() => (this.busy = false));
		},
		submitProcedureForm() {
			const f = this.form;
			const create = f.kind === "create";
			const args = create ? { technical_service: f.service, department: f.department } : { source: this.doc.name, technical_service: f.service, department: f.department };
			return this.run(() =>
				this.call(create ? "create_procedure" : "copy_procedure", args)
					.then((r) => this.refreshList().then(() => this.load(r.name)))
					.catch((e) =>
						// FR-PROC-002 / Q3: dẫn tới bản đã có
						this.call("find_existing", { technical_service: f.service, department: f.department })
							.then((x) => {
								const existing = x.draft || x.published || "";
								if (!existing) return; // lỗi khác (mã dịch vụ sai, thiếu quyền...): giữ thông báo chung
								this.error = __("This service already has a procedure for the department:");
								this.existing = existing;
							})
							.catch(() => {})
					)
			);
		},
		saveSection(key) {
			return this.run(() => this.call("save_sections", { procedure: this.doc.name, sections: { [key]: this.drafts[key] } }).then(() => this.reload()));
		},
		submitStep() {
			const f = this.form;
			const base = { procedure: this.doc.name, phase: f.phase, step_title: f.step_title, description: f.description };
			return this.run(() =>
				this.call(f.row ? "update_step" : "add_step", f.row ? { ...base, step_id: f.row.step_id } : base).then(() => this.reload())
			);
		},
		deleteStep(st) {
			frappe.confirm(__("Delete this step?"), () =>
				this.run(() => this.call("delete_step", { procedure: this.doc.name, step_id: st.step_id }).then(() => this.reload()))
			);
		},
		move(i, delta, ev) {
			const order = this.doc.steps.map((s) => s.step_id);
			[order[i], order[i + delta]] = [order[i + delta], order[i]];
			const key = ev.currentTarget.dataset.move;
			return this.run(() => this.call("reorder_steps", { procedure: this.doc.name, order }).then(() => this.reload())).then(() =>
				// K3: chỉ đặt tiêu điểm sau khi busy về false (nút hết disabled)
				this.$nextTick(() => {
					const btn = this.$el.querySelector(`[data-move="${key}"]:not([disabled])`);
					if (btn) btn.focus();
				})
			);
		},
		onType() {
			this.form.uom = this.isLabor ? this.laborUom : "";
			this.form.linked_name = "";
			this.suggestions = [];
		},
		suggest() {
			if (!this.isLabor) return (this.suggestions = []);
			return this.call("suggest_catalog", { resource_type: this.form.resource_type, text: this.form.resource_text })
				.then((r) => {
					this.suggestions = r || [];
					const hit = this.suggestions.find((s) => s.label === this.form.resource_text);
					this.form.linked_name = hit ? hit.name : "";
				})
				.catch(() => {});
		},
		submitResource() {
			const f = this.form;
			const common = { procedure: this.doc.name, resource_text: f.resource_text, quantity: f.quantity, uom: this.isLabor ? this.laborUom : f.uom, headcount: this.isLabor ? f.headcount : null, linked_name: f.linked_name || "" };
			const call = f.row
				? this.call("update_resource", { ...common, resource_row_id: f.row.resource_row_id, step_id: f.step_id })
				: this.call("add_resource", { ...common, step_id: f.step_id, resource_type: f.resource_type });
			return this.run(() => call.then(() => this.reload()));
		},
		deleteResource(r) {
			frappe.confirm(__("Delete this resource?"), () =>
				this.run(() => this.call("delete_resource", { procedure: this.doc.name, resource_row_id: r.resource_row_id }).then(() => this.reload()))
			);
		},
		submitCitation() {
			const f = this.form;
			const target = this.selection.type === "step" ? { target_step_id: this.selection.key } : { target_section: this.selection.key };
			const body = { procedure: this.doc.name, relation: f.relation, legal_document: f.legal_document || "", legal_section: f.legal_section || "", quote: f.quote || "", deviation_reason: f.deviation_reason || "" };
			return this.run(() =>
				(f.row ? this.call("update_citation", { ...body, citation: f.row.name }) : this.call("add_citation", { ...body, ...target })).then(() => this.reload())
			);
		},
		deleteCitation(c) {
			frappe.confirm(__("Delete this citation?"), () =>
				this.run(() => this.call("delete_citation", { procedure: this.doc.name, citation: c.name }).then(() => this.reload()))
			);
		},
	},
};
</script>

<style scoped>
.nc-pe {
	color: var(--text-color);
	background: var(--card-bg);
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	padding: var(--padding-lg);
}
.nc-pe__bar,
.nc-pe__title {
	margin-bottom: var(--margin-md);
	display: flex;
	gap: var(--padding-sm);
	align-items: center;
	flex-wrap: wrap;
}
.nc-pe__select {
	max-width: 360px;
}
.nc-pe__layout {
	display: grid;
	grid-template-columns: 2fr 1fr;
	gap: var(--padding-lg);
}
.nc-pe__section {
	margin-bottom: var(--margin-lg);
}
.nc-pe__h {
	font-size: var(--text-md);
	margin: 0 0 var(--margin-sm);
}
.nc-pe__h--sel {
	border-left: 3px solid var(--primary);
	padding-left: var(--padding-sm);
}
.nc-pe__link {
	background: none;
	border: 0;
	padding: 0;
	color: var(--text-color);
	text-align: left;
	font-weight: 600;
}
.nc-pe__card {
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	padding: var(--padding-md);
	margin-bottom: var(--margin-sm);
}
.nc-pe__card--sel {
	border-color: var(--primary);
}
.nc-pe__cardhead {
	display: flex;
	justify-content: space-between;
	gap: var(--padding-sm);
	flex-wrap: wrap;
}
.nc-pe__desc {
	margin: var(--margin-sm) 0;
	color: var(--text-color);
}
.nc-pe__table {
	width: 100%;
	border-collapse: collapse;
	margin-bottom: var(--margin-sm);
}
.nc-pe__table th,
.nc-pe__table td {
	border-bottom: 1px solid var(--border-color);
	padding: var(--padding-xs) var(--padding-sm);
	text-align: left;
}
.nc-pe__table th {
	color: var(--text-muted);
	font-weight: 500;
}
.nc-pe__form {
	display: grid;
	grid-template-columns: 140px 1fr 2fr auto auto;
	gap: var(--padding-sm);
	margin: var(--margin-md) 0;
}
.nc-pe__form--res {
	grid-template-columns: 120px 1fr 110px 90px 90px auto auto;
}
.nc-pe__form--cite {
	grid-template-columns: 160px 2fr 2fr auto auto;
}
.nc-pe__side {
	border-left: 1px solid var(--border-color);
	padding-left: var(--padding-md);
}
.nc-pe__cite {
	margin-bottom: var(--margin-md);
}
.nc-pe__quote {
	margin: var(--margin-xs) 0;
	padding-left: var(--padding-sm);
	border-left: 2px solid var(--border-color);
}
.nc-pe__legal {
	font-weight: 600;
}
.nc-pe__rel {
	font-weight: 600;
}
.nc-pe__rel--ok {
	color: var(--green-800);
}
.nc-pe__rel--warn {
	color: var(--orange-700);
}
.nc-pe__rel--none {
	color: var(--red-600);
}
.nc-pe__notice {
	background: var(--bg-light-gray);
	border: 1px solid var(--border-color);
	padding: var(--padding-sm) var(--padding-md);
	margin-bottom: var(--margin-md);
}
.nc-pe__error {
	color: var(--red-600);
	margin-bottom: var(--margin-md);
}
.nc-pe__hint {
	margin-top: var(--margin-md);
}
.nc-pe input::placeholder,
.nc-pe textarea::placeholder {
	color: var(--text-muted);
	opacity: 1;
}
.nc-pe button:focus-visible,
.nc-pe input:focus-visible,
.nc-pe select:focus-visible,
.nc-pe textarea:focus-visible,
.nc-pe a:focus-visible {
	outline: 2px solid var(--primary);
	outline-offset: 1px;
}
.sr-only {
	position: absolute;
	width: 1px;
	height: 1px;
	overflow: hidden;
	clip: rect(0 0 0 0);
}
@media (max-width: 900px) {
	.nc-pe__layout,
	.nc-pe__form,
	.nc-pe__form--res,
	.nc-pe__form--cite {
		grid-template-columns: 1fr;
	}
	.nc-pe__side {
		border-left: 0;
		padding-left: 0;
	}
}
</style>
