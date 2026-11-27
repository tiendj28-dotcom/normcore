"""Đóng gói hồ sơ xuất thành một tệp nén tất định (FR-OUT-009). Thuần, không phụ thuộc frappe."""

import io
import zipfile

from normcore.exports import meta as meta_mod

INFO_NAME = "thong-tin-xuat.txt"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)


def _unique(name: str, used: set) -> str:
	if name not in used:
		return name
	stem, dot, ext = name.rpartition(".")
	if not dot:
		stem, ext = name, ""
	n = 2
	while True:
		cand = f"{stem}-{n}" + (f".{ext}" if ext else "")
		if cand not in used:
			return cand
		n += 1


def zip_files(files: list[tuple[str, bytes]], meta: dict) -> bytes:
	"""Giữ thứ tự tệp, đổi tên khi trùng, thêm `thong-tin-xuat.txt`; cùng đầu vào cho cùng bytes."""
	buf = io.BytesIO()
	used: set = set()
	info = "\n".join(f"{k}: {v}" for k, v in meta_mod.info_rows(meta)) + "\n"
	with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
		for name, content in [*files, (INFO_NAME, info.encode("utf-8"))]:
			name = _unique(name, used)
			used.add(name)
			zi = zipfile.ZipInfo(name, FIXED_TIME)
			zi.compress_type = zipfile.ZIP_DEFLATED
			zf.writestr(zi, content)
	return buf.getvalue()
