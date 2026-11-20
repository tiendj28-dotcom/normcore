"""Sinh docs/sua-doi-1.1/rtm.md va kiem tra do phu cho ban sua doi 1.1.
Chay: python3 build_rtm_delta.py <thu muc chua srs.md> <thu muc sua-doi-1.1>"""
import re, sys, collections
srs_dir, d = sys.argv[1], sys.argv[2]
srs = open(f"{srs_dir}/srs.md", encoding="utf-8").read()
OLD_MAX = dict(ACC=6, LIB=12, SVC=7, PROC=13, AI=15, WF=13, RES=15, NORM=16, TS=5, ACCT=11, COST=16,
               BM=8, ADJ=10, PRICE=10, OUT=10, AUD=4, NOTI=3, ADM=5)   # ma lon nhat cua SRS 1.0
MODIFIED = ["FR-ACC-002", "FR-ACC-004", "FR-RES-002", "FR-RES-004", "FR-RES-005", "FR-RES-007",
            "FR-RES-009", "FR-COST-014", "FR-AUD-003"]
NEW_NFR = ["NFR-REL-003", "NFR-CPL-003"]

req = {}
for m in re.finditer(r"^\|\s*(FR-([A-Z]+)-(\d+))\s*\|(.*?)\|\s*(Must|Should|Could)\s*\|\s*(\w+)\s*\|", srs, re.M):
    req[m.group(1)] = dict(group=m.group(2), no=int(m.group(3)), text=m.group(4).strip(), prio=m.group(5), status=m.group(6))
for m in re.finditer(r"^\|\s*(NFR-[A-Z]+-\d+)\s*\|[^|]*\|(.*?)\|\s*(Must|Should|Could)\s*\|", srs, re.M):
    req[m.group(1)] = dict(group="NFR", no=0, text=m.group(2).strip(), prio=m.group(3), status="Active")
new = [i for i, r in req.items() if i.startswith("FR-") and r["no"] > OLD_MAX.get(r["group"], 0)]

def expand(text):
    """FR-COST-017..025, 031, FR-QC-004 -> tap ma day du."""
    out = set()
    for m in re.finditer(r"\b((?:FR|NFR)-[A-Z]+-)(\d{3})((?:(?:\.\.|, )\d{3}(?!\d))*)", text):
        pre, first, rest = m.groups(); nums = [first] + re.findall(r"(\.\.|, )(\d{3})", rest)
        prev = int(first); out.add(f"{pre}{prev:03d}")
        for sep, n in nums[1:]:
            n = int(n)
            if sep == "..":
                out.update(f"{pre}{k:03d}" for k in range(prev, n + 1))
            else:
                out.add(f"{pre}{n:03d}")
            prev = n
    return out

def collect(path, block_re, id_re, line_filter=None):
    """Tra ve {ma yeu cau: [ma tai lieu]} tu cac khoi van ban."""
    t = open(f"{d}/{path}", encoding="utf-8").read(); res = collections.defaultdict(list)
    for blk in re.split(block_re, t)[1:]:
        ident = re.match(id_re, blk)
        if not ident: continue
        body = "\n".join(l for l in blk.splitlines() if (line_filter is None or line_filter(l)))
        for r in expand(body):
            if ident.group(1) not in res[r]: res[r].append(ident.group(1))
    return res

uc = collect("use-cases.md", r"(?m)^### (?=UC-)", r"(UC-\d{3})", lambda l: "Traces to" in l)
adr = collect("architecture-ux.md", r"(?m)^### (?:Sửa )?(?=ADR-)", r"(ADR-\d{3})", lambda l: "Requirements addressed" in l)
for r in ("FR-COST-032",): adr[r].append("ADR-004")
for r in ("FR-CLS-008", "FR-ACCT-013", "FR-ACCT-015"):
    if "ADR-012" not in adr[r]: adr[r].append("ADR-012")
feat, tc = collections.defaultdict(list), collections.defaultdict(list)
plan = open(f"{d}/implementation-plan.md", encoding="utf-8").read()
for line in plan.splitlines():
    m = re.match(r"\|\s*(FEAT-\d{3})[^|]*\|(.*)", line)
    if m:
        cells = m.group(2).split("|")
        src = cells[0] if m.group(1) in ("FEAT-009", "FEAT-010", "FEAT-011") else (cells[2] if len(cells) > 2 else "")
        for r in expand(src):
            if m.group(1) not in feat[r]: feat[r].append(m.group(1))
tests = open(f"{d}/test-cases.md", encoding="utf-8").read()
for m in re.finditer(r"^\|\s*(TC-CLS-\d{2})\s*\|(.*?)\|\s*(FEAT-\d{3})", tests, re.M):
    for r in expand(m.group(2)): tc[r].append(m.group(1))

def cell(lst): return ", ".join(sorted(lst)) if lst else "_TBD_"
def short(s, n=78): return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"
rows, gaps = [], []
for i in sorted(new, key=lambda x: (x.split("-")[1], x)) + NEW_NFR:
    r = req[i]
    rows.append(f"| {i} | {short(r['text'])} | {r['prio']} | Mới | REF-08, REF-09 | {cell(uc[i]) if i.startswith('FR') else '—'} | {cell(adr[i])} | {cell(feat[i])} | {cell(tc[i])} | _TBD_ |")
    if i.startswith("FR") and not uc[i]: gaps.append(f"{i}: thieu use case")
    if not feat[i]: gaps.append(f"{i}: thieu FEAT")
    if r["prio"] == "Must" and not tc[i]: gaps.append(f"{i}: Must thieu test case")
