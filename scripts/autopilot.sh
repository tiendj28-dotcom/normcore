#!/usr/bin/env bash
# Normcore Autopilot — chạy Claude Code không người duyệt, từ bộ tài liệu đến app hoàn chỉnh.
# Cách dùng:
#   ./scripts/autopilot.sh            # chạy (tiếp tục từ chỗ dừng)
#   ./scripts/autopilot.sh status     # xem trạng thái 39 FEAT
#   ./scripts/autopilot.sh unhalt     # gỡ cờ HALT sau khi đã xử lý nguyên nhân
#   ./scripts/autopilot.sh pause      # tạm dừng trước phiên kế tiếp (lấy lại quota Max cho người)
#   ./scripts/autopilot.sh resume     # chạy tiếp
# Mọi trạng thái nằm trong git (docs/features/*) nên dừng giữa chừng rồi chạy lại là an toàn.
#
# Chế độ gói Claude Max (mặc định): đăng nhập bằng `claude` (không dùng ANTHROPIC_API_KEY).
#   - Hết hạn mức 5 giờ / tuần: phiên đó không bị tính là kẹt, runner chờ tới giờ reset rồi chạy lại.
#   - RUN_WINDOW="22-07": chỉ chạy ban đêm, ban ngày nhường quota cho người.
#   - MODEL (mặc định Sonnet) cho phần lớn giai đoạn; MODEL_STRONG (Opus) cho STRONG_STAGES.

set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)" || { echo "Phải chạy trong kho git của normcore"; exit 1; }
cd "$ROOT"

AP=".autopilot"
MODEL="${MODEL:-claude-sonnet-5-5}"
MODEL_STRONG="${MODEL_STRONG:-claude-opus-5-5}"
STRONG_STAGES="${STRONG_STAGES:-design verify release}"  # "all" = mọi giai đoạn dùng MODEL_STRONG
RUN_WINDOW="${RUN_WINDOW:-}"                   # "22-07" = chỉ chạy 22h–7h; trống = chạy mọi lúc
LIMIT_FALLBACK_WAIT="${LIMIT_FALLBACK_WAIT:-1800}"  # giây chờ khi không đọc được giờ reset
MAX_LIMIT_WAITS="${MAX_LIMIT_WAITS:-200}"      # số lần chờ hết lượt tối đa trước khi HALT
MAX_TURNS="${MAX_TURNS:-300}"          # số lượt tối đa trong một phiên
STAGE_TIMEOUT="${STAGE_TIMEOUT:-4h}"   # thời gian tối đa một phiên
MAX_CYCLES="${MAX_CYCLES:-4}"          # số lần làm lại (rework/design-defect) tối đa mỗi FEAT
MAX_RUNS="${MAX_RUNS:-400}"            # trần tổng số phiên — chặn chi phí
VERIFY_EVERY="${VERIFY_EVERY:-5}"      # chạy pipeline-verify sau mỗi N FEAT xong
RELEASES="${RELEASES:-R1 R2 R3}"
export BENCH_DIR="${BENCH_DIR:-$HOME/frappe-bench}"
export AUTO_DEPLOY_PROD="${AUTO_DEPLOY_PROD:-false}"

mkdir -p "$AP/logs" "$AP/cycles"
touch "$AP/run.log" "$AP/counted" "$AP/runs"

log()  { echo "[$(date '+%F %T')] $*" | tee -a "$AP/run.log"; }
halt() { echo "$*" > "$AP/HALT"; log "HALT: $*"; exit 2; }

# ---------- git helpers ----------
sync_develop() {
  git fetch -q origin || halt "git fetch lỗi"
  git checkout -q develop 2>/dev/null || git checkout -q -b develop origin/develop || halt "không checkout được develop"
  git pull -q --ff-only origin develop || halt "develop không fast-forward được"
}

feat_remote_branch() {  # in ra tên nhánh feat/FEAT-NNN-* trên origin, nếu có
  git for-each-ref --format='%(refname:short)' "refs/remotes/origin/feat/$1-*" | head -1
}

