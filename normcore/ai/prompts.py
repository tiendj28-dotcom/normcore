"""Mẫu lệnh AI: dựng Jinja trong sandbox và kiểm lược đồ đầu ra (FR-AI-014, ADR-005). Thuần, không phụ thuộc frappe."""

import json


class PromptError(Exception):
	"""Mẫu lệnh hoặc lược đồ không hợp lệ."""


def _tojson(value):
	return json.dumps(value, ensure_ascii=False, default=str)


def _env():
	# jinja2 do Frappe cài sẵn; import muộn để phần kiểm lược đồ chạy được ở CI unit thuần (không có jinja2)
	from jinja2 import StrictUndefined
	from jinja2.sandbox import SandboxedEnvironment

	env = SandboxedEnvironment(undefined=StrictUndefined, autoescape=False)
	env.filters["tojson"] = _tojson
	return env


def render(user_prompt: str, variables: dict, sources: list) -> str:
	from jinja2.exceptions import TemplateError

	try:
		return _env().from_string(user_prompt).render(variables=variables or {}, sources=sources or [])
	except TemplateError as e:
		raise PromptError(f"Không dựng được mẫu lệnh: {e}") from None
	except Exception as e:  # SecurityError, lỗi thuộc tính… trong sandbox
		raise PromptError(f"Không dựng được mẫu lệnh: {type(e).__name__}: {e}") from None


def check_syntax(user_prompt: str) -> None:
	from jinja2.exceptions import TemplateError

	try:
		_env().parse(user_prompt)
	except TemplateError as e:
		raise PromptError(f"Cú pháp mẫu lệnh sai: {e}") from None


def parse_schema(text: str) -> dict:
	try:
		schema = json.loads(text or "")
	except ValueError as e:
		raise PromptError(f"Lược đồ JSON không hợp lệ: {e}") from None
	if not isinstance(schema, dict):
		raise PromptError("Lược đồ JSON phải là một đối tượng")
	return schema


_TYPES = {
	"object": lambda v: isinstance(v, dict),
	"array": lambda v: isinstance(v, list),
	"string": lambda v: isinstance(v, str),
	"boolean": lambda v: isinstance(v, bool),
	"integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
	"number": lambda v: isinstance(v, int | float) and not isinstance(v, bool),
	"null": lambda v: v is None,
}


def check_output(data, schema: dict, path: str = "$") -> list[str]:
	"""Kiểm tối thiểu `type`, `required`, `properties`, `items` (ASM-023-07). Rỗng = đạt."""
	errors: list[str] = []
	t = schema.get("type")
	if t:
		check = _TYPES.get(t)
		if check and not check(data):
			return [f"{path}: cần kiểu {t}"]
	if isinstance(data, dict):
		for key in schema.get("required", []) or []:
			if key not in data:
				errors.append(f"{path}: thiếu trường {key}")
		for key, sub in (schema.get("properties") or {}).items():
			if key in data and isinstance(sub, dict):
				errors += check_output(data[key], sub, f"{path}.{key}")
	if isinstance(data, list) and isinstance(schema.get("items"), dict):
		for i, row in enumerate(data):
			errors += check_output(row, schema["items"], f"{path}[{i}]")
	return errors
