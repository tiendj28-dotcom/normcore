#!/usr/bin/env bash
# Bot pr-sync (NORM-37): sau mỗi lần develop đổi, gộp develop vào mọi PR mở nhắm develop để PR khác
# không bị conflict khi một PR merge. Chạy trên runner (merge=union của .gitattributes có tác dụng, khác
# nút Merge của GitHub). Dùng bởi .github/workflows/pr-sync.yml.
#
# Môi trường: GH_TOKEN (PAT, để push kích hoạt CI), tùy chọn:
#   PR_SYNC_REMOTE=origin   remote chứa develop và nhánh PR
#   PR_SYNC_BASE=develop    nhánh nền
#   PR_SYNC_LOCAL=1         thử cục bộ: không gọi gh; danh sách nhánh lấy từ PR_SYNC_BRANCHES (cách nhau bởi
#                           dấu cách), nhãn/bình luận chỉ ghi ra stdout
# NORM-60: sau khi gộp develop, mọi bước sinh và kiểm (scripts/pr_sync_fix.py, docs/tools/build_rtm.py,
# scripts/check_conventions.py) chạy bằng script TRONG CÂY ĐÃ GỘP (có thay đổi của cả hai bên), không dùng bản
# chép từ develop: nhánh vừa sửa phần dựng workspace thì bản develop xóa mất phần đó (0d15f23). Chỉ có
# chính pr_sync.sh được chép ra ngoài trước khi checkout nhánh PR (git checkout ghi đè tệp đang chạy).
set -uo pipefail

if [ -z "${PR_SYNC_SELF:-}" ]; then
	SELF="$(mktemp)"
	cp "$0" "$SELF"
	PR_SYNC_SELF="$SELF" exec bash "$SELF" "$@"
fi

REMOTE="${PR_SYNC_REMOTE:-origin}"
BASE="${PR_SYNC_BASE:-develop}"
LABEL="conflict"
LOCAL="${PR_SYNC_LOCAL:-0}"
TOOLS="$(mktemp -d)"
trap 'rm -rf "$TOOLS" "$PR_SYNC_SELF"' EXIT

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

git config user.name >/dev/null || git config user.name "normcore-pr-sync"
git config user.email >/dev/null || git config user.email "pr-sync@users.noreply.github.com"
git fetch -q "$REMOTE" "$BASE"

say() { echo "[pr-sync] $*"; }

label_add() { # PR
	if [ "$LOCAL" = 1 ]; then say "PR $1: gắn nhãn $LABEL"; return; fi
	gh label create "$LABEL" --color D93F0B --description "PR conflict với $BASE, bot không tự gỡ được" >/dev/null 2>&1 || true
	gh pr edit "$1" --add-label "$LABEL" >/dev/null || true
}
label_remove() {
	if [ "$LOCAL" = 1 ]; then say "PR $1: gỡ nhãn $LABEL"; return; fi
	gh pr edit "$1" --remove-label "$LABEL" >/dev/null 2>&1 || true
}
comment() { # PR, file
	if [ "$LOCAL" = 1 ]; then say "PR $1: bình luận:"; sed 's/^/    /' "$2"; return; fi
	gh pr comment "$1" --body-file "$2" >/dev/null || true
}

list_prs() { # in "số<TAB>nhánh" mỗi PR cùng repo, nhắm $BASE
	if [ "$LOCAL" = 1 ]; then
		local n=0
		for b in ${PR_SYNC_BRANCHES:-}; do n=$((n + 1)); printf '%s\t%s\n' "$n" "$b"; done
		return
	fi
	gh pr list --base "$BASE" --state open --limit 100 \
		--json number,headRefName,isCrossRepository,isDraft \
		--jq '.[] | select(.isCrossRepository | not) | [.number, .headRefName] | @tsv'
}

