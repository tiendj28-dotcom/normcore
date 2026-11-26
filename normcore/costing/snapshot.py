"""Ảnh chụp đầu vào của lần tính giá và tái lập kết quả từ ảnh chụp (FEAT-036). Hàm thuần Python.

FR-COST-032, NFR-REL-001 (tái lập), NFR-REL-003 (cùng đầu vào, cùng k). Lưu tệp và mã băm khi khóa là
việc của FEAT-018 (ASM-036-21); ở đây chỉ dựng, tuần tự hóa và tái lập.
"""

import dataclasses
import hashlib
import json
from datetime import date
from decimal import Decimal

from normcore.costing import cls, engine, runner

VERSION = 1
_CLASSES = {
	c.__name__: c
	for c in (
		engine.ServiceInput,
		engine.NormLine,
		engine.LineRate,
		engine.PricingParams,
		cls.PowerInput,
		cls.ComponentInput,
		cls.RecordInput,
		cls.EquipmentInput,
		cls.ClsNormLine,
		cls.IqcLine,
		cls.CalLine,
		cls.AuxCounts,
		cls.TestSystemInput,
		cls.EqaInput,
		cls.ClsServiceInput,
	)
}


def to_plain(obj):
	"""Dataclass, Decimal, date, tuple, dict -> cấu trúc JSON; có khóa `__type__` để dựng lại đúng lớp."""
	if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
		if type(obj).__name__ not in _CLASSES:
			raise TypeError(f"Lớp không được phép đưa vào ảnh chụp: {type(obj).__name__}")
		out = {"__type__": type(obj).__name__}
		for fld in dataclasses.fields(obj):
			out[fld.name] = to_plain(getattr(obj, fld.name))
		return out
	if isinstance(obj, Decimal):
		return {"__dec__": str(obj)}
	if isinstance(obj, date):
		return {"__date__": obj.isoformat()}
	if isinstance(obj, tuple):
		return {"__tuple__": [to_plain(x) for x in obj]}
	if isinstance(obj, list):
		return [to_plain(x) for x in obj]
	if isinstance(obj, dict) or hasattr(obj, "items"):
		return {"__map__": [[str(k), to_plain(v)] for k, v in sorted(obj.items(), key=lambda kv: str(kv[0]))]}
	if obj is None or isinstance(obj, (bool, int, str)):
		return obj
	raise TypeError(f"Kiểu không đưa được vào ảnh chụp: {type(obj).__name__}")


def from_plain(data):
	if isinstance(data, list):
		return [from_plain(x) for x in data]
	if not isinstance(data, dict):
		return data
	if "__dec__" in data:
		return Decimal(data["__dec__"])
	if "__date__" in data:
		return date.fromisoformat(data["__date__"])
	if "__tuple__" in data:
		return tuple(from_plain(x) for x in data["__tuple__"])
	if "__map__" in data:
		return {k: from_plain(v) for k, v in data["__map__"]}
	if "__type__" in data:
		klass = _CLASSES[data["__type__"]]
		return klass(**{k: from_plain(v) for k, v in data.items() if k != "__type__"})
	raise ValueError("Ảnh chụp có đối tượng không nhận dạng được")


def build(inputs, params, sources=None) -> dict:
	"""Ảnh chụp: tham số, đầu vào đã phân giải của từng dịch vụ và bản ghi nguồn phần cận lâm sàng."""
	return {
		"version": VERSION,
		"params": to_plain(params),
		"inputs": [to_plain(i) for i in sorted(inputs, key=lambda i: (i.service, i.department))],
		"sources": sources or {},
	}


def dumps(snap: dict) -> bytes:
	"""JSON chuẩn hóa: cùng nội dung cho cùng byte."""
	return json.dumps(snap, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def reproduce(snap: dict) -> list:
	"""Tính lại từ ảnh chụp, không đọc CSDL. Chưa phân bổ cấp 2 (allocate=None)."""
	if snap.get("version") != VERSION:
		raise ValueError("Phiên bản ảnh chụp không được hỗ trợ")
	params = from_plain(snap["params"])
	inputs = {(i.service, i.department): i for i in (from_plain(x) for x in snap["inputs"])}
	eligible = [{"service": s, "department": d, "norm_set": i.norm_set} for (s, d), i in inputs.items()]
	return runner.run(eligible, lambda e: inputs[(e["service"], e["department"])], params)
