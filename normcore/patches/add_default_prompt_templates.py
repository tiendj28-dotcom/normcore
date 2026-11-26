from normcore.ai.prompts_install import ensure_default_templates


def execute():
	"""FEAT-023 (ASM-023-06): nạp 7 mẫu lệnh mặc định cho site cài trước FEAT-023; không ghi đè."""
	ensure_default_templates()
