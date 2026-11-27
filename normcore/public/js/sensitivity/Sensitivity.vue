<template>
	<div class="nc-sens__root">
		<div class="nc-sens__banner" role="status">
			<strong>{{ __("Trial result, not saved") }}</strong>
			<span class="text-muted">{{ __("Changes here are not written to the costing run.") }}</span>
		</div>

		<div v-if="!name && !loading" class="text-muted" role="note">{{ __("Open this page from the cost explanation of a service (Sensitivity analysis button).") }}</div>
		<div v-if="loading" class="text-muted" role="status">{{ __("Loading...") }}</div>
		<div v-if="loadError" class="nc-sens__error" role="alert">{{ loadError }}</div>

		<template v-if="base">
			<header class="nc-sens__title">
				<strong>{{ base.service }} · {{ base.service_name }}</strong>
				<span class="text-muted">{{ __("Department") }} {{ base.department }}</span>
				<a :href="'/app/nc-costing-run/' + encodeURIComponent(base.run)">{{ base.run }}</a>
				<span class="indicator-pill" :class="base.run_status === 'Đã khóa' ? 'green' : 'blue'">{{ base.run_status }}</span>
				<a :href="'/app/nc-service-cost/' + encodeURIComponent(base.service_cost)">{{ __("Cost explanation") }}</a>
			</header>

			<section class="nc-sens__block" :aria-label="__('Assumptions')">
				<h6>{{ __("Volume") }}</h6>
				<table v-if="base.is_paraclinical" class="table table-bordered nc-sens__table">
					<thead><tr><th>{{ __("Test system") }}</th><th class="text-right">{{ __("Original Qbn") }}</th><th>{{ __("Assumed Qbn") }}</th></tr></thead>
					<tbody>
						<tr v-for="s in base.inputs.systems" :key="s.test_system">
							<td>{{ s.test_system }}</td>
							<td class="text-right">{{ fmt(s.qbn, 0) }}</td>
							<td>
								<input v-model="form.system_volumes[s.test_system]" type="number" step="any" class="form-control input-sm" :class="{ 'nc-sens__invalid': fieldErr['v:' + s.test_system] }" :aria-label="__('Assumed Qbn') + ' ' + s.test_system" :aria-invalid="Boolean(fieldErr['v:' + s.test_system])" @keydown.enter.prevent />
								<div v-if="fieldErr['v:' + s.test_system]" class="nc-sens__help" role="alert">{{ fieldErr["v:" + s.test_system] }}</div>
							</td>
						</tr>
					</tbody>
				</table>
				<div v-else class="nc-sens__row">
					<span class="text-muted">{{ __("Original volume") }}: {{ fmt(base.inputs.volume, 0) }}</span>
					<input v-model="form.volume" type="number" step="any" class="form-control input-sm" :class="{ 'nc-sens__invalid': fieldErr.volume }" :aria-label="__('Assumed volume')" @keydown.enter.prevent />
					<div v-if="fieldErr.volume" class="nc-sens__help" role="alert">{{ fieldErr.volume }}</div>
				</div>

				<h6>{{ __("Unit price") }}</h6>
				<input v-if="base.inputs.items.length > 10" v-model="q" type="search" class="form-control input-sm nc-sens__search" :placeholder="__('Search item')" :aria-label="__('Search item')" />
				<table class="table table-bordered nc-sens__table">
					<thead><tr><th>{{ __("Item") }}</th><th>{{ __("Purchase unit") }}</th><th class="text-right">{{ __("Original price per purchase unit") }}</th><th>{{ __("Assumed price") }}</th></tr></thead>
					<tbody>
						<tr v-for="i in items" :key="i.item">
							<td>{{ i.item }} · {{ i.item_name }}</td>
							<td>{{ i.uom }}</td>
							<td class="text-right">{{ i.purchase_price === null ? "—" : fmt(i.purchase_price, 2) }}</td>
							<td>
								<input v-model="form.prices[i.item]" type="number" step="any" class="form-control input-sm" :class="{ 'nc-sens__invalid': fieldErr['p:' + i.item] }" :aria-label="__('Assumed price') + ' ' + i.item" @keydown.enter.prevent />
								<div v-if="fieldErr['p:' + i.item]" class="nc-sens__help" role="alert">{{ fieldErr["p:" + i.item] }}</div>
							</td>
						</tr>
					</tbody>
				</table>

				<template v-if="base.inputs.equipments.length">
					<h6>{{ __("Acquisition mode") }}</h6>
					<table class="table table-bordered nc-sens__table">
						<thead><tr><th>{{ __("Equipment") }}</th><th>{{ __("Original mode") }}</th><th>{{ __("Assumed mode") }}</th><th>{{ __("Annual contract cost") }}</th></tr></thead>
						<tbody>
							<tr v-for="e in base.inputs.equipments" :key="e.equipment">
								<td>{{ e.equipment }}</td>
								<td>{{ e.mode }}</td>
								<td>
									<select v-model="form.modes[e.equipment].mode" class="form-control input-sm" :aria-label="__('Assumed mode') + ' ' + e.equipment">
										<option value="">{{ __("Keep original") }}</option>
										<option v-for="m in base.modes" :key="m" :value="m">{{ m }}</option>
									</select>
								</td>
								<td>
									<input v-if="needsContract(e.equipment)" v-model="form.modes[e.equipment].contract_cost" type="number" step="any" class="form-control input-sm" :class="{ 'nc-sens__invalid': fieldErr['e:' + e.equipment] }" :aria-label="__('Annual contract cost') + ' ' + e.equipment" @keydown.enter.prevent />
									<div v-if="fieldErr['e:' + e.equipment]" class="nc-sens__help" role="alert">{{ fieldErr["e:" + e.equipment] }}</div>
								</td>
							</tr>
						</tbody>
					</table>
				</template>

				<div class="nc-sens__actions">
					<button type="button" class="btn btn-primary btn-sm" :disabled="busy" @click="compute">{{ busy ? __("Calculating...") : __("Calculate trial") }}</button>
					<button type="button" class="btn btn-default btn-sm" :disabled="busy" @click="reset">{{ __("Reset") }}</button>
					<span class="text-muted nc-sens__small">{{ __("Empty cell keeps the original value. Ctrl+Enter calculates.") }}</span>
				</div>
			</section>

			<div v-if="error" class="nc-sens__error" role="alert">{{ error }}</div>
			<div v-for="w in warnings" :key="w" class="nc-sens__warn" role="status">{{ w }}</div>
			<div v-if="trial && trial.status === 'Lỗi'" class="nc-sens__error" role="alert">{{ trial.message }}</div>

			<section class="nc-sens__block" :aria-label="__('Comparison')">
				<table class="table table-bordered nc-sens__table">
					<thead>
						<tr>
							<th>{{ __("Item") }}</th>
							<th class="text-right">{{ __("Original") }}</th>
							<th class="text-right nc-sens__trial">{{ __("Trial") }}</th>
							<th class="text-right">{{ __("Difference") }}</th>
							<th class="text-right">{{ __("Difference (%)") }}</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="r in rows" :key="r.key" :class="{ 'nc-sens__total': r.total }">
							<td>{{ r.label }}</td>
							<td class="text-right">{{ money(r.origin) }}</td>
							<td class="text-right nc-sens__trial">{{ r.trial === null ? "—" : money(r.trial) }}</td>
							<td class="text-right">{{ r.trial === null ? "—" : money(r.trial - r.origin) }}</td>
							<td class="text-right">{{ r.trial === null || !r.origin ? "—" : fmt(((r.trial - r.origin) / r.origin) * 100, 2) + "%" }}</td>
						</tr>
					</tbody>
				</table>
				<div v-if="!trial" class="text-muted nc-sens__small">{{ __("Enter assumptions, then press Calculate trial.") }}</div>
			</section>

			<section v-if="systems.length" class="nc-sens__block" :aria-label="__('By test system')">
				<h6>{{ __("By test system") }}</h6>
				<table class="table table-bordered nc-sens__table">
					<thead><tr><th>{{ __("Test system") }}</th><th class="text-right">{{ __("Original k") }}</th><th class="text-right nc-sens__trial">{{ __("Trial k") }}</th><th class="text-right">{{ __("Original direct cost per result") }}</th><th class="text-right nc-sens__trial">{{ __("Trial direct cost per result") }}</th></tr></thead>
					<tbody>
						<tr v-for="s in systems" :key="s.test_system">
							<td>{{ s.test_system }}</td>
							<td class="text-right">{{ fmt(s.k_origin, 6) }}</td>
							<td class="text-right nc-sens__trial">{{ fmt(s.k_trial, 6) }}</td>
							<td class="text-right">{{ money(s.direct_origin) }}</td>
							<td class="text-right nc-sens__trial">{{ money(s.direct_trial) }}</td>
						</tr>
					</tbody>
				</table>
			</section>
		</template>
	</div>
