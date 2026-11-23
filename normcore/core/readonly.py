"""NC Auditor chỉ đọc (FR-ACC-007; TC-CLS-44). Hàm thuần, không phụ thuộc frappe.

`core/permissions.py::read_only_violations` đọc CSDL rồi gọi vào đây.
"""

READ_ONLY_ROLE = "NC Auditor"
# Cùng tập với AUDITOR_FORBIDDEN của scripts/check_conventions.py (NC-06); test đơn vị so hai tập bằng nhau.
WRITE_PTYPES = (
	"write",
	"create",
	"delete",
	"submit",
	"cancel",
	"amend",
	"import",
	"share",
	"set_user_permissions",
)


def _on(value):
	return value in (1, True, "1")


def perm_violations(doctype, perms, role=READ_ONLY_ROLE):
	"""Vi phạm quyền của `role` trên một DocType. `perms`: list dict (role, permlevel, cờ quyền)."""
	rows = [p for p in perms if p.get("role") == role]
	out = []
	if not any(_on(p.get("read")) and not (p.get("permlevel") or 0) for p in rows):
		out.append(f"{doctype}: {role} thiếu quyền read (permlevel 0)")
	for p in rows:
		level = p.get("permlevel") or 0
		for ptype in WRITE_PTYPES:
			if _on(p.get(ptype)):
				out.append(f"{doctype}: {role} có quyền {ptype} (permlevel {level})")
	return out


def workflow_violations(workflows, role=READ_ONLY_ROLE):
	"""Vi phạm Workflow: `role` được chuyển trạng thái (duyệt) hoặc sửa ở một trạng thái."""
	out = []
	for wf in workflows:
		name = wf.get("name")
		for t in wf.get("transitions") or []:
			if t.get("allowed") == role:
				out.append(f'Workflow {name}: {role} được chuyển "{t.get("action")}" từ "{t.get("state")}"')
		for s in wf.get("states") or []:
			if s.get("allow_edit") == role:
				out.append(f'Workflow {name}: {role} có allow_edit ở trạng thái "{s.get("state")}"')
	return out