checkout_feat() {  # chuyển về nhánh của FEAT nếu đã có, ngược lại về develop
  local rb lb
  git fetch -q origin
  rb="$(feat_remote_branch "$1")"
  if [ -n "$rb" ]; then
    lb="${rb#origin/}"
    git checkout -q "$lb" 2>/dev/null || git checkout -q -b "$lb" "$rb" || halt "không checkout được $lb"
    git pull -q --ff-only origin "$lb" || true
  else
    sync_develop
  fi
}

autocommit_push() {  # lưới an toàn: không để mất việc của agent
  if [ -n "$(git status --porcelain)" ]; then
    git add -A && git commit -q -m "autopilot: lưu việc dở sau giai đoạn $1 $2" || true
  fi
  git push -q -u origin HEAD 2>/dev/null || log "cảnh báo: push lỗi ($1 $2)"
}

on_develop() { git cat-file -e "origin/develop:$1" 2>/dev/null; }

# ---------- trạng thái FEAT ----------
is_done()    { on_develop "docs/features/$1/DONE"; }
is_blocked() { on_develop "docs/features/$1/BLOCKED" || [ -f "docs/features/$1/BLOCKED" ]; }

mark_blocked() {  # $1 FEAT, $2 lý do — ghi lên develop để bền
  local f="$1" why="$2"
  autocommit_push "mark-blocked" "$f"
  sync_develop
  mkdir -p "docs/features/$f"
  printf '%s\n%s\n' "$(date '+%F %T')" "$why" > "docs/features/$f/BLOCKED"
  git add "docs/features/$f/BLOCKED" && git commit -q -m "autopilot: $f BLOCKED — $why" && git push -q origin develop
  log "$f BLOCKED: $why"
}

verified_state_sha() {  # commit cuối cùng không tính tệp kết quả kiểm định và tài liệu tích hợp
  local f="$1"
  git log -1 --format=%H -- . \
    ":(exclude)docs/features/$f/acceptance.md" ":(exclude)docs/features/$f/verdict.json" \
    ":(exclude)docs/features/$f/DONE" ":(exclude)docs/as-built/$f.md" \
    ":(exclude)docs/rtm.md" ":(exclude)docs/rtm-testref.md" ":(exclude)docs/verification-report.md" \
    ":(exclude).github" ":(exclude).autopilot"
}

verdict_field() {  # $1 FEAT, $2 trường
  python3 -c "import json,sys;d=json.load(open('docs/features/$1/verdict.json',encoding='utf-8'));print(d.get('$2','') if '$2'!='reasons' else '\n'.join('- '+r for r in d.get('reasons',[])))" 2>/dev/null
}

next_stage() {  # in ra giai đoạn kế tiếp của FEAT (sau khi đã checkout_feat)
  local f="$1" d="docs/features/$1"
  if is_done "$f"; then echo done; return; fi
  if is_blocked "$f"; then echo blocked; return; fi
  [ -f "$d/technical-design.md" ] || { echo design; return; }
  [ -f "$d/ui-design.md" ]        || { echo ui; return; }
  if grep -q -- '- \[ \]' "$d/tasks.md" 2>/dev/null; then echo implement; return; fi
  [ -f "$d/verdict.json" ]        || { echo verify; return; }
  local v c
  v="$(verdict_field "$f" verdict)"; c="$(verdict_field "$f" commit)"
  if [ "$c" != "$(verified_state_sha "$f")" ]; then echo verify; return; fi
  case "$v" in
    accepted)           echo integrate ;;
    rework)             echo rework ;;
    design-defect)      echo redesign ;;
    requirement-defect) echo reqdefect ;;
    *)                  echo verify ;;
  esac
}

count_cycle() {  # đếm một lần làm lại cho mỗi verdict khác nhau; trả về số lần
  local f="$1" key; key="$f $(verdict_field "$f" commit) $(verdict_field "$f" verdict)"
  if ! grep -qxF "$key" "$AP/counted"; then
    echo "$key" >> "$AP/counted"
    echo $(( $(cat "$AP/cycles/$f" 2>/dev/null || echo 0) + 1 )) > "$AP/cycles/$f"
  fi
  cat "$AP/cycles/$f"
}

