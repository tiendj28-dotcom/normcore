<template>
	<div class="nc-pc__root">
		<div v-if="!run" class="nc-pc__pick">
			<label>{{ __("Costing run") }}
				<select v-model="picked" class="form-control input-sm" :aria-label="__('Costing run')" @change="picked && load(picked)">
					<option value="">{{ __("Select a costing run") }}</option>
					<option v-for="r in runs" :key="r.name" :value="r.name">{{ r.title || r.name }}</option>
				</select>
			</label>
		</div>
		<div v-if="error" class="alert alert-warning" role="alert">{{ error }}</div>

		<template v-if="data">
			<section class="nc-pc__scenario" :aria-busy="scenarioLoading ? 'true' : 'false'">
				<div v-if="data.run.based_on_run" class="alert alert-warning" role="status">
					{{ __("This is an adjustment scenario of {0}; suggestions are handled on the original run", [data.run.based_on_run]) }}
					<a href="#" @click.prevent="load(data.run.based_on_run)">{{ __("Open original run") }}</a>
				</div>
				<div v-if="scenario" class="alert alert-info" role="status">
					{{ __("Open scenario {0} · {1} changes · calculated {2}", [scenario.name, scenario.change_count, date(scenario.created_on)]) }}
					<button type="button" class="btn btn-default btn-xs" :aria-pressed="showScenario ? 'true' : 'false'" @click="showScenario = !showScenario">{{ __("Show scenario") }}</button>
					<button v-if="scenario.can_create" type="button" class="btn btn-default btn-xs" @click="newScenario">{{ __("New scenario") }}</button>
				</div>
				<div v-for="w in (scenario ? scenario.warnings : [])" :key="w" class="alert alert-warning nc-pc__small" role="status">{{ w }}</div>
				<a v-if="!scenario && canCreateScenario" href="#" class="nc-pc__small" @click.prevent="newScenario">{{ __("Create scenario") }}</a>
			</section>

			<header class="nc-pc__head">
				<strong>{{ data.run.title }}</strong>
				<span class="indicator-pill" :class="data.run.status === 'Đã khóa' ? 'gray' : 'blue'">{{ data.run.status }}</span>
				<span class="text-muted">{{ __("Costing date") }}: {{ date(data.run.costing_date) }}</span>
				<span class="text-muted">{{ __("Price category") }}: {{ data.run.price_category }}</span>
				<span class="text-muted">{{ __("Parameter set") }}: {{ data.run.parameter_set }}</span>
				<span class="text-muted nc-pc__small">{{ __("Window {0} months · at least {1} facilities · tolerance {2}%", [data.run.window_months, data.run.min_facilities, fmt(data.run.tolerance, 0)]) }}</span>
			</header>

			<section class="nc-pc__filters" :aria-label="__('Filters')">
				<label v-for="f in filterDefs" :key="f.key">{{ f.label }}
					<select v-model="filters[f.key]" multiple class="form-control input-sm" :aria-label="f.label" @change="reload">
						<option v-for="o in data.filter_options[f.key]" :key="o" :value="o">{{ o }}</option>
					</select>
				</label>
				<label class="nc-pc__check"><input v-model="useAdjusted" type="checkbox" @change="reload" /> {{ __("Use CPI-adjusted prices") }}</label>
				<label class="nc-pc__check"><input v-model="onlyOver" type="checkbox" /> {{ __("Only over tolerance") }}</label>
				<input v-model="q" type="search" class="form-control input-sm nc-pc__search" :placeholder="__('Search service')" :aria-label="__('Search service')" />
			</section>

			<div v-if="!data.rows.length" class="alert alert-info" role="status">{{ __("This costing run has no service results") }}</div>

			<div v-else class="nc-pc__cols">
				<div class="nc-pc__list" :aria-busy="loading ? 'true' : 'false'">
					<table class="table table-bordered nc-pc__table">
						<thead>
							<tr>
								<th v-for="c in columns" :key="c.key" scope="col" :class="{ 'text-right': c.num }">
									<a href="#" @click.prevent="sortBy(c.key)">{{ c.label }}</a>
								</th>
								<th v-if="scenario" scope="col" class="text-right">{{ __("Scenario price") }}</th>
								<th scope="col">{{ __("Price comparison bar") }}</th>
								<th scope="col" class="text-right">{{ __("Suggestions") }}</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="r in rows" :key="r.service_cost" tabindex="0" :class="{ 'nc-pc__sel': r.service_cost === selected }" @click="select(r)" @keydown.enter="select(r)" @keydown.down.prevent="move(1)" @keydown.up.prevent="move(-1)">
								<td>{{ r.technical_service }}</td>
								<td>{{ r.service_name }}</td>
								<td>{{ r.department }}</td>
								<td class="text-right">{{ money(r.calculated_price) }}</td>
								<td class="text-right">{{ r.count }}</td>
								<template v-if="r.sufficient">
									<td class="text-right">{{ money(r.min) }}</td>
									<td class="text-right">{{ money(r.median) }}</td>
									<td class="text-right">{{ money(r.max) }}</td>
									<td class="text-right">
										{{ pct(r.deviation_pct) }}
										<span v-if="r.exceeds" class="indicator-pill orange">{{ __("Over tolerance") }}</span>
									</td>
								</template>
								<template v-else>
									<td class="text-right">—</td>
									<td class="text-right">—</td>
									<td class="text-right">—</td>
									<td><span class="indicator-pill gray">{{ __("Not enough comparison data") }}</span></td>
								</template>
								<td v-if="scenario" class="text-right">
									<template v-if="scenarioPrice(r) !== null">
										{{ money(scenarioPrice(r)) }}
										<span v-if="scenarioDiff(r)" class="text-muted nc-pc__small">{{ signedMoney(scenarioDiff(r)) }}</span>
									</template>
									<span v-else>—</span>
								</td>
								<td>
									<div v-if="r.sufficient" class="nc-pc__bar" role="img" :aria-label="__('Min {0}, median {1}, max {2}, hospital {3}', [money(r.min), money(r.median), money(r.max), money(r.calculated_price)])">
										<span class="nc-pc__tick" :style="{ left: pos(r, r.median) + '%' }"></span>
										<span class="nc-pc__dot" :style="{ left: pos(r, r.calculated_price) + '%' }"></span>
									</div>
								</td>
								<td class="text-right">{{ r.suggestion_counts["Mới"] }}<span v-if="r.suggestion_counts[FORWARDED]" class="text-muted nc-pc__small"> · {{ __("Sent as procedure change request") }}: {{ r.suggestion_counts[FORWARDED] }}</span></td>
							</tr>
						</tbody>
					</table>
				</div>

				<div class="nc-pc__detail" role="region" aria-live="polite" :aria-busy="detailLoading ? 'true' : 'false'">
					<section v-if="showScenario && scenario" role="region" :aria-label="__('Scenario')">
						<h6>{{ __("Scenario") }} {{ scenario.name }}</h6>
						<table class="table table-bordered nc-pc__table">
							<thead><tr>
								<th scope="col">{{ __("Type") }}</th><th scope="col">{{ __("Service") }}</th><th scope="col">{{ __("Target") }}</th><th scope="col">{{ __("Field") }}</th>
								<th scope="col">{{ __("Old") }} → {{ __("New") }}</th><th scope="col">{{ __("Source suggestion") }}</th>
							</tr></thead>
							<tbody>
								<tr v-if="!scenario.changes.length"><td colspan="6" class="text-muted">{{ __("No changes yet") }}</td></tr>
								<tr v-for="(c, i) in scenario.changes" :key="i">
									<td>{{ c.change_type }}</td><td>{{ c.technical_service || __("Whole run") }}</td><td>{{ c.target_ref }}</td><td>{{ fieldLabel(c.field) }}</td>
									<td>{{ c.old_value }} → {{ c.new_value }}</td>
									<td><a v-if="c.source_suggestion" :href="'/app/nc-adjustment-suggestion/' + encodeURIComponent(c.source_suggestion)">{{ c.source_suggestion }}</a></td>
								</tr>
							</tbody>
						</table>
						<label class="nc-pc__check"><input v-model="showAllServices" type="checkbox" /> {{ __("Show all services") }}</label>
						<table class="table table-bordered nc-pc__table">
							<thead><tr>
								<th scope="col">{{ __("Service") }}</th><th scope="col">{{ __("Department") }}</th><th scope="col" class="text-right">{{ __("Original price") }}</th>
								<th scope="col" class="text-right">{{ __("Scenario price") }}</th><th scope="col" class="text-right">{{ __("Difference") }}</th><th scope="col" class="text-right">{{ __("Difference %") }}</th>
							</tr></thead>
							<tbody>
								<tr v-for="r in scenarioRows" :key="r.technical_service + r.department">
									<td>{{ r.technical_service }}</td><td>{{ r.department }}</td><td class="text-right">{{ money(r.base_price) }}</td>
									<td class="text-right">{{ money(r.scenario_price) }}</td><td class="text-right">{{ signedMoney(r.diff) }}</td><td class="text-right">{{ pct(r.diff_pct) }}</td>
								</tr>
							</tbody>
						</table>
						<a v-if="canCompareRuns" href="#" @click.prevent="compareRuns">{{ __("Compare runs") }}</a>
					</section>
					<div v-if="detailError" class="alert alert-danger" role="alert">{{ detailError }}</div>
					<div v-if="!detail && !detailError && !showScenario" class="text-muted">{{ __("Select a service to see details") }}</div>
					<template v-if="detail && !showScenario">
						<section>
							<h6>{{ __("Reference prices") }}</h6>
							<table class="table table-bordered nc-pc__table">
								<thead><tr>
									<th scope="col">{{ __("Facility") }}</th><th scope="col">{{ __("Province/City") }}</th><th scope="col">{{ __("Level") }}</th><th scope="col">{{ __("Ownership") }}</th>
									<th scope="col">{{ __("Effective date") }}</th><th scope="col" class="text-right">{{ __("Price") }}</th><th scope="col" class="text-right">{{ __("Adjusted price") }}</th><th scope="col">{{ __("Source") }}</th>
								</tr></thead>
								<tbody>
									<tr v-for="p in detail.prices" :key="p.name">
										<td>{{ p.facility_name || p.facility }}</td><td>{{ p.province }}</td><td>{{ p.facility_level }}</td><td>{{ p.ownership }}</td>
										<td>{{ date(p.effective_date) }}</td><td class="text-right">{{ money(p.price) }}</td>
										<td class="text-right">{{ p.adjusted && p.adjusted.adjusted_price !== null && p.adjusted.adjusted_price !== undefined ? money(p.adjusted.adjusted_price) : __("Missing price index") }}</td>
										<td><a v-if="p.source_url" :href="p.source_url" target="_blank" rel="noopener">{{ p.source_doc_no || p.source_url }}</a><span v-else>{{ p.source_doc_no }}</span></td>
									</tr>
								</tbody>
							</table>
							<details v-if="detail.excluded.length">
								<summary>{{ __("Excluded prices ({0})", [detail.excluded.length]) }}</summary>
								<ul>
									<li v-for="e in detail.excluded" :key="e.name">{{ e.facility }} · {{ date(e.effective_date) }} · {{ money(e.price) }} — {{ e.reason }}</li>
								</ul>
							</details>
						</section>

						<section>
							<h6>{{ __("Cost structure") }}</h6>
							<div class="nc-pc__stack" role="img" :aria-label="__('Cost structure')">
								<span v-for="(r, i) in positive" :key="r.field" class="nc-pc__seg" :style="{ width: r.share_pct + '%', background: palette(i) }" :title="r.label + ' ' + pct(r.share_pct, false)"></span>
							</div>
							<table class="table table-bordered nc-pc__table">
								<thead><tr><th scope="col">{{ __("Group") }}</th><th scope="col">{{ __("Component") }}</th><th scope="col" class="text-right">{{ __("Value") }}</th><th scope="col" class="text-right">{{ __("Share") }}</th></tr></thead>
								<tbody>
									<tr v-for="r in detail.breakdown.rows" :key="r.field">
										<td>{{ r.group }}</td><td>{{ r.label }}</td><td class="text-right">{{ money(r.value) }}</td><td class="text-right">{{ pct(r.share_pct, false) }}</td>
									</tr>
									<tr class="nc-pc__total">
										<td colspan="2">{{ __("Full cost") }}</td><td class="text-right">{{ money(detail.breakdown.full_cost) }}</td><td class="text-right">100%</td>
									</tr>
								</tbody>
							</table>
						</section>

						<section>
							<h6>{{ __("Adjustment suggestions") }}</h6>
							<div v-if="!detail.stats.sufficient" class="alert alert-info" role="status">{{ __("Not enough comparison data: no comparison-based suggestions") }}</div>
							<div v-else-if="!detail.stats.exceeds" class="alert alert-success" role="status">{{ __("Within tolerance, no adjustment needed") }}</div>
							<template v-else>
								<button v-if="detail.can_generate" type="button" class="btn btn-primary btn-sm" :disabled="generating" :aria-busy="generating ? 'true' : 'false'" @click="generate">{{ detail.suggestions.length ? __("Regenerate") : __("Generate suggestions") }}</button>
								<div v-else-if="!detail.suggestions.length" class="text-muted nc-pc__small">{{ __("No suggestions generated yet") }}</div>
							</template>
							<div v-for="s in detail.suggestions" :key="s.name" class="nc-pc__card">
								<div>
									<strong>{{ s.rule_code }}</strong>
									<span class="indicator-pill" :class="s.direction === 'Giảm' ? 'green' : 'orange'">{{ s.direction }}</span>
									<span v-if="s.requires_procedure_change" class="indicator-pill red">{{ __("Requires procedure change") }}</span>
									<span class="indicator-pill" :class="statusColor(s.status)">{{ s.status }}</span>
								</div>
								<div>{{ s.text }}</div>
								<div class="text-muted nc-pc__small">{{ __("Target") }}: {{ s.target_ref }} · {{ __("Current") }}: {{ s.current_value }} → {{ __("Suggested") }}: {{ s.suggested_value }}</div>
								<div>{{ __("Impact") }}: <span v-if="s.estimated_impact !== null && s.estimated_impact !== undefined">{{ money(s.estimated_impact) }}</span><span v-else class="text-muted">{{ __("Not estimated") }}</span></div>
								<div v-if="s.status !== 'Mới'" class="text-muted nc-pc__small">{{ s.decided_by }} · {{ s.decided_on }}<span v-if="s.decision_reason"> · {{ s.decision_reason }}</span></div>
								<div v-if="s.status === FORWARDED && s.change_request" class="text-muted nc-pc__small">
									<a :href="'/app/nc-procedure-change-request/' + encodeURIComponent(s.change_request)">{{ s.change_request }}</a>
								</div>
								<div v-if="s.status === 'Chấp nhận' && scenario && !s.requires_procedure_change" class="text-muted nc-pc__small">{{ __("In scenario {0}", [scenario.name]) }}</div>
								<div v-if="s.status === 'Mới' && detail.can_decide" class="nc-pc__actions">
									<button v-if="!s.requires_procedure_change" type="button" class="btn btn-default btn-sm" :disabled="accepting === s.name" :aria-busy="accepting === s.name ? 'true' : 'false'" @click="accept(s)">{{ accepting === s.name ? __("Recalculating scenario…") : __("Accept") }}</button>
									<button v-else type="button" class="btn btn-default btn-sm" @click="sendRequest(s)">{{ __("Send procedure change request") }}</button>
									<button type="button" class="btn btn-default btn-sm" @click="reject(s)">{{ __("Reject") }}</button>
								</div>
							</div>
							<div v-if="detail.suggestions.length" class="text-muted nc-pc__small">{{ __("Estimated impact, level-2 allocation not recomputed") }}</div>
							<button v-if="detail.can_request_change" type="button" class="btn btn-default btn-sm" @click="proposeChange">{{ __("Propose procedure change") }}</button>
						</section>
					</template>
				</div>
			</div>
		</template>
	</div>
