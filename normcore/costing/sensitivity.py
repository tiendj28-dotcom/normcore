"""Phân tích độ nhạy: tính thử giá thành một dịch vụ với giả định (FEAT-037; FR-COST-030, UC-024).

Hàm thuần Python, không ghi gì: dựng bản sao đầu vào (`dataclasses.replace`) rồi tính lại từ ảnh chụp bằng
`snapshot.recompute`, đúng đường tính của lần tính giá (không công thức mới).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from decimal import Decimal, InvalidOperation

from normcore.costing import cls, engine, pricing, resources, snapshot

NOTE = "Kết quả thử, không lưu"
ASSUMED = " · giả định"


class InvalidAssumption(ValueError):
	"""Giả định không hợp lệ (UC-024 2a); không tính."""


def _num(value, message: str) -> Decimal:
	try:
		d = Decimal(str(value))
	except (InvalidOperation, ValueError):
		raise InvalidAssumption(message) from None
	if not d.is_finite():
		raise InvalidAssumption(message)
	return d


def _volume(value) -> Decimal:
	msg = "Sản lượng giả định phải lớn hơn 0"
	d = _num(value, msg)
	if d <= 0:
		raise InvalidAssumption(msg)
	return d


def _used_equipment(c: cls.ClsServiceInput) -> set:
	used = set()
	for s in c.systems:
		used.add(s.equipment)
		for x in s.lines:
			if x.attach_equipment:
				used.add(x.attach_equipment)
			if x.norm.component == "EQUIPMENT" and x.norm.resource in c.equipment:
				used.add(x.norm.resource)
	return used


def _items(inp: engine.ServiceInput) -> set:
	out = {x.norm.resource for s in (inp.paraclinical.systems if inp.paraclinical else ()) for x in s.lines}
	out |= {i.item for s in (inp.paraclinical.systems if inp.paraclinical else ()) for i in s.iqc}
	out |= {x.resource for x in inp.lines}
	return {x for x in out if x}


def _assumed(rate, new_rate: Decimal):
	src = (rate.source if rate is not None else "") + ASSUMED
	return engine.LineRate(new_rate, src)


def _reprice(rates: Mapping, line_ids, new_rate: Decimal) -> dict:
	out = dict(rates)
	for lid in line_ids:
		out[lid] = _assumed(rates.get(lid), new_rate)
	return out


def _equipment(eq: cls.EquipmentInput, spec) -> cls.EquipmentInput:
	if not isinstance(spec, Mapping):
		raise InvalidAssumption("Hình thức có máy không hợp lệ")
	mode = spec.get("mode") or eq.mode
	if mode not in resources.ACQUISITION_MODES:
		raise InvalidAssumption("Hình thức có máy không hợp lệ")
	contract = eq.contract_cost
	if spec.get("contract_cost") not in (None, ""):
		contract = _num(spec["contract_cost"], "Nhập chi phí năm theo hợp đồng")
	if mode in (resources.RENT, resources.JOINT) and (contract is None or Decimal(contract) <= 0):
		raise InvalidAssumption("Nhập chi phí năm theo hợp đồng")
	if mode == resources.BUY and (not eq.original_cost or not eq.life_years):
		raise InvalidAssumption("Thiết bị chưa có nguyên giá hoặc số năm sử dụng")
	return replace(eq, mode=mode, contract_cost=contract)


def apply(inp: engine.ServiceInput, overrides: Mapping, units: Mapping) -> engine.ServiceInput:
	"""Bản sao của `inp` với giả định; ném `InvalidAssumption`. Không sửa `inp`."""
	if not overrides or not any(
		overrides.get(k) for k in ("volume", "system_volumes", "prices", "equipment_modes")
	):
		raise InvalidAssumption("Nhập ít nhất một giả định")
	c = inp.paraclinical
	out = inp
	if overrides.get("volume") not in (None, ""):
		if c is not None:
			raise InvalidAssumption("Dịch vụ này nhập sản lượng theo hệ thống xét nghiệm")
		out = replace(out, volume=_volume(overrides["volume"]))
	sv = overrides.get("system_volumes") or {}
	if sv:
		if c is None or any(code not in {s.code for s in c.systems} for code in sv):
			bad = next((k for k in sv if c is None or k not in {s.code for s in c.systems}), "")
			raise InvalidAssumption(f"{bad} không thuộc dịch vụ này")
		systems = tuple(
			replace(s, qbn=_volume(sv[s.code]), has_volume=True) if s.code in sv else s for s in c.systems
		)
		c = replace(c, systems=systems)
		out = replace(out, volume=sum((Decimal(s.qbn) for s in systems), Decimal(0)))
	prices = overrides.get("prices") or {}
	if prices:
		known = _items(inp)
		for item in prices:
			if item not in known:
				raise InvalidAssumption(f"{item} không thuộc dịch vụ này")
		for item, price in prices.items():
			p = _num(price, "Đơn giá giả định không được âm")
			if p < 0:
				raise InvalidAssumption("Đơn giá giả định không được âm")
			new = pricing.unit_price_per_norm(p, Decimal(units.get(item) or 1))
			out = replace(
				out, rates=_reprice(out.rates, [x.line_id for x in out.lines if x.resource == item], new)
			)
			if c is not None:
				c = replace(
					c,
					systems=tuple(
						replace(
							s,
							rates=_reprice(
								s.rates, [x.norm.line_id for x in s.lines if x.norm.resource == item], new
							),
							iqc=tuple(
								replace(i, rate=_assumed(i.rate, new)) if i.item == item else i for i in s.iqc
							),
						)
						for s in c.systems
					),
				)
	modes = overrides.get("equipment_modes") or {}
	if modes:
		used = _used_equipment(c) if c is not None else set()
		for code in modes:
			if code not in used or code not in c.equipment:
				raise InvalidAssumption(f"{code} không thuộc dịch vụ này")
		eqs = dict(c.equipment)
		for code, spec in modes.items():
			eqs[code] = _equipment(eqs[code], spec)
		c = replace(c, equipment=eqs)
	if c is not None:
		out = replace(out, paraclinical=c)
	return out


def trial(
	snap: dict, service: str, department: str, overrides: Mapping, units: Mapping
) -> engine.ServiceResult:
	"""Giá thành thử của một cặp (dịch vụ, khoa) từ ảnh chụp; không đọc, không ghi CSDL."""
	inputs = [snapshot.from_plain(x) for x in snap["inputs"]]
	pos = next((i for i, x in enumerate(inputs) if (x.service, x.department) == (service, department)), None)
	if pos is None:
		raise InvalidAssumption(f"{service} không có trong lần tính này")
	inputs[pos] = apply(inputs[pos], overrides, units)
	snap2 = {**snap, "inputs": [snapshot.to_plain(x) for x in inputs]}
	for r in snapshot.recompute(snap2).results:
		if (r.service, r.department) == (service, department):
			return r
	raise InvalidAssumption(f"{service} không có kết quả")
