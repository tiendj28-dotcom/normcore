"""Báo cáo thiếu dữ liệu của một phạm vi tính giá (FEAT-037; FR-OUT-012, UC-024). Hàm thuần Python."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import Decimal

PRICE, VOLUME, TIME_STUDY, QC_PLAN, COMPLIANCE = (
	"Thiếu đơn giá",
	"Thiếu sản lượng",
	"Thiếu bấm giờ",
	"Thiếu kế hoạch chất lượng",
	"Thiếu hồ sơ tuân thủ",
)
KINDS = (PRICE, VOLUME, TIME_STUDY, QC_PLAN, COMPLIANCE)
TIMED = "Bấm giờ"


@dataclass(frozen=True)
class PairData:
	service: str
	department: str
	input: object | None = None  # engine.ServiceInput
	norm_lines_basis: dict = field(default_factory=dict)  # line_id -> basis (dòng LABOR)
	has_time_study: bool = True
	systems_without_plan: tuple = ()
	systems_without_volume: tuple = ()
	missing_compliance: tuple = ()  # (thiết bị, loại)
	imaging: bool = False
	scenario: str = ""


@dataclass(frozen=True)
class Gap:
	service: str
	department: str
	kind: str
	detail: str


def _price_gaps(inp) -> list[str]:
	out = []
	for x in inp.lines:
		if not x.excluded and inp.rates.get(x.line_id) is None and x.component != "EQUIPMENT":
			out.append(f"{x.line_id} · {x.resource_label or x.resource}")
	c = inp.paraclinical
	if c is not None:
		for s in c.systems:
			if not s.norm_set:
				continue
			for x in s.lines:
				n = x.norm
				if not n.excluded and n.component != "EQUIPMENT" and s.rates.get(n.line_id) is None:
					out.append(f"{s.code} · {n.line_id} · {n.resource_label or n.resource}")
			out += [f"{s.code} · nội kiểm {i.item}" for i in s.iqc if i.rate is None]
	return out


def _volume_gaps(p: PairData) -> list[str]:
	inp = p.input
	if inp is not None and inp.paraclinical is None:
		if inp.volume is None or Decimal(inp.volume) <= 0:
			return [f"Kịch bản {p.scenario}" if p.scenario else "Sản lượng năm"]
		return []
	return [f"Hệ thống {s}" for s in p.systems_without_volume]


def collect(pairs: Sequence[PairData]) -> list[Gap]:
	"""Mọi chỗ thiếu của các cặp (dịch vụ, khoa), sắp theo dịch vụ, khoa, loại."""
	gaps: list[Gap] = []
	for p in pairs:
		if p.input is not None:
			gaps += [Gap(p.service, p.department, PRICE, d) for d in _price_gaps(p.input)]
		gaps += [Gap(p.service, p.department, VOLUME, d) for d in _volume_gaps(p)]
		if not p.has_time_study:
			timed = sorted(lid for lid, b in p.norm_lines_basis.items() if b == TIMED)
			if timed:
				gaps.append(Gap(p.service, p.department, TIME_STUDY, "Dòng " + ", ".join(timed)))
		if not p.imaging:
			gaps += [Gap(p.service, p.department, QC_PLAN, f"Hệ thống {s}") for s in p.systems_without_plan]
		gaps += [Gap(p.service, p.department, COMPLIANCE, f"{e} · {t}") for e, t in p.missing_compliance]
	order = {k: i for i, k in enumerate(KINDS)}
	return sorted(gaps, key=lambda g: (g.service, g.department, order[g.kind], g.detail))
