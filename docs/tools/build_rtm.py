"""Sinh docs/rtm.md va docs/verification-report.md cho bo tai lieu Normcore (ban 1.1).

Chay:  python3 build_rtm.py <thu muc docs>
Doc:   srs.md, use-cases.md, architecture.md, ux-foundations.md, implementation-plan.md, test-cases.md,
       data-model.md, design.md
Ghi:   rtm.md, verification-report.md (GHI DE). Chi dung thu vien chuan cua Python 3.

Tep nay duoc viet lai o ban 1.1: script cua ban 1.0 khong nam trong kho tai lieu. Bang BASELINE ben
duoi chep ba cot Use case, Design ref, Plan ref cua rtm.md 1.0 de so: moi khac biet o yeu cau cu duoc
in ra man hinh va ghi vao bao cao kiem tra.
"""
import re, sys, collections, datetime

d = sys.argv[1] if len(sys.argv) > 1 else "."
def rd(name): return open(f"{d}/{name}", encoding="utf-8").read()
srs, ucs_t, arch, ux, plan, tests = (rd(n) for n in ("srs.md", "use-cases.md", "architecture.md",
                                     "ux-foundations.md", "implementation-plan.md", "test-cases.md"))
others = {n: rd(n) for n in ("data-model.md", "design.md")}
VERSION = re.search(r"Version:\s*([\d.]+)", srs).group(1)
# Ghi tay: cap nhat dong nay moi lan dung hinh thu cac khoi Mermaid bang mmdc (mermaid-cli).
MERMAID_RENDER_NOTE = ("Lần dựng hình thử gần nhất bằng `mmdc` (mermaid-cli): 13/11/2026, bản 1.1, 17 khối, không lỗi. "
                       "Khi sửa sơ đồ, dựng hình thử lại và cập nhật dòng này trong script.")

# ---------- 1. Yeu cau trong SRS ----------
req = collections.OrderedDict()
for m in re.finditer(r"^\|\s*(FR-([A-Z]+)-(\d+))\s*\|(.*?)\|\s*(Must|Should|Could)\s*\|\s*(\w+)\s*\|(.*)$", srs, re.M):
    req[m.group(1)] = dict(kind="FR", group=m.group(2), no=int(m.group(3)), text=m.group(4).strip(),
                           prio=m.group(5), status=m.group(6), row=m.group(0))
for m in re.finditer(r"^\|\s*(NFR-([A-Z]+)-(\d+))\s*\|[^|]*\|(.*?)\|\s*(Must|Should|Could)\s*\|.*$", srs, re.M):
    req[m.group(1)] = dict(kind="NFR", group=m.group(2), no=int(m.group(3)), text=m.group(4).strip(),
                           prio=m.group(5), status="Active", row=m.group(0))
FR = [i for i, r in req.items() if r["kind"] == "FR"]; NFR = [i for i, r in req.items() if r["kind"] == "NFR"]
groups = list(collections.OrderedDict((req[i]["group"], 1) for i in FR))
BR = re.findall(r"^\|\s*(BR-[A-Z]+-\d+)\s*\|", srs, re.M)
TBD = re.findall(r"^\|\s*(TBD-\d+)\s*\|", srs, re.M)

OLD_MAX = dict(ACC=6, LIB=12, SVC=7, PROC=13, AI=15, WF=13, RES=15, NORM=16, TS=5, ACCT=11, COST=16,
               BM=8, ADJ=10, PRICE=10, OUT=10, AUD=4, NOTI=3, ADM=5)          # ma lon nhat cua SRS 1.0
OLD_NFR_NEW = {"NFR-REL-003", "NFR-CPL-003"}
is_new = lambda i: (req[i]["no"] > OLD_MAX.get(req[i]["group"], 0)) if req[i]["kind"] == "FR" else i in OLD_NFR_NEW
NEW = [i for i in req if is_new(i)]
MODIFIED = [i for i in req if not is_new(i) and "Sửa ở 1.1" in req[i]["row"]] + ["FR-COST-014"]