</template>

<script>
const API = "normcore.api.price_compare.";
const SCENARIO_API = "normcore.api.scenario.";
const FORWARDED = "Đã chuyển yêu cầu sửa quy trình";
const PALETTE = ["--blue-500", "--green-500", "--orange-500", "--purple-500", "--cyan-500", "--yellow-500", "--red-400", "--pink-500", "--teal-500", "--gray-500", "--blue-300", "--green-300"];

function serverMessage(r) {
	if (!r || !r._server_messages) return "";
	try {
		return JSON.parse(r._server_messages)
			.map((m) => (typeof m === "string" && m.startsWith("{") ? JSON.parse(m).message : m))
			.join(" ")
			.replace(/<[^>]+>/g, " ")
			.trim();
	} catch (e) {
		return "";
	}
}

export default {
	name: "PriceCompare",
	props: { initialRun: { type: String, default: "" } },
	data() {
		return {
			run: this.initialRun,
			picked: "",
			runs: [],
			data: null,
			loading: false,
			error: "",
			filters: { provinces: [], levels: [], ownerships: [] },
			useAdjusted: false,
			onlyOver: false,
			q: "",
			sort: { key: "deviation_pct", dir: -1 },
			selected: "",
			detail: null,
			detailLoading: false,
			detailError: "",
			generating: false,
			timer: null,
			FORWARDED,
			scenario: null,
			scenarioLoading: false,
			showScenario: false,
			showAllServices: false,
			accepting: "",
		};
	},
	computed: {
		filterDefs() {
			return [
				{ key: "provinces", label: __("Province/City") },
				{ key: "levels", label: __("Level") },
				{ key: "ownerships", label: __("Ownership") },
			];
		},
		columns() {
			return [
				{ key: "technical_service", label: __("Code") },
				{ key: "service_name", label: __("Service name") },
				{ key: "department", label: __("Department") },
				{ key: "calculated_price", label: __("Calculated price"), num: true },
				{ key: "count", label: __("Facilities"), num: true },
				{ key: "min", label: __("Lowest"), num: true },
				{ key: "median", label: __("Median"), num: true },
				{ key: "max", label: __("Highest"), num: true },
				{ key: "deviation_pct", label: __("Deviation %"), num: true },
			];
		},
		rows() {
			const q = this.q.trim().toLowerCase();
			let rows = this.data.rows.filter((r) => (!this.onlyOver || r.exceeds) && (!q || `${r.technical_service} ${r.service_name}`.toLowerCase().includes(q)));
			const { key, dir } = this.sort;
			const val = (r) => (key === "deviation_pct" ? (r.deviation_pct === null ? null : Math.abs(r.deviation_pct)) : r[key]);
			rows = rows.slice().sort((a, b) => {
				const x = val(a), y = val(b);
				if (x === null || x === undefined) return 1;
				if (y === null || y === undefined) return -1;
				return (x < y ? -1 : x > y ? 1 : 0) * dir;
			});
			return rows;
		},
		canCreateScenario() {
			return !!frappe.model.can_create("NC Costing Run") && !(this.data && this.data.run.based_on_run);
		},
		canCompareRuns() {
			return ["NC Finance", "NC Director", "NC Admin", "NC Auditor"].some((r) => frappe.user.has_role(r));
		},
		scenarioRows() {
			const rows = this.scenario ? this.scenario.rows : [];
			return this.showAllServices ? rows : rows.filter((r) => r.diff);
		},
		positive() {
			return (this.detail ? this.detail.breakdown.rows : []).filter((r) => r.share_pct > 0);
		},
	},
	mounted() {
		if (this.run) this.load(this.run);
		else this.loadRuns();
	},
	methods: {
		fmt(v, digits) {
			if (v === null || v === undefined) return "—";
			return Number(v).toLocaleString("vi-VN", { minimumFractionDigits: digits, maximumFractionDigits: digits });
		},
		pct(v, signed = true) {
			if (v === null || v === undefined) return "—";
			const n = Number(v);
			return (signed && n > 0 ? "+" : "") + this.fmt(n, 2) + "%";
		},
		money(v) {
			return frappe.format(v || 0, { fieldtype: "Currency" });
		},
		date(v) {
			return v ? frappe.datetime.str_to_user(v) : "";
		},
		palette(i) {
			return `var(${PALETTE[i % PALETTE.length]})`;
		},
		statusColor(s) {
			return { "Mới": "blue", "Chấp nhận": "green", "Từ chối": "gray" }[s] || "purple";
		},
		signedMoney(v) {
			const n = Number(v || 0);
			return (n < 0 ? "−" : n > 0 ? "+" : "") + this.money(Math.abs(n));
		},
		fieldLabel(f) {
			return { utilization_rate: __("Utilization rate"), hospital_qty: __("Minutes"), wastage_rate: __("Wastage %"), accumulation_rate: __("Accumulation rate %") }[f] || f;
		},
		scenarioRow(r) {
			return this.scenario && this.scenario.rows.find((x) => x.technical_service === r.technical_service && x.department === r.department);
		},
		scenarioPrice(r) {
			const x = this.scenarioRow(r);
			return x ? x.scenario_price : null;
		},
		scenarioDiff(r) {
			const x = this.scenarioRow(r);
			return x ? x.diff : 0;
		},
		callApi(method, args, failure) {
			let serverError = null;
			return frappe
				.call({ method, args, freeze: false, silent: true, error(r) { serverError = r; } })
				.then((r) => {
					if (!r || !r.message) throw new Error(serverMessage(serverError) || failure);
					return r.message;
				})
				.catch((e) => {
					throw new Error(serverMessage(serverError) || (e && e.message) || failure);
				});
		},
		loadScenario(run) {
			this.scenarioLoading = true;
			return this.callApi(SCENARIO_API + "get_open_scenario", { run }, "")
				.then((m) => (this.scenario = m))
				.catch(() => (this.scenario = null))
				.finally(() => (this.scenarioLoading = false));
		},
		newScenario() {
			frappe.confirm(__("Start a new empty scenario? The current one is kept."), () =>
				this.callApi(SCENARIO_API + "create_scenario", { run: this.run }, __("Cannot create the scenario."))
					.then(() => this.loadScenario(this.run).then(() => (this.showScenario = true)))
					.catch((e) => frappe.msgprint({ message: e.message, indicator: "red" }))
			);
		},
		compareRuns() {
			frappe.set_route("query-report", "NC Costing Run Comparison", { base_run: this.run, other_run: this.scenario.name });
		},
		accept(s) {
			if (this.accepting) return;
			this.accepting = s.name;
			this.callApi(SCENARIO_API + "accept_suggestion", { name: s.name }, __("Cannot save the decision."))
				.then((m) => {
					this.accepting = "";
					if (m.outcome === "scenario") {
						frappe.show_alert({ message: __("Added to scenario {0}; new price {1}", [m.scenario, this.money(m.scenario_price)]), indicator: "green" });
						if (m.norm_set) {
							const text = m.norm_set_created
								? __("Draft norm set {0} created with the new value, waiting for re-confirmation", [m.norm_set])
								: __("Applied to draft norm set {0}", [m.norm_set]);
							frappe.msgprint({ message: text + ` <a href="/app/norm-grid/${encodeURIComponent(m.norm_set)}">${__("Open norm set")}</a>`, indicator: "blue" });
						}
					} else {
						frappe.show_alert({ message: (m.warnings || []).join(" "), indicator: "orange" });
					}
					this.afterDecision();
				})
				.catch((e) => {
					this.accepting = "";
					frappe.msgprint({ message: e.message, indicator: "red" });
				});
		},
		sendRequest(s) {
			const dialog = new frappe.ui.Dialog({
				title: __("Send procedure change request"),
				fields: [
					{ fieldtype: "HTML", options: `<p>${frappe.utils.escape_html(__("The change will not be applied to the scenario or norm set; a request is sent to the department in charge"))}</p><p>${frappe.utils.escape_html(s.text)}</p>` },
					{ fieldname: "note", fieldtype: "Small Text", label: __("Note") },
				],
				primary_action_label: __("Send procedure change request"),
				primary_action: (v) => {
					this.callApi(SCENARIO_API + "accept_suggestion", { name: s.name, note: v.note }, __("Cannot save the decision."))
						.then((m) => {
							dialog.hide();
							frappe.show_alert({ message: __("Request {0} sent", [m.change_request]), indicator: "green" });
							(m.warnings || []).forEach((w) => frappe.show_alert({ message: w, indicator: "orange" }));
							this.afterDecision();
						})
						.catch((e) => frappe.msgprint({ message: e.message, indicator: "red" }));
				},
			});
			dialog.show();
		},
		proposeChange() {
			frappe.prompt(
				[
					{ fieldname: "proposed_change", fieldtype: "Text", label: __("Proposed change (add, remove or change steps/resources)"), reqd: 1 },
					{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 },
				],
				(v) =>
					this.callApi(SCENARIO_API + "request_procedure_change", { service_cost: this.selected, ...v }, __("Cannot save the decision."))
						.then((m) => frappe.show_alert({ message: __("Request {0} sent", [m.change_request]), indicator: "green" }))
						.catch((e) => frappe.msgprint({ message: e.message, indicator: "red" })),
				__("Propose procedure change"),
				__("Send")
			);
		},
		afterDecision() {
			this.load(this.run); // tải lại bảng, dải kịch bản và chi tiết dịch vụ đang chọn
		},
		pos(r, v) {
			const span = Number(r.max) - Number(r.min);
			if (!span) return 50;
			return Math.max(0, Math.min(100, ((Number(v) - Number(r.min)) / span) * 100));
		},
		sortBy(key) {
			this.sort = { key, dir: this.sort.key === key ? -this.sort.dir : -1 };
		},
		loadRuns() {
			frappe.db
				.get_list("NC Costing Run", { filters: { status: ["in", ["Đã tính", "Đã khóa"]] }, fields: ["name", "title"], limit: 100 })
				.then((rows) => (this.runs = rows || []))
				.catch(() => (this.runs = []));
		},
		args() {
			return { provinces: this.filters.provinces, levels: this.filters.levels, ownerships: this.filters.ownerships, use_adjusted: this.useAdjusted ? 1 : 0 };
		},
		load(run) {
			this.run = run;
			this.loading = true;
			this.error = "";
			let serverError = null;
			frappe
				.call({ method: API + "get_comparison", args: { run, ...this.args() }, freeze: false, silent: true, error(r) { serverError = r; } })
				.then((r) => {
					this.loading = false;
					if (!r || !r.message) {
						this.error = serverMessage(serverError) || __("Cannot open the price comparison.");
						this.data = null;
						return;
					}
					this.data = r.message;
					this.loadScenario(run);
					const keep = this.data.rows.find((x) => x.service_cost === this.selected);
					if (keep) this.openDetail(keep.service_cost);
					else {
						this.selected = "";
						this.detail = null;
					}
				})
				.catch(() => {
					this.loading = false;
					this.error = serverMessage(serverError) || __("Cannot open the price comparison.");
				});
		},
		reload() {
			clearTimeout(this.timer);
			this.timer = setTimeout(() => this.load(this.run), 300);
		},
		select(r) {
			this.selected = r.service_cost;
			this.openDetail(r.service_cost);
		},
		move(step) {
			const i = this.rows.findIndex((r) => r.service_cost === this.selected);
			const next = this.rows[Math.max(0, Math.min(this.rows.length - 1, i + step))];
			if (next) this.select(next);
		},
		openDetail(name) {
			this.detailLoading = true;
			this.detailError = "";
			let serverError = null;
			frappe
				.call({ method: API + "get_service_detail", args: { service_cost: name, ...this.args() }, freeze: false, silent: true, error(r) { serverError = r; } })
				.then((r) => {
					this.detailLoading = false;
					if (!r || !r.message) {
						this.detail = null;
						this.detailError = serverMessage(serverError) || __("Cannot open the service detail.");
						return;
					}
					this.detail = r.message;
				})
				.catch(() => {
					this.detailLoading = false;
					this.detailError = serverMessage(serverError) || __("Cannot open the service detail.");
				});
		},
		generate() {
			if (this.generating) return;
			this.generating = true;
			let serverError = null;
			frappe
				.call({ method: API + "generate_suggestions", args: { service_cost: this.selected, ...this.args() }, freeze: false, silent: true, error(r) { serverError = r; } })
				.then((r) => {
					this.generating = false;
					if (!r || !r.message) {
						this.detailError = serverMessage(serverError) || __("Cannot generate suggestions.");
						return;
					}
					this.detail.suggestions = r.message;
					this.refreshCounts();
				})
				.catch(() => {
					this.generating = false;
					this.detailError = serverMessage(serverError) || __("Cannot generate suggestions.");
				});
		},
		reject(s) {
			frappe.prompt(
				[{ fieldname: "reason", fieldtype: "Small Text", label: __("Reason"), reqd: 1 }],
				(v) => this.decide(s, "Từ chối", v.reason),
				__("Reject suggestion"),
				__("Reject")
			);
		},
		decide(s, decision, reason) {
			let serverError = null;
			frappe
				.call({ method: API + "decide_suggestion", args: { name: s.name, decision, reason }, freeze: false, silent: true, error(r) { serverError = r; } })
				.then((r) => {
					if (!r || !r.message) {
						frappe.msgprint(serverMessage(serverError) || __("Cannot save the decision."));
						return;
					}
					Object.assign(s, r.message);
					this.refreshCounts();
				})
				.catch(() => frappe.msgprint(serverMessage(serverError) || __("Cannot save the decision.")));
		},
		refreshCounts() {
			const row = this.data.rows.find((x) => x.service_cost === this.selected);
			if (!row || !this.detail) return;
			const c = { "Mới": 0, "Chấp nhận": 0, "Từ chối": 0, [FORWARDED]: 0 };
			this.detail.suggestions.forEach((s) => {
				if (s.status in c) c[s.status] += 1;
			});
			row.suggestion_counts = c;
		},
	},
};
</script>

