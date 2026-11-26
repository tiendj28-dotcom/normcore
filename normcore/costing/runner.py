"""Điều phối lần tính giá: phạm vi, đủ điều kiện, ngưỡng chạy nền, vòng tính. Hàm thuần Python (ADR-003).

FR-COST-002, FR-COST-006, FR-COST-015, NFR-REL-002 (tất định: sắp theo dịch vụ, khoa).
"""

from collections.abc import Callable, Mapping

from normcore.costing import engine

BACKGROUND_THRESHOLD = 50


def scope_pairs(services, scope_services=(), scope_departments=()) -> list[tuple[str, str]]:
	"""`services`: dãy (dịch vụ, khoa) có trong hệ thống. Phạm vi trống = toàn viện (ASM-015-03)."""
	ss, sd = set(scope_services or ()), set(scope_departments or ())
	return sorted({(s, d) for s, d in services if (not ss or s in ss) and (not sd or d in sd)})


def eligibility(pairs, locked_norm_sets: Mapping, scope_services=(), scope_departments=()):
	"""Trả (đủ điều kiện, chưa đủ). `locked_norm_sets`: {(dịch vụ, khoa): tên bộ định mức "Đã khóa"}.
	Dịch vụ nằm trong phạm vi mà chưa có cặp nào cũng bị liệt kê, với khoa rỗng (FR-COST-002)."""
	ss, sd = set(scope_services or ()), set(scope_departments or ())
	pairs = sorted(set(pairs))
	eligible, ineligible = [], []
	for service, dept in pairs:
		ns = locked_norm_sets.get((service, dept))
		if ns:
			eligible.append({"service": service, "department": dept, "norm_set": ns})
		else:
			ineligible.append((service, dept))
	seen = {s for s, _ in pairs}
	for s in sorted(ss - seen):
		if not sd:
			ineligible.append((s, ""))
	return eligible, ineligible


def needs_background(n_eligible: int) -> bool:
	return n_eligible > BACKGROUND_THRESHOLD


def run(
	eligible,
	load: Callable[[dict], engine.ServiceInput],
	params: engine.PricingParams,
	progress: Callable[[int, int], None] | None = None,
	extension=None,
	allocate: Callable[[list], Mapping] | None = None,
) -> list[engine.ServiceResult]:
	"""Tính từng cặp đủ điều kiện rồi phân bổ (điểm cắm của FEAT-017) và tính giá."""
	ordered = sorted(eligible, key=lambda e: (e["service"], e["department"]))
	n = len(ordered)
	costed = []
	for i, e in enumerate(ordered, 1):
		costed.append(engine.cost_service(load(e), params, extension))
		if progress is not None:
			progress(i, n)
	alloc = allocate(costed) if allocate is not None else {}
	return [engine.finish_service(r, alloc.get((r.service, r.department), []), params) for r in costed]