# ---------- 2. Nguon (cot Source) ----------
SRC_GROUP = dict(ACC="BA đề xuất (yêu cầu nền của hệ thống)", AUD="BA đề xuất (yêu cầu nền của hệ thống)",
                 NOTI="BA đề xuất (yêu cầu nền của hệ thống)", ADM="BA đề xuất (yêu cầu nền của hệ thống)",
                 AI="REF-01; ràng buộc C-04, C-08", ACCT="REF-01; ràng buộc C-03, C-07")
SRC_REF03 = {"FR-RES-003", "FR-NORM-006", "FR-NORM-013", "FR-BM-008", "FR-ADJ-001", "FR-ADJ-003"} | \
            {f"FR-OUT-{n:03d}" for n in range(1, 10)}                           # nhu rtm.md 1.0
SRC_NFR = {"NFR-REL-001": "REF-01 (có giải trình)", "NFR-SEC-005": "REF-01 mục 12; ràng buộc C-08",
           "NFR-CMP-001": "Ràng buộc C-01, C-02", "NFR-CPL-001": "REF-01 (tính đúng, tính đủ, có giải trình)",
           "NFR-CPL-002": "REF-03", "NFR-MNT-002": "Ràng buộc C-06", "NFR-MNT-003": "Ràng buộc C-05"}
def source(i):
    r = req[i]
    if is_new(i):
        return "REF-08; REF-09" + ("; REF-10" if "REF-10" in r["row"] else "")
    if r["kind"] == "NFR":
        return SRC_NFR.get(i, "BA đề xuất, chờ chủ dự án xác nhận")
    return SRC_GROUP.get(r["group"], "REF-01") + ("; REF-03" if i in SRC_REF03 else "")

# ---------- 3. Thu thap truy vet ----------
def expand(text):
    """FR-COST-017..025, FR-QC-004 -> tap ma day du."""
    out = set()
    for m in re.finditer(r"\b((?:FR|NFR)-[A-Z]+-)(\d{3})(?:\.\.(\d{3}))?", text):
        a = int(m.group(2)); b = int(m.group(3) or a)
        out.update(f"{m.group(1)}{k:03d}" for k in range(a, b + 1))
    return out

def blocks(text, head_re):
    """[(ma, than khoi)] theo tieu de cap 3."""
    parts = re.split(r"(?m)^### ", text)[1:]
    return [(m.group(1), p) for p in parts for m in [re.match(head_re, p)] if m]

uc, adr, feat, tc = (collections.defaultdict(list) for _ in range(4))
UC = [i for i, _ in blocks(ucs_t, r"(UC-\d{3})")]
for i, body in blocks(ucs_t, r"(UC-\d{3})"):
    for line in body.splitlines():
        if "Traces to" in line:
            for r in sorted(expand(line)): uc[r].append(i)
ADR = [i for i, _ in blocks(arch, r"(ADR-\d{3})")]
for i, body in blocks(arch, r"(ADR-\d{3})"):
    for line in body.splitlines():
        if "Requirements addressed" in line:
            for r in sorted(expand(line)): adr[r].append(i)
FEAT, feat_scr, feat_frs = [], {}, {}
for line in plan.splitlines():
    m = re.match(r"\|\s*(FEAT-\d{3})[^|]*\|[^|]*\|([^|]*)\|[^|]*\|([^|]*)\|", line)
    if m:
        f = m.group(1); FEAT.append(f); feat_frs[f] = expand(m.group(2)); feat_scr[f] = set(re.findall(r"SCR-DSK-\d{3}", m.group(3)))
        for r in sorted(feat_frs[f]): feat[r].append(f)
found = re.search(r"(?ms)^## 6\. Engineering Foundations(.*?)^\*\*Mẫu tài liệu As-Built", plan).group(1)
FOUND = expand(found)
SCR = re.findall(r"^\|\s*(SCR-DSK-\d{3})", ux, re.M)
TC, tc_rows = [], []
for m in re.finditer(r"^\|\s*(TC-[A-Z]+-\d{2})\s*\|([^|]*)\|\s*(FEAT-\d{3}|Foundations)\s*\|", tests, re.M):
    TC.append(m.group(1)); tc_rows.append((m.group(1), expand(m.group(2)), m.group(3)))
    for r in sorted(expand(m.group(2))): tc[r].append(m.group(1))

def plan_ref(i):
    if feat[i]: return ", ".join(feat[i])
    return "Foundations" if i in FOUND else "_TBD_"
