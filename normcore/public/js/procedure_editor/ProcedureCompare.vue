<template>
	<div class="nc-cmp" @keydown.alt.left.prevent="shift(-1)" @keydown.alt.right.prevent="shift(1)" @keydown.esc="openStep = ''">
		<div class="nc-cmp__bar">
			<strong class="nc-cmp__title">{{ __("Compare versions") }}<template v-if="data"> — {{ data.base.name }}</template></strong>
			<label class="sr-only" for="nc-cmp-base">{{ __("Base version") }}</label>
			<select id="nc-cmp-base" v-model="baseSel" class="form-control nc-cmp__select" :disabled="loading" @change="go">
				<option v-for="v in versions" :key="v.name" :value="v.name">{{ label(v) }}</option>
			</select>
			<label class="sr-only" for="nc-cmp-target">{{ __("Compared version") }}</label>
			<select id="nc-cmp-target" v-model="targetSel" class="form-control nc-cmp__select" :disabled="loading" @change="go">
				<option v-for="v in versions" :key="v.name" :value="v.name">{{ label(v) }}</option>
			</select>
			<button type="button" class="btn btn-default btn-sm" :aria-label="__('Swap direction')" @click="swap">⇄</button>
			<button type="button" class="btn btn-default btn-sm" @click="$emit('close', targetSel)">{{ __("Close comparison") }}</button>
		</div>

		<div v-if="loading" class="text-muted" role="status">{{ __("Loading...") }}</div>
		<div v-else-if="error" class="nc-cmp__error" role="alert">
			{{ error }}
			<button type="button" class="btn btn-default btn-xs" @click="fetch">{{ __("Retry") }}</button>
		</div>
		<div v-else-if="versions.length < 2" class="text-muted">
			{{ __("This procedure has only one version. Comparison is available once a revision exists.") }}
		</div>

		<template v-else-if="data">
			<div class="nc-cmp__summary" role="group" :aria-label="__('Summary of differences')">
				<div v-for="g in groups" :key="g.key" class="nc-cmp__group">
					<strong>{{ g.label }}</strong>
					<span class="indicator-pill green">{{ __("Added") }} {{ data.summary[g.key].added }}</span>
					<span class="indicator-pill red">{{ __("Removed") }} {{ data.summary[g.key].removed }}</span>
					<span class="indicator-pill yellow">{{ __("Changed") }} {{ data.summary[g.key].changed }}</span>
				</div>
				<label class="nc-cmp__only"><input v-model="onlyDiff" type="checkbox" /> {{ __("Show differences only") }}</label>
			</div>
			<div v-if="total === 0" class="text-muted">{{ __("The two versions do not differ in sections, steps or resources.") }}</div>

			<section class="nc-cmp__block">
				<h4 class="nc-cmp__h">{{ __("Sections") }}</h4>
				<div v-for="s in shownSections" :key="s.key" class="nc-cmp__card" :class="'nc-cmp__' + s.status">
					<div class="nc-cmp__cardhead">
						<strong>{{ __(s.label) }}</strong>
						<span class="indicator-pill" :class="color(s.status)">{{ statusLabel(s.status) }}</span>
					</div>
					<div v-if="s.status !== 'same'" class="nc-cmp__cols">
						<div class="nc-cmp__col"><div class="text-muted">v{{ data.base.version_no }}</div><div v-html="clean(s.old)"></div></div>
						<div class="nc-cmp__col"><div class="text-muted">v{{ data.target.version_no }}</div><div v-html="clean(s.new)"></div></div>
					</div>
				</div>
			</section>

			<section class="nc-cmp__block">
				<h4 class="nc-cmp__h">{{ __("Steps") }}</h4>
				<div class="nc-cmp__scroll">
					<table class="table table-bordered nc-cmp__table">
						<thead>
							<tr>
								<th scope="col">{{ __("Step code") }}</th>
								<th scope="col">{{ __("Phase") }}</th>
								<th scope="col">{{ __("Step title") }}</th>
								<th scope="col">{{ __("Status") }}</th>
								<th scope="col">{{ __("Changed fields") }}</th>
							</tr>
						</thead>
						<tbody>
							<template v-for="st in shownSteps" :key="st.step_id">
								<tr class="nc-cmp__row" :class="'nc-cmp__' + st.status" tabindex="0" :aria-expanded="openStep === st.step_id" @click="toggle(st)" @keydown.enter.prevent="toggle(st)">
									<td>{{ st.step_id }}</td>
									<td>{{ (st.new || st.old).phase }}</td>
									<td :class="{ 'nc-cmp__strike': st.status === 'removed' }">{{ (st.new || st.old).step_title }}</td>
									<td>
										<span class="indicator-pill" :class="color(st.status)">{{ statusLabel(st.status) }}</span>
										<span v-if="st.moved" class="indicator-pill gray">{{ __("Moved") }}</span>
									</td>
									<td>{{ changedFields(st).join(", ") }}</td>
								</tr>
								<tr v-if="openStep === st.step_id" class="nc-cmp__detail">
									<td colspan="5">
										<div v-for="f in st.fields" :key="f">{{ fieldLabel(f) }}: {{ st.old[f] }} → {{ st.new[f] }}</div>
										<div v-for="r in resourcesOf(st.step_id)" :key="r.resource_row_id">
											{{ r.resource_row_id }}: {{ statusLabel(r.status) }}
										</div>
									</td>
								</tr>
							</template>
						</tbody>
					</table>
				</div>
			</section>

			<section class="nc-cmp__block">
				<h4 class="nc-cmp__h">{{ __("Resource lines") }}</h4>
				<div class="nc-cmp__scroll">
					<table class="table table-bordered nc-cmp__table">
						<thead>
							<tr>
								<th scope="col">{{ __("Line code") }}</th>
								<th scope="col">{{ __("Step code") }}</th>
								<th scope="col">{{ __("Type") }}</th>
								<th scope="col">{{ __("Name") }}</th>
								<th scope="col">{{ __("Quantity") }}</th>
								<th scope="col">{{ __("Unit") }}</th>
								<th scope="col">{{ __("Headcount") }}</th>
								<th scope="col">{{ __("Status") }}</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="r in shownResources" :key="r.resource_row_id" :class="'nc-cmp__' + r.status">
								<td>{{ r.resource_row_id }}</td>
								<td>{{ r.step_id }}</td>
								<td>{{ cell(r, "resource_type") }}</td>
								<td>{{ cell(r, "resource_text") }}</td>
								<td class="text-right">{{ cell(r, "quantity", true) }}</td>
								<td>{{ cell(r, "uom") }}</td>
								<td class="text-right">{{ cell(r, "headcount", true) }}</td>
								<td><span class="indicator-pill" :class="color(r.status)">{{ statusLabel(r.status) }}</span></td>
							</tr>
						</tbody>
					</table>
				</div>
			</section>
		</template>
	</div>
