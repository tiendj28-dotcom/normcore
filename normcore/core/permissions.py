"""Phạm vi theo khoa (FR-ACC-003, FR-ACC-006; architecture.md mục 8).

Khoa được gán của người dùng lưu bằng User Permission trên NC Department. Hai hook dưới đây
(`has_permission`, `permission_query_conditions`) áp phạm vi cho mọi DocType khai trong `SCOPE_RULES`;
DocType về sau (phiếu bấm giờ, hệ thống xét nghiệm...) chỉ thêm một dòng vào `SCOPE_RULES` và `hooks.py`.

Quy tắc (ASM-039, ASM-042, ASM-043):
- Chỉ áp cho quyền đến từ vai trò NC Clinician / NC Department Head. Vai trò khác của cùng người dùng
  cấp quyền thì quyền đó giữ nguyên (G4).
- Ghi (sửa, tạo, xóa...): chỉ bản ghi thuộc khoa được gán; chưa gán khoa nào thì không ghi được gì (G5).
- Đọc: bản ghi thuộc khoa được gán, hoặc bản ghi "công khai" theo `public_read` (quy trình "Đã ban hành").
"""

from dataclasses import dataclass, field

import frappe
from frappe import _

from normcore.core import readonly

DEPARTMENT = "NC Department"
SCOPED_ROLES = frozenset({"NC Clinician", "NC Department Head"})
# User Permission của khoa gán với applicable_for này: bộ lọc mặc định của Frappe (lọc đọc mọi DocType có
# Link tới NC Department, kể cả NC Department) không kích hoạt; phạm vi do hook ở đây quyết định.
UP_APPLICABLE_FOR = "NC Cost Center"
READ_TYPES = frozenset({"read", "select", "print", "email", "export", "report", "share"})


@dataclass(frozen=True)
class ScopeRule:
	department_field: str = "department"
	# {trường: giá trị}: bản ghi khớp thì mọi người có quyền đọc theo vai trò đều đọc được, kể cả khoa khác
	public_read: dict = field(default_factory=dict)


SCOPE_RULES = {
	"NC Clinical Procedure": ScopeRule(public_read={"workflow_state": "Đã ban hành"}),
	"NC Norm Set": ScopeRule(),
	"NC Test System": ScopeRule(),  # FR-ACC-008, ASM-113
}


def get_user_departments(user=None):
	"""Tập mã khoa được gán cho người dùng (đọc thẳng CSDL: có hiệu lực ngay ở yêu cầu kế tiếp, FR-ACC-006)."""
	user = user or frappe.session.user
	return set(frappe.get_all("User Permission", {"user": user, "allow": DEPARTMENT}, pluck="for_value"))


def _is_scoped(doctype, ptype, user):
	"""True nếu quyền `ptype` của người dùng trên DocType chỉ đến từ NC Clinician / NC Department Head."""
	if user == "Administrator":
		return False
	roles = set(frappe.get_roles(user))
	if not roles & SCOPED_ROLES:
		return False
	key = "read" if ptype in READ_TYPES or not ptype else ptype
	for perm in frappe.get_meta(doctype).get("permissions") or []:
		if perm.role in roles and perm.role not in SCOPED_ROLES and not perm.permlevel and perm.get(key):
			return False  # vai trò khác cấp quyền: không hẹp lại (G4)
	return True


def has_permission(doc, ptype=None, user=None, debug=False):
	"""Hook `has_permission`: chỉ từ chối, không bao giờ cấp thêm."""
	rule = SCOPE_RULES.get(doc.doctype)
	user = user or frappe.session.user
	if not rule or not _is_scoped(doc.doctype, ptype, user):
		return None
	depts = get_user_departments(user)
	if not ptype or ptype in READ_TYPES:
		if doc.get(rule.department_field) in depts:
			return None
		if rule.public_read and all(doc.get(k) == v for k, v in rule.public_read.items()):
			return None
		return False
	if doc.get(rule.department_field) not in depts:
		return False
	if not doc.is_new():  # không chuyển bản ghi của khoa khác sang khoa mình bằng cách đổi trường khoa
		stored = frappe.db.get_value(doc.doctype, doc.name, rule.department_field)
		if stored and stored not in depts:
			return False
	return None


