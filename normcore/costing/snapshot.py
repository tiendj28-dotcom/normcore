"""Ảnh chụp đầu vào của lần tính giá và tái lập kết quả từ ảnh chụp (FEAT-036). Hàm thuần Python.

FR-COST-032, NFR-REL-001 (tái lập), NFR-REL-003 (cùng đầu vào, cùng k). Lưu tệp và mã băm khi khóa là
việc của FEAT-018 (ASM-036-21); ở đây chỉ dựng, tuần tự hóa và tái lập.
"""

import dataclasses
import gzip
import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import NamedTuple

from normcore.costing import allocation, cls, engine, reconcile, runner

VERSION = 2  # 2 = 1 + mục `allocation` và `meta` (FEAT-018); đọc được cả 1 (ADR-004 [1.1])
SUPPORTED = (1, 2)
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
		allocation.Rule,
		allocation.AllocationInput,
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
		pairs = [(k if isinstance(k, str) else to_plain(k), to_plain(v)) for k, v in obj.items()]
		pairs.sort(
			key=lambda kv: (
				not isinstance(kv[0], str),
				kv[0] if isinstance(kv[0], str) else dumps(kv[0]).decode(),
			)
		)
		return {"__map__": [[k, v] for k, v in pairs]}
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
		return {(from_plain(k) if isinstance(k, dict) else k): from_plain(v) for k, v in data["__map__"]}
	if "__type__" in data:
		klass = _CLASSES[data["__type__"]]
		return klass(**{k: from_plain(v) for k, v in data.items() if k != "__type__"})
	raise ValueError("Ảnh chụp có đối tượng không nhận dạng được")


def build(inputs, params, sources=None, allocation=None, meta=None) -> dict:
	"""Ảnh chụp: tham số, đầu vào đã phân phối của từng dịch vụ, bản ghi nguồn phần cận lâm sàng; tùy chọn
	`allocation` ({"input": AllocationInput, "dept_center": {khoa: trung tâm}, "tolerance": "<chuỗi>"}) và
	`meta`. Không có thời điểm trong nội dung để mã băm tất định."""
	snap = {
		"version": VERSION,
		"params": to_plain(params),
		"inputs": [to_plain(i) for i in sorted(inputs, key=lambda i: (i.service, i.department))],
		"sources": sources or {},
	}
	if allocation is not None:
		snap["allocation"] = {
			"input": to_plain(allocation["input"]),
			"dept_center": to_plain(allocation["dept_center"]),
			"tolerance": str(allocation["tolerance"]),
		}
	if meta is not None:
		snap["meta"] = to_plain(meta)
	return snap


def dumps(snap: dict) -> bytes:
	"""JSON chuẩn hóa: cùng nội dung cho cùng byte."""
	return json.dumps(snap, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest(data: bytes) -> str:
	return hashlib.sha256(data).hexdigest()


def pack(snap: dict) -> tuple[bytes, str]:
	"""(nội dung nén, sha256 của JSON chuẩn hóa trước khi nén). `mtime=0` để cùng nội dung cùng byte."""
	data = dumps(snap)
	return gzip.compress(data, mtime=0), digest(data)


def unpack(blob: bytes, expected_hash: str | None = None) -> dict:
	data = gzip.decompress(blob)
	if expected_hash is not None and digest(data) != expected_hash:
		raise ValueError("Ảnh chụp không còn nguyên vẹn: mã băm không khớp")
	return json.loads(data.decode("utf-8"))


class Recomputed(NamedTuple):
	results: list
	recon_rows: list
	warnings: list


def recompute(snap: dict) -> Recomputed:
	"""Tính lại từ ảnh chụp, không đọc CSDL, cùng thứ tự với `NCCostingRun._run` + `execute_costing`.
	Ảnh chụp lược đồ 1 (không có `allocation`) chỉ tính trực tiếp, không phân bổ, không đối soát."""
	if snap.get("version") not in SUPPORTED:
		raise ValueError("Phiên bản ảnh chụp không được hỗ trợ")
	params = from_plain(snap["params"])
	inputs = {(i.service, i.department): i for i in (from_plain(x) for x in snap["inputs"])}
	eligible = [{"service": s, "department": d, "norm_set": i.norm_set} for (s, d), i in inputs.items()]
	alloc = snap.get("allocation")
	if alloc is None:
		return Recomputed(
			runner.run(eligible, lambda e: inputs[(e["service"], e["department"])], params), [], []
		)
	ainput = from_plain(alloc["input"])
	dept_center = from_plain(alloc["dept_center"])
	drivers = {}
	outcome = {}

	def load(e):
		key = (e["service"], e["department"])
		drivers[key] = allocation.service_drivers(inputs[key], dept_center.get(e["department"]))
		return inputs[key]

	def allocate(rs):
		outcome["o"] = allocation.allocate(rs, drivers, ainput)
		return outcome["o"].lines

	results = [allocation.mark_volume(r) for r in runner.run(eligible, load, params, allocate=allocate)]
	out = outcome["o"]
	rows = reconcile.reconcile(
		out.pools,
		float(alloc["tolerance"]),
		ainput.include_depreciation,
		reconcile.depreciation_centers(ainput.accounting, out.pools),
	)
	return Recomputed(results, rows, list(out.warnings))


def reproduce(snap: dict) -> list:
	"""Tính lại từ ảnh chụp, trả kết quả (giữ chữ ký của FEAT-036)."""
	return recompute(snap).results


def _norm(v, places):
	if v is None or v == "":
		return None
	if isinstance(v, (bool, int, float, Decimal)):
		return Decimal(str(int(v) if isinstance(v, bool) else v)).quantize(Decimal(1).scaleb(-places))
	return str(v)


def _label(key) -> str:
	kind = key[0]
	if kind == "cost":
		return f"{key[1]} · {key[2]}"
	if kind == "recon":
		return f"{key[1]} · {key[2]}"
	return f"{key[1]} · {key[2]} dòng {key[3]}"


_KIND_NAME = {
	"cost": "kết quả",
	"line": "dòng chi phí",
	"system": "dòng hệ thống xét nghiệm",
	"recon": "dòng đối soát",
}


def diff_rows(expected, actual, places=6) -> list[str]:
	"""So hai danh sách bản ghi phẳng {"key": (loại, ...), "values": {...}}; trả câu tiếng Việt cho mỗi khác biệt."""
	exp = {tuple(r["key"]): r["values"] for r in expected}
	act = {tuple(r["key"]): r["values"] for r in actual}
	out = []
	for key in sorted(set(exp) | set(act), key=lambda k: tuple(str(x) for x in k)):
		name = _KIND_NAME[key[0]]
		if key not in act:
			out.append(f"Thiếu {name} {_label(key)}")
		elif key not in exp:
			out.append(f"Thừa {name} {_label(key)}")
		else:
			a, b = exp[key], act[key]
			for f in sorted(set(a) | set(b)):
				if _norm(a.get(f), places) != _norm(b.get(f), places):
					out.append(f"{_label(key)} · {f}: {a.get(f)} ≠ {b.get(f)}")
	return out