</template>

<script>
const API = "normcore.api.costing.";
const COMP_LABEL = { LABOR: "Labor", DRUG: "Drug and chemical", SUPPLY: "Supply", EQUIPMENT: "Equipment", INFRA: "Infrastructure", UTILITY: "Utility" };

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
	name: "Sensitivity",
	props: { initialName: { type: String, default: "" } },
	data() {
		return {
			name: this.initialName,
			base: null,
			loading: false,
			loadError: "",
			busy: false,
			error: "",
			fieldErr: {},
			trial: null,
			origin: null,
			systems: [],
			warnings: [],
			q: "",
			form: { volume: "", system_volumes: {}, prices: {}, modes: {} },
		};
	},
	computed: {
		items() {
			const q = this.q.trim().toLowerCase();
			const all = (this.base && this.base.inputs.items) || [];
			return q ? all.filter((i) => `${i.item} ${i.item_name}`.toLowerCase().includes(q)) : all;
		},
		rows() {
			const o = (this.base && this.base.origin) || {};
			const t = this.trial;
			const comp = (k) => (o.by_component || {})[k] || 0;
			const rows = Object.keys(COMP_LABEL).map((k) => ({ key: k, label: __(COMP_LABEL[k]), origin: comp(k), trial: t ? (t.by_component || {})[k] || 0 : null }));
			rows.push({ key: "alloc", label: __("Allocation"), origin: o.alloc_total || 0, trial: t ? t.alloc_total || 0 : null });
			rows.push({ key: "full", label: __("Full cost"), origin: o.full_cost || 0, trial: t ? t.full_cost : null, total: true });
			rows.push({ key: "calc", label: __("Calculated price"), origin: o.calculated_price || 0, trial: t ? t.calculated_price : null });
			rows.push({ key: "round", label: __("Rounded price"), origin: o.rounded_price || 0, trial: t ? t.rounded_price : null, total: true });
			return rows;
		},
	},
	mounted() {
		this.onKey = (e) => {
			if (e.ctrlKey && e.key === "Enter") this.compute();
		};
		this.$el.addEventListener("keydown", this.onKey);
		if (this.name) this.load(this.name);
	},
	methods: {
		fmt(v, digits) {
			if (v === null || v === undefined) return "—";
			return Number(v).toLocaleString("vi-VN", { minimumFractionDigits: digits, maximumFractionDigits: digits });
		},
		money(v) {
			return frappe.format(v || 0, { fieldtype: "Currency" });
		},
		needsContract(code) {
			const m = this.form.modes[code] && this.form.modes[code].mode;
			return m === "Thuê" || m === "Liên doanh, liên kết";
		},
		clearResult() {
			this.trial = null;
			this.systems = [];
			this.warnings = [];
		},
		load(name) {
			this.name = name;
			this.loading = true;
			this.loadError = "";
			this.base = null;
			this.clearResult();
			let serverError = null;
			frappe
				.call({ method: API + "get_sensitivity_base", args: { service_cost: name }, freeze: false, silent: true, error(r) { serverError = r; } })
				.then((r) => {
					this.loading = false;
					if (!r || !r.message) {
						this.loadError = serverMessage(serverError) || __("Cannot open the sensitivity analysis.");
						return;
					}
					this.base = r.message;
					this.reset();
				})
				.catch(() => {
					this.loading = false;
					this.loadError = serverMessage(serverError) || __("Cannot open the sensitivity analysis.");
				});
		},
		reset() {
			const modes = {};
			((this.base && this.base.inputs.equipments) || []).forEach((e) => (modes[e.equipment] = { mode: "", contract_cost: "" }));
			this.form = { volume: "", system_volumes: {}, prices: {}, modes };
			this.fieldErr = {};
			this.error = "";
			this.clearResult();
		},
		blank(v) {
			return v === "" || v === null || v === undefined;
		},
		validate() {
			const err = {};
			const f = this.form;
			Object.entries(f.system_volumes).forEach(([k, v]) => {
				if (!this.blank(v) && !(Number(v) > 0)) err["v:" + k] = __("Assumed volume must be greater than 0");
			});
			if (!this.blank(f.volume) && !(Number(f.volume) > 0)) err.volume = __("Assumed volume must be greater than 0");
			Object.entries(f.prices).forEach(([k, v]) => {
				if (!this.blank(v) && Number(v) < 0) err["p:" + k] = __("Assumed price must not be negative");
			});
			Object.entries(f.modes).forEach(([k, m]) => {
				if (m.mode && this.needsContract(k) && !(Number(m.contract_cost) > 0)) err["e:" + k] = __("Enter the annual contract cost");
			});
			return err;
		},
		overrides() {
			const f = this.form;
			const out = {};
			const pick = (obj) => Object.fromEntries(Object.entries(obj).filter(([, v]) => !this.blank(v)).map(([k, v]) => [k, Number(v)]));
			if (!this.blank(f.volume)) out.volume = Number(f.volume);
			const sv = pick(f.system_volumes);
			if (Object.keys(sv).length) out.system_volumes = sv;
			const pr = pick(f.prices);
			if (Object.keys(pr).length) out.prices = pr;
			const eq = {};
			Object.entries(f.modes).forEach(([k, m]) => {
				if (m.mode) eq[k] = { mode: m.mode, contract_cost: this.needsContract(k) ? Number(m.contract_cost) : undefined };
			});
			if (Object.keys(eq).length) out.equipment_modes = eq;
			return out;
		},
		compute() {
			if (!this.base || this.busy) return;
			this.error = "";
			this.fieldErr = this.validate();
			this.clearResult();
			if (Object.keys(this.fieldErr).length) return;
			const ov = this.overrides();
			if (!Object.keys(ov).length) {
				this.error = __("Enter at least one assumption");
				return;
			}
			this.busy = true;
			let serverError = null;
			frappe
				.call({ method: API + "run_sensitivity", args: { service_cost: this.name, overrides: JSON.stringify(ov) }, freeze: false, silent: true, error(r) { serverError = r; } })
				.then((r) => {
					this.busy = false;
					if (!r || !r.message) {
						this.error = serverMessage(serverError) || __("The trial calculation failed.");
						return;
					}
					this.trial = r.message.trial;
					this.systems = r.message.systems || [];
					this.warnings = r.message.warnings || [];
				})
				.catch(() => {
					this.busy = false;
					this.error = serverMessage(serverError) || __("The trial calculation failed.");
				});
		},
	},
};
</script>