cell = lambda lst: ", ".join(lst) if lst else "_TBD_"
def short(s, n=78): return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"

# ---------- 4. So voi rtm.md 1.0 ----------
BASELINE = """
ACC-001..006|017|-|001
LIB-001..002|001|-|020
LIB-003|001|009|020
LIB-004..006|001|-|020
LIB-007..009|002|-|021
LIB-010|001|006|020
LIB-011..012|001|-|020
SVC-001|003|012|005
SVC-002..004|003|-|005
SVC-005..007|003|006|022
PROC-001..002|004|-|006
PROC-003..004|005|002|006
PROC-005|005|-|006
PROC-006|005|002|006
PROC-007|005|010|006
PROC-008|005,006|-|007
PROC-009|005|014|006
PROC-010..011|006|015|007
PROC-012|006|-|007
PROC-013|005|-|006
AI-001|004|006|024
AI-002|004|007|024
AI-003..004|004|-|024
AI-005|004|007|024
AI-006|005|-|025
AI-007|009|-|025
AI-008|004,009|007|024
AI-009..010|004|005|023
AI-011|004|007,008|023
AI-012..013|017|005|023
AI-014|017|-|023
AI-015|004,017|005|023
WF-001..005|006|011|007
WF-006|006|-|007
WF-007|006|011|007
WF-008|006|-|007
WF-009|002,007|-|008
WF-010|007|-|008
WF-011|007|002|008
WF-012|007|-|008
WF-013|006|-|007
RES-001..002|008|-|009
RES-003..004|008,012|-|009
RES-005..006|008|-|010
RES-007|008,012|-|010
RES-008|008|-|010
RES-009..011|008|-|011
RES-012|008|012|009,010,011
RES-013..014|008|-|009
RES-015|008|-|011
NORM-001|009|002|012
NORM-002..014|009|-|012
NORM-015|009|002|013
NORM-016|009|010|012
TS-001..005|010|-|014
ACCT-001..002|011|012|016
ACCT-003..004|011|013|016
ACCT-005..006|011|-|016
ACCT-007|011|012|016
ACCT-008|011|-|016
ACCT-009|011|013|016
ACCT-010..011|011|-|016
COST-001..002|012|-|015
COST-003|012|003|015
COST-004..005|012|003|017
COST-006|012|003|015
COST-007|012|-|015
COST-008..009|012|-|017
COST-010|012|-|015
COST-011..012|012|004|018
COST-013|012|-|018
COST-014|012|-|017
COST-015|012|009|015
COST-016|012|-|015
BM-001|013|-|026
BM-002|013|012|026
BM-003|013|-|027
BM-004..008|013|-|026
ADJ-001..004|014|-|028
ADJ-005|014|008|028
ADJ-006..007|014|008|029
ADJ-008|014|-|028
ADJ-009|014|-|029
ADJ-010|014|010|028
PRICE-001..003|015|-|030
PRICE-004..005|015|011|030
PRICE-006..008|015|-|030
PRICE-009|015|011|030
PRICE-010|015|-|030
OUT-001..006|016|015|019
OUT-007|016|015|030
OUT-008|016|015|019
OUT-009|016|009|019
OUT-010|018|-|002
AUD-001..003|018|014|003
AUD-004|016|014|003
NOTI-001|002,006|011|002
NOTI-002|006|-|002
NOTI-003|018|-|002
ADM-001|017|-|F
ADM-002|008|012|004
ADM-003|017|-|002
ADM-004|017|-|001
ADM-005|008|-|001
N:PERF-001||-|-
N:PERF-002||003,009|-
N:PERF-003||-|-
N:PERF-004||009|-
N:PERF-005||006|-
N:SCAL-001..002||-|-
N:AVL-001||016|-
N:AVL-002||016|F
N:REL-001||003,004|-
N:REL-002||003|-
N:SEC-001||016|F
N:SEC-002||-|F
N:SEC-003||016|F
N:SEC-004||005|-
N:SEC-005||007|-
N:SEC-006||014|-
N:USE-001||010|F
N:USE-002..003||010|-
N:USE-004||-|-
N:CMP-001||001|-
N:CPL-001||002|-
N:CPL-002||015|-
N:MNT-001||003|F
N:MNT-002||-|F
N:MNT-003||001|F
N:LOC-001||-|F
N:OBS-001||009|F
N:OBS-002||-|F
"""
def _lst(s, pre):
    if s in ("", "-"): return []
    return ["Foundations" if x == "F" else f"{pre}-{x}" for x in s.split(",")]
