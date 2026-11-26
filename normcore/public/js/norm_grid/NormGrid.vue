<template>
	<div class="nc-ng">
		<div v-if="!name && !loading" class="text-muted" role="note">
			{{ __("Pick a norm set from the list.") }}
			<a href="/app/nc-norm-set">{{ __("Norm sets") }}</a>
		</div>
		<div v-if="loading" class="text-muted" role="status">{{ __("Loading...") }}</div>
		<div v-if="error" class="nc-ng__error" role="alert">
			{{ error }}
			<button v-if="name" type="button" class="btn btn-default btn-xs" @click="load(name)">{{ __("Retry") }}</button>
		</div>

		<template v-if="data">
			<header class="nc-ng__head">
				<div class="nc-ng__title">
					<strong>{{ data.doc.technical_service_name || data.doc.technical_service }}</strong>
					<span class="text-muted">{{ data.doc.department }}</span>
					<span>{{ __("Version") }} {{ data.doc.version_no }}</span>
					<a :href="'/app/nc-clinical-procedure/' + encodeURIComponent(data.doc.procedure)">{{ data.doc.procedure }}</a>
					<a v-if="data.doc.previous_version" href="#" @click.prevent="open(data.doc.previous_version)">{{ __("Previous version") }}: {{ data.doc.previous_version }}</a>
					<span ref="state" tabindex="-1" class="indicator-pill" :class="stateColor(data.doc.status)">{{ __(data.doc.status) }}</span>
					<span v-if="data.doc.needs_update" class="indicator-pill yellow">{{ __("Needs update") }}</span>
					<a v-if="data.doc.newer_procedure" :href="'/app/nc-clinical-procedure/' + encodeURIComponent(data.doc.newer_procedure)">{{ __("New procedure: {0}", [data.doc.newer_procedure]) }}</a>
					<span v-if="data.doc.needs_update && data.doc.step_change_note" class="text-muted">{{ data.doc.step_change_note }}</span>
				</div>
				<div class="nc-ng__actions" role="toolbar" :aria-label="__('Norm set actions')">
					<button v-if="can('confirm_set')" type="button" class="btn btn-primary btn-sm" :disabled="busy" @click="startAction('confirm_set')">{{ __("Confirm professionally") }}</button>
					<button v-if="can('lock_set')" type="button" class="btn btn-primary btn-sm" :disabled="busy" @click="startAction('lock_set')">{{ __("Lock") }}</button>
					<button v-if="can('new_version')" type="button" class="btn btn-primary btn-sm" :disabled="busy" @click="startAction('new_version')">{{ data.doc.newer_procedure ? __("Create version from new procedure") : __("Create new version") }}</button>
					<button v-if="can('return_set')" type="button" class="btn btn-default btn-sm" :disabled="busy" @click="startAction('return_set')">{{ __("Return to draft") }}</button>
					<button v-if="can('save_line')" type="button" class="btn btn-default btn-sm" :disabled="busy" @click="openAdd">{{ __("Add line") }}</button>
				</div>
			</header>

			<div v-if="data.doc.status === 'Đã xác nhận chuyên môn'" class="nc-ng__notice" role="note">{{ __("Confirmed professionally, waiting for Finance to lock. It cannot be edited.") }}</div>
			<div v-else-if="closed" class="nc-ng__notice" role="note">{{ __("This record is {0} and cannot be edited. Create a new version.", [__(data.doc.status)]) }}</div>
			<div v-else-if="!canEdit" class="nc-ng__notice" role="note">{{ __("You can only view this norm set.") }}</div>
			<section v-if="changeStrip" class="nc-ng__warn" role="status" :aria-label="__('Changes from new procedure')">
				<strong>{{ __("Changes from new procedure") }}</strong>
				<div v-if="removedCount">
					{{ __("Removed step: {0}", [removedCount]) }} <span class="indicator-pill red">{{ __("Removed step") }}</span>
					<button type="button" class="btn btn-default btn-xs" @click="focusRemoved">{{ __("View these lines") }}</button>
					<div class="text-muted nc-ng__small">{{ __("Assign another step, move to whole service, or delete before professional confirmation.") }}</div>
				</div>
				<div v-if="data.steps_without_lines.length">
					{{ __("Steps without lines") }}:
					<template v-for="m in data.steps_without_lines" :key="m.step_id">
						<button v-if="canEdit" type="button" class="indicator-pill orange nc-ng__link" :aria-label="__('Add line for step {0}', [m.step_id])" @click="openAddFor(m.step_id)">{{ m.step_id }} · {{ m.step_title }}</button>
						<span v-else class="indicator-pill orange">{{ m.step_id }} · {{ m.step_title }}</span>
					</template>
				</div>
			</section>
			<div v-if="blockers.length && data.doc.status === 'Nháp'" class="nc-ng__warn" role="note">
				{{ __("{0} lines are not ready for professional confirmation", [blockers.length]) }}
				<button type="button" class="btn btn-default btn-xs" @click="onlyAttention = !onlyAttention">{{ onlyAttention ? __("Show all lines") : __("Filter these lines") }}</button>
			</div>
			<div v-if="!data.summary.parameter_set" class="text-muted nc-ng__small">
				{{ __("Wastage cap {0}% (Assumption, to be confirmed: no effective parameter set)", [data.wastage_cap]) }}
			</div>

			<div v-if="actionError" class="nc-ng__error" role="alert">
				<div v-for="(l, i) in actionError.lines" :key="i">
					<button v-if="l.line_id" type="button" class="nc-ng__link" @click="focusLine(l.line_id)">{{ l.text }}</button>
					<span v-else>{{ l.text }}</span>
				</div>
			</div>

			<form v-if="pending && pending.needsReason" class="nc-ng__form" @submit.prevent="runAction" @keydown.esc="pending = null">
				<label for="nc-ng-reason">{{ __("Return reason") }}</label>
				<textarea id="nc-ng-reason" v-model="reason" class="form-control" rows="2" required></textarea>
				<button type="submit" class="btn btn-primary btn-sm" :disabled="busy || !reason.trim()">{{ __("Return to draft") }}</button>
				<button type="button" class="btn btn-default btn-sm" @click="pending = null">{{ __("Cancel") }}</button>
			</form>
			<div v-else-if="pending" class="nc-ng__form" role="alertdialog" :aria-label="pending.message">
				<span>{{ pending.message }}</span>
				<button type="button" class="btn btn-primary btn-sm" :disabled="busy" @click="runAction">{{ __("Confirm") }}</button>
				<button type="button" class="btn btn-default btn-sm" @click="pending = null">{{ __("Cancel") }}</button>
			</div>

			<form v-if="add" class="nc-ng__form nc-ng__add" @submit.prevent="submitAdd" @keydown.esc="add = null">
				<label>{{ __("Component") }}
					<select v-model="add.component" class="form-control" @change="add.resourceText = ''">
						<option v-for="c in data.options.component" :key="c" :value="c">{{ compLabel(c) }}</option>
					</select>
				</label>
				<label>{{ __("Resource") }}
					<input v-model="add.resourceText" class="form-control" :list="'nc-ng-dl-' + add.component" :aria-label="__('Resource')" @focus="loadOptions(add.component, '')" @input="loadOptions(add.component, add.resourceText)" />
				</label>
				<label>{{ __("Attach to") }}
					<select v-model="add.target" class="form-control" required>
						<option value="">{{ __("Choose a step") }}</option>
						<option v-for="s in data.steps" :key="s.step_id" :value="s.step_id">{{ s.step_id }} · {{ s.step_title }}</option>
						<option value="__service__">{{ __("Whole service") }}</option>
					</select>
				</label>
				<label v-if="add.component === 'LABOR'">{{ __("Headcount") }}<input v-model.number="add.headcount" type="number" min="1" class="form-control" /></label>
				<label>{{ __("Hospital norm") }}<input v-model.number="add.hospital_qty" type="number" step="any" min="0" class="form-control" required /></label>
				<label>{{ __("Unit") }}<input v-model="add.uom" class="form-control" required /></label>
				<label>{{ __("Basis") }}
					<select v-model="add.basis" class="form-control"><option v-for="b in data.options.basis" :key="b" :value="b">{{ __(b) }}</option></select>
				</label>
				<button type="submit" class="btn btn-primary btn-sm" :disabled="busy">{{ __("Add") }}</button>
				<button type="button" class="btn btn-default btn-sm" @click="add = null">{{ __("Cancel") }}</button>
				<div v-if="add.error" class="nc-ng__error" role="alert">{{ add.error }}</div>
			</form>

			<div class="nc-ng__filters">
				<label class="sr-only" for="nc-ng-q">{{ __("Search") }}</label>
				<input id="nc-ng-q" v-model="q" class="form-control nc-ng__q" :placeholder="__('Search line or resource')" />
				<label class="sr-only" for="nc-ng-comp">{{ __("Component") }}</label>
				<select id="nc-ng-comp" v-model="compFilter" class="form-control nc-ng__comp">
					<option value="">{{ __("All components") }}</option>
					<option v-for="c in data.options.component" :key="c" :value="c">{{ compLabel(c) }}</option>
				</select>
				<label><input v-model="onlyAttention" type="checkbox" /> {{ __("Only lines needing attention") }}</label>
				<label><input v-model="showExcluded" type="checkbox" /> {{ __("Show excluded lines") }}</label>
				<button type="button" class="btn btn-default btn-xs" @click="toggleAll">{{ __("Collapse or expand all steps") }}</button>
			</div>

			<datalist v-for="c in data.options.component" :id="'nc-ng-dl-' + c" :key="c">
				<option v-for="o in resourceOptions[c] || []" :key="o.value" :value="o.label"></option>
			</datalist>

			<div v-if="!totalLines" class="text-muted" role="note">{{ __("This norm set has no lines yet.") }}</div>
			<div class="nc-ng__scroll">
				<table v-if="totalLines" class="nc-ng__table" role="grid" :aria-label="__('Norm grid')">
					<thead>
						<tr>
							<th scope="col">{{ __("Line") }}</th>
							<th scope="col">{{ __("Component") }}</th>
							<th scope="col">{{ __("Resource") }}</th>
							<th scope="col" class="num">{{ __("Headcount") }}</th>
							<th scope="col" class="num">{{ __("Hospital norm") }}</th>
							<th scope="col" class="num">{{ __("Authority norm") }}</th>
							<th scope="col" class="num">{{ __("Applied qty") }}</th>
							<th scope="col">{{ __("Unit") }}</th>
							<th scope="col" class="num">{{ __("Wastage %") }}</th>
							<th scope="col">{{ __("Basis") }}</th>
							<th scope="col">{{ __("Excluded") }}</th>
							<th scope="col" class="num">{{ __("Provisional amount") }}</th>
							<th scope="col">{{ __("Confirmation") }}</th>
							<th scope="col"></th>
						</tr>
					</thead>
					<tbody v-for="g in groups" :key="g.key">
						<tr class="nc-ng__group">
							<td colspan="11">
								<button type="button" class="nc-ng__link" :aria-expanded="!collapsed[g.key]" @click="collapsed[g.key] = !collapsed[g.key]">
									<strong>{{ g.step_id || "" }}</strong> {{ g.title }} <span v-if="g.removed" class="indicator-pill red">{{ __("Removed step") }}</span> <span v-if="g.phase" class="text-muted">· {{ __(g.phase) }}</span>
									<span class="text-muted">({{ g.lines.length }})</span>
								</button>
							</td>
							<td class="num"><span v-if="g.total !== null">{{ money(g.total) }}</span></td>
							<td colspan="2"></td>
						</tr>
						<template v-if="!collapsed[g.key]">
							<template v-for="l in g.lines" :key="l.line_id">
								<tr :id="'nc-ng-' + l.line_id" class="nc-ng__row" :class="{ 'nc-ng__row--off': l.excluded, 'nc-ng__row--ai': l.ai_suggested }">
									<th scope="row">
										<button type="button" class="nc-ng__link" :aria-label="__('Line details') + ' ' + l.line_id" @click="detail = detail === l.line_id ? '' : l.line_id">{{ l.line_id }}</button>
										<span v-if="l.procedure_resource_row" class="text-muted nc-ng__small" :title="__('Source resource row') + ' ' + l.procedure_resource_row">·{{ l.procedure_resource_row }}</span>
										<span v-if="l.step_removed" class="indicator-pill red">{{ __("Removed step: {0}", [l.step_id]) }}</span>
										<span v-if="l.duplicate_of.length" class="indicator-pill orange" :title="__('Duplicate of {0}', [l.duplicate_of.join(', ')])">{{ __("Duplicate") }}</span>
									</th>
									<td>
										<select v-if="canEdit" :value="l.component" class="form-control nc-ng__cell" :aria-label="__('Component')" @change="commit(l, 'component', $event.target.value)">
											<option v-for="c in data.options.component" :key="c" :value="c">{{ compLabel(c) }}</option>
										</select>
										<span v-else>{{ compLabel(l.component) }}</span>
									</td>
									<td>
										<input v-if="canEdit" :key="l.line_id + (l.resource || '') + l.component" :value="l.resource_label" class="form-control nc-ng__cell" :list="'nc-ng-dl-' + l.component" :aria-label="__('Resource')" @focus="loadOptions(l.component, '')" @input="loadOptions(l.component, $event.target.value)" @change="commitResource(l, $event.target.value)" />
										<span v-else>{{ l.resource_label }}</span>
										<span v-if="l.unlinked" class="indicator-pill orange">{{ __("Not linked") }}</span>
										<span v-if="l.ai_suggested" class="indicator-pill purple">{{ __("Suggested") }}</span>
									</td>
									<td class="num">
										<input v-if="canEdit && l.component === 'LABOR'" :value="l.headcount" type="number" min="1" class="form-control nc-ng__cell num" :aria-label="__('Headcount')" @change="commit(l, 'headcount', Number($event.target.value))" />
										<span v-else-if="l.component === 'LABOR'">{{ l.headcount }}</span>
									</td>
									<td class="num">
										<input v-if="canEdit" :value="l.hospital_qty" type="number" step="any" class="form-control nc-ng__cell num" :aria-label="__('Hospital norm')" @change="commit(l, 'hospital_qty', Number($event.target.value))" />
										<span v-else>{{ num(l.hospital_qty) }}</span>
									</td>
									<td class="num">
										<input v-if="canEdit" :value="l.authority_qty || ''" type="number" step="any" class="form-control nc-ng__cell num" :aria-label="__('Authority norm')" @change="commit(l, 'authority_qty', Number($event.target.value))" />
										<span v-else>{{ l.authority_qty ? num(l.authority_qty) : "" }}</span>
									</td>
									<td class="num" :class="{ 'nc-ng__strong': l.authority_qty && l.applied_qty !== l.hospital_qty }">{{ num(l.applied_qty) }}</td>
									<td>
										<input v-if="canEdit" :value="l.uom" class="form-control nc-ng__cell" :aria-label="__('Unit')" @change="commit(l, 'uom', $event.target.value)" />
										<span v-else>{{ l.uom }}</span>
									</td>
									<td class="num">
										<template v-if="isMaterial(l)">
											<input v-if="canEdit" :value="l.wastage_rate || ''" type="number" step="any" min="0" class="form-control nc-ng__cell num" :aria-label="__('Wastage %')" @change="commit(l, 'wastage_rate', Number($event.target.value))" />
											<span v-else>{{ l.wastage_rate }}</span>
											<span v-if="l.wastage_rate > data.wastage_cap" class="indicator-pill yellow">{{ __("Over cap") }}</span>
										</template>
									</td>
									<td>
										<select v-if="canEdit" :value="l.basis" class="form-control nc-ng__cell" :aria-label="__('Basis')" @change="commit(l, 'basis', $event.target.value)">
											<option v-for="b in data.options.basis" :key="b" :value="b">{{ __(b) }}</option>
										</select>
										<span v-else>{{ __(l.basis) }}</span>
									</td>
									<td>
										<input v-if="canEdit" type="checkbox" :checked="!!l.is_excluded" :aria-label="__('Excluded')" @change="toggleExcluded(l, $event.target.checked)" />
										<span v-else-if="l.is_excluded">{{ __("Yes") }}</span>
										<span v-if="l.is_excluded" class="text-muted">{{ l.exclude_reason }}</span>
									</td>
									<td class="num">
										<span v-if="l.cost.missing" class="text-muted">{{ l.cost.missing }}</span>
										<span v-else>{{ money(l.cost.amount, 2) }}</span>
									</td>
									<td>
										<span v-if="l.confirmed_by" :title="l.confirmed_by + ' ' + (l.confirmed_on || '')">✓ {{ l.confirmed_by.split("@")[0] }}</span>
										<span v-else-if="l.step_removed" class="text-muted">{{ __("Needs a step") }}</span>
										<button v-else-if="can('confirm_line')" type="button" class="btn btn-default btn-xs" :disabled="busy" @click="confirmLine(l)">{{ __("Confirm") }}</button>
									</td>
									<td>
										<button type="button" class="btn btn-default btn-xs" :aria-label="__('Line details') + ' ' + l.line_id" @click="detail = detail === l.line_id ? '' : l.line_id">&hellip;</button>
									</td>
								</tr>
								<tr v-if="rowError[l.line_id]" class="nc-ng__rowerr"><td colspan="14" role="alert" class="nc-ng__error">{{ rowError[l.line_id] }}</td></tr>
								<tr v-if="detail === l.line_id" class="nc-ng__detail">
									<td colspan="14">
										<label>{{ __("Authority document") }}<input :value="l.authority_ref || ''" :disabled="!canEdit" class="form-control" @change="commit(l, 'authority_ref', $event.target.value)" /></label>
										<label>{{ __("Wastage reason") }}<textarea :value="l.wastage_reason || ''" :disabled="!canEdit" class="form-control" rows="2" @change="commit(l, 'wastage_reason', $event.target.value)"></textarea></label>
										<label>{{ __("Basis reference") }}<input :value="l.basis_ref || ''" :disabled="!canEdit" class="form-control" @change="commit(l, 'basis_ref', $event.target.value)" /></label>
										<label>{{ __("Exclusion reason") }}
											<select :value="l.exclude_reason || ''" :disabled="!canEdit" class="form-control" @change="commit(l, 'exclude_reason', $event.target.value)">
												<option value=""></option>
												<option v-for="r in data.options.exclude_reason" :key="r" :value="r">{{ r }}</option>
											</select>
										</label>
										<label v-if="canEdit && l.step_removed">{{ __("Attach to") }}
											<select class="form-control" required @change="reassign(l, $event.target.value)">
												<option value="">{{ __("Choose a step") }}</option>
												<option v-for="s in data.steps" :key="s.step_id" :value="s.step_id">{{ s.step_id }} · {{ s.step_title }}</option>
												<option value="__service__">{{ __("Whole service") }}</option>
											</select>
										</label>
										<button v-if="can('delete_line') && (!l.procedure_resource_row || l.step_removed)" type="button" class="btn btn-default btn-xs" :disabled="busy" @click="deleteLine(l)">{{ __("Delete line") }}</button>
									</td>
								</tr>
							</template>
						</template>
					</tbody>
				</table>
			</div>

			<section class="nc-ng__summary" :aria-label="__('Provisional direct cost')">
				<h4 class="nc-ng__h">{{ __("Provisional direct cost") }}<span v-if="data.summary.parameter_set"> ({{ data.summary.parameter_set }})</span></h4>
				<span v-if="data.summary.incomplete" class="indicator-pill yellow">{{ __("Incomplete: some lines have no price or are not linked") }}</span>
				<table class="nc-ng__table nc-ng__sumtable">
					<thead>
						<tr>
							<th scope="col">{{ __("Step") }}</th>
							<th v-for="c in data.options.component" :key="c" scope="col" class="num">{{ compLabel(c) }}</th>
							<th scope="col" class="num">{{ __("Total") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="(comps, key) in data.summary.by_step_component" :key="key">
							<th scope="row">{{ key === "service" ? __("Whole service") : key }}</th>
							<td v-for="c in data.options.component" :key="c" class="num">{{ comps[c] && Number(comps[c]) ? money(comps[c]) : "–" }}</td>
							<td class="num">{{ money(rowTotal(comps)) }}</td>
						</tr>
						<tr class="nc-ng__strong">
							<th scope="row">{{ __("Total") }}</th>
							<td v-for="c in data.options.component" :key="c" class="num">{{ data.summary.by_component[c] && Number(data.summary.by_component[c]) ? money(data.summary.by_component[c]) : "–" }}</td>
							<td class="num">{{ money(data.summary.total) }}</td>
						</tr>
					</tbody>
				</table>
				<p class="text-muted nc-ng__small">{{ __("For reference only; the official cost is calculated in the costing run.") }}</p>
			</section>
		</template>
	</div>
</template>

<script>
const API = "normcore.api.norm.";
// Màu chỉ báo theo design.md mục 3
const STATE_COLOR = { "Nháp": "gray", "Đã xác nhận chuyên môn": "blue", "Đã khóa": "green", "Đã thay thế": "darkgrey" };
const COMP_LABEL = { LABOR: "Nhân lực", DRUG: "Thuốc và hóa chất", SUPPLY: "Vật tư", EQUIPMENT: "Thiết bị", INFRA: "Hạ tầng", UTILITY: "Tiện ích" };
const MATERIAL = ["DRUG", "SUPPLY"];

function messageLines(r) {
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

export default {
	name: "NormGrid",
	props: { initialName: { type: String, default: "" } },
	data() {
		return {
			name: this.initialName,
			data: null,
			loading: false,
			error: "",
			busy: false,
			rowError: {},
			actionError: null,
			q: "",
			compFilter: "",
			onlyAttention: false,
			showExcluded: true,
			collapsed: {},
			detail: "",
			add: null,
			resourceOptions: {},
			pending: null,
			reason: "",
		};
	},
	computed: {
		actions() {
			return this.data ? this.data.actions : [];
		},
		canEdit() {
			return this.actions.includes("save_line");
		},
		closed() {
			return this.data && ["Đã khóa", "Đã thay thế"].includes(this.data.doc.status);
		},
		removedCount() {
			return this.data ? this.data.groups.filter((g) => g.removed).reduce((n, g) => n + g.lines.length, 0) : 0;
		},
		changeStrip() {
			return !!(this.data && this.data.doc.status === "Nháp" && this.data.doc.previous_version && (this.removedCount || this.data.steps_without_lines.length));
		},
		blockers() {
			return this.data ? this.data.blockers : [];
		},
		blockerIds() {
			return new Set(this.blockers.map((b) => b.line_id));
		},
		totalLines() {
			return this.data ? this.data.groups.reduce((n, g) => n + g.lines.length, 0) : 0;
		},
		groups() {
			if (!this.data) return [];
			const text = this.q.trim().toLowerCase();
			return this.data.groups.map((g, i) => {
				const step = this.data.steps.find((s) => s.step_id === g.step_id);
				const lines = g.lines.filter((l) => {
					if (this.compFilter && l.component !== this.compFilter) return false;
					if (!this.showExcluded && l.excluded) return false;
					if (this.onlyAttention && !(this.blockerIds.has(l.line_id) || l.duplicate_of.length || l.unlinked)) return false;
					if (text && !(l.line_id.toLowerCase().includes(text) || (l.resource || "").toLowerCase().includes(text))) return false;
					return true;
				});
				return { key: g.removed ? "removed" : g.step_id || "service", step_id: g.step_id, removed: !!g.removed, title: g.title, phase: step ? step.phase : "", lines, total: g.total };
			});
		},
	},
	mounted() {
		if (this.name) this.load(this.name);
	},
	methods: {
		stateColor: (s) => STATE_COLOR[s] || "gray",
		compLabel: (c) => COMP_LABEL[c] || c,
		isMaterial: (l) => MATERIAL.includes(l.component),
		can(a) {
			return this.actions.includes(a);
		},
		num(v) {
			return v === null || v === undefined || v === "" ? "" : format_number(Number(v), null, 2);
		},
		money(v, digits) {
			return format_number(Number(v || 0), null, digits || 0);
		},
		rowTotal(comps) {
			return Object.values(comps).reduce((s, v) => s + Number(v), 0);
		},
		doctypeOf(component) {
			return this.data.options.resource_doctype_by_component[component];
		},
		// Gọi API whitelisted; lỗi máy chủ hiện ở dải role="alert", không mở hộp thoại của Desk.
		call(method, args) {
			let serverError = null;
			return Promise.resolve(
				frappe.call({ method: API + method, args, freeze: false, silent: true, error(r) { serverError = r; } })
			)
				.then((r) => r.message)
				.catch((e) => {
					const r = serverError || (e && e.responseJSON) || e;
					const err = new Error(messageLines(r).join(" ") || __("Could not complete the request. See the message from the server."));
					err.lines = messageLines(r);
					err.status = e && e.status;
					throw err;
				});
		},
		open(name) {
			frappe.set_route("norm-grid", name);
		},
		load(name) {
			this.name = name;
			this.loading = true;
			this.error = "";
			return this.call("get_norm_set", { name })
				.then((d) => this.show(d))
				.catch((e) => {
					this.data = null;
					this.error = e.status === 403 ? __("You do not have permission to view this norm set.") : e.message;
				})
				.finally(() => (this.loading = false));
		},
		show(d) {
			this.data = d;
			this.name = d.doc.name;
			this.rowError = {};
		},
		run(fn) {
			this.busy = true;
			this.actionError = null;
			return fn().finally(() => (this.busy = false));
		},
		// Sửa một ô: gửi cả giá trị đổi của dòng (FR-NORM-003..014); lỗi → viền lỗi dưới dòng, lưới trở về giá trị đã lưu.
		commit(line, field, value, allowDuplicate) {
			const values = { [field]: value };
			if (field === "component") {
				values.resource_doctype = this.doctypeOf(value);
				values.resource = null;
			}
			return this.run(() =>
				this.call("save_line", { norm_set: this.name, values, line_id: line.line_id, allow_duplicate: allowDuplicate ? 1 : 0 })
					.then((r) => {
						if (r.saved) return this.show(r.norm_set);
						const others = r.duplicates.map((d) => d.line_id).join(", ");
						frappe.confirm(__("This resource is already in {0} of the same step. Save anyway?", [others]), () => this.commit(line, field, value, true), () => this.load(this.name));
					})
					.catch((e) => {
						this.rowError = { [line.line_id]: e.lines.join(" ") || e.message };
						return this.reloadKeepingError();
					})
			);
		},
		reloadKeepingError() {
			const keep = this.rowError;
			return this.call("get_norm_set", { name: this.name }).then((d) => {
				this.data = d;
				this.rowError = keep;
			});
		},
		toggleExcluded(line, on) {
			return this.commit(line, "is_excluded", on ? 1 : 0);
		},
		confirmLine(line) {
			return this.run(() =>
				this.call("confirm_line", { norm_set: this.name, line_id: line.line_id })
					.then((d) => {
						this.show(d);
						frappe.show_alert({ message: __("Confirmed {0}", [line.line_id]), indicator: "green" });
					})
					.catch((e) => (this.rowError = { [line.line_id]: e.message }))
			);
		},
		deleteLine(line) {
			return this.run(() =>
				this.call("delete_line", { norm_set: this.name, line_id: line.line_id })
					.then((d) => this.show(d))
					.catch((e) => (this.rowError = { [line.line_id]: e.message }))
			);
		},
		// Gợi ý nguồn lực lấy từ máy chủ (search_resources), không kiểm liên kết ở trình duyệt trên DocType người dùng không được đọc.
		loadOptions(component, txt) {
			return this.call("search_resources", { norm_set: this.name, component, txt: txt || "" })
				.then((rows) => (this.resourceOptions = { ...this.resourceOptions, [component]: rows }))
				.catch(() => {});
		},
		// Chữ người dùng nhập/chọn (nhãn hoặc mã) → mã nguồn lực; trống = bỏ liên kết.
		resolveResource(component, text) {
			const t = (text || "").trim().toLowerCase();
			if (!t) return Promise.resolve("");
			return this.loadOptions(component, text).then(() => {
				const rows = this.resourceOptions[component] || [];
				const hit = rows.find((o) => o.label.toLowerCase() === t || o.value.toLowerCase() === t);
				return hit ? hit.value : null;
			});
		},
		commitResource(line, text) {
			return this.resolveResource(line.component, text).then((value) => {
				if (value === null) {
					this.rowError = { [line.line_id]: __("Resource not found: {0}", [text]) };
					return this.reloadKeepingError();
				}
				if (value !== (line.resource || "")) return this.commit(line, "resource", value);
			});
		},
		openAddFor(step) {
			this.openAdd();
			this.add.target = step;
		},
		focusRemoved() {
			this.collapsed = { ...this.collapsed, removed: false };
			this.$nextTick(() => {
				const g = this.groups.find((x) => x.removed);
				if (g && g.lines.length) this.focusLine(g.lines[0].line_id);
			});
		},
		reassign(line, target) {
			if (!target) return;
			const values = target === "__service__" ? { service_level: 1, step_id: null } : { step_id: target, service_level: 0 };
			return this.run(() =>
				this.call("save_line", { norm_set: this.name, values, line_id: line.line_id, allow_duplicate: 1 })
					.then((r) => {
						this.show(r.norm_set);
						frappe.show_alert({ message: __("Moved {0} to {1}", [line.line_id, target === "__service__" ? __("Whole service") : target]), indicator: "green" });
					})
					.catch((e) => {
						this.rowError = { [line.line_id]: e.lines.join(" ") || e.message };
						return this.reloadKeepingError();
					})
			);
		},
		openAdd() {
			this.add = { component: "SUPPLY", resourceText: "", target: "", headcount: 1, hospital_qty: null, uom: "", basis: "Ước tính", error: "" };
		},
		submitAdd() {
			const f = this.add;
			return this.resolveResource(f.component, f.resourceText).then((resource) => {
				if (resource === null) {
					f.error = __("Resource not found: {0}", [f.resourceText]);
					return;
				}
				return this.sendAdd(f, resource || null);
			});
		},
		sendAdd(f, resource) {
			const values = {
				component: f.component,
				resource_doctype: this.doctypeOf(f.component),
				resource,
				hospital_qty: f.hospital_qty,
				uom: f.uom,
				basis: f.basis,
			};
			if (f.component === "LABOR") values.headcount = f.headcount;
			if (f.target === "__service__") values.service_level = 1;
			else values.step_id = f.target;
			const send = (allow) =>
				this.run(() =>
					this.call("save_line", { norm_set: this.name, values, allow_duplicate: allow ? 1 : 0 })
						.then((r) => {
							if (r.saved) {
								this.add = null;
								return this.show(r.norm_set);
							}
							const others = r.duplicates.map((d) => d.line_id).join(", ");
							frappe.confirm(__("This resource is already in {0} of the same step. Save anyway?", [others]), () => send(true));
						})
						.catch((e) => (f.error = e.lines.join(" ") || e.message))
				);
			return send(false);
		},
		startAction(a) {
			this.actionError = null;
			const msg = {
				confirm_set: __("After confirming, the set cannot be edited until Finance returns it."),
				lock_set: __("After locking, the norm set can no longer be edited and is used for costing."),
				new_version: this.data.doc.newer_procedure
					? __("Create a draft of version {0} from procedure {1}? Lines of existing steps are carried over; lines of removed steps are flagged.", [this.data.doc.version_no + 1, this.data.doc.newer_procedure])
					: __("Create a draft of version {0} from this set?", [this.data.doc.version_no + 1]),
			};
			this.pending = { action: a, message: msg[a], needsReason: a === "return_set" };
			this.reason = "";
		},
		runAction() {
			const p = this.pending;
			const args = { norm_set: this.name };
			if (p.action === "return_set") args.reason = this.reason;
			return this.run(() =>
				this.call(p.action, args)
					.then((d) => {
						this.pending = null;
						if (p.action === "new_version") {
							if (d.existing) frappe.msgprint(d.message);
							else if (d.procedure) {
								frappe.msgprint(
									[
										__("Carried over: {0} lines ({1})", [d.carried.length, d.carried.join(", ")]),
										__("Removed step: {0}", [d.removed.length]) + " (" + d.removed_steps.join(", ") + ")",
										__("Steps without lines") + ": " + (d.steps_without_lines.join(", ") || "-"),
									].join("<br>"),
									__("Open grid")
								);
							}
							return this.open(d.name);
						}
						this.show(d);
						frappe.show_alert({ message: __("Moved to {0}", [__(d.doc.status)]), indicator: "green" });
						this.$nextTick(() => this.$refs.state && this.$refs.state.focus());
					})
					.catch((e) => {
						this.pending = null;
						this.actionError = { lines: this.toActionLines(e) };
					})
			);
		},
		// "L002: Chưa xác nhận, ..." → một hàng bấm được, cuộn tới dòng đó
		toActionLines(e) {
			return (e.lines.length ? e.lines : [e.message]).map((text) => {
				const m = /^(L\d+)\b/.exec(text);
				return { text, line_id: m ? m[1] : "" };
			});
		},
		focusLine(id) {
			this.collapsed = {};
			this.$nextTick(() => {
				const el = document.getElementById("nc-ng-" + id);
				if (el) {
					el.scrollIntoView({ block: "center" });
					const b = el.querySelector("button");
					if (b) b.focus();
				}
			});
		},
		toggleAll() {
			const open = this.groups.some((g) => !this.collapsed[g.key]);
			const next = {};
			this.groups.forEach((g) => (next[g.key] = open));
			this.collapsed = next;
		},
	},
};
</script>

<style scoped>
.nc-ng {
	color: var(--text-color);
	background: var(--card-bg);
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	padding: var(--padding-lg);
}
.nc-ng__head {
	position: sticky;
	top: 0;
	z-index: 2;
	background: var(--card-bg);
	display: flex;
	justify-content: space-between;
	gap: var(--padding-md);
	flex-wrap: wrap;
	margin-bottom: var(--margin-md);
}
.nc-ng__title,
.nc-ng__actions,
.nc-ng__filters,
.nc-ng__form {
	display: flex;
	gap: var(--padding-sm);
	align-items: center;
	flex-wrap: wrap;
	margin-bottom: var(--margin-sm);
}
.nc-ng__notice,
.nc-ng__warn {
	background: var(--subtle-fg, var(--bg-light-gray));
	border-radius: var(--border-radius);
	padding: var(--padding-sm) var(--padding-md);
	margin-bottom: var(--margin-sm);
}
.nc-ng__warn {
	border-left: 3px solid var(--yellow-500, var(--primary));
}
.nc-ng__error {
	color: var(--red-600, var(--text-color));
	border-left: 3px solid var(--red-500, var(--text-color));
	padding: var(--padding-xs) var(--padding-sm);
	margin-bottom: var(--margin-sm);
}
.nc-ng__small {
	font-size: var(--text-xs);
}
.nc-ng__q {
	max-width: 260px;
}
.nc-ng__comp {
	max-width: 200px;
}
.nc-ng__scroll {
	overflow-x: auto;
	max-width: 100%;
}
.nc-ng__table {
	width: 100%;
	border-collapse: collapse;
	font-variant-numeric: tabular-nums;
}
.nc-ng__table th,
.nc-ng__table td {
	border-bottom: 1px solid var(--border-color);
	padding: var(--padding-xs) var(--padding-sm);
	text-align: left;
	vertical-align: middle;
	white-space: nowrap;
}
.nc-ng__table .num {
	text-align: right;
}
.nc-ng__table tbody th[scope="row"] {
	position: sticky;
	left: 0;
	background: var(--card-bg);
}
.nc-ng__group td {
	background: var(--subtle-fg, var(--bg-light-gray));
}
.nc-ng__row--off {
	color: var(--text-muted);
}
.nc-ng__row--ai {
	background: var(--subtle-fg, var(--bg-light-gray));
}
.nc-ng__cell {
	border-color: transparent;
	background: transparent;
	min-width: 70px;
	height: 28px;
	padding: 0 var(--padding-xs);
}
.nc-ng__cell:hover,
.nc-ng__cell:focus {
	border-color: var(--border-color);
}
.nc-ng__strong {
	font-weight: var(--weight-bold, bold);
}
.nc-ng__link {
	background: none;
	border: 0;
	padding: 0;
	color: var(--text-color);
	text-align: left;
}
.nc-ng__link:focus-visible,
.nc-ng button:focus-visible {
	outline: 2px solid var(--focus, var(--primary));
	outline-offset: 1px;
}
.nc-ng__detail td {
	background: var(--subtle-fg, var(--bg-light-gray));
	white-space: normal;
}
.nc-ng__detail label {
	display: inline-block;
	margin-right: var(--margin-md);
	vertical-align: top;
}
.nc-ng__summary {
	margin-top: var(--margin-lg);
}
.nc-ng__h {
	font-size: var(--text-md);
}
</style>