def permission_query_conditions(user=None, doctype=None):
	"""Hook `permission_query_conditions`: điều kiện SQL cho `frappe.get_list` / báo cáo."""
	rule = SCOPE_RULES.get(doctype)
	user = user or frappe.session.user
	if not rule or not _is_scoped(doctype, "read", user):
		return ""
	table = f"`tab{doctype}`"
	conds = []
	depts = sorted(get_user_departments(user))
	if depts:
		in_list = ", ".join(frappe.db.escape(d) for d in depts)
		conds.append(f"{table}.`{rule.department_field}` in ({in_list})")
	for key, value in rule.public_read.items():
		conds.append(f"{table}.`{key}` = {frappe.db.escape(value)}")
	return "(" + " or ".join(conds) + ")" if conds else "1=0"


def assert_can_assign(user=None):
	"""Chỉ NC Admin (hoặc Administrator) gán / bỏ gán khoa (FR-ACC-006, G3)."""
	user = user or frappe.session.user
	if user != "Administrator" and "NC Admin" not in frappe.get_roles(user):
		frappe.throw(_("Chỉ NC Admin được gán hoặc bỏ gán khoa cho người dùng"), frappe.PermissionError)


def assign_department(user, department):
	assert_can_assign()
	for label, doctype, value in (("Người dùng", "User", user), ("Khoa", DEPARTMENT, department)):
		if not value or not frappe.db.exists(doctype, value):
			frappe.throw(_("{0} {1} không tồn tại").format(_(label), value or ""))
	if department in get_user_departments(user):
		return False
	frappe.get_doc(
		{
			"doctype": "User Permission",
			"user": user,
			"allow": DEPARTMENT,
			"for_value": department,
			"apply_to_all_doctypes": 0,
			"applicable_for": UP_APPLICABLE_FOR,
		}
	).insert(ignore_permissions=True)
	return True


def unassign_department(user, department):
	assert_can_assign()
	names = frappe.get_all(
		"User Permission", {"user": user, "allow": DEPARTMENT, "for_value": department}, pluck="name"
	)
	for name in names:
		frappe.delete_doc("User Permission", name, ignore_permissions=True)
	return bool(names)


def readable_departments(doctype, user=None):
	"""Tập khoa người dùng đọc được trên DocType; None nếu quyền đọc không bị hẹp theo khoa (FEAT-005)."""
	user = user or frappe.session.user
	if doctype not in SCOPE_RULES or not _is_scoped(doctype, "read", user):
		return None
	return get_user_departments(user)


def nc_doctypes():
	"""Mọi DocType cha tên `NC ` (đọc CSDL, không liệt kê cứng: tự gồm DocType FEAT sau thêm)."""
	return frappe.get_all("DocType", {"name": ["like", "NC %"], "istable": 0}, pluck="name", order_by="name")


def read_only_violations(role=readonly.READ_ONLY_ROLE):
	"""Quét quyền hiệu lực (DocPerm, Custom DocPerm, Workflow) của `role`; rỗng = chỉ đọc (FR-ACC-007).

	Vận hành: `bench --site <site> execute normcore.core.permissions.read_only_violations`.
	"""
	doctypes = nc_doctypes()
	out = []
	for dt in doctypes:
		perms = [p.as_dict() for p in frappe.get_meta(dt).get("permissions") or []]
		out.extend(readonly.perm_violations(dt, perms, role))
	names = frappe.get_all("Workflow", {"document_type": ["in", doctypes]}, pluck="name") if doctypes else []
	workflows = []
	for name in names:
		wf = frappe.get_doc("Workflow", name)
		workflows.append(
			{
				"name": wf.name,
				"document_type": wf.document_type,
				"transitions": [
					{"state": t.state, "action": t.action, "allowed": t.allowed} for t in wf.transitions
				],
				"states": [{"state": s.state, "allow_edit": s.allow_edit} for s in wf.states],
			}
		)
	out.extend(readonly.workflow_violations(workflows, role))
	return out