base = {}
for line in BASELINE.split():
    ident, u, a, p = line.split("|")
    kind = "NFR" if ident.startswith("N:") else "FR"; ident = ident[2:] if kind == "NFR" else ident
    g, rng = ident.split("-"); lo, _, hi = rng.partition(".."); hi = hi or lo
    for k in range(int(lo), int(hi) + 1):
        base[f"{kind}-{g}-{k:03d}"] = (_lst(u, "UC"), _lst(a, "ADR"), _lst(p, "FEAT"))
changes, lost = [], []
for i in req:
    if is_new(i): continue
    if i not in base: lost.append(f"{i}: khong co trong bang doi chieu 1.0"); continue
    now = (uc[i], adr[i], feat[i] or (["Foundations"] if i in FOUND else []))
    for col, b, n in zip(("Use case", "Design ref", "Plan ref"), base[i], now):
        add, rem = [x for x in n if x not in b], [x for x in b if x not in n]
        if rem: lost.append(f"{i}: cot {col} mat {', '.join(rem)}")
        if add: changes.append((i, col, add))
for i in base:
    if i not in req: lost.append(f"{i}: co o 1.0 nhung khong con trong SRS")

# ---------- 5. Kiem tra ----------
problems, notes = list(lost), []
defined = dict(FR=set(FR), NFR=set(NFR), BR=set(BR), TBD=set(TBD), UC=set(UC), ADR=set(ADR), SCR=set(SCR),
               FEAT=set(FEAT), TC=set(TC))
docs = {"srs.md": srs, "use-cases.md": ucs_t, "architecture.md": arch, "ux-foundations.md": ux,
        "implementation-plan.md": plan, "test-cases.md": tests, **others}
PAT = dict(BR=r"\bBR-[A-Z]+-\d{3}\b", TBD=r"\bTBD-\d{2}\b", UC=r"\bUC-\d{3}\b", ADR=r"\bADR-\d{3}\b",
           SCR=r"\bSCR-DSK-\d{3}\b", FEAT=r"\bFEAT-\d{3}\b", TC=r"\bTC-[A-Z]+-\d{2}\b")
dangling = []
for name, t in docs.items():
    for x in sorted(expand(t)):
        if x not in defined["FR"] and x not in defined["NFR"]: dangling.append(f"{name}: {x}")
    for k, p in PAT.items():
        for x in sorted(set(re.findall(p, t)) - defined[k]): dangling.append(f"{name}: {x}")
for m in re.finditer(r"(TC-[A-Z]+)-(\d{2}) đến TC-[A-Z]+-(\d{2})", plan):       # dai ma "TC-CLS-01 den TC-CLS-15"
    for k in range(int(m.group(2)), int(m.group(3)) + 1):
        if f"{m.group(1)}-{k:02d}" not in defined["TC"]: dangling.append(f"implementation-plan.md: {m.group(1)}-{k:02d}")
problems += [f"Mã được dẫn nhưng không tồn tại: {x}" for x in dangling]
for name, ids in (("FR", FR + NFR), ("UC", UC), ("ADR", ADR), ("SCR", SCR), ("FEAT", FEAT), ("TC", TC), ("BR", BR), ("TBD", TBD)):
    dup = [k for k, v in collections.Counter(ids).items() if v > 1]
    if dup: problems.append(f"Mã {name} bị định nghĩa trùng: {', '.join(dup)}")
no_uc = [i for i in FR if not uc[i]]
must_no_plan = [i for i in FR if req[i]["prio"] == "Must" and plan_ref(i) == "_TBD_"]
no_plan = [i for i in FR if plan_ref(i) == "_TBD_"]
scr_in_feat = set().union(*feat_scr.values())
scr_orphan = [s for s in SCR if s not in scr_in_feat]
for lst, msg in ((no_uc, "FR chưa có use case"), (no_plan, "FR chưa có Plan ref"), (scr_orphan, "Màn hình chưa thuộc tính năng nào")):
    if lst: problems.append(f"{msg}: {', '.join(lst)}")

