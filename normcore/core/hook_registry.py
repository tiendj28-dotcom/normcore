"""Sổ đăng ký hook dạng danh sách theo tệp (NORM-60). Python thuần, hooks.py nạp ở cuối tệp.

Mỗi FEAT/issue một tệp `normcore/hook_registry/<FEAT-NNN|NORM-NN>.json`, ví dụ:
    {"scheduler_events": {"daily": ["normcore.api.x.daily_job"]}, "app_include_js": ["/assets/normcore/js/x.js"]}
Khóa hỗ trợ: app_include_js, after_install, after_migrate, before_migrate, fixtures, normcore_pending_sources,
scheduler_events.<all|hourly|daily|weekly|monthly>. Ghép theo tên tệp (sắp chuỗi), bỏ phần tử trùng, giữ thứ tự.
Khóa lạ: ValueError nêu tên tệp.
"""

import json
from pathlib import Path

LIST_KEYS = (
	"app_include_js",
	"after_install",
	"after_migrate",
	"before_migrate",
	"fixtures",
	"normcore_pending_sources",
)
FREQUENCIES = ("all", "hourly", "daily", "weekly", "monthly")
DEFAULT_DIR = Path(__file__).resolve().parent.parent / "hook_registry"


def _extend(target: list, items, where: str, key: str):
	if not isinstance(items, list):
		raise ValueError(f"{where}: '{key}' phải là danh sách")
	for item in items:
		if item not in target:
			target.append(item)


def load(directory=None) -> dict:
	directory = Path(directory) if directory else DEFAULT_DIR
	reg = {k: [] for k in LIST_KEYS}
	reg["scheduler_events"] = {}
	if not directory.is_dir():
		return reg
	for path in sorted(directory.glob("*.json"), key=lambda p: p.name):
		try:
			data = json.loads(path.read_text(encoding="utf-8"))
		except ValueError as e:
			raise ValueError(f"{path.name}: không đọc được JSON: {e}") from e
		if not isinstance(data, dict):
			raise ValueError(f"{path.name}: JSON không phải đối tượng")
		for key, value in data.items():
			if key in LIST_KEYS:
				_extend(reg[key], value, path.name, key)
			elif key == "scheduler_events":
				if not isinstance(value, dict):
					raise ValueError(f"{path.name}: 'scheduler_events' phải là đối tượng theo tần suất")
				for freq, items in value.items():
					if freq not in FREQUENCIES:
						raise ValueError(f"{path.name}: tần suất scheduler_events lạ '{freq}'")
					_extend(
						reg["scheduler_events"].setdefault(freq, []),
						items,
						path.name,
						f"scheduler_events.{freq}",
					)
			else:
				raise ValueError(f"{path.name}: khóa hook lạ '{key}'")
	return reg
