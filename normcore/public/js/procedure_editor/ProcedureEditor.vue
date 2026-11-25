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
				<span class="indicator-pill" :class="stateColor(doc.workflow_state)">{{ __(doc.workflow_state) }}</span>
				<span v-if="doc.needs_review" class="indicator-pill orange">{{ __("Needs review") }}</span>
			</div>
			<div v-if="review" class="nc-pe__reviewbar" role="toolbar" :aria-label="__('Review actions')">
				<button v-for="a in primaryActions" :key="a" type="button" class="btn btn-primary btn-sm" :disabled="busy" @click="openAction(a)">{{ __(a) }}</button>
				<button v-if="review.actions.includes(reject)" type="button" class="btn btn-default btn-sm" :disabled="busy" @click="openAction(reject)">{{ __(reject) }}</button>
				<button type="button" class="btn btn-default btn-sm" @click="download('download_pdf')">{{ __("Print PDF") }}</button>
				<button type="button" class="btn btn-default btn-sm" @click="download('download_docx')">{{ __("Download DOCX") }}</button>
				<span v-if="review.open_comments" class="nc-pe__open" :aria-label="review.open_comments + ' ' + __('open comments')">{{ __("Open comments") }}: {{ review.open_comments }}</span>
			</div>
			<div v-if="reviewError" class="nc-pe__error" role="alert">{{ reviewError }}</div>
			<div v-if="review && doc.workflow_state !== draft && !closed" class="nc-pe__notice" role="note">{{ __("This procedure is awaiting approval and cannot be edited.") }}</div>
			<div v-else-if="closed" class="nc-pe__notice" role="note">{{ __("This procedure is issued or closed and cannot be edited. Create a new version in the revision function.") }}</div>
			<div v-else-if="!doc.can_edit" class="nc-pe__notice" role="note">{{ __("You can only view this procedure.") }}</div>
			<div v-if="review && review.last_reject && doc.workflow_state === draft" class="nc-pe__reject" role="note">
				{{ __("Rejected by") }} {{ review.last_reject.by }}: {{ review.last_reject.reason }}
			</div>
			<section v-if="review && doc.workflow_state !== draft" class="nc-pe__dev" :aria-label="__('Deviations summary')">
				<h4 class="nc-pe__h">{{ __("Deviations summary") }}</h4>
				<div v-if="!review.deviations.length" class="text-muted">{{ __("No deviations or unsupported items.") }}</div>
				<ul v-else class="nc-pe__devlist">
					<li v-for="d in review.deviations" :key="d.idx">
						<span class="nc-pe__rel" :class="relClass(d.relation)">{{ __(d.relation) }}</span>
						<a href="#" @click.prevent="jump(d)">{{ d.target_step_id || __(d.target_section) }}</a>
						<span v-if="d.deviation_reason" class="text-muted"> — {{ d.deviation_reason }}</span>
					</li>
				</ul>
			</section>

			<div class="nc-pe__layout">
				<div class="nc-pe__main">
					<section v-for="s in doc.sections" :key="s.key" class="nc-pe__section">
						<h4 class="nc-pe__h" :class="{ 'nc-pe__h--sel': isSelected('section', s.label) }">
							<button type="button" class="nc-pe__link" @click="select('section', s.label)">{{ __(s.label) }}</button>
							<span v-if="badge('section', s.label)" class="nc-pe__badge" :aria-label="badge('section', s.label) + ' ' + __('open comments')">{{ __("Comments") }}: {{ badge('section', s.label) }}</span>
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
									<span v-if="badge('step', st.step_id)" class="nc-pe__badge" :aria-label="badge('step', st.step_id) + ' ' + __('open comments')">{{ __("Comments") }}: {{ badge('step', st.step_id) }}</span>
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
					<div v-if="review" class="nc-pe__comments">
						<h4 class="nc-pe__h">{{ __("Review comments") }}</h4>
						<label class="nc-pe__only"><input v-model="onlyOpen" type="checkbox" /> {{ __("Only unresolved") }}</label>
						<div v-if="!shownComments.length" class="text-muted">{{ __("No review comments yet.") }}</div>
						<div v-for="c in shownComments" :key="c.name" class="nc-pe__comment" :class="{ 'text-muted': c.resolved }">
							<div class="text-muted">{{ c.owner }} · {{ __(c.review_state) }} · {{ c.creation }}<span v-if="c.target_step_id"> · {{ c.target_step_id }}</span><span v-else-if="c.target_section"> · {{ __(c.target_section) }}</span></div>
							<div>{{ c.comment }}</div>
							<label v-if="canResolve"><input type="checkbox" :checked="!!c.resolved" @change="resolve(c, $event.target.checked)" /> {{ __("Resolved") }}</label>
							<span v-else-if="c.resolved">{{ __("Resolved") }}</span>
						</div>
						<form v-if="canComment" class="nc-pe__form nc-pe__form--comment" @submit.prevent="submitComment">
							<select v-model="commentForm.target" class="form-control" :aria-label="__('Attach to')">
								<option value="">{{ __("General comment") }}</option>
								<option v-for="sec in textSections" :key="sec.label" :value="'section:' + sec.label">{{ __(sec.label) }}</option>
								<option v-for="st in doc.steps" :key="st.step_id" :value="'step:' + st.step_id">{{ st.step_id }}</option>
							</select>
							<textarea v-model="commentForm.text" class="form-control" rows="3" :aria-label="__('Comment')" required></textarea>
							<button type="submit" class="btn btn-primary btn-sm" :disabled="busy">{{ __("Save comment") }}</button>
						</form>
					</div>
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
const WF = "normcore.api.procedure_workflow.";
const PRIMARY = ["Gửi duyệt", "Đồng ý", "Thông qua", "Ban hành"];
const CLOSED = ["Đã ban hành", "Đã thay thế", "Đã thu hồi"];
// Màu chỉ báo theo design.md mục 3
const STATE_COLOR = { "Nháp": "gray", "Chờ trưởng khoa duyệt": "orange", "Chờ hội đồng thẩm định": "orange", "Chờ ban hành": "orange", "Đã ban hành": "green", "Đã thay thế": "darkgrey", "Đã thu hồi": "red" };
const NEXT_LABEL = { "Gửi duyệt": "Chờ trưởng khoa duyệt", "Đồng ý": "Chờ hội đồng thẩm định", "Thông qua": "Chờ ban hành" };