# do thi phu thuoc va thu tu xay
seq = {}
for m in re.finditer(r"^\|\s*(\d+)(a?)\s*(?:\*\*\[1\.1\]\*\*)?\s*\|([^|]*)\|", re.search(r"(?ms)^## 4\. Build Sequence(.*?)^```mermaid", plan).group(1), re.M):
    for f in re.findall(r"FEAT-\d{3}", m.group(3)): seq[f] = int(m.group(1)) + (0.5 if m.group(2) else 0)
graph_txt = re.search(r"(?ms)^## 4\. Build Sequence.*?```mermaid(.*?)```", plan).group(1)
nodes = {f"FEAT-{n}" for n in re.findall(r"^\s*F(\d{3})\[", graph_txt, re.M)}
edges = [(f"FEAT-{a}", f"FEAT-{b}") for a, b in re.findall(r"F(\d{3})\s*-->\s*F(\d{3})", graph_txt)]
indeg = collections.Counter(b for _, b in edges); queue = [n for n in nodes if not indeg[n]]; seen = 0
while queue:
    n = queue.pop(); seen += 1
    for a, b in edges:
        if a == n:
            indeg[b] -= 1
            if not indeg[b]: queue.append(b)
graph_ok = nodes == set(FEAT) and seen == len(nodes)
if not graph_ok: problems.append(f"Đồ thị phụ thuộc: {len(nodes)} nút so với {len(FEAT)} tính năng, hoặc có chu trình")
order_bad = [f"{a} (bước {seq.get(a)}) phải trước {b} (bước {seq.get(b)})" for a, b in edges if seq.get(a, 99) > seq.get(b, -1)]
order_bad += [f"{f} không có trong thứ tự xây" for f in FEAT if f not in seq]
first = re.search(r"(?m)^## 5\. First Vertical Slice\s*\n\s*\n\*\*(FEAT-\d{3})", plan)
first_ok = bool(first) and seq.get(first.group(1)) == 1
problems += [f"Thứ tự xây: {x}" for x in order_bad]
if not first_ok: problems.append("Lát cắt đầu tiên không ở bước 1")

# mermaid
mm_bad, mm_count = [], 0
for name, t in docs.items():
    if t.count("```") % 2: mm_bad.append(f"{name}: khối mã chưa đóng")
    for blk in re.findall(r"(?s)```mermaid(.*?)```", t):
        mm_count += 1
        for lab in re.findall(r"\w\[([^\]\n]*)\]", blk):
            lab = lab.strip("()[]{}/\\")                                  # bo ky hieu hinh dang: [("...")], [["..."]]
            if " " in lab and not (lab.startswith('"') and lab.endswith('"')): mm_bad.append(f"{name}: nhãn chưa đặt trong ngoặc kép: {lab[:40]}")
        if re.search(r"(?m)(?:-->\s*end\b|^\s*end\s*[\[\(])", blk): mm_bad.append(f"{name}: có nút tên end")
problems += [f"Mermaid: {x}" for x in mm_bad]

for t_id, frs, f in tc_rows:
    for r in sorted(frs):
        if r in req and req[r]["kind"] == "FR" and f not in feat[r] and f != "Foundations":
            notes.append(f"{t_id}: {r} không thuộc {f} (thuộc {cell(feat[r])})")
must_no_tc = [i for i in FR if req[i]["prio"] == "Must" and not tc[i]]
other_no_tc = [i for i in FR if req[i]["prio"] != "Must" and not tc[i]]
nfr_no_adr = [i for i in NFR if not adr[i]]

# ---------- 6. Ghi rtm.md ----------
today = datetime.date.today().isoformat()
rows = [f"| {i} | {short(r['text'])} | {r['prio']} | {r['status']} | {source(i)} | "
        f"{cell(uc[i]) if r['kind'] == 'FR' else '—'} | {cell(adr[i])} | {plan_ref(i)} | _TBD_ |" for i, r in req.items()]
