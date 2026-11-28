"""NORM-91: preview_env.sh phải cập nhật normcore.pth về checkout hiện tại."""

from pathlib import Path

SCRIPT = (Path(__file__).resolve().parents[1] / "preview_env.sh").read_text()


def test_updates_pth_to_app_dir():
	assert "normcore.pth" in SCRIPT
	assert '> "$pth"' in SCRIPT and '"$APP_DIR"' in SCRIPT


def test_pth_updated_before_migrate():
	assert SCRIPT.index("normcore.pth") < SCRIPT.index('bench --site "$SITE" migrate')