# ---------- chạy một phiên Claude ----------
render() {  # thay {{KEY}} bằng biến môi trường P_KEY
  python3 - "$1" <<'PY'
import os, re, sys
t = open(sys.argv[1], encoding="utf-8").read()
print(re.sub(r"\{\{(\w+)\}\}", lambda m: os.environ.get("P_" + m.group(1), ""), t))
PY
}

# ---------- gói Max: khung giờ, tạm dừng, hết lượt ----------
stage_model() {  # $1 giai đoạn
  if [ "$STRONG_STAGES" = "all" ] || [[ " $STRONG_STAGES " == *" $1 "* ]]; then echo "$MODEL_STRONG"; else echo "$MODEL"; fi
}

secs_left_in_window() {  # in ra số giây còn lại trong RUN_WINDOW; 0 nếu đang ngoài khung; rất lớn nếu không đặt khung
  [ -z "$RUN_WINDOW" ] && { echo 999999999; return; }
  python3 - "$RUN_WINDOW" <<'PY'
import sys, datetime as dt
s, e = (int(x) % 24 for x in sys.argv[1].split("-"))  # "0-24" = cả ngày
now = dt.datetime.now()
def at(h, day=0):
    return (now + dt.timedelta(days=day)).replace(hour=h, minute=0, second=0, microsecond=0)
inside = (s <= now.hour < e) if s < e else (now.hour >= s or now.hour < e)
if not inside:
    print(0)
else:
    end = at(e) if now < at(e) else at(e, 1)
    print(int((end - now).total_seconds()))
PY
}

wait_until_allowed() {  # chờ khi PAUSE hoặc ngoài khung giờ
  local said=""
  while :; do
    [ -f "$AP/HALT" ] && { log "Đang HALT: $(cat "$AP/HALT")"; exit 2; }
    if [ -f "$AP/PAUSE" ]; then
      [ "$said" = pause ] || { log "⏸ đang tạm dừng (xóa .autopilot/PAUSE hoặc chạy 'resume')"; said=pause; }
      sleep 60; continue
    fi
    if [ "$(secs_left_in_window)" -le 300 ]; then
      [ "$said" = window ] || { log "🌙 ngoài khung giờ chạy $RUN_WINDOW, chờ…"; said=window; }
      sleep 300; continue
    fi
    return
  done
}

limit_check() {  # $1 log phiên -> in "LIMIT <epoch reset>" | "AUTH" | "APIKEY" | ""
  python3 - "$1" "$LIMIT_FALLBACK_WAIT" <<'PY'
import json, re, sys, time, datetime as dt
path, fallback = sys.argv[1], int(sys.argv[2])
texts = []
try:
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        try:
            ev = json.loads(line)
        except Exception:
            texts.append(line)  # stderr thô của CLI
            continue
        # chỉ xét sự kiện lỗi / kết quả, không xét nội dung agent viết ra
        if ev.get("type") == "result" and (ev.get("is_error") or ev.get("subtype") != "success"):
            texts.append(str(ev.get("result", "")) + " " + str(ev.get("subtype", "")))
        elif ev.get("type") in ("error", "system") and "error" in json.dumps(ev).lower():
            texts.append(json.dumps(ev, ensure_ascii=False))
        elif ev.get("type") == "assistant" and ev.get("error"):
            texts.append(json.dumps(ev, ensure_ascii=False))
except FileNotFoundError:
    pass
blob = "\n".join(texts[-40:])
low = blob.lower()
if re.search(r"credit balance|invalid api key|x-api-key", low):
    print("APIKEY"); sys.exit()
if re.search(r"/login|oauth token|authentication_error|not logged in|please log in", low):
    print("AUTH"); sys.exit()
if not re.search(r"usage limit|hit your (usage )?limit|limit reached|rate_limit|rate limit|weekly limit|session limit|limit will reset|resets? (at )?\d", low):
    print(""); sys.exit()
now = time.time()
m = re.search(r"\|(\d{10})\b", blob)                     # "…limit reached|1763712000"
if m:
    print("LIMIT", int(m.group(1)) + 120); sys.exit()
m = re.search(r"resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", low)  # "resets 3pm" / "resets 15:00"
if m:
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3)
    if ap == "pm" and h < 12: h += 12
    if ap == "am" and h == 12: h = 0
    t = dt.datetime.now().replace(hour=h % 24, minute=mi, second=0, microsecond=0)
    if t.timestamp() <= now: t += dt.timedelta(days=1)
    # hạn mức tuần có thể ghi ngày ("resets Nov 24") -> regex trên không khớp, dùng fallback
    print("LIMIT", int(t.timestamp()) + 120); sys.exit()
