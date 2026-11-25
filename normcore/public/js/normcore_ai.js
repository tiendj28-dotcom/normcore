// FR-AI-015: nút gọi AI chỉ hiện khi AI bật trong NC AI Settings.
// FEAT thêm nút AI phải bọc bằng normcore.ai.enabled() và gọi gateway.ensure_enabled() ở máy chủ.
frappe.provide("normcore.ai");

normcore.ai.enabled = function () {
	return !!(frappe.boot && frappe.boot.normcore_ai_enabled);
};

// Ẩn (hoặc hiện) một nút của form theo cấu hình AI: normcore.ai.toggle(frm, __("Soạn bằng AI"))
normcore.ai.toggle = function (frm, label, group) {
	if (!normcore.ai.enabled()) {
		frm.remove_custom_button(label, group);
		return false;
	}
	return true;
};
