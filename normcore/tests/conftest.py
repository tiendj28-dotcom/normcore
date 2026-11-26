"""Sinh vi.csv và normcore.json từ mảnh trước phiên pytest (NORM-60): các test UI đọc hai tệp sinh này."""

from pathlib import Path

from normcore import generated


def pytest_configure(config):
	generated.build_all(Path(__file__).resolve().parents[2])
