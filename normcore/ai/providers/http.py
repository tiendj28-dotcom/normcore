"""Gọi HTTP dùng chung cho bộ chuyển đổi: ánh xạ quá hạn, che khóa (FR-AI-010, NFR-SEC-004)."""

from normcore.ai.providers.base import ProviderError, ProviderTimeout


def default_post(url, headers, payload, timeout):
	import requests

	try:
		resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
		resp.raise_for_status()
		return resp.json()
	except requests.exceptions.Timeout as e:
		raise ProviderTimeout(f"Dịch vụ AI không phản hồi trong {timeout} giây") from None


def _is_timeout(e: Exception) -> bool:
	if isinstance(e, TimeoutError):  # gồm socket.timeout
		return True
	try:
		import requests

		return isinstance(e, requests.exceptions.Timeout)
	except ImportError:  # pragma: no cover
		return False


def call(post, url, headers, payload, timeout, secret=None):
	"""Gọi `post`; quá hạn → ProviderTimeout, lỗi khác → ProviderError đã che khóa."""
	try:
		return post(url, headers, payload, timeout)
	except ProviderError:
		raise
	except Exception as e:
		if _is_timeout(e):
			raise ProviderTimeout(f"Dịch vụ AI không phản hồi trong {timeout} giây") from None
		msg = str(e)
		if secret:
			msg = msg.replace(secret, "***")
		raise ProviderError(f"Lỗi gọi nhà cung cấp AI: {type(e).__name__}: {msg}") from None