</template>

<script>
const API = "normcore.api.procedure.";
const STATUS_COLOR = { added: "green", removed: "red", changed: "yellow", same: "gray" };
const FIELD_LABEL = { phase: "Phase", step_title: "Step title", description: "Description", reference_minutes: "Reference minutes" };

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
	name: "ProcedureCompare",
	props: { base: { type: String, required: true }, target: { type: String, required: true } },
	emits: ["close", "route"],
	data() {
		return { baseSel: this.base, targetSel: this.target, versions: [], data: null, loading: false, error: "", onlyDiff: true, openStep: "" };
	},
	computed: {
		groups() {
			return [
				{ key: "sections", label: __("Sections") },
				{ key: "steps", label: __("Steps") },
				{ key: "resources", label: __("Resource lines") },
			];
		},
		total() {
			const s = this.data.summary;
			return ["sections", "steps", "resources"].reduce((n, k) => n + s[k].added + s[k].removed + s[k].changed, 0);
		},
		shownSections() {
			return this.data.sections.filter((s) => !this.onlyDiff || s.status !== "same");
		},
		shownSteps() {
			return this.data.steps.filter((s) => !this.onlyDiff || s.status !== "same" || s.moved);
		},
		shownResources() {
			return this.data.resources.filter((r) => !this.onlyDiff || r.status !== "same");
		},
	},
	watch: {
		base(v) { this.baseSel = v; this.fetch(); },
		target(v) { this.targetSel = v; this.fetch(); },
	},
	mounted() {
		this.fetch();
	},
	methods: {
		call(method, args) {
			let serverError = null;
			return Promise.resolve(frappe.call({ method: API + method, args, freeze: false, silent: true, error(r) { serverError = r; } }))
				.then((r) => r.message)
				.catch((e) => {
					throw new Error(messageFromError(serverError || (e && e.responseJSON)) || __("Could not complete this action"));
				});
		},
		fetch() {
			this.loading = true;
			this.error = "";
			return this.call("list_versions", { procedure: this.baseSel })
				.then((v) => {
					this.versions = v || [];
					if (this.versions.length < 2) {
						this.data = null;
						return null;
					}
					return this.call("compare_versions", { base: this.baseSel, target: this.targetSel }).then((d) => (this.data = d));
				})
				.catch((e) => {
					this.data = null;
					this.error = e.message;
				})
				.finally(() => (this.loading = false));
		},
		go() {
			this.$emit("route", this.baseSel, this.targetSel);
		},
		swap() {
			[this.baseSel, this.targetSel] = [this.targetSel, this.baseSel];
			this.go();
		},
		shift(d) {
			const names = this.versions.map((v) => v.name);
			const i = names.indexOf(this.targetSel) + d;
			if (i >= 0 && i < names.length) {
				this.targetSel = names[i];
				this.go();
			}
		},
		label(v) {
			const date = v.effective_date ? frappe.datetime.str_to_user(v.effective_date) : "—";
			return `v${v.version_no} · ${__(v.workflow_state)} · ${date}`;
		},
		color(status) {
			return STATUS_COLOR[status] || "gray";
		},
		statusLabel(status) {
			return { added: __("Added"), removed: __("Removed"), changed: __("Changed"), same: __("Unchanged") }[status];
		},
		clean(html) {
			return frappe.utils.xss_sanitise ? frappe.utils.xss_sanitise(html || "") : frappe.utils.escape_html(html || "");
		},
		fieldLabel(f) {
			return __(FIELD_LABEL[f] || f);
		},
		resourcesOf(stepId) {
			return this.data.resources.filter((r) => r.step_id === stepId && r.status !== "same");
		},
		changedFields(st) {
			const out = st.fields.map((f) => this.fieldLabel(f));
			if (st.status === "changed" && this.resourcesOf(st.step_id).length) out.push(__("Resources"));
			if (st.status === "same" && this.resourcesOf(st.step_id).length) out.push(__("Resources"));
			return out;
		},
		toggle(st) {
			this.openStep = this.openStep === st.step_id ? "" : st.step_id;
		},
		cell(r, f, number) {
			const fmt = (v) => (v === null || v === undefined || v === "" ? "" : number ? Number(v).toLocaleString("vi-VN") : v);
			const o = r.old ? fmt(r.old[f]) : "";
			const n = r.new ? fmt(r.new[f]) : "";
			return r.status === "changed" && r.fields.includes(f) ? `${o} → ${n}` : n || o;
		},
	},
};
</script>

