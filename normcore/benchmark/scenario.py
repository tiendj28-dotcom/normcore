"""Kịch bản điều chỉnh giá (FEAT-029; FR-ADJ-006, FR-ADJ-009): logic thuần, không phụ thuộc frappe.

Không có công thức mới (ASM-029-03..05): kịch bản đổi đầu vào của ảnh chụp lần tính gốc
(`dataclasses.replace`) rồi tính lại bằng `snapshot.recompute`, đúng đường tính của lần tính
(như `costing/sensitivity.py`). Đơn giá giờ máy mới dùng `resources.machine_hourly_rate` (BR-COST-004).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation

from normcore.costing import resources, snapshot

PARAM, EQUIPMENT, NORM_LINE = CHANGE_TYPES = ("Tham số", "Thiết bị", "Dòng định mức")
FIELDS = {
	PARAM: ("accumulation_rate",),
	EQUIPMENT: ("utilization_rate",),
	NORM_LINE: ("hospital_qty", "wastage_rate"),
}
SCENARIO_SOURCE = " · kịch bản"
PROCEDURE = object()  # gợi ý cần yêu cầu sửa quy trình (FR-ADJ-007)

_RULE_TO_CHANGE = {
	"BR-ADJ-001": (EQUIPMENT, "utilization_rate"),
	"BR-ADJ-002": (NORM_LINE, "hospital_qty"),
	"BR-ADJ-004": (NORM_LINE, "wastage_rate"),
	"BR-ADJ-005": (PARAM, "accumulation_rate"),
}
_NO_VALUE = ("BR-ADJ-006", "BR-ADJ-007")


class InvalidChange(ValueError):
	"""Thay đổi không áp được; thông báo tiếng Việt."""


@dataclass(frozen=True)
class Change:
	change_type: str
	target_ref: str
	field: str
	new_value: Decimal
	old_value: Decimal | None = None
	service: str | None = None
	department: str | None = None

	@property
	def key(self) -> tuple:
		return (self.change_type, self.target_ref, self.field, self.service, self.department)


def parse_value(text) -> Decimal:
	"""`"0,5"`, `"15 phút"`, `"5%"` -> Decimal (bỏ hậu tố đơn vị, dấu phẩy thành dấu chấm)."""
	msg = "Giá trị gợi ý không đọc được"
	if text is None:
		raise InvalidChange(msg)
	s = str(text).strip()
	for suffix in ("phút", "%"):
		if s.endswith(suffix):
			s = s[: -len(suffix)].strip()
	try:
		d = Decimal(s.replace(",", "."))
	except InvalidOperation:
		raise InvalidChange(msg) from None
	if not d.is_finite():
		raise InvalidChange(msg)
	return d


def change_for(rule_code, target_ref, current, suggested, service, department):
	"""Gợi ý -> `Change`, `PROCEDURE` (cần sửa quy trình) hoặc None (không có giá trị để áp)."""
	if rule_code == "BR-ADJ-003":
		return PROCEDURE
	if rule_code in _NO_VALUE:
		return None
	if rule_code not in _RULE_TO_CHANGE:
		raise InvalidChange(f"Quy tắc {rule_code} không có trong danh sách")
	ctype, field = _RULE_TO_CHANGE[rule_code]
	scoped = ctype == NORM_LINE
	try:
		old = parse_value(current)
	except InvalidChange:
		old = None
	return Change(
		ctype,
		str(target_ref),
		field,
		parse_value(suggested),
		old,
		service if scoped else None,
		department if scoped else None,
	)


def merge(changes, new: Change) -> list:
	"""Cùng khóa: thay `new_value`, giữ `old_value` của dòng đầu (ASM-029-04); khác khóa: nối cuối."""
	out, found = [], False
	for c in changes:
		if c.key == new.key:
			out.append(replace(c, new_value=new.new_value))
			found = True
		else:
			out.append(c)
	if not found:
		out.append(new)
	return out


def _check(c: Change):
	if c.change_type not in FIELDS or c.field not in FIELDS[c.change_type]:
		raise InvalidChange(f"Thay đổi {c.change_type} · {c.field} không hợp lệ")


def _apply_param(snap, c):
	params = snapshot.from_plain(snap["params"])
	snap["params"] = snapshot.to_plain(replace(params, accumulation_rate=c.new_value / 100))


def _apply_equipment(snap, c, equipment):
	facts = equipment.get(c.target_ref)
	if not facts or not facts.get("annual_cost") or not facts.get("planned_hours"):
		raise InvalidChange(f"Thiếu chi phí năm hoặc giờ kế hoạch của thiết bị {c.target_ref}")
	try:
		rate = resources.machine_hourly_rate(facts["annual_cost"], facts["planned_hours"], c.new_value)
	except ValueError as e:
		raise InvalidChange(str(e)) from None
	inputs = []
	for plain in snap["inputs"]:
		inp = snapshot.from_plain(plain)
		rates = dict(inp.rates)
		for ln in inp.lines:
			old = rates.get(ln.line_id)
			if ln.component == "EQUIPMENT" and ln.resource == c.target_ref and not ln.excluded and old is not None:
				rates[ln.line_id] = replace(old, rate=rate, source=old.source + SCENARIO_SOURCE)
		inputs.append(snapshot.to_plain(replace(inp, rates=rates)))
	snap["inputs"] = inputs


def _apply_norm_line(snap, c):
	missing = f"{c.target_ref} không có trong lần tính này"
	inputs, done = [], False
	for plain in snap["inputs"]:
		inp = snapshot.from_plain(plain)
		if (inp.service, inp.department) == (c.service, c.department):
			lines = []
			for ln in inp.lines:
				if ln.line_id == c.target_ref:
					done = True
					value = c.new_value if c.field == "hospital_qty" else c.new_value / 100
					ln = replace(ln, **{c.field: value})
				lines.append(ln)
			inp = replace(inp, lines=tuple(lines))
			plain = snapshot.to_plain(inp)
		inputs.append(plain)
	if not done:
		raise InvalidChange(missing)
	snap["inputs"] = inputs


def apply(snap: dict, changes, equipment) -> dict:
	"""Bản sao ảnh chụp với các thay đổi; không sửa `snap`."""
	out = copy.deepcopy(snap)
	for c in changes:
		_check(c)
		if c.change_type == PARAM:
			_apply_param(out, c)
		elif c.change_type == EQUIPMENT:
			_apply_equipment(out, c, equipment)
		else:
			_apply_norm_line(out, c)
	return out


def recompute(snap: dict, changes, equipment) -> snapshot.Recomputed:
	return snapshot.recompute(apply(snap, changes, equipment))


def proposal_text(rule_code, target_ref, current, suggested, text, note=None) -> str:
	out = (
		f"Quy tắc {rule_code}: {text}\nHiện tại: {current} → Đề xuất: {suggested}\n"
		"Lý do: giá tính toán vượt ngưỡng lệch so với đơn vị tham chiếu"
	)
	return out + (f"\nGhi chú: {note}" if note else "")
