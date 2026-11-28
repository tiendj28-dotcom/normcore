#!/usr/bin/env bash
# Bật site Frappe chạy mã của checkout hiện tại, cho Multica Environments (.multica/environments.toml).
# Agent gọi qua `multica env start preview`; không chạy tay (cần MULTICA_PORT do daemon cấp).
#
# Preview chạy trên bench RIÊNG ($PREVIEW_BENCH_DIR), không phải bench dev ($BENCH_DIR) mà Dev, QA
# dùng để chạy test qua scripts/with_bench.sh. Nếu dùng chung, preview giữ liên kết apps/normcore
# hàng giờ và run test khác sẽ trỏ nó đi chỗ khác (hoặc preview hiện mã của FEAT khác).
# Mỗi máy chỉ một preview tại một thời điểm: script giữ khóa suốt đời của máy chủ web.
set -euo pipefail

DEV_BENCH="${BENCH_DIR:-$HOME/frappe-bench}"
BENCH_DIR="${PREVIEW_BENCH_DIR:-$HOME/preview-bench}"
SITE="${PREVIEW_SITE:-normcore.test}"
PORT="${MULTICA_PORT:?MULTICA_PORT chưa đặt: chỉ chạy qua multica env start}"
APP_DIR="$(pwd -P)"

[ -f "$APP_DIR/normcore/hooks.py" ] || { echo "[preview] $APP_DIR không phải gốc app normcore"; exit 1; }
[ -d "$BENCH_DIR/sites/$SITE" ] || { echo "[preview] chưa có site $SITE trong $BENCH_DIR (tạo một lần theo multica/README.md mục Preview site)"; exit 1; }
if [ "$(readlink -f "$BENCH_DIR")" = "$(readlink -f "$DEV_BENCH")" ]; then
	echo "[preview] PREVIEW_BENCH_DIR trùng bench dev $DEV_BENCH. Preview phải chạy trên bench riêng."
	exit 1
fi

# 0. Một preview mỗi máy. Khóa được giữ tới khi máy chủ web dừng (fd 9 đi theo exec).
exec 9>>"$BENCH_DIR/.normcore-preview.lock"
flock -n 9 || { echo "[preview] máy này đang có preview khác chạy; dừng nó trước (multica env stop)"; exit 1; }

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

# 1b. Bản cài editable của app (normcore.pth) cũng phải trỏ về checkout này, nếu không
# `bench migrate` lỗi ModuleNotFoundError khi checkout cũ đã bị xóa.
pth="$(env/bin/python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')/normcore.pth"
if [ -f "$pth" ] && [ "$(head -n1 "$pth")" != "$APP_DIR" ]; then
	echo "[preview] normcore.pth: $(head -n1 "$pth") -> $APP_DIR"
	printf '%s\n' "$APP_DIR" > "$pth"
elif [ ! -f "$pth" ]; then
	echo "[preview] chưa có normcore.pth, cài editable: $APP_DIR"
	env/bin/pip install -q -e "$APP_DIR"
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
