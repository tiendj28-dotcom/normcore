"""Giao diện chung của provider AI (ADR-005)."""

from dataclasses import dataclass
from typing import Protocol


class ProviderError(Exception):
	"""Lỗi từ provider. Thông báo không được chứa khóa API."""


class ProviderTimeout(ProviderError):
	"""Dịch vụ AI không phản hồi trong thời hạn cấu hình (FR-AI-010)."""


@dataclass(frozen=True)
class ProviderResponse:
	text: str
	tokens_in: int = 0
	tokens_out: int = 0


class Provider(Protocol):
	def complete(
		self,
		purpose: str,
		template_code: str,
		variables: dict,
		sources: list,
		*,
		system: str | None = None,
		user: str | None = None,
	) -> ProviderResponse: ...