app = [f"| {i} | {', '.join(tc[i])} |" for i in req if tc[i]]
rng = lambda ids: ", ".join(ids)
rtm = f"""# Requirements Traceability Matrix: Normcore

> Source: docs/srs.md v{VERSION}, docs/use-cases.md v{VERSION} · Last updated: {today}
> Cột Design ref do kiến trúc ghi (ADR có trường "Requirements addressed" dẫn yêu cầu đó); thiết kế chi tiết từng tính năng sẽ ghi nối thêm.
> Cột Plan ref do kế hoạch triển khai ghi (mã tính năng hoặc Foundations). Cột Test ref do giai đoạn kiểm thử ghi khi nghiệm thu; test case dự kiến xem Phụ lục A.
> Tệp này được sinh bằng `docs/tools/build_rtm.py`; chạy lại sau mỗi lần sửa tài liệu nguồn. Không sửa tay.
> Bản {VERSION}: {len(FR)} FR và {len(NFR)} NFR. So với bản 1.0: thêm {len([i for i in NEW if i.startswith('FR')])} FR và {len([i for i in NEW if i.startswith('NFR')])} NFR, sửa {len(MODIFIED)} FR (giữ nguyên mã); danh sách ở Phụ lục B.

| Req ID | Requirement (short) | Priority | Status | Source | Use case(s) | Design ref | Plan ref | Test ref |
| :----- | :------------------ | :------- | :----- | :----- | :---------- | :--------- | :------- | :------- |
{chr(10).join(rows)}

## Phụ lục A — Test case dự kiến theo yêu cầu

Bảng này chỉ để tra cứu; không thay cho cột Test ref.

| Req ID | Test case dự kiến |
| :-- | :-- |
{chr(10).join(app)}

## Phụ lục B — Thay đổi ở bản 1.1

**Yêu cầu mới ({len(NEW)}):** {rng(NEW)}.

**Yêu cầu sửa, giữ nguyên mã ({len(MODIFIED)}):** {rng(MODIFIED)}. Nội dung sửa ghi ở cột ghi chú của `docs/srs.md`.

**Dòng của yêu cầu có từ bản 1.0 được ghi thêm truy vết ở bản 1.1**

| Req ID | Cột | Thêm |
| :-- | :-- | :-- |
{chr(10).join(f"| {i} | {c} | {', '.join(a)} |" for i, c, a in changes) or "| — | — | — |"}

Không dòng nào của bản 1.0 bị bớt truy vết.
"""
open(f"{d}/rtm.md", "w", encoding="utf-8").write(rtm)