<style scoped>
.nc-pc__root {
	color: var(--text-color);
}
.nc-pc__head,
.nc-pc__filters {
	display: flex;
	gap: var(--padding-md);
	align-items: center;
	flex-wrap: wrap;
	margin-bottom: var(--margin-md);
}
.nc-pc__filters select {
	min-width: 160px;
}
.nc-pc__check {
	display: flex;
	gap: var(--padding-xs);
	align-items: center;
}
.nc-pc__search {
	max-width: 240px;
}
.nc-pc__cols {
	display: grid;
	grid-template-columns: 3fr 2fr;
	gap: var(--padding-lg);
}
@media (max-width: 1365px) {
	.nc-pc__cols {
		grid-template-columns: 1fr;
	}
}
.nc-pc__list,
.nc-pc__detail {
	overflow: auto;
	max-height: 75vh;
}
.nc-pc__table td,
.nc-pc__table th {
	white-space: nowrap;
}
.nc-pc__sel {
	background: var(--control-bg);
}
.nc-pc__small {
	font-size: var(--text-sm);
}
.nc-pc__bar {
	position: relative;
	height: 8px;
	min-width: 90px;
	background: var(--gray-200);
	border-radius: var(--border-radius-sm);
}
.nc-pc__tick {
	position: absolute;
	top: -3px;
	width: 2px;
	height: 14px;
	background: var(--text-color);
}
.nc-pc__dot {
	position: absolute;
	top: -2px;
	width: 12px;
	height: 12px;
	margin-left: -6px;
	border-radius: 50%;
	background: var(--primary);
}
.nc-pc__stack {
	display: flex;
	height: 14px;
	margin-bottom: var(--margin-sm);
	border-radius: var(--border-radius-sm);
	overflow: hidden;
	background: var(--gray-200);
}
.nc-pc__seg {
	display: block;
	height: 100%;
}
.nc-pc__total td {
	font-weight: var(--weight-bold, 700);
}
.nc-pc__card {
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	padding: var(--padding-sm) var(--padding-md);
	margin: var(--margin-sm) 0;
}
.nc-pc__actions {
	display: flex;
	gap: var(--padding-sm);
	align-items: center;
	margin-top: var(--margin-sm);
}
</style>