fail_pr() { # PR, nhánh, lý do, tệp...
	local pr="$1" branch="$2" why="$3"
	shift 3
	git merge --abort >/dev/null 2>&1 || true
	local body="$TOOLS/body.md"
	{
		echo "pr-sync: không tự gộp được \`$BASE\` vào \`$branch\`: $why"
		echo
		for f in "$@"; do echo "- \`$f\`"; done
		echo
		echo "Cần người hoặc Dev gỡ: \`git merge $REMOTE/$BASE\`, sửa tệp trên, chạy lại CI."
	} >"$body"
	label_add "$pr"
	comment "$pr" "$body"
	say "PR $pr ($branch): DỪNG, $why"
	STATUS_FAIL=$((STATUS_FAIL + 1))
}

STATUS_FAIL=0
SYNCED=0
SKIPPED=0

while IFS=$'\t' read -r PR BRANCH; do
	[ -n "${PR:-}" ] || continue
	say "PR $PR ($BRANCH)"
	if ! git fetch -q "$REMOTE" "$BRANCH"; then say "  không lấy được nhánh, bỏ qua"; continue; fi
	git merge --abort >/dev/null 2>&1 || true
	git reset -q --hard
	git checkout -q -B "pr-sync/$PR" "$REMOTE/$BRANCH"
	# a) develop đã là tổ tiên: bỏ qua
	if git merge-base --is-ancestor "$REMOTE/$BASE" HEAD; then
		say "  đã chứa $BASE, bỏ qua"
		label_remove "$PR"
		SKIPPED=$((SKIPPED + 1))
		continue
	fi
	# b) gộp develop
	if git merge --no-edit "$REMOTE/$BASE" >"$TOOLS/merge.log" 2>&1; then
		say "  gộp sạch"
	else
		say "  có conflict, thử tệp sinh"
	fi
	# c) sinh và sửa tệp sinh bằng script của cây đã gộp (chạy cả khi gộp sạch)
	python3 scripts/pr_sync_fix.py "$REPO_ROOT" >"$TOOLS/fixed.txt" 2>"$TOOLS/fix.err" || {
		fail_pr "$PR" "$BRANCH" "không sinh lại được tệp sinh ($(head -c 300 "$TOOLS/fix.err"))" "(xem log chạy)"
		continue
	}
	if [ -f docs/tools/build_rtm.py ]; then
		python3 docs/tools/build_rtm.py docs >"$TOOLS/rtm.log" 2>&1 || true
	fi
	UNRESOLVED="$(git diff --name-only --diff-filter=U)"
	# d) còn conflict hoặc check_conventions lỗi: hủy
	if [ -n "$UNRESOLVED" ]; then
		# shellcheck disable=SC2086
		fail_pr "$PR" "$BRANCH" "còn tệp conflict" $UNRESOLVED
		continue
	fi
	if ! python3 scripts/check_conventions.py "$REPO_ROOT" >"$TOOLS/conv.log" 2>&1; then
		mapfile -t LINES <"$TOOLS/conv.log"
		fail_pr "$PR" "$BRANCH" "check_conventions.py báo lỗi sau khi gộp" "${LINES[@]:0:15}"
		continue
	fi
	# e) sạch: thêm tệp sinh vừa sửa, commit, push, gỡ nhãn
	git add -u
	if git rev-parse -q --verify MERGE_HEAD >/dev/null; then
		git commit -q --no-edit
	elif ! git diff --cached --quiet; then
		git commit -q -m "pr-sync: sinh lại tệp sinh sau khi gộp $BASE"
	fi
	if [ "$LOCAL" = 1 ] || git push -q "$REMOTE" "HEAD:refs/heads/$BRANCH"; then
		[ "$LOCAL" = 1 ] && git push -q "$REMOTE" "HEAD:refs/heads/$BRANCH"
		say "  đã đẩy $(git rev-parse --short HEAD) lên $BRANCH"
		label_remove "$PR"
		SYNCED=$((SYNCED + 1))
	else
		fail_pr "$PR" "$BRANCH" "push bị từ chối (nhánh đổi giữa chừng hoặc quyền)" "$BRANCH"
	fi
done < <(list_prs)

say "xong: đồng bộ $SYNCED, đã mới $SKIPPED, cần gỡ tay $STATUS_FAIL"
exit 0
