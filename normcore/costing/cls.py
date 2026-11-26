"""Tính giá dịch vụ cận lâm sàng (FEAT-036) - hàm thuần Python, không phụ thuộc frappe (ADR-003, ADR-017).

Đối chiếu docs/golden/golden_cls.py: `k_factor`, `system_lines`, `service_direct`, `per_result`,
`compliance_annual`, `equipment_annual`, `part_per_result`, `power_per_result`, `low_volume`.
Làm tròn như golden: đơn giá r4, thành tiền một kết quả r2, k r6; phép chia trung gian không làm tròn.
BR-CLS-001..013, BR-CLS-016, BR-COST-004, FR-COST-017..025, FR-CLS-003, FR-CLS-004, FR-QC-004, FR-QC-006.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from normcore.costing import engine, resources

_ZERO = Decimal(0)
_Q0, _Q2, _Q4, _Q6 = Decimal("1"), Decimal("0.01"), Decimal("0.0001"), Decimal("0.000001")

# cấp phát sinh (cost_level)
RESULT, TUBE, BATCH, DAY, PERIOD = "RESULT", "TUBE", "BATCH", "DAY", "PERIOD"
LEVELS = (RESULT, TUBE, BATCH, DAY, PERIOD)
# nguồn của dòng (line_origin)
ORIGIN_NORM, ORIGIN_QC, ORIGIN_EQA, ORIGIN_EQUIP = "Định mức", "Kế hoạch chất lượng", "Ngoại kiểm", "Thiết bị"
SRC_ACTUAL, SRC_ESTIMATED = "Thực tế", "Ước tính từ kế hoạch"
ESTIMATED_LABEL = SRC_ESTIMATED
SHARE_FROM_RESULTS, SHARE_MANUAL = "Từ số kết quả trả", "Khai tay"
ALLOC_ASSET, ALLOC_DIRECT = "ASSET", "DIRECT"
ATTACH_SYSTEM, ATTACH_EQUIP = "SYSTEM", "EQUIP"
LIFE_RESULT, LIFE_HOUR = "Số kết quả", "Giờ chạy"
LOW_VOLUME_LABEL = "Sản lượng thấp"
EXPIRED_ZERO_NOTE = "Hết thời gian sử dụng: khấu hao = 0 (ZERO)"
EXPIRED_CONTINUE_NOTE = "Hết thời gian sử dụng: tiếp tục tính khấu hao (CONTINUE)"
_CATEGORY_COMPONENT = {"LABOR": "LABOR", "DRUG_SUPPLY": "DRUG", "DEPRECIATION": "EQUIPMENT", "UTILITY": "UTILITY"}


def _q(x, quantum) -> Decimal:
	return Decimal(x).quantize(quantum, rounding=ROUND_HALF_UP)


def r0(x) -> Decimal:
	return _q(x, _Q0)


def r2(x) -> Decimal:
	return _q(x, _Q2)


def r4(x) -> Decimal:
	return _q(x, _Q4)


def r6(x) -> Decimal:
	return _q(x, _Q6)


def vn(x, digits=2) -> str:
	"""Số kiểu Việt Nam: 1.234,56."""
	s = f"{Decimal(x):,.{digits}f}"
	return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# ---------------------------------------------------------------------------
# Dữ liệu đầu vào đã phân giải (đóng băng; loader dựng, cũng là nội dung ảnh chụp)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PowerInput:
	run_kw: Decimal
	run_h: Decimal
	standby_kw: Decimal
	standby_h: Decimal
	continuous: bool


@dataclass(frozen=True)
class ComponentInput:
	cost: Decimal
	life_basis: str  # "Tháng" | LIFE_RESULT | LIFE_HOUR
	life_value: Decimal
	vendor_paid: bool = False


@dataclass(frozen=True)
class RecordInput:
	cost_per_time: Decimal
	cycle_months: Decimal
	valid: bool  # còn hạn tại ngày tính giá


@dataclass(frozen=True)
class EquipmentInput:
	code: str
	department: str
	mode: str  # resources.BUY / RENT / VENDOR / JOINT
	basis: str  # resources.BASIS_*
	original_cost: Decimal | None = None
	life_years: Decimal | None = None
	in_service: date | None = None
	contract_cost: Decimal | None = None
	maintenance: Decimal = _ZERO
	maintenance_vendor_paid: bool = False
	components: tuple = ()
	dept_share: Decimal = Decimal(1)
	asset_value: Decimal | None = None
	power: PowerInput | None = None
	manual_calibration: Decimal = _ZERO
	records: tuple = ()
	planned_hours: Decimal | None = None
	utilization: Decimal | None = None
	qtb: Decimal | None = None
	mtb: Decimal | None = None
	compliance_required: bool = False


@dataclass(frozen=True)
class ClsNormLine:
	norm: engine.NormLine
	cost_level: str
	apply_k: bool = False
	attach: str = ""  # ATTACH_SYSTEM | ATTACH_EQUIP | ""
	attach_equipment: str = ""
	is_main_reagent: bool = False
	nominal_tests: Decimal | None = None
	open_days: Decimal | None = None


@dataclass(frozen=True)
class IqcLine:
	item: str
	levels: Decimal
	runs_per_day: Decimal
	qty_per_run: Decimal
	shared_params: Decimal
	rate: engine.LineRate | None = None


@dataclass(frozen=True)
class CalLine:
	points: Decimal
	replicates: Decimal
	per_year: Decimal
	cost_per_calibration: Decimal


@dataclass(frozen=True)
class AuxCounts:
	"""Số test phụ thực tế; None = không có số thực tế (FR-QC-006)."""

	qnk: Decimal | None = None
	qcal: Decimal | None = None
	qrerun: Decimal | None = None
	qeqa: Decimal | None = None
	h: Decimal | None = None


@dataclass(frozen=True)
class TestSystemInput:
	__test__ = False
	code: str
	norm_set: str | None
	equipment: str
	qbn: Decimal | None = None
	has_volume: bool = True
	actual: AuxCounts = AuxCounts()
	est_rerun_rate: Decimal = _ZERO
	est_h: Decimal = _ZERO
	est_qnk: Decimal = _ZERO  # từ kế hoạch chất lượng (qc_plans.estimated_tests)
	est_qcal: Decimal = _ZERO
	eqa_tests_est: Decimal = _ZERO
	run_days: Decimal | None = None
	plan_run_days: Decimal | None = None
	batch: Decimal | None = None
	tests_per_tube: Decimal | None = None
	manual_share_pct: Decimal | None = None
	minutes_per_case: Decimal | None = None
	lines: tuple = ()
	rates: Mapping = field(default_factory=dict)
	iqc: tuple = ()
	cal: tuple = ()


@dataclass(frozen=True)
class EqaInput:
	program: str
	fee: Decimal
	shipping: Decimal
	share: Decimal  # phân số từ qc_plans.eqa_shares


@dataclass(frozen=True)
class ClsServiceInput:
	scenario: str
	fiscal_year: int | str
	systems: tuple
	equipment: Mapping
	eqa: tuple = ()
	allocation_mode: str = ALLOC_ASSET
	expired_mode: str | None = resources.ZERO
	on: date | None = None
	include_depr: bool = True
	electricity_price: Decimal = _ZERO
	imaging: bool = False
	eqa_category: str | None = None
	rental_category: str | None = None
	jv_category: str | None = None


@dataclass(frozen=True)
class TestSystemCost:
	__test__ = False
	test_system: str
	norm_set: str | None
	patient_results: Decimal
	share_pct: Decimal
	q_iqc: Decimal
	q_calibration: Decimal
	q_rerun: Decimal
	q_eqa: Decimal
	wastage_rate: Decimal  # phần trăm (3 = 3%)
	k_factor: Decimal
	k_estimated: bool
	direct_cost: Decimal
	low_volume_warning: bool
	share_source: str = SHARE_FROM_RESULTS
	total_tests: Decimal = _ZERO
	equipment: str = ""


# ---------------------------------------------------------------------------
# BR-CLS-001: hệ số k
# ---------------------------------------------------------------------------


def aux_counts(sys: TestSystemInput, imaging: bool = False):
	"""(qnk, qcal, qrerun, qeqa, h, estimated). Ô có số thực tế dùng số đó; ô None suy từ kế hoạch."""
	a = sys.actual
	qbn = Decimal(sys.qbn)
	estimated = False

	def pick(actual, est):
		nonlocal estimated
		if actual is None:
			estimated = True
			return est
		return Decimal(actual)

	qrerun = pick(a.qrerun, r0(Decimal(sys.est_rerun_rate) * qbn))
	if imaging:  # BR-CLS-001: chẩn đoán hình ảnh k = 1 + Qlai / Qbn
		return _ZERO, _ZERO, qrerun, _ZERO, _ZERO, estimated
	qnk = pick(a.qnk, Decimal(sys.est_qnk))
	qcal = pick(a.qcal, Decimal(sys.est_qcal))
	qeqa = pick(a.qeqa, Decimal(sys.eqa_tests_est))
	h = pick(a.h, Decimal(sys.est_h))
	return qnk, qcal, qrerun, qeqa, h, estimated


def k_factor(qbn, qnk, qcal, qrerun, qeqa, h):
	"""BR-CLS-001: k = r6(tổng test / ((1 - h) x Qbn)). Trả (k, tổng test)."""
	qbn, h = Decimal(qbn), Decimal(h)
	if qbn <= 0 or h >= 1:
		raise ValueError("Qbn phải lớn hơn 0 và hao hụt phải nhỏ hơn 100%")
	total = qbn + Decimal(qnk) + Decimal(qcal) + Decimal(qrerun) + Decimal(qeqa)
	return r6(total / ((1 - h) * qbn)), total


# ---------------------------------------------------------------------------
# Thiết bị: BR-CLS-009..012, BR-COST-004
# ---------------------------------------------------------------------------


def _own_compliance(eq: EquipmentInput):
	valid = [r for r in eq.records if r.valid]
	if not valid:
		return None
	return sum((Decimal(r.cost_per_time) * 12 / Decimal(r.cycle_months) for r in valid), _ZERO)


def compliance_annual(eq: EquipmentInput, peers, mode: str) -> Decimal:
	"""BR-CLS-011, FR-CMP-002..004. `peers`: thiết bị cùng khoa (gồm cả `eq`)."""
	own = _own_compliance(eq)
	if own is None:  # không có hồ sơ còn hạn: số nhập tay, tính như Gắn trực tiếp (ASM-036-11)
		return Decimal(eq.manual_calibration or 0)
	if mode == ALLOC_DIRECT or eq.asset_value is None:
		return own
	pool_eq = [p for p in peers if p.asset_value is not None and _own_compliance(p) is not None]
	pool = sum((_own_compliance(p) for p in pool_eq), _ZERO)
	return pool * Decimal(eq.asset_value) / sum((Decimal(p.asset_value) for p in pool_eq), _ZERO)


def _peers(eq: EquipmentInput, inp: ClsServiceInput):
	return [e for e in inp.equipment.values() if e.department == eq.department]


def equipment_annual(eq: EquipmentInput, inp: ClsServiceInput):
	"""BR-CLS-009: chi phí thiết bị năm của khoa và các ghi chú hiển thị. Trả (annual, notes)."""
	machine = resources.machine_annual(
		eq.mode, eq.original_cost, eq.life_years, eq.in_service, eq.contract_cost,
		inp.on, inp.expired_mode, inp.include_depr,
	)
	calibration = compliance_annual(eq, _peers(eq, inp), inp.allocation_mode)
	comps = [(c.cost, c.life_basis, c.life_value, c.vendor_paid) for c in eq.components]
	annual = resources.equipment_annual(
		machine, eq.maintenance, calibration, comps, eq.mode, eq.maintenance_vendor_paid, eq.dept_share
	)
	notes = []
	if eq.mode == resources.BUY:
		if not inp.include_depr:
			notes.append(engine.DEPR_EXCLUDED_WARNING)
		elif inp.on is not None and eq.in_service is not None and resources.is_expired(
			eq.in_service, eq.life_years, inp.on
		):
			notes.append(EXPIRED_CONTINUE_NOTE if inp.expired_mode == resources.CONTINUE else EXPIRED_ZERO_NOTE)
	return annual, notes


def per_result(eq: EquipmentInput, annual: Decimal, m=None):
	"""Chia chi phí năm cho một kết quả theo tiêu chí chia. Trả (số tiền, tên mẫu số, giá trị mẫu số)."""
	if eq.basis == resources.BASIS_RESULT:
		if not eq.qtb or Decimal(eq.qtb) <= 0:
			raise ValueError(f"Thiết bị {eq.code} thiếu Qtb")
		return r2(Decimal(annual) / Decimal(eq.qtb)), "Qtb", Decimal(eq.qtb)
	if eq.basis == resources.BASIS_MINUTE:
		if not eq.mtb or Decimal(eq.mtb) <= 0:
			raise ValueError(f"Thiết bị {eq.code} thiếu phút khai thác (Mtb)")
		if m is None:
			raise ValueError("Thiếu số phút chiếm máy một ca")
		return r2(r4(Decimal(annual) / Decimal(eq.mtb)) * Decimal(m)), "Mtb", Decimal(eq.mtb)
	if eq.basis == resources.BASIS_HOURS:
		if m is None:
			raise ValueError("Thiếu số phút máy áp dụng")
		rate = resources.machine_hourly_rate(annual, eq.planned_hours, eq.utilization)
		return r2(Decimal(m) / 60 * rate), "Giờ kế hoạch × hệ số sử dụng", Decimal(eq.planned_hours) * Decimal(eq.utilization)
	raise ValueError(f"Tiêu chí chia không hợp lệ: {eq.basis}")


def part_per_result(eq: EquipmentInput, m=None) -> Decimal:
	"""BR-CLS-010: linh kiện tính theo số kết quả và giờ chạy (linh kiện theo tháng nằm trong thiết bị năm)."""
	out = _ZERO
	for p in eq.components:
		if eq.mode == resources.VENDOR and p.vendor_paid:
			continue
		if p.life_basis == LIFE_RESULT:
			out += r2(Decimal(p.cost) / Decimal(p.life_value))
		elif p.life_basis == LIFE_HOUR:
			if m is None:
				raise ValueError(f"Thiết bị {eq.code} có linh kiện tính theo giờ chạy mà thiếu phút chiếm máy một ca")
			out += r2(Decimal(p.cost) / Decimal(p.life_value) * Decimal(m) / 60)
	return out


def has_per_use_parts(eq: EquipmentInput) -> bool:
	return any(c.life_basis in (LIFE_RESULT, LIFE_HOUR) for c in eq.components)


def power_per_result(eq: EquipmentInput, run_days, price, m=None):
	"""BR-CLS-012: điện. Không khai công suất -> (0, '', 0)."""
	p = eq.power
	if p is None:
		return _ZERO, "", _ZERO
	day = (p.run_kw * p.run_h + p.standby_kw * p.standby_h) * Decimal(price)
	days = Decimal(365) if p.continuous else Decimal(run_days)
	return per_result(eq, day * days * Decimal(eq.dept_share), m)


# ---------------------------------------------------------------------------
# Dòng chi phí của một hệ thống
# ---------------------------------------------------------------------------


def _days(sys: TestSystemInput):
	return sys.run_days if sys.run_days is not None else sys.plan_run_days


def _equip_of(sys: TestSystemInput, code, inp: ClsServiceInput) -> EquipmentInput:
	return inp.equipment[code or sys.equipment]


def _category_for(eq: EquipmentInput, inp: ClsServiceInput):
	if eq.mode == resources.RENT:
		return inp.rental_category
	if eq.mode == resources.JOINT:
		return inp.jv_category
	return None


def _src(estimated: bool) -> str:
	return SRC_ESTIMATED if estimated else SRC_ACTUAL


def norm_line_cost(sys, line: ClsNormLine, k, rate: engine.LineRate | None, inp, estimated=False):
	"""Mục 4.3 của thiết kế: chi phí một kết quả của một dòng định mức."""
	n = line.norm
	rate = rate or engine.LineRate(_ZERO, "")
	common = dict(test_system=sys.code, line_origin=ORIGIN_NORM, cost_level=line.cost_level)

	def base(cl: engine.CostLine, label="Kết quả", value=Decimal(1), source=SRC_ACTUAL, **kw):
		from dataclasses import replace

		return replace(cl, **common, divisor_label=label, divisor_value=value, divisor_source=source, **kw)

	if n.excluded or rate.billed_separately:
		return base(engine.direct_line(n, rate))
	q = engine.applied_qty(n.hospital_qty, n.authority_qty)
	w = Decimal(n.wastage_rate)
	u = Decimal(rate.rate)

	def made(amount, label, value, source=SRC_ACTUAL, **kw):
		return base(
			engine.CostLine(
				engine.LINE_DIRECT, n.component, amount, n.step_id, n.line_id, n.resource_label,
				q, u, rate.source, "; ".join(rate.warnings),
			),
			label, value, source, **kw,
		)

	if n.component == "LABOR":
		return base(engine.direct_line(n, rate))
	if n.component == "EQUIPMENT":
		eq = _equip_of(sys, n.resource if n.resource in inp.equipment else "", inp)
		annual, notes = equipment_annual(eq, inp)
		m = sys.minutes_per_case if eq.basis == resources.BASIS_MINUTE else q
		amount, label, value = per_result(eq, annual, m)
		return base(
			engine.CostLine(
				engine.LINE_DIRECT, "EQUIPMENT", amount, n.step_id, n.line_id, n.resource_label or eq.code,
				q, None,
				f"{eq.code} · {eq.mode} · {'Theo giá trị tài sản' if inp.allocation_mode == ALLOC_ASSET else 'Gắn trực tiếp thiết bị'}",
				"; ".join(notes),
			),
			label, value, SRC_ACTUAL, cost_category=_category_for(eq, inp),
		)
	if line.cost_level == RESULT:
		if line.apply_k:
			return made(r2(q * u * Decimal(k)), "Kết quả", Decimal(1), _src(estimated), k_factor=Decimal(k))
		return base(engine.direct_line(n, rate))
	if line.cost_level == TUBE:
		return made(r2(q * (1 + w) * u / Decimal(sys.tests_per_tube)), "Số xét nghiệm mỗi ống", Decimal(sys.tests_per_tube))
	if line.cost_level == BATCH:
		return made(r2(q * (1 + w) * u / Decimal(sys.batch)), "Cỡ mẻ", Decimal(sys.batch))
	# DAY, PERIOD (BR-CLS-005)
	annual = q * (1 + w) * u
	if line.cost_level == DAY:
		annual *= Decimal(_days(sys))
	if line.attach == ATTACH_EQUIP:
		eq = _equip_of(sys, line.attach_equipment, inp)
		amount, label, value = per_result(eq, annual, sys.minutes_per_case)
		return made(amount, label, value)
	return made(r2(annual / Decimal(sys.qbn)), "Qbn", Decimal(sys.qbn))


def _auto(sys, comp, lid, label, amount, level, origin, dl, dv, **kw):
	return engine.CostLine(
		engine.LINE_DIRECT, comp, amount, "", lid, label, None, None, "", kw.pop("warning", ""),
		test_system=sys.code, line_origin=origin, cost_level=level, divisor_label=dl, divisor_value=dv,
		divisor_source=SRC_ACTUAL, **kw,
	)


def system_lines(sys: TestSystemInput, inp: ClsServiceInput):
	"""Dòng chi phí một kết quả của hệ thống. Trả (lines, k, tổng test, ước tính)."""
	qnk, qcal, qrerun, qeqa, h, estimated = aux_counts(sys, inp.imaging)
	k, total = k_factor(sys.qbn, qnk, qcal, qrerun, qeqa, h)
	qbn = Decimal(sys.qbn)
	out = []
	for ln in sorted(sys.lines, key=lambda x: x.norm.line_id):
		out.append(norm_line_cost(sys, ln, k, sys.rates.get(ln.norm.line_id), inp, estimated))
	eq = inp.equipment[sys.equipment]
	m = sys.minutes_per_case
	parts = part_per_result(eq, m)
	if parts > 0 or has_per_use_parts(eq):
		out.append(_auto(sys, "EQUIPMENT", "EQ-P", eq.code, parts, RESULT, ORIGIN_EQUIP, "Tuổi thọ linh kiện", Decimal(1)))
	if eq.power is not None:
		amount, label, value = power_per_result(eq, _days(sys), inp.electricity_price, m)
		out.append(_auto(sys, "UTILITY", "EQ-E", eq.code, amount, DAY, ORIGIN_EQUIP, label, value))
	for i, c in enumerate(sys.iqc, 1):  # BR-CLS-006
		u = Decimal(c.rate.rate)
		amount = r2(
			Decimal(c.qty_per_run) * Decimal(c.levels) * Decimal(c.runs_per_day) * Decimal(_days(sys)) * u
			/ Decimal(c.shared_params) / qbn
		)
		out.append(_auto(sys, "DRUG", f"QC-N{i}", c.item, amount, PERIOD, ORIGIN_QC, "Qbn", qbn))
	for i, c in enumerate(sys.cal, 1):  # BR-CLS-007
		amount = r2(Decimal(c.cost_per_calibration) * Decimal(c.per_year) / qbn)
		out.append(_auto(sys, "DRUG", f"QC-C{i}", "Chất chuẩn", amount, PERIOD, ORIGIN_QC, "Qbn", qbn))
	return out, k, total, estimated


# ---------------------------------------------------------------------------
# Tỷ trọng, ngoại kiểm, sản lượng thấp
# ---------------------------------------------------------------------------


def shares(systems):
	"""FR-CLS-004, BR-CLS-013. Trả ({mã: phân số}, nguồn)."""
	systems = list(systems)
	if all(s.qbn and Decimal(s.qbn) > 0 for s in systems):
		tot = sum((Decimal(s.qbn) for s in systems), _ZERO)
		return {s.code: Decimal(s.qbn) / tot for s in systems}, SHARE_FROM_RESULTS
	if len(systems) == 1:
		return {systems[0].code: Decimal(1)}, SHARE_MANUAL
	return {s.code: Decimal(s.manual_share_pct or 0) / 100 for s in systems}, SHARE_MANUAL


def eqa_per_result(eqa, qsum) -> Decimal:
	"""BR-CLS-008, FR-QC-004: r2(Σ (phí + vận chuyển) × tỷ lệ ÷ ΣQbn)."""
	total = sum(((Decimal(e.fee) + Decimal(e.shipping)) * Decimal(e.share) for e in eqa), _ZERO)
	return r2(total / Decimal(qsum))


def open_tests(total, open_days) -> Decimal:
	return r2(Decimal(total) * Decimal(open_days) / 365)


def low_volume(total, reagent) -> bool:
	"""BR-CLS-016. `reagent`: (nominal_tests, open_days)."""
	nominal, open_days = reagent
	return Decimal(total) * Decimal(open_days) / 365 < Decimal(nominal)


# ---------------------------------------------------------------------------
# Kiểm dữ liệu (FR-COST-023, FR-CLS-003)
# ---------------------------------------------------------------------------


def validate(c: ClsServiceInput, service="", department="") -> list:
	errors = []
	systems = sorted(c.systems, key=lambda s: s.code)
	if len(systems) > 1 and not all(s.qbn and Decimal(s.qbn) > 0 for s in systems):
		total = sum((Decimal(s.manual_share_pct or 0) for s in systems), _ZERO)
		if total != 100:
			errors.append(
				f"Tổng tỷ trọng sản lượng các hệ thống của dịch vụ {service} tại khoa {department} "
				f"là {vn(total, 0) if total == total.to_integral() else vn(total)}%, khác 100%"
			)
	used = {}
	for s in systems:
		if not s.norm_set:
			errors.append(f"Hệ thống {s.code} chưa có bộ định mức Đã khóa")
			continue
		used[s.equipment] = True
		if not s.has_volume:
			errors.append(f"Hệ thống {s.code} thiếu sản lượng năm {c.fiscal_year}, kịch bản {c.scenario}")
			continue
		if s.qbn is None or Decimal(s.qbn) <= 0:
			errors.append(f"Hệ thống {s.code} có số kết quả trả bằng 0")
			continue
		batch_lines = [x.norm.line_id for x in s.lines if x.cost_level == BATCH and not x.norm.excluded]
		if batch_lines and (not s.batch or Decimal(s.batch) <= 0):
			errors.append(f"Hệ thống {s.code} có dòng Theo mẻ ({', '.join(batch_lines)}) nhưng thiếu cỡ mẻ bình quân")
		if any(x.cost_level == TUBE and not x.norm.excluded for x in s.lines) and (
			not s.tests_per_tube or Decimal(s.tests_per_tube) <= 0
		):
			errors.append(f"Bộ định mức {s.norm_set} có dòng Theo ống mẫu nhưng thiếu số xét nghiệm mỗi ống")
		eq = c.equipment.get(s.equipment)
		needs_days = (
			any(x.cost_level == DAY and not x.norm.excluded for x in s.lines)
			or bool(s.iqc)
			or (eq is not None and eq.power is not None and not eq.power.continuous)
		)
		if needs_days and _days(s) is None:
			errors.append(f"Hệ thống {s.code} thiếu số ngày chạy máy")
		missing = [
			f"{x.norm.line_id} ({x.norm.resource})"
			for x in s.lines
			if not x.norm.excluded and x.norm.component != "EQUIPMENT" and s.rates.get(x.norm.line_id) is None
		]
		if missing:
			errors.append(f"Hệ thống {s.code}: dòng thiếu đơn giá: {', '.join(missing)}")
		for i in s.iqc:
			if i.rate is None:
				errors.append(f"Hệ thống {s.code}: vật liệu nội kiểm {i.item} thiếu đơn giá")
		if s.actual.h is not None and Decimal(s.actual.h) >= 1 or (s.actual.h is None and Decimal(s.est_h) >= 1):
			errors.append(f"Hệ thống {s.code} có tỷ lệ hao hụt từ 100% trở lên")
		if eq is not None and eq.basis == resources.BASIS_MINUTE and not s.minutes_per_case:
			errors.append(f"Hệ thống {s.code} thiếu số phút chiếm máy một ca")
		for x in s.lines:
			if x.attach == ATTACH_EQUIP and x.attach_equipment:
				used[x.attach_equipment] = True
			if x.norm.component == "EQUIPMENT" and x.norm.resource in c.equipment:
				used[x.norm.resource] = True
	for code in sorted(used):
		eq = c.equipment.get(code)
		if eq is None:
			errors.append(f"Thiết bị {code} không có dữ liệu")
		elif eq.basis == resources.BASIS_RESULT and (not eq.qtb or Decimal(eq.qtb) <= 0):
			errors.append(f"Thiết bị {code} thiếu Qtb năm {c.fiscal_year}, kịch bản {c.scenario}")
		elif eq.basis == resources.BASIS_MINUTE and (not eq.mtb or Decimal(eq.mtb) <= 0):
			errors.append(f"Thiết bị {code} thiếu phút khai thác (Mtb) năm {c.fiscal_year}, kịch bản {c.scenario}")
		elif eq.basis == resources.BASIS_HOURS and (
			not eq.planned_hours or not eq.utilization or Decimal(eq.planned_hours) <= 0 or Decimal(eq.utilization) <= 0
		):
			errors.append(f"Thiết bị {code} thiếu giờ khai thác kế hoạch hoặc hệ số sử dụng")
	return errors


# ---------------------------------------------------------------------------
# Dịch vụ
# ---------------------------------------------------------------------------


def _fix_rounding(parts: dict, total: Decimal) -> dict:
	diff = total - sum(parts.values(), _ZERO)
	if diff != 0 and parts:
		biggest = max(sorted(parts), key=lambda k: parts[k])
		parts[biggest] += diff
	return parts


def _error(inp, c, msg):
	vols = [Decimal(s.qbn) for s in c.systems if s.qbn]
	return engine.ServiceResult(
		inp.service, inp.department, inp.norm_set, engine.STATUS_ERROR, msg, (), {}, {}, _ZERO, {}, None,
		sum(vols, _ZERO) if vols else inp.volume, True,
	)


def cost_service(inp: engine.ServiceInput, params=None) -> engine.ServiceResult:
	"""BR-CLS-013 và mục 4.5: chi phí trực tiếp của dịch vụ cận lâm sàng."""
	c: ClsServiceInput = inp.paraclinical
	errors = validate(c, inp.service, inp.department)
	if errors:
		return _error(inp, c, "; ".join(errors))
	try:
		return _cost(inp, c)
	except ValueError as e:  # dữ liệu thiết bị hỏng: lỗi của dịch vụ, không phải của cả lần tính (ASM-036-18)
		return _error(inp, c, f"Thiết bị: {e}")


def _cost(inp, c: ClsServiceInput):
	systems = sorted(c.systems, key=lambda s: s.code)
	share, source = shares(systems)
	qsum = sum((Decimal(s.qbn) for s in systems), _ZERO)
	sys_lines, sys_costs, low = {}, [], []
	for s in systems:
		lines, k, total, estimated = system_lines(s, c)
		qnk, qcal, qrerun, qeqa, h, _est = aux_counts(s, c.imaging)
		direct = sum((x.amount for x in lines), _ZERO)
		is_low = False
		for x in s.lines:
			if x.is_main_reagent and x.nominal_tests and x.open_days and low_volume(total, (x.nominal_tests, x.open_days)):
				is_low = True
				low.append(f"{s.code} ({vn(open_tests(total, x.open_days))} test trong {vn(x.open_days, 0)} ngày < {vn(x.nominal_tests, 0)})")
		sys_lines[s.code] = lines
		sys_costs.append(
			TestSystemCost(
				s.code, s.norm_set, Decimal(s.qbn), r6(share[s.code] * 100), qnk, qcal, qrerun, qeqa,
				h * 100, k, estimated, direct, is_low, source, total, s.equipment,
			)
		)
	weighted = r2(sum((share[s.code] * tc.direct_cost for s, tc in zip(systems, sys_costs)), _ZERO))
	eqa = eqa_per_result(c.eqa, qsum) if c.eqa else _ZERO
	direct_total = weighted + eqa

	def agg(key):
		acc: dict = {}
		for s in systems:
			for ln in sys_lines[s.code]:
				kk = key(ln)
				acc[kk] = acc.get(kk, _ZERO) + share[s.code] * ln.amount
		return acc

	eqa_cat = c.eqa_category or "DRUG_SUPPLY"
	eqa_comp = _CATEGORY_COMPONENT.get(eqa_cat, "DRUG")
	eqa_lines = []
	if c.eqa:
		eqa_lines.append(
			engine.CostLine(
				engine.LINE_DIRECT, eqa_comp, eqa, "", "EQA", "Ngoại kiểm", None, None, "", "",
				line_origin=ORIGIN_EQA, cost_level=PERIOD, divisor_label="Tổng Qbn của dịch vụ",
				divisor_value=qsum, divisor_source=SRC_ACTUAL, cost_category=c.eqa_category,
			)
		)
	by_comp = {k: r2(v) for k, v in agg(lambda x: x.component).items()}
	by_cat = {k: r2(v) for k, v in agg(lambda x: x.cost_category or engine.COMPONENT_CATEGORY[x.component]).items()}
	if c.eqa:
		by_comp[eqa_comp] = by_comp.get(eqa_comp, _ZERO) + eqa
		by_cat[eqa_cat] = by_cat.get(eqa_cat, _ZERO) + eqa
	by_comp = _fix_rounding(by_comp, direct_total)
	by_cat = _fix_rounding(by_cat, direct_total)
	lines = tuple(x for s in systems for x in sys_lines[s.code]) + tuple(eqa_lines)
	line_warned = any(engine._STALE in x.warning or engine._UNVERIFIED in x.warning for x in lines)
	status = engine.STATUS_WARN if (low or line_warned) else engine.STATUS_OK
	message = f"{LOW_VOLUME_LABEL}: " + "; ".join(low) if low else ""
	return engine.ServiceResult(
		inp.service, inp.department, inp.norm_set, status, message, lines, by_comp, by_cat, direct_total,
		{}, None, qsum, True, eqa, tuple(sys_costs),
	)


def group_by_system(lines) -> list:
	"""Gom dòng theo hệ thống rồi theo cấu phần/bước (SCR-DSK-023). Dòng cấp dịch vụ vào nhóm trống."""
	out = []
	codes = sorted({x.test_system for x in lines if x.test_system})
	for code in codes + [""]:
		rows = [x for x in lines if x.test_system == code]
		if rows:
			out.append({"test_system": code, "groups": engine.group_explanation(rows)})
	return out