print("LIMIT", int(now) + fallback)
PY
}

run_stage() {  # $1 tên giai đoạn, $2 tệp lời nhắc, $3 FEAT/RELEASE
  local waits=0
  while :; do
    wait_until_allowed
    local n; n=$(( $(wc -l < "$AP/runs") + 1 ))
    [ "$n" -gt "$MAX_RUNS" ] && halt "đã chạm trần MAX_RUNS=$MAX_RUNS phiên"
    echo "$1 $3" >> "$AP/runs"

    local prompt logf before after model tmo left
    prompt="$(render "$AP/prompts/$2")"
    logf="$AP/logs/$(date '+%Y%m%d-%H%M%S')-$3-$1.jsonl"
    before="$(git rev-parse HEAD)"
    model="$(stage_model "$1")"
    # không cho phiên chạy lố khung giờ: thời gian tối đa = min(STAGE_TIMEOUT, thời gian còn lại của khung)
    tmo="$STAGE_TIMEOUT"; left="$(secs_left_in_window)"
    if [ "$left" -lt 999999999 ]; then tmo="${left}s"; fi
    log "▶ phiên #$n: $1 $3 ($model, tối đa $tmo)"

    env -u ANTHROPIC_API_KEY AUTOPILOT_STAGE="$1" AUTOPILOT_FEAT="$3" \
    timeout "$tmo" claude -p "$prompt" \
        --model "$model" \
        --max-turns "$MAX_TURNS" \
        --dangerously-skip-permissions \
        --output-format stream-json --verbose \
        < /dev/null > "$logf" 2>&1
    local rc=$?
    autocommit_push "$1" "$3"
    after="$(git rev-parse HEAD)"

    local lim; lim="$(limit_check "$logf")"
    case "$lim" in
      APIKEY) halt "CLI đang dùng API key thay vì gói Max (xem $logf). Chạy 'claude' rồi /login bằng tài khoản Max" ;;
      AUTH)   halt "Claude chưa đăng nhập hoặc phiên đăng nhập hết hạn (xem $logf). Chạy 'claude' rồi /login" ;;
      LIMIT*)
        # hết lượt: không tính phiên này, không tính là kẹt; chờ reset rồi chạy lại giai đoạn
        sed -i '$ d' "$AP/runs"
        waits=$((waits + 1))
        [ "$waits" -gt "$MAX_LIMIT_WAITS" ] && halt "đã chờ hết lượt $MAX_LIMIT_WAITS lần liền ở $1 $3"
        local until_ts="${lim#LIMIT }"
        log "⏳ $1 $3: hết hạn mức Max, chờ tới $(date -d "@$until_ts" '+%F %T') rồi chạy lại"
        while [ "$(date +%s)" -lt "$until_ts" ]; do
          [ -f "$AP/HALT" ] && exit 2
          sleep 60
        done
        continue ;;
    esac

    if [ "$rc" -eq 124 ] && [ "$tmo" != "$STAGE_TIMEOUT" ]; then
      log "■ $1 $3 bị dừng vì hết khung giờ $RUN_WINDOW (việc dở đã được lưu)"
      sed -i '$ d' "$AP/runs"
      continue   # wait_until_allowed sẽ chờ tới đêm sau rồi chạy lại giai đoạn này
    fi

    log "■ $1 $3 xong (mã thoát $rc, $( [ "$before" = "$after" ] && echo 'không có commit mới' || echo "HEAD $after"))"
    [ "$before" = "$after" ] && return 10
    return 0
  done
}

