#!/usr/bin/env bash
# Chạy lệnh bench trên mã của checkout hiện tại, có khóa để hai run không dẫm nhau.
#
# Bench dev chỉ phục vụ một bản mã: $BENCH_DIR/apps/normcore là liên kết tới một checkout.
# Nhiều agent (Dev, QA) có thể chạy cùng lúc trên các FEAT khác nhau; nếu mỗi run tự trỏ liên kết
# rồi chạy test, run này sẽ test nhầm mã của run kia. Script giữ khóa suốt lệnh: trỏ liên kết về
# checkout này, chạy lệnh, rồi nhả khóa. Run khác phải chờ.
#
# Dùng (từ gốc checkout):
#   scripts/with_bench.sh '<lệnh shell, chạy trong $BENCH_DIR>'
# Ví dụ:
#   scripts/with_bench.sh 'bench --site normcore.test migrate && bench --site normcore.test run-tests --app normcore'
#
# Mọi lệnh cần cùng một trạng thái mã và site (migrate rồi test, new-site rồi install-app rồi test)
# phải nằm trong MỘT lần gọi. Giữa hai lần gọi, run khác có thể đổi mã và CSDL của site.
set -euo pipefail

BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
WAIT="${BENCH_LOCK_WAIT:-5400}" # giây chờ khóa tối đa (mặc định 90 phút)
LOCK="$BENCH_DIR/.normcore-bench.lock"

[ $# -eq 1 ] || { echo "Dùng: $0 '<lệnh>'" >&2; exit 64; }
APP_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
[ -f "$APP_DIR/normcore/hooks.py" ] || { echo "[bench] $APP_DIR không phải gốc app normcore" >&2; exit 1; }
[ -d "$BENCH_DIR/apps" ] || { echo "[bench] không thấy bench ở $BENCH_DIR" >&2; exit 1; }
command -v flock >/dev/null || { echo "[bench] thiếu flock (gói util-linux)" >&2; exit 1; }

exec 9>>"$LOCK"
if ! flock -n 9; then
	echo "[bench] bench đang bận: $(cat "$LOCK.owner" 2>/dev/null || echo '?'). Chờ tối đa ${WAIT}s..."
	flock -w "$WAIT" 9 || { echo "[bench] hết giờ chờ khóa; thử lại sau, đừng chạy bench không khóa" >&2; exit 75; }
fi
echo "$(date -Is) pid=$$ $APP_DIR @ $(git -C "$APP_DIR" rev-parse --short HEAD 2>/dev/null)" >"$LOCK.owner"
trap 'rm -f "$LOCK.owner"' EXIT

cd "$BENCH_DIR"
if [ -L apps/normcore ]; then
	[ "$(readlink -f apps/normcore)" = "$APP_DIR" ] || ln -sfn "$APP_DIR" apps/normcore
elif [ -e apps/normcore ]; then
	echo "[bench] $BENCH_DIR/apps/normcore là thư mục thật, không phải liên kết." >&2
	echo "[bench] Đổi một lần: mv apps/normcore apps/normcore.bak && ln -s <checkout> apps/normcore" >&2
	exit 1
else
	ln -s "$APP_DIR" apps/normcore
fi

echo "[bench] mã: $APP_DIR @ $(git -C "$APP_DIR" rev-parse --short HEAD)"
bash -c "$1"