# ---------- 7. Ghi verification-report.md ----------
pc = collections.Counter(req[i]["prio"] for i in FR)
ok = lambda cond: "Đạt" if cond else "**Không đạt**"
rep = f"""# Verification Report: bộ tài liệu Normcore

> Sinh bởi `docs/tools/build_rtm.py` ngày {today} cho bản {VERSION}. Kiểm tra cơ học về ID và cấu trúc; không thay cho rà soát nghiệp vụ.

## Số lượng

| Hạng mục | Số lượng | Bản 1.0 |
| :-- | --: | --: |
| Yêu cầu chức năng (FR) | {len(FR)} | 179 |
| trong đó mức Must / Should / Could | {pc['Must']} / {pc['Should']} / {pc['Could']} | 146 / 30 / 3 |
| Nhóm chức năng | {len(groups)} | 18 |
| Yêu cầu phi chức năng (NFR) | {len(NFR)} | 30 |
| Quy tắc nghiệp vụ (BR) | {len(BR)} | 25 |
| Use case | {len(UC)} | 18 |
| ADR | {len(ADR)} | 16 |
| Màn hình (SCR) | {len(SCR)} | 31 |
| Tính năng (FEAT) | {len(FEAT)} | 30 |
| Test case | {len(TC)} | 119 |
| Câu hỏi mở (TBD), kể cả câu đã đóng | {len(TBD)} | 13 |

## Kết quả kiểm tra

| Kiểm tra | Kết quả |
| :-- | :-- |
| Mọi ID được dẫn (FR, NFR, BR, UC, ADR, SCR, FEAT, TC, TBD) đều tồn tại ở tài liệu định nghĩa | {ok(not dangling)} |
| Không mã nào bị định nghĩa trùng | {ok(not any('trùng' in p for p in problems))} |
| Mọi FR có ít nhất một use case | {ok(not no_uc)} |
| Mọi FR mức Must thuộc một tính năng hoặc nền kỹ thuật | {ok(not must_no_plan)} |
| Mọi FR (kể cả Should, Could) đã có Plan ref | {ok(not no_plan)} |
| Mọi màn hình thuộc ít nhất một tính năng | {ok(not scr_orphan)} |
| Đồ thị phụ thuộc: đủ {len(FEAT)} tính năng, không chu trình | {ok(graph_ok)} |
| Thứ tự xây tôn trọng phụ thuộc; lát cắt đầu tiên ở bước 1 | {ok(not order_bad and first_ok)} |
| Khối Mermaid ({mm_count} khối): đóng đủ, nhãn có khoảng trắng nằm trong ngoặc kép, không có nút tên end | {ok(not mm_bad)} |
| Không yêu cầu nào của bản 1.0 bị mất hoặc bị bớt truy vết (use case, ADR, tính năng) so với `rtm.md` 1.0 | {ok(not lost)} |
| Mọi yêu cầu mới của bản 1.1 có use case (FR), tính năng, và test case nếu là Must | {ok(all((uc[i] or i.startswith('NFR')) and plan_ref(i) != '_TBD_' and (tc[i] or req[i]['prio'] != 'Must') for i in NEW))} |

Script chỉ kiểm cú pháp cơ bản của Mermaid. {MERMAID_RENDER_NOTE}

## Vấn đề cần sửa

{chr(10).join('- ' + p for p in problems) or 'Không có.'}

## Khoảng trống đã biết (không chặn bàn giao)

- FR mức Must chưa có test case dự kiến ({len(must_no_tc)}): {rng(must_no_tc) or 'không có'}.
- FR mức Should hoặc Could chưa có test case dự kiến ({len(other_no_tc)}): {rng(other_no_tc) or 'không có'}. Test case cho các FR này được viết khi tính năng tương ứng đến lượt xây.
- NFR chưa có ADR dẫn tới ({len(nfr_no_adr)}): {rng(nfr_no_adr)}. Các NFR này được xử lý ở mục 8 và mục 10 của tài liệu kiến trúc hoặc ở nền kỹ thuật, không cần quyết định kiến trúc riêng.
- Câu hỏi mở ở Phụ lục B của SRS cần người có thẩm quyền chốt; trạng thái từng câu xem tại đó.
- Các tệp bản 1.1 (`srs.md`, `data-model.md`, `use-cases.md`, `architecture.md`, `ux-foundations.md`, `design.md`, `implementation-plan.md`, `test-cases.md`) được soạn lại từ bản 1.0 rồi chèn phần thêm. Script này chỉ so được truy vết theo mã với `rtm.md` 1.0; nó không so từng câu chữ. Khi đưa vào kho mã, nên `git diff` với bản 1.0 để xác nhận phần cũ không đổi ngoài các chỗ mang nhãn [1.1].

## Ghi chú

Các dòng dưới đây không phải lỗi: test case được đặt ở tính năng nơi yêu cầu được kiểm bằng số liệu (thường là tính năng tính giá), còn yêu cầu thuộc tính năng khai báo dữ liệu. Khi lập As-Built, ghi mã test case ở cả hai tính năng.

{chr(10).join('- ' + n for n in notes) or 'Không có.'}
"""
open(f"{d}/verification-report.md", "w", encoding="utf-8").write(rep)

print(f"FR {len(FR)} ({dict(pc)}) | NFR {len(NFR)} | BR {len(BR)} | TBD {len(TBD)} | nhom {len(groups)}")
print(f"UC {len(UC)} | ADR {len(ADR)} | SCR {len(SCR)} | FEAT {len(FEAT)} | TC {len(TC)} | mermaid {mm_count}")
print(f"moi {len(NEW)} | sua {len(MODIFIED)}: {MODIFIED}")
print("THEM TRUY VET O YEU CAU CU:"); [print("  ", c) for c in changes]
print("VAN DE:", len(problems)); [print("  -", p) for p in problems]
print("GHI CHU:"); [print("  -", n) for n in notes]
print("Must chua co TC:", len(must_no_tc), "| moi:", [i for i in must_no_tc if is_new(i)], "| NFR chua co ADR:", nfr_no_adr)
