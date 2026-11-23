from normcore.install import ensure_default_account_mapping


def execute():
	"""FEAT-016 (ASM-118): nạp bảng ánh xạ tài khoản mặc định cho site đã cài; không ghi đè bản đã sửa."""
	ensure_default_account_mapping()