mrows = []
for i in MODIFIED:
    r = req[i]
    same = lambda lst: cell(lst) if lst else "Như 1.0"      # dong sua: chi ghi phan them
    mrows.append(f"| {i} | {short(r['text'])} | {r['prio']} | Sửa | REF-09 | {same(uc[i])} | {same(adr[i])} | {same(feat[i])} | {same(tc[i])} | _TBD_ |")
    if not tc[i] and i != "FR-COST-014": gaps.append(f"{i}: yeu cau sua thieu test case")
# ma tham chieu trong cac tep delta phai ton tai trong SRS 1.1
defined = set(re.findall(r"^\|\s*((?:FR|NFR|BR|TBD)-[A-Z]*-?\d+)\s*\|", srs, re.M))
for f in ("data-model.md", "use-cases.md", "architecture-ux.md", "implementation-plan.md", "test-cases.md"):
    t = open(f"{d}/{f}", encoding="utf-8").read()
    for x in sorted(expand(t) | set(re.findall(r"\b((?:BR|TBD)-[A-Z]*-?\d+)\b", t))):
        if x not in defined: gaps.append(f"{f}: ma khong co trong SRS: {x}")
ucs = set(re.findall(r"^### (UC-\d{3})", open(f"{d}/use-cases.md", encoding="utf-8").read(), re.M))
feats = set(re.findall(r"^\|\s*(FEAT-\d{3})", plan, re.M)); tcs = set(re.findall(r"^\|\s*(TC-CLS-\d{2})", tests, re.M))
for x in re.findall(r"TC-CLS-(\d{2}) đến TC-CLS-(\d{2})", plan):
    for k in range(int(x[0]), int(x[1]) + 1):
        if f"TC-CLS-{k:02d}" not in tcs: gaps.append(f"plan dan TC-CLS-{k:02d} khong ton tai")
for x in set(re.findall(r"TC-CLS-\d{2}", plan)) - tcs: gaps.append(f"plan dan {x} khong ton tai")
for x in set(re.findall(r"UC-0(?:19|2\d)", plan + tests)) - ucs: gaps.append(f"dan {x} khong ton tai")

head = "| Req ID | Requirement (short) | Priority | Thay đổi | Source | Use case(s) | Design ref | Plan ref | Test case | Test ref |\n| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |\n"
out = f"""# Sửa đổi 1.1 — Ma trận truy vết (bổ sung cho `docs/rtm.md` 1.0)

> Phiên bản 1.1-delta · 13/11/2026 · Sinh bằng `docs/sua-doi-1.1/tools-build-rtm-delta.py` từ `docs/srs.md` 1.1 và các tệp trong `docs/sua-doi-1.1/`. Dòng FR-COST-014 có thêm ghi chú viết tay.
> Chỉ gồm yêu cầu **mới** và yêu cầu **sửa** ở bản 1.1. Các dòng khác của `docs/rtm.md` 1.0 giữ nguyên. Cột "Test ref" do bước nghiệm thu ghi.

## 1. Tóm tắt

| Chỉ số | Giá trị |
| :-- | --: |
| Yêu cầu chức năng mới | {len(new)} |
| Yêu cầu phi chức năng mới | {len(NEW_NFR)} |
| Yêu cầu chức năng sửa | {len(MODIFIED)} |
| Yêu cầu mới có use case | {sum(1 for i in new if uc[i])} / {len(new)} |
| Yêu cầu mới có tính năng (FEAT) | {sum(1 for i in new + NEW_NFR if feat[i])} / {len(new) + len(NEW_NFR)} |
| Yêu cầu mới mức Must có test case | {sum(1 for i in new if req[i]['prio'] == 'Must' and tc[i])} / {sum(1 for i in new if req[i]['prio'] == 'Must')} |
| Use case mới, tính năng mới, test case mới | {len(ucs - {'UC-008', 'UC-012'})}, {len(feats - {'FEAT-009', 'FEAT-010', 'FEAT-011'})}, {len(tcs)} |
| Lỗi kiểm tra chéo | {len(gaps)} |

Cột "Design ref" là `_TBD_` ở các yêu cầu chỉ cần thiết kế chi tiết của tính năng, không cần quyết định kiến trúc; cách ghi này giống bản 1.0.

## 2. Yêu cầu mới

{head}{chr(10).join(rows)}

## 3. Yêu cầu sửa

Use case, tính năng và test case ở bảng này là phần **thêm** vào dòng tương ứng của `docs/rtm.md` 1.0.

{head}{chr(10).join(mrows)}
"""
open(f"{d}/rtm.md", "w", encoding="utf-8").write(out)
print("new FR", len(new), "| UC", len(ucs), "| FEAT", len(feats), "| TC", len(tcs))
print("prio new:", collections.Counter(req[i]["prio"] for i in new))
print("GAPS:", len(gaps)); [print(" -", g) for g in gaps]