<style scoped>
.nc-cmp { color: var(--text-color); }
.nc-cmp__bar, .nc-cmp__summary, .nc-cmp__cardhead, .nc-cmp__group { display: flex; gap: var(--padding-sm); align-items: center; flex-wrap: wrap; margin-bottom: var(--margin-md); }
.nc-cmp__select { max-width: 280px; }
.nc-cmp__error { color: var(--text-color); background: var(--bg-red); border: 1px solid var(--red-500); border-radius: var(--border-radius-md); padding: var(--padding-sm); }
.nc-cmp__h { font-size: var(--text-md); margin: var(--margin-lg) 0 var(--margin-sm); }
.nc-cmp__card { border: 1px solid var(--border-color); border-radius: var(--border-radius-md); padding: var(--padding-md); margin-bottom: var(--margin-sm); }
.nc-cmp__cols { display: grid; grid-template-columns: 1fr 1fr; gap: var(--padding-md); min-width: 0; }
.nc-cmp__col { min-width: 520px; max-width: 100%; overflow-wrap: anywhere; }
.nc-cmp__scroll { max-width: 100%; overflow-x: auto; }
.nc-cmp__table { margin-bottom: 0; }
.nc-cmp__added { background: var(--bg-green); border-left: 3px solid var(--green-500); }
.nc-cmp__removed { background: var(--bg-red); border-left: 3px solid var(--red-500); }
.nc-cmp__changed { background: var(--bg-yellow); border-left: 3px solid var(--yellow-500); }
.nc-cmp__strike { text-decoration: line-through; }
.nc-cmp__row { cursor: pointer; }
.nc-cmp__row:focus-visible { outline: 2px solid var(--primary); }
</style>
