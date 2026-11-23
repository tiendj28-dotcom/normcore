"""Số liệu kế toán (FEAT-016; FR-ACCT-001..006, 009; BR-COST-008; ADR-013).

Module thuần Python: không phụ thuộc framework. Dòng là dict với các khóa `account_code`, `account_name`,
`cost_center`, `amount`, `cost_category`, `is_excluded`, `change_reason`, `changed_by`.
"""

from __future__ import annotations

from decimal import Decimal

COST_CATEGORIES = ("LABOR", "DRUG_SUPPLY", "DEPRECIATION", "UTILITY", "MANAGEMENT", "EXCLUDED")
ALLOCATABLE = COST_CATEGORIES[:-1]
EXCLUDED = "EXCLUDED"
REGIMES = ("Hành chính sự nghiệp", "Doanh nghiệp")
DEFAULT_REGIME = REGIMES[0]
STATUS_DRAFT = "Nháp"
STATUS_FINAL = "Đã chốt"
SOURCE_FIELDS = ("account_code", "account_name", "cost_center", "amount")
ASSUMPTION_NOTE = "Giả định — chờ xác nhận (TBD-03)"


# ASM-118: bảng ánh xạ mặc định chế độ Hành chính sự nghiệp (TBD-03). (tiền tố, loại chi phí)
DEFAULT_ACCOUNT_MAPPING = (
	("61111", "LABOR"),
	("61112", "DRUG_SUPPLY"),
	("611122", "UTILITY"),
	("61113", "DEPRECIATION"),
	("61118", "MANAGEMENT"),
	("61121", "LABOR"),
	("61122", "DRUG_SUPPLY"),
	("611222", "UTILITY"),
	("61123", "DEPRECIATION"),
	("61128", "MANAGEMENT"),
	("642", "MANAGEMENT"),
	("811", "EXCLUDED"),
	("821", "EXCLUDED"),
)


def normalize_account(code) -> str:
	"""ASM-120: chuỗi, `61111.0` → `61111`, bỏ khoảng trắng và dấu chấm, chữ in hoa."""
	if code is None:
		return ""
	if isinstance(code, float) and code == int(code):
		code = int(code)
	s = str(code).strip()
	if s.endswith(".0") and s[:-2].isdigit():
		s = s[:-2]
	return "".join(s.split()).replace(".", "").upper()


def match_category(account_code, mappings) -> str | None:
	"""Tiền tố dài nhất của mã tài khoản trong `mappings` {tiền tố: loại}; không khớp → None."""
	code = normalize_account(account_code)
	best = None
	for prefix in mappings:
		p = normalize_account(prefix)
		if p and code.startswith(p) and (best is None or len(p) > len(best)):
			best = prefix
	return mappings[best] if best is not None else None


def assign_categories(lines, mappings, keep_manual=False) -> int:
	"""Gán `cost_category`, `is_excluded` theo ánh xạ. Trả số dòng đổi."""
	norm = {normalize_account(k): v for k, v in mappings.items()}
	changed = 0
	for ln in lines:
		if keep_manual and ln.get("changed_by"):
			continue
		cat = match_category(ln.get("account_code"), norm)
		excluded = 1 if cat == EXCLUDED else 0
		if (ln.get("cost_category") or None) != cat or int(ln.get("is_excluded") or 0) != excluded:
			changed += 1
		ln["cost_category"] = cat
		ln["is_excluded"] = excluded
	return changed


def _dec(v) -> Decimal:
	return Decimal(str(v if v is not None else 0))


def _excluded(ln) -> bool:
	return bool(ln.get("is_excluded")) or ln.get("cost_category") == EXCLUDED


def check_line_changes(before, after) -> list[str]:
	"""Lỗi khi sửa dòng của lần nhập "Nháp" (FR-ACCT-004, ASM-122). Ghép dòng theo vị trí."""
	if len(before) != len(after):
		return ["Dòng chỉ thay đổi bằng cách đọc lại tệp"]
	errors = []
	for i, (b, a) in enumerate(zip(before, after, strict=True), start=1):
		if any(
			(_dec(b.get(f)) != _dec(a.get(f)))
			if f == "amount"
			else ((b.get(f) or "") != (a.get(f) or ""))
			for f in SOURCE_FIELDS
		):
			errors.append(f"Dòng {i}: dòng chỉ thay đổi bằng cách đọc lại tệp")
			continue
		b_cat, a_cat = b.get("cost_category") or None, a.get("cost_category") or None
		b_ex, a_ex = int(bool(b.get("is_excluded"))), int(bool(a.get("is_excluded")))
		if a_cat == EXCLUDED and a_cat != b_cat:
			a_ex = 1
		if a_cat == EXCLUDED and not a_ex:
			errors.append(f"Dòng {i}: loại EXCLUDED phải đi cùng loại trừ, chọn loại chi phí khác")
			continue
		if a_cat == b_cat and a_ex == b_ex:
			continue
		reason = (a.get("change_reason") or "").strip()
		if not reason or reason == (b.get("change_reason") or "").strip():
			errors.append(f"Dòng {i}: nhập lý do khi đổi loại chi phí hoặc loại trừ")
	return errors


def unassigned(lines) -> list[dict]:
	"""Dòng không loại trừ mà chưa có loại chi phí (kèm `idx` từ 1)."""
	out = []
	for i, ln in enumerate(lines, start=1):
		if not _excluded(ln) and not ln.get("cost_category"):
			out.append({**ln, "idx": i})
	return out


def finalize_blockers(status, error_count, lines) -> list[str]:
	"""Lý do không chốt được (rỗng = chốt được). FR-ACCT-002, 005."""
	out = []
	if status != STATUS_DRAFT:
		return ["Lần nhập không ở trạng thái Nháp"]
	if error_count and error_count > 0:
		out.append(f"còn {error_count} dòng lỗi khi đọc tệp")
	if not lines:
		out.append("không có dòng nào")
	un = unassigned(lines)
	if un:
		detail = ", ".join(f"dòng {u['idx']} (tài khoản {u.get('account_code')}, trung tâm {u.get('cost_center')})" for u in un)
		out.append(f"{len(un)} dòng chưa có loại chi phí: {detail}")
	return out


def totals(lines) -> list[tuple]:
	"""Tổng theo (trung tâm, loại) bỏ dòng loại trừ; sắp theo trung tâm rồi thứ tự ALLOCATABLE."""
	acc: dict[tuple, Decimal] = {}
	for ln in lines:
		if _excluded(ln) or not ln.get("cost_category"):
			continue
		k = (ln["cost_center"], ln["cost_category"])
		acc[k] = acc.get(k, Decimal(0)) + _dec(ln.get("amount"))
	return [(c, cat, v) for (c, cat), v in sorted(acc.items(), key=lambda kv: (kv[0][0], ALLOCATABLE.index(kv[0][1])))]


def total_amount(lines) -> Decimal:
	"""Tổng mọi dòng (kể cả loại trừ, ASM-123)."""
	return sum((_dec(ln.get("amount")) for ln in lines), Decimal(0))