// Các dòng lỗi của máy chủ (frappe.throw nối bằng <br>), mỗi lỗi một dòng.
function linesFromError(r) {
	if (!r || !r._server_messages) return [];
	try {
		return JSON.parse(r._server_messages)
			.map((m) => (typeof m === "string" && m.startsWith("{") ? JSON.parse(m).message : m))
			.flatMap((m) => String(m).split(/<br\s*\/?>/i))
			.map((m) => m.replace(/<[^>]*>/g, "").trim())
			.filter(Boolean);
	} catch (e) {
		return [];
	}
}

// Lấy nội dung lỗi của máy chủ (frappe.throw → _server_messages) thành chữ thuần để hiện ở dải lỗi.
function messageFromError(r) {
	if (!r || !r._server_messages) return "";
	try {
		return JSON.parse(r._server_messages)
			.map((m) => (typeof m === "string" && m.startsWith("{") ? JSON.parse(m).message : m))
			.map((m) => String(m).replace(/<[^>]*>/g, "").trim())
			.filter(Boolean)
			.join(" ");
	} catch (e) {
		return "";
	}
}
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
			review: null,
			reviewError: "",
			draft: "Nháp",
			reject: "Từ chối",
			onlyOpen: false,
			commentForm: { target: "", text: "" },
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
		closed() {
			return !!this.doc && CLOSED.includes(this.doc.workflow_state);
		},
		primaryActions() {
			return PRIMARY.filter((a) => this.review && this.review.actions.includes(a));
		},
		textSections() {
			return this.doc.sections.filter((x) => x.key !== "steps");
		},
		allComments() {
			const r = this.review;
			if (!r) return [];
			const rows = [...r.comments_general, ...Object.values(r.comments_by_section).flat(), ...Object.values(r.comments_by_step).flat()];
			return rows.sort((a, b) => String(a.creation).localeCompare(String(b.creation)));
		},
		shownComments() {
			const sel = this.selection;
			let rows = this.allComments;
			if (sel.key) rows = rows.filter((c) => (sel.type === "step" ? c.target_step_id === sel.key : c.target_section === sel.key));
			return this.onlyOpen ? rows.filter((c) => !c.resolved) : rows;
		},
		canResolve() {
			return !!this.review && frappe.model.can_write("NC Review Comment");
		},
		canComment() {
			// Ghi ý kiến chỉ ở trạng thái chờ duyệt, người có quyền tạo NC Review Comment (Auditor không)
			return !!this.review && !this.closed && this.doc.workflow_state !== this.draft && frappe.model.can_create("NC Review Comment");
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
			// silent: không để Desk mở hộp thoại "Tin nhắn"; lỗi hiện ở dải role="alert" (ui-design.md, E15)
			let serverMessage = "";
			// frappe.call trả về jQuery Deferred (không có .finally): bọc thành Promise chuẩn để mọi chỗ gọi dùng được .finally
			return Promise.resolve(
				frappe.call({
					method: API + method,
					args,
					freeze: false,
					silent: true,
					error(r) {
						serverMessage = messageFromError(r);
					},
				})
			)
				.then((r) => r.message)
				.catch((e) => {
					this.error = serverMessage || messageFromError(e && e.responseJSON) || __("Could not complete the request. See the message from the server.");
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
					return Promise.all([this.loadReview(), this.selection.key ? this.loadCitations() : null]);
				})
				.catch(() => {})
				.finally(() => (this.loading = false));
		},
		reload() {
			return this.load(this.doc.name);
		},
		// --- thẩm định và duyệt (FEAT-007, SCR-DSK-010) ---
		callWf(method, args) {
			let serverError = null;
			return Promise.resolve(
				frappe.call({ method: WF + method, args, freeze: false, silent: true, error(r) { serverError = r; } })
			)
				.then((r) => r.message)
				.catch((e) => {
					const err = new Error("workflow call failed");
					err.lines = linesFromError(serverError || (e && e.responseJSON));
					throw err;
				});
		},
		loadReview() {
			this.reviewError = "";
			return this.callWf("get_review", { procedure: this.doc.name })
				.then((r) => {
					this.review = r && r.actions ? r : null;
				})
				.catch((e) => {
					this.review = null;
					this.reviewError = (e.lines && e.lines[0]) || __("You do not have permission to view this procedure");
				});
		},
		stateColor(state) {
			return STATE_COLOR[state] || "gray";
		},
		badge(type, key) {
			const rows = this.allComments.filter((c) => !c.resolved && (type === "step" ? c.target_step_id === key : c.target_section === key));
			return rows.length;
		},
		jump(d) {
			return this.select(d.target_step_id ? "step" : "section", d.target_step_id || d.target_section);
		},
		download(method) {
			window.open("/api/method/" + WF + method + "?procedure=" + encodeURIComponent(this.doc.name));
		},
		resolve(c, value) {
			return this.run(() => this.callWf("set_comment_resolved", { name: c.name, resolved: value ? 1 : 0 }).then(() => this.loadReview()).catch((e) => (this.error = (e.lines || [])[0] || "")));
		},
		submitComment() {
			const [kind, key] = (this.commentForm.target || ":").split(":");
			const args = { procedure: this.doc.name, comment: this.commentForm.text };
			if (kind === "step") args.target_step_id = key;
			else if (kind === "section") args.target_section = key;
			return this.run(() =>
				this.callWf("add_review_comment", args)
					.then(() => {
						this.commentForm.text = "";
						return this.loadReview();
					})
					.catch((e) => (this.error = (e.lines || [])[0] || ""))
			);
		},
		// Hộp thoại của Desk (không tự tạo kiểu); lỗi máy chủ hiện ngay trong hộp thoại, từng lỗi một dòng.
		openAction(action) {
			const fields = [];
			let message = "";
			if (action === this.reject) fields.push({ fieldname: "reason", fieldtype: "Small Text", label: __("Rejection reason"), reqd: 1 });
			else if (action === "Ban hành") {
				fields.push({ fieldname: "decision_no", fieldtype: "Data", label: __("Decision number"), reqd: 1 });
				fields.push({ fieldname: "effective_date", fieldtype: "Date", label: __("Effective date"), reqd: 1, default: frappe.datetime.get_today() });
				message = __("After issuing, the content of this version cannot be edited.");
			} else if (action === "Gửi duyệt") message = __("After submitting, the procedure cannot be edited until it is returned.");
			else message = __("The procedure will move to") + " " + __(NEXT_LABEL[action]) + ".";
			fields.push({ fieldname: "errors", fieldtype: "HTML" });
			const dialog = new frappe.ui.Dialog({
				title: __(action),
				fields: message ? [{ fieldname: "msg", fieldtype: "HTML", options: "<p>" + frappe.utils.escape_html(message) + "</p>" }, ...fields] : fields,
				primary_action_label: __(action),
				primary_action: (values) => this.doAction(action, values, dialog),
			});
			dialog.show();
		},
		showDialogErrors(dialog, lines) {
			const items = lines.map((l) => "<li>" + frappe.utils.escape_html(l).replace(/(S\d{3})/g, '<a href="#" data-step="$1">$1</a>') + "</li>");
			const html = '<div class="nc-pe__error" role="alert"><strong>' + frappe.utils.escape_html(__("Could not complete this action")) + "</strong><ul>" + items.join("") + "</ul></div>";
			const wrapper = dialog.fields_dict.errors.$wrapper;
			wrapper.html(html);
			wrapper.find("a[data-step]").on("click", (ev) => {
				ev.preventDefault();
				dialog.hide();
				this.select("step", ev.currentTarget.dataset.step);
			});
		},
		doAction(action, values, dialog) {
			const args = { procedure: this.doc.name, action };
			if (values.reason) args.reason = values.reason;
			if (values.decision_no) args.decision_no = values.decision_no;
			if (values.effective_date) args.effective_date = values.effective_date;
			return this.run(() =>
				this.callWf("apply_action", args)
					.then((r) => {
						dialog.hide();
						frappe.show_alert({ message: __("Moved to") + " " + __(r.workflow_state), indicator: "green" });
						return this.refreshList().then(() => this.reload());
					})
					.catch((e) => this.showDialogErrors(dialog, e.lines && e.lines.length ? e.lines : [__("Could not complete the request. See the message from the server.")]))
			);
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
			return Promise.resolve(fn())
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
					.catch((e) => {
						const message = this.error;
						// FR-PROC-002 / Q3: dẫn tới bản đã có
						return this.call("find_existing", { technical_service: f.service, department: f.department })
							.then((x) => {
								const existing = x.draft || x.published || "";
								if (!existing) {
									// lỗi khác (mã dịch vụ sai, thiếu quyền...): giữ thông báo của máy chủ trong dải lỗi
									this.error = message;
									return;
								}
								this.error = __("This service already has a procedure for the department:");
								this.existing = existing;
							})
							.catch(() => {
								this.error = message;
							});
					})
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
			const stepId = key.split(":")[0];
			return this.run(() => this.call("reorder_steps", { procedure: this.doc.name, order }).then(() => this.reload())).then(() =>
				// K3: chỉ đặt tiêu điểm sau khi busy về false (nút hết disabled)
				this.$nextTick(() => {
					// ASM-064: ở biên nút vừa bấm bị khóa, chuyển sang nút còn lại của cùng bước
					const btn =
						this.$el.querySelector(`[data-move="${key}"]:not([disabled])`) ||
						this.$el.querySelector(`[data-move^="${stepId}:"]:not([disabled])`);
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
.nc-pe__reviewbar {
	position: sticky;
	top: 0;
	z-index: 1;
	display: flex;
	gap: var(--padding-sm);
	align-items: center;
	flex-wrap: wrap;
	background: var(--card-bg);
	border-bottom: 1px solid var(--border-color);
	padding: var(--padding-sm) 0;
	margin-bottom: var(--margin-md);
}
.nc-pe__open {
	margin-left: auto;
	font-weight: 600;
}
.nc-pe__reject {
	background: var(--yellow-100);
	color: var(--text-color);
	border: 1px solid var(--yellow-500);
	padding: var(--padding-sm) var(--padding-md);
	margin-bottom: var(--margin-md);
}
.nc-pe__dev {
	margin-bottom: var(--margin-md);
}
.nc-pe__devlist {
	padding-left: var(--padding-lg);
}
.nc-pe__badge {
	font-size: var(--text-xs);
	font-weight: 600;
	color: var(--orange-700);
	margin-left: var(--margin-sm);
}
.nc-pe__comments {
	margin-top: var(--margin-lg);
	border-top: 1px solid var(--border-color);
	padding-top: var(--padding-md);
}
.nc-pe__comment {
	border-bottom: 1px solid var(--border-color);
	padding: var(--padding-sm) 0;
}
.nc-pe button:focus-visible,
.nc-pe a:focus-visible,
.nc-pe select:focus-visible,
.nc-pe textarea:focus-visible {
	outline: 2px solid var(--primary);
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
