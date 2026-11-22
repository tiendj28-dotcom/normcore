#!/usr/bin/env bash
# Bật site Frappe chạy mã của checkout hiện tại, cho Multica Environments (.multica/environments.toml).
# Agent gọi qua `multica env start preview`; không chạy tay (cần MULTICA_PORT do daemon cấp).
#
# Giới hạn: bench dev chỉ phục vụ một bản mã tại một thời điểm. Script trỏ $BENCH_DIR/apps/normcore
# về checkout này, nên mỗi lúc chỉ nên có một environment preview đang chạy trên một máy.
set -euo pipefail

BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
SITE="${PREVIEW_SITE:-normcore.test}"
PORT="${MULTICA_PORT:?MULTICA_PORT chưa đặt: chỉ chạy qua multica env start}"
APP_DIR="$(pwd -P)"

[ -f "$APP_DIR/normcore/hooks.py" ] || { echo "[preview] $APP_DIR không phải gốc app normcore"; exit 1; }
[ -d "$BENCH_DIR/sites/$SITE" ] || { echo "[preview] chưa có site $SITE trong $BENCH_DIR (tạo một lần theo CLAUDE.md mục 10)"; exit 1; }

cd "$BENCH_DIR"

# 1. Trỏ app về checkout của run này.
if [ -L apps/normcore ]; then
	current="$(readlink -f apps/normcore)"
	if [ "$current" != "$APP_DIR" ]; then
		echo "[preview] apps/normcore: $current -> $APP_DIR"
		ln -sfn "$APP_DIR" apps/normcore
	fi
elif [ -e apps/normcore ]; then
	echo "[preview] $BENCH_DIR/apps/normcore là thư mục thật, không phải liên kết."
	echo "[preview] Đổi một lần: mv apps/normcore apps/normcore.bak && ln -s <checkout> apps/normcore"
	exit 1
else
	ln -s "$APP_DIR" apps/normcore
fi

# 2. Redis của bench, nếu chưa chạy. Chạy nền trong cùng nhóm tiến trình nên dừng environment là dừng theo.
for conf in config/redis_cache.conf config/redis_queue.conf; do
	[ -f "$conf" ] || continue
	rport="$(awk '/^port/ {print $2}' "$conf")"
	if ! redis-cli -p "$rport" ping >/dev/null 2>&1; then
		redis-server "$conf" &
	fi
done

# 3. Đồng bộ CSDL và tài nguyên với mã của checkout.
bench --site "$SITE" migrate
bench build --app normcore
bench --site "$SITE" clear-cache

# 4. Máy chủ web ở tiền cảnh trên cổng Multica cấp.
echo "[preview] http://localhost:$PORT/app (site $SITE, mã $(git -C "$APP_DIR" rev-parse --short HEAD))"
exec bench --site "$SITE" serve --port "$PORT" --noreload
