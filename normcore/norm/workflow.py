"""Luồng trạng thái bộ định mức (data-model 5.2, FR-NORM-010..012). Hàm thuần."""

DRAFT, CONFIRMED, LOCKED, REPLACED = "Nháp", "Đã xác nhận chuyên môn", "Đã khóa", "Đã thay thế"

TRANSITIONS = {
	(DRAFT, "confirm_set"): CONFIRMED,
	(CONFIRMED, "lock_set"): LOCKED,
	(CONFIRMED, "return_set"): DRAFT,
	(LOCKED, "replace"): REPLACED,
}
EDITABLE = {DRAFT}  # ASM-012-05
ROLE_OF_ACTION = {
	"confirm_set": ("NC Department Head",),
	"lock_set": ("NC Finance",),
	"return_set": ("NC Finance",),
	"confirm_line": ("NC Clinician", "NC Department Head"),
}


def next_status(status: str, action: str) -> str | None:
	return TRANSITIONS.get((status, action))
