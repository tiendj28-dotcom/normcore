"""Phương án giá (FEAT-030): logic thuần, không phụ thuộc framework.

FR-PRICE-001..010. Không có công thức tiền mới: giá đề xuất mặc định là `rounded_price` do bộ máy tính
(golden DV-TEST-A 302.100, DV-TEST-B 92.600); ở đây chỉ chép, so sánh và ghi giá.
Giả định ASM-030-01..16 (docs/decisions/assumptions/FEAT-030.md).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

DRAFT = "Nháp"
WAIT_DEPT = "Chờ khoa xác nhận"
WAIT_DIRECTOR = "Chờ phê duyệt"
APPROVED = "Đã duyệt"
WAIT_AUTHORITY = "Đã duyệt nội bộ, chờ trình"
AUTHORITY_APPROVED = "Đã được cấp thẩm quyền duyệt"
STATES = (DRAFT, WAIT_DEPT, WAIT_DIRECTOR, APPROVED, WAIT_AUTHORITY, AUTHORITY_APPROVED)
LOCKED_STATES = (APPROVED, WAIT_AUTHORITY, AUTHORITY_APPROVED)
PENDING_STATES = (WAIT_DEPT, WAIT_DIRECTOR)

ACT_SUBMIT = "Gửi duyệt"
ACT_CONFIRM = "Xác nhận"
ACT_APPROVE = "Phê duyệt"
ACT_REJECT = "Từ chối"
ACT_RECORD = "Ghi kết quả phê duyệt"

FINANCE, DEPT_HEAD, DIRECTOR = "NC Finance", "NC Department Head", "NC Director"
HOSPITAL = "Bệnh viện"
AUTHORITY = "Cơ quan có thẩm quyền"

# (từ, hành động, đến, vai) — data-model 5.3; điều kiện kiểm ở api/price_proposal.py
TRANSITIONS = (
	(DRAFT, ACT_SUBMIT, WAIT_DEPT, FINANCE),
	(WAIT_DEPT, ACT_CONFIRM, WAIT_DEPT, DEPT_HEAD),
	(WAIT_DEPT, ACT_CONFIRM, WAIT_DIRECTOR, DEPT_HEAD),
	(WAIT_DEPT, ACT_REJECT, DRAFT, DEPT_HEAD),
	(WAIT_DIRECTOR, ACT_APPROVE, APPROVED, DIRECTOR),
	(WAIT_DIRECTOR, ACT_APPROVE, WAIT_AUTHORITY, DIRECTOR),
	(WAIT_DIRECTOR, ACT_REJECT, DRAFT, DIRECTOR),
	(WAIT_AUTHORITY, ACT_RECORD, AUTHORITY_APPROVED, FINANCE),
)


def _dec(value) -> Decimal:
	return Decimal(str(value))


def _date(value):
	if isinstance(value, datetime):
		return value.date()
	if isinstance(value, date):
		return value
	return date.fromisoformat(str(value)[:10])


def is_below_cost(proposed, full_cost) -> bool:
	"""FR-PRICE-003: giá đề xuất thấp hơn giá thành toàn bộ."""
	if proposed is None or full_cost is None:
		return False
	return _dec(proposed) < _dec(full_cost)


def build_items(costs, bench) -> list[dict]:
	"""FR-PRICE-001: mỗi NC Service Cost không lỗi một dòng; giá đề xuất mặc định = giá làm tròn."""
	items = []
	for c in sorted(costs, key=lambda x: x["technical_service"]):
		if c.get("calc_status") == "Lỗi":
			continue
		median, count = bench.get(c["technical_service"], (None, 0))
		rounded = _dec(c["rounded_price"])
		full = _dec(c["full_cost"]) if c.get("full_cost") is not None else None
		items.append(
			{
				"technical_service": c["technical_service"],
				"department": c.get("department"),
				"full_cost": full,
				"calculated_price": _dec(c["calculated_price"]) if c.get("calculated_price") is not None else None,
				"rounded_price": rounded,
				"benchmark_median": median,
				"benchmark_count": count,
				"proposed_price": rounded,
				"below_cost": 1 if is_below_cost(rounded, full) else 0,
			}
		)
	return items


def needs_basis(item) -> bool:
	"""FR-PRICE-002: giá đề xuất khác giá làm tròn."""
	return _dec(item["proposed_price"]) != _dec(item["rounded_price"])


def submit_errors(items, approval_authority, apply_from) -> list[str]:
	"""FR-PRICE-002, ASM-030-04, 05: lỗi chặn "Gửi duyệt"."""
	if not items:
		return ["Phương án chưa có dòng nào"]
	errors = []
	for it in items:
		code = it["technical_service"]
		if it.get("proposed_price") is None or _dec(it["proposed_price"]) <= 0:
			errors.append(f"Dòng {code}: giá đề xuất phải lớn hơn 0")
			continue
		if needs_basis(it) and not (it.get("adjustment_basis") or "").strip():
			errors.append(f"Dòng {code}: giá đề xuất khác giá làm tròn, cần ghi căn cứ điều chỉnh")
	if approval_authority == HOSPITAL and not apply_from:
		errors.append("Loại giá do bệnh viện quyết định: cần nhập ngày áp dụng")
	return errors


def departments(items) -> list[str]:
	"""FR-PRICE-004: các khoa có dòng trong phương án, sắp theo tên."""
	return sorted({it["department"] for it in items if it.get("department")})


def confirm(confirmations, depts, user, now):
	"""FR-PRICE-004, 005: đặt xác nhận cho các khoa `depts` chưa xác nhận → (số dòng đặt, đã đủ khoa)."""
	wanted = set(depts)
	count = 0
	for row in confirmations:
		if row["department"] in wanted and not row.get("confirmed_by"):
			row["confirmed_by"] = user
			row["confirmed_on"] = now
			count += 1
	if not count:
		raise ValueError("Không có khoa nào cần xác nhận")
	return count, all(r.get("confirmed_by") for r in confirmations)


def approve_errors(items, acknowledged) -> list[str]:
	"""FR-PRICE-003: dòng dưới giá thành phải được Giám đốc xác nhận riêng."""
	ack = set(acknowledged or [])
	for it in items:
		if it.get("below_cost") and it.get("name") in ack:
			it["director_ack"] = 1
	return [
		f"Dòng {it['technical_service']}: giá đề xuất {_dec(it['proposed_price']):,.2f} thấp hơn giá thành toàn bộ "
		f"{_dec(it['full_cost']):,.2f}, Giám đốc cần xác nhận riêng dòng này"
		for it in items
		if it.get("below_cost") and not it.get("director_ack")
	]


def approved_state(approval_authority) -> str:
	"""FR-PRICE-006, 007: trạng thái sau phê duyệt theo cấp phê duyệt của loại giá."""
	if approval_authority == HOSPITAL:
		return APPROVED
	if approval_authority == AUTHORITY:
		return WAIT_AUTHORITY
	raise ValueError(f"Cấp phê duyệt chưa hợp lệ: {approval_authority!r}")


def history_rows(items, price_category, effective_date, proposal, authority_doc_no=None, use_authority=False):
	"""FR-PRICE-006, 008, 010: dòng NC Service Price History cho từng dịch vụ."""
	field = "authority_price" if use_authority else "proposed_price"
	return [
		{
			"technical_service": it["technical_service"],
			"price_category": price_category,
			"price": _dec(it[field]),
			"effective_date": effective_date,
			"price_proposal": proposal,
			"authority_doc_no": authority_doc_no if use_authority else None,
		}
		for it in items
	]


def history_conflicts(existing, new) -> list[dict]:
	"""ASM-030-09: dòng mới trùng (dịch vụ, loại giá, ngày áp dụng) với lịch sử đã có.

	`existing`: {dịch vụ: [dòng lịch sử]}. Trả dòng mới kèm `price_proposal` của dòng cũ.
	"""
	conflicts = []
	for row in new:
		for old in existing.get(row["technical_service"], []):
			if old["price_category"] == row["price_category"] and _date(old["effective_date"]) == _date(
				row["effective_date"]
			):
				conflicts.append({**row, "price_proposal": old.get("price_proposal")})
	return conflicts


def authority_errors(items, prices, doc_no, doc_date) -> list[str]:
	"""FR-PRICE-008: thiếu số/ngày văn bản hoặc giá được duyệt của dòng."""
	errors = []
	if not (doc_no or "").strip():
		errors.append("Cần nhập số văn bản phê duyệt")
	if not doc_date:
		errors.append("Cần nhập ngày văn bản phê duyệt")
	for it in items:
		raw = (prices or {}).get(it["name"])
		try:
			ok = raw is not None and _dec(raw) > 0
		except Exception:
			ok = False
		if not ok:
			errors.append(f"Dòng {it['technical_service']}: cần nhập giá được duyệt lớn hơn 0")
	return errors


def reset_for_draft(items, confirmations) -> list:
	"""FR-PRICE-009, ASM-030-08: bỏ xác nhận của Giám đốc và của khoa khi về "Nháp"."""
	for it in items:
		it["director_ack"] = 0
	return []