<style scoped>
.nc-sens__root {
	color: var(--text-color);
	max-width: 1300px;
}
.nc-sens__banner {
	position: sticky;
	top: 0;
	z-index: 2;
	display: flex;
	gap: var(--padding-md);
	align-items: baseline;
	padding: var(--padding-sm) var(--padding-md);
	background: var(--alert-bg-info, var(--bg-light-gray));
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	margin-bottom: var(--margin-md);
}
.nc-sens__title {
	display: flex;
	gap: var(--padding-md);
	align-items: center;
	flex-wrap: wrap;
	margin-bottom: var(--margin-md);
}
.nc-sens__block {
	margin-bottom: var(--margin-lg);
}
.nc-sens__table input,
.nc-sens__table select {
	max-width: 220px;
}
.nc-sens__trial {
	background: var(--bg-light-gray);
}
.nc-sens__total td {
	font-weight: var(--weight-bold, 700);
}
.nc-sens__actions {
	display: flex;
	gap: var(--padding-sm);
	align-items: center;
	flex-wrap: wrap;
}
.nc-sens__small {
	font-size: var(--text-sm);
}
.nc-sens__search {
	max-width: 280px;
	margin-bottom: var(--margin-sm);
}
.nc-sens__invalid {
	border-color: var(--red-500);
}
.nc-sens__help {
	color: var(--red-600);
	font-size: var(--text-sm);
}
.nc-sens__error,
.nc-sens__warn {
	padding: var(--padding-sm) var(--padding-md);
	border-radius: var(--border-radius-md);
	margin-bottom: var(--margin-md);
}
.nc-sens__error {
	background: var(--red-50, var(--bg-light-gray));
	color: var(--red-700, var(--text-color));
	border: 1px solid var(--red-300, var(--border-color));
}
.nc-sens__warn {
	background: var(--yellow-50, var(--bg-light-gray));
	border: 1px solid var(--yellow-300, var(--border-color));
}
</style>
