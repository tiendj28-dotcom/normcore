// Thẻ tình trạng chuỗi: bốn chấm nối bằng một đường mảnh (SCR-DSK-005, FEAT-002).
// Dùng biến CSS của Desk; chấm có title và aria-label, màu không là kênh duy nhất.
frappe.provide("normcore.chain_dots");

normcore.chain_dots.STAGE_ORDER = ["procedure", "norm_set", "cost", "price"];

normcore.chain_dots.LABELS = function () {
	return {
		procedure: __("Procedure"),
		norm_set: __("Norm set"),
		cost: __("Service cost"),
		price: __("Approved price"),
	};
};

normcore.chain_dots.COLORS = {
	green: "var(--green-500)",
	blue: "var(--blue-500)",
	yellow: "var(--yellow-500)",
	red: "var(--red-500)",
	gray: "var(--gray-400)",
};

// dots: [{key, state, indicator}] (state: ok | empty | no_permission)
normcore.chain_dots.render = function (dots) {
	const labels = normcore.chain_dots.LABELS();
	const parts = (dots || []).map((d) => {
		const label = labels[d.key] || d.key;
		const state =
			d.state === "no_permission"
				? __("No permission to view")
				: d.state === "ok"
					? __("Available")
					: __("Not available");
		const text = frappe.utils.escape_html(`${label}: ${state}`);
		const hollow = d.state === "no_permission";
		const color = normcore.chain_dots.COLORS[d.indicator] || normcore.chain_dots.COLORS.gray;
		const style = hollow
			? "background: transparent; border: 1px solid var(--gray-500)"
			: `background: ${color}; border: 1px solid ${color}`;
		return `<span class="nc-chain-dot" role="img" title="${text}" aria-label="${text}"
			style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; ${style}"></span>`;
	});
	return `<span class="nc-chain-dots" style="display: inline-flex; align-items: center; gap: 4px">${parts.join(
		'<span style="width: 6px; border-top: 1px solid var(--border-color)"></span>'
	)}</span>`;
};