# ---------- vòng đời một FEAT ----------
build_feat() {  # $1 FEAT, $2 phụ thuộc
  local f="$1" deps="$2" stuck=0 last="" st
  IFS=',' read -ra D <<< "$deps"
  for dep in "${D[@]}"; do
    if is_blocked "$dep"; then mark_blocked "$f" "chờ $dep (đang BLOCKED)"; return; fi
    is_done "$dep" || { log "$f: $dep chưa xong, bỏ qua lượt này"; return; }
  done

  while true; do
    checkout_feat "$f"
    st="$(next_stage "$f")"
    case "$st" in
      done)      log "✔ $f DONE"; return ;;
      blocked)   log "✖ $f BLOCKED"; return ;;
      reqdefect) mark_blocked "$f" "requirement-defect: $(verdict_field "$f" reasons | head -3 | tr '\n' ' ')"; return ;;
    esac

    if [ "$st" = "rework" ] || [ "$st" = "redesign" ]; then
      local c; c="$(count_cycle "$f")"
      if [ "$c" -gt "$MAX_CYCLES" ]; then mark_blocked "$f" "quá $MAX_CYCLES lần làm lại"; return; fi
    fi

    export P_FEAT="$f" P_ATTEMPT="$(( $(cat "$AP/cycles/$f" 2>/dev/null || echo 0) + 1 ))"
    export P_REWORK_CONTEXT="" P_DEFECT_CONTEXT=""
    case "$st" in
      design)    run_stage design    10-design.md    "$f" ;;
      ui)        run_stage ui        20-ui.md        "$f" ;;
      implement) run_stage implement 30-implement.md "$f" ;;
      verify)    run_stage verify    40-verify.md    "$f" ;;
      integrate) run_stage integrate 50-integrate.md "$f" ;;
      rework)
        P_REWORK_CONTEXT="
LÀM LẠI theo kết luận kiểm định (docs/features/$f/acceptance.md). Lý do:
$(verdict_field "$f" reasons)
Trước tiên thêm vào cuối tasks.md (trước task 'Kiểm toàn bộ', và bỏ đánh dấu task đó) các task R01, R02… cho từng lý do, rồi làm như bình thường."
        export P_REWORK_CONTEXT
        run_stage implement 30-implement.md "$f" ;;
      redesign)
        P_DEFECT_CONTEXT="
THIẾT KẾ BỊ KẾT LUẬN SAI (design-defect). Lý do:
$(verdict_field "$f" reasons)
Sửa technical-design.md (và ui-design.md nếu cần), ghi mục 'Sửa sau kiểm định'. Thêm task mới chưa đánh dấu vào tasks.md cho phần phải làm lại; bỏ đánh dấu task 'Kiểm toàn bộ'. Không xóa task đã làm."
        export P_DEFECT_CONTEXT
        run_stage design 10-design.md "$f" ;;
    esac
    local rc=$?

    # chống kẹt: cùng giai đoạn chạy 2 lần liền mà không có commit mới
    if [ "$rc" -eq 10 ] && [ "$st" = "$last" ]; then stuck=$((stuck + 1)); else stuck=0; fi
    last="$st"
    if [ "$stuck" -ge 1 ]; then mark_blocked "$f" "kẹt ở giai đoạn $st (không tiến triển)"; return; fi
  done
}

done_count() { local n=0; while IFS='|' read -r f _ _; do [[ "$f" =~ ^FEAT ]] && is_done "$f" && n=$((n+1)); done < "$AP/build-order.txt"; echo $n; }

status() {
  git fetch -q origin
  printf '%-9s %-3s %-10s %s\n' FEAT REL TRẠNG_THÁI "LẦN_LÀM_LẠI"
  while IFS='|' read -r f r _; do
    [[ "$f" =~ ^FEAT ]] || continue
    local s="chờ"; is_done "$f" && s="DONE"; is_blocked "$f" && s="BLOCKED"
    [ "$s" = "chờ" ] && [ -n "$(feat_remote_branch "$f")" ] && s="đang làm"
    printf '%-9s %-3s %-10s %s\n' "$f" "$r" "$s" "$(cat "$AP/cycles/$f" 2>/dev/null || echo 0)"
  done < "$AP/build-order.txt"
  [ -f "$AP/HALT" ] && echo "HALT: $(cat "$AP/HALT")"
  echo "Số phiên đã chạy: $(wc -l < "$AP/runs") / $MAX_RUNS"
}

