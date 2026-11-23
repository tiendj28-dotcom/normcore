from normcore.install import ensure_sample_price_categories


def execute():
	"""FEAT-011 (ASM-074): nạp hai loại giá mẫu cho site đã có trước FEAT-011; không ghi đè bản đã có."""
	ensure_sample_price_categories()
