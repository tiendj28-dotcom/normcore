"""Luồng duyệt ba cấp (FR-WF-001..008, FR-WF-013, ADR-011). Thuần Python, không phụ thuộc frappe.

`TRANSITIONS` là dữ liệu; fixture Workflow phải khớp (có test).
"""

DRAFT = "Nháp"
WAIT_HEAD = "Chờ trưởng khoa duyệt"
WAIT_COUNCIL = "Chờ hội đồng thẩm định"
WAIT_PUBLISH = "Chờ ban hành"
PUBLISHED = "Đã ban hành"
SUPERSEDED = "Đã thay thế"
WITHDRAWN = "Đã thu hồi"

PENDING_STATES = (WAIT_HEAD, WAIT_COUNCIL, WAIT_PUBLISH)
CLOSED_STATES = (PUBLISHED, SUPERSEDED, WITHDRAWN)

# (từ, hành động, đến, vai trò được làm)
TRANSITIONS = (
	(DRAFT, "Gửi duyệt", WAIT_HEAD, "NC Clinician"),
	(WAIT_HEAD, "Đồng ý", WAIT_COUNCIL, "NC Department Head"),
	(WAIT_HEAD, "Từ chối", DRAFT, "NC Department Head"),
	(WAIT_COUNCIL, "Thông qua", WAIT_PUBLISH, "NC Council Member"),
	(WAIT_COUNCIL, "Từ chối", DRAFT, "NC Council Member"),
	(WAIT_PUBLISH, "Ban hành", PUBLISHED, "NC Director"),
	(WAIT_PUBLISH, "Từ chối", DRAFT, "NC Director"),
)

# Thu hồi không nằm trong TRANSITIONS/fixture Workflow (ASM-008-02); đi đường hệ thống như "Đã thay thế"
WITHDRAW = (PUBLISHED, "Thu hồi", WITHDRAWN, "NC Director")
ACTIONS = (*TRANSITIONS, WITHDRAW)

_LEVELS = {WAIT_HEAD: "trưởng khoa", WAIT_COUNCIL: "hội đồng", WAIT_PUBLISH: "giám đốc"}


def next_state(state, action):
	for src, act, dst, _role in ACTIONS:
		if src == state and act == action:
			return dst
	raise ValueError(f"Hành động '{action}' không áp dụng ở trạng thái '{state}'")


def reject_level(state):
	return _LEVELS[state]


def _current(published, service, department, today):
	"""Bản đang hiệu lực của (dịch vụ, khoa): effective_date <= today lớn nhất, bằng nhau thì version_no lớn."""
	cands = [
		r
		for r in published
		if r["technical_service"] == service
		and r["department"] == department
		and r.get("effective_date")
		and r["effective_date"] <= today
	]
	if not cands:
		return None
	return max(cands, key=lambda r: (r["effective_date"], r["version_no"]))


def to_supersede(published, today):
	"""Tên các bản "Đã ban hành" phải chuyển "Đã thay thế" tại ngày `today` (FR-WF-006)."""
	out = []
	for key in {(r["technical_service"], r["department"]) for r in published}:
		cur = _current(published, key[0], key[1], today)
		if cur is None:
			continue
		out += [
			r["name"]
			for r in published
			if (r["technical_service"], r["department"]) == key and r["version_no"] < cur["version_no"]
		]
	return sorted(out)


def effective_procedure(published, service, department, on_date):
	"""Tên quy trình đang hiệu lực cho FEAT-012; None nếu chưa có."""
	cur = _current(published, service, department, on_date)
	return cur["name"] if cur else None


def overdue(pending, today, days):
	"""Các mục chờ duyệt quá hạn: (today - entered_on).days >= days (FR-WF-013)."""
	return [p for p in pending if (today - p["entered_on"]).days >= days]
