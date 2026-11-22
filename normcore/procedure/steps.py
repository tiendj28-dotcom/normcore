"""Thêm, xóa, sắp lại bước (FR-PROC-003, FR-PROC-006). Thuần Python: bước là dict có khóa `step_id`.

Hàm không sửa đầu vào, luôn trả danh sách mới. Mã bước không bao giờ đổi khi sắp lại.
"""

from normcore.procedure.codes import next_code


def add_step(steps, counter, data):
	"""Thêm bước cuối danh sách; mã lấy từ bộ đếm. Trả `(danh sách mới, bộ đếm mới)`."""
	counter, code = next_code("S", counter, [s.get("step_id") for s in steps])
	return [*steps, {**data, "step_id": code}], counter


def remove_step(steps, step_id):
	if step_id not in [s["step_id"] for s in steps]:
		raise ValueError(step_id)
	return [s for s in steps if s["step_id"] != step_id]


def reorder(steps, order):
	"""Sắp theo `order` (danh sách mã bước). `order` phải là hoán vị đầy đủ của các mã đang có."""
	by_id = {s["step_id"]: s for s in steps}
	if len(order) != len(set(order)) or set(order) != set(by_id):
		raise ValueError("order phải là hoán vị đầy đủ của các mã bước hiện có")
	return [by_id[i] for i in order]


def move(steps, step_id, delta):
	"""Đổi chỗ một bước lên (delta < 0) hoặc xuống (delta > 0) một vị trí; ở biên thì giữ nguyên."""
	ids = [s["step_id"] for s in steps]
	if step_id not in ids:
		raise ValueError(step_id)
	i = ids.index(step_id)
	j = i + (1 if delta > 0 else -1)
	if not 0 <= j < len(ids):
		return list(steps)
	ids[i], ids[j] = ids[j], ids[i]
	return reorder(steps, ids)