# ---------- chương trình chính ----------
case "${1:-run}" in
  status) status; exit 0 ;;
  unhalt) rm -f "$AP/HALT"; echo "Đã gỡ HALT"; exit 0 ;;
  pause)  touch "$AP/PAUSE"; echo "Sẽ tạm dừng trước phiên kế tiếp (phiên đang chạy không bị ngắt)"; exit 0 ;;
  resume) rm -f "$AP/PAUSE"; echo "Đã bỏ tạm dừng"; exit 0 ;;
  run) ;;
  *) echo "Lệnh không hợp lệ: $1"; exit 1 ;;
esac

[ -f "$AP/HALT" ] && { echo "Đang HALT: $(cat "$AP/HALT"). Xử lý xong thì chạy: $0 unhalt"; exit 2; }
command -v claude >/dev/null || halt "chưa cài Claude Code CLI"
command -v gh >/dev/null     || halt "chưa cài GitHub CLI (gh)"
[ -d "$BENCH_DIR" ]          || halt "không thấy bench ở $BENCH_DIR"
if [ -n "${ANTHROPIC_API_KEY:-}" ] && [ "${ALLOW_API_KEY:-0}" != "1" ]; then
  echo "ANTHROPIC_API_KEY đang được đặt: autopilot chạy bằng gói Max nên sẽ bỏ qua khóa này cho mọi phiên."
  echo "Muốn dùng API key thật thì đặt ALLOW_API_KEY=1 và sửa run_stage (bỏ 'env -u ANTHROPIC_API_KEY')."
fi

log "=== Autopilot bắt đầu (model $MODEL, mạnh $MODEL_STRONG cho: $STRONG_STAGES, khung giờ: ${RUN_WINDOW:-cả ngày}) ==="
sync_develop

# 0. Walking skeleton
until is_done FEAT-000; do
  export P_FEAT=FEAT-000
  run_stage bootstrap 00-bootstrap.md FEAT-000
  sync_develop
  if ! is_done FEAT-000 && [ "$(grep -c '^bootstrap' "$AP/runs")" -ge 3 ]; then halt "bootstrap chưa xong sau 3 phiên"; fi
done

# 1. Từng bản phát hành, từng FEAT theo thứ tự
last_verify=$(done_count)
for rel in $RELEASES; do
  log "=== Bản phát hành $rel ==="
  while IFS='|' read -r f r deps; do
    [[ "$f" =~ ^FEAT ]] && [ "$r" = "$rel" ] || continue
    build_feat "$f" "$deps"
    sync_develop
    if [ $(( $(done_count) - last_verify )) -ge "$VERIFY_EVERY" ]; then
      run_stage pipeline-verify 95-pipeline-verify.md "PIPELINE"; sync_develop; last_verify=$(done_count)
    fi
  done < "$AP/build-order.txt"

  # lượt hai: FEAT bị bỏ qua vì phụ thuộc chưa xong ở lượt một
  while IFS='|' read -r f r deps; do
    [[ "$f" =~ ^FEAT ]] && [ "$r" = "$rel" ] || continue
    is_done "$f" || is_blocked "$f" || { build_feat "$f" "$deps"; sync_develop; }
  done < "$AP/build-order.txt"

  export P_RELEASE="$rel" P_RELEASE_LOWER="$(echo "$rel" | tr 'R' 'r')" P_TAG="v${rel#R}.0.0"
  run_stage release 90-release.md "$rel"
  sync_develop
done

run_stage pipeline-verify 95-pipeline-verify.md "PIPELINE"; sync_develop
run_stage report 99-report.md "REPORT"; sync_develop
log "=== Autopilot kết thúc. Xem docs/BUILD-REPORT.md ==="
status
