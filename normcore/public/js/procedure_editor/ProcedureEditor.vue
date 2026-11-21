<template>
	<div class="nc-pe">
		<div class="nc-pe__bar">
			<select v-model="selected" class="form-control nc-pe__select" @change="load(selected)">
				<option value="">{{ __("Select a procedure") }}</option>
				<option v-for="p in procedures" :key="p.name" :value="p.name">
					{{ p.name }} ({{ p.workflow_state }})
				</option>
			</select>
		</div>

		<div v-if="error" class="nc-pe__error">{{ error }}</div>

		<div v-if="!doc" class="nc-pe__empty text-muted">
			{{ __("Pick a procedure to see its steps.") }}
		</div>

		<template v-else>
			<div class="nc-pe__title">
				<strong>{{ doc.name }}</strong>
				<span class="indicator-pill" :class="doc.workflow_state === published ? 'green' : 'gray'">
					{{ doc.workflow_state }}
				</span>
			</div>

			<table class="nc-pe__table">
				<thead>
					<tr>
						<th>{{ __("Step ID") }}</th>
						<th>{{ __("Phase") }}</th>
						<th>{{ __("Step title") }}</th>
						<th>{{ __("Description") }}</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="s in doc.steps" :key="s.step_id">
						<td>{{ s.step_id }}</td>
						<td>{{ s.phase }}</td>
						<td>{{ s.step_title }}</td>
						<td>{{ s.description }}</td>
					</tr>
					<tr v-if="!doc.steps.length">
						<td colspan="4" class="text-muted">{{ __("No steps yet. Add the first step below.") }}</td>
					</tr>
				</tbody>
			</table>

			<form v-if="doc.can_edit" class="nc-pe__form" @submit.prevent="addStep">
				<select v-model="form.phase" class="form-control">
					<option v-for="p in phases" :key="p" :value="p">{{ p }}</option>
				</select>
				<input v-model="form.step_title" class="form-control" :placeholder="__('Step title')" />
				<input v-model="form.description" class="form-control" :placeholder="__('Description')" />
				<button type="submit" class="btn btn-primary btn-sm" :disabled="busy">{{ __("Add step") }}</button>
			</form>
			<div v-else class="nc-pe__readonly text-muted">
				{{ __("This procedure cannot be edited by you or is already issued.") }}
			</div>
		</template>
	</div>
</template>

<script>
export default {
	name: "ProcedureEditor",
	props: { initialName: { type: String, default: "" } },
	data() {
		return {
			procedures: [],
			selected: this.initialName,
			doc: null,
			error: "",
			busy: false,
			published: "Đã ban hành",
			phases: ["Chuẩn bị", "Thực hiện", "Theo dõi", "Kết thúc"],
			form: { phase: "Thực hiện", step_title: "", description: "" },
		};
	},
	mounted() {
		this.call("normcore.api.procedure.list_procedures").then((r) => (this.procedures = r || []));
		if (this.selected) this.load(this.selected);
	},
	methods: {
		call(method, args) {
			this.error = "";
			return frappe
				.call({ method, args, freeze: false, error() {} })
				.then((r) => r.message)
				.catch(() => {
					this.error = __("Could not complete the request. Check your permissions.");
				});
		},
		load(name) {
			if (!name) {
				this.doc = null;
				return Promise.resolve();
			}
			this.selected = name;
			return this.call("normcore.api.procedure.get_procedure", { name }).then((doc) => {
				if (doc) this.doc = doc;
			});
		},
		addStep() {
			this.busy = true;
			return this.call("normcore.api.procedure.add_step", { procedure: this.doc.name, ...this.form })
				.then((step) => {
					if (step) {
						this.form.step_title = "";
						this.form.description = "";
						return this.load(this.doc.name);
					}
				})
				.finally(() => (this.busy = false));
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
	max-width: 1100px;
}
.nc-pe__bar,
.nc-pe__title {
	margin-bottom: var(--margin-md);
	display: flex;
	gap: var(--padding-sm);
	align-items: center;
}
.nc-pe__select {
	max-width: 420px;
}
.nc-pe__table {
	width: 100%;
	border-collapse: collapse;
	margin-bottom: var(--margin-md);
}
.nc-pe__table th,
.nc-pe__table td {
	border-bottom: 1px solid var(--border-color);
	padding: var(--padding-sm) var(--padding-md);
	text-align: left;
	vertical-align: top;
}
.nc-pe__table th {
	color: var(--text-muted);
	font-weight: 500;
}
.nc-pe__form {
	display: grid;
	grid-template-columns: 140px 1fr 2fr auto;
	gap: var(--padding-sm);
}
.nc-pe__error {
	color: var(--red-500);
	margin-bottom: var(--margin-md);
}
@media (max-width: 800px) {
	.nc-pe__form {
		grid-template-columns: 1fr;
	}
}
</style>
