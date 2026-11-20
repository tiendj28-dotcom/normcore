"""Normcore - bo du lieu vang (golden dataset) va cai dat tham chieu cua BR-COST-001..016.

Day la DAC TA CHAY DUOC: ma thuan Python, khong phu thuoc frappe. Doi phat trien dung tep nay
lam chuan doi chieu cho normcore/costing/engine.py (ADR-003). Moi so lieu la SO THU NGHIEM,
khong phai so lieu thuc te hay muc quy dinh.

Chay:  python3 golden_engine.py            -> in ket qua mong doi
       python3 golden_engine.py --no-depr  -> bien the loai gia khong ket cau khau hao
"""
from dataclasses import dataclass, field
from decimal import Decimal as D, ROUND_HALF_UP
from datetime import date
import sys

Q2, Q4 = D("0.01"), D("0.0001")
def r2(x): return x.quantize(Q2, rounding=ROUND_HALF_UP)
def r4(x): return x.quantize(Q4, rounding=ROUND_HALF_UP)

# ---------------- Tham so (NC Costing Parameter Set) ----------------
PARAM = dict(base_salary=D("2500000"), contribution=D("0.235"), days=D("264"), hours=D("8"),
             accumulation_mode="ON_COST", accumulation_rate=D("0.05"), obligation_rate=D("0"),
             rounding_unit=D("100"), recon_tolerance=D("10"),
             electricity_price=D("3000"))
COSTING_DATE = date(2026, 12, 31)

# ---------------- Chuc danh (BR-COST-001) ----------------
JOB = {"BS": dict(coef=D("4.40"), allow=D("0.60"), other=D("0")),
       "DD": dict(coef=D("3.00"), allow=D("0.40"), other=D("0"))}
def job_rate(code):
    j = JOB[code]
    annual = PARAM["base_salary"] * (j["coef"] + j["allow"]) * 12 * (1 + PARAM["contribution"]) + j["other"]
    return annual, r4(annual / (PARAM["days"] * PARAM["hours"]))

# ---------------- Mat hang va don gia ----------------
ITEM = {"GANG": dict(price=D("3000"), reuse=1), "THUOCX": dict(price=D("25000"), reuse=1),
        "DUNGCU": dict(price=D("2000000"), reuse=200), "DIEN": dict(price=PARAM["electricity_price"], reuse=1),
        "THUOCY": dict(price=D("80000"), reuse=1)}

# ---------------- Thiet bi (BR-COST-004), phong (BR-COST-005) ----------------
EQUIP = {"EQ1": dict(cost=D("1200000000"), life=D("8"), in_service=date(2022, 1, 1),
                     maint=D("30000000"), calib=D("6000000"), hours=D("2112"), util=D("0.5"))}
ROOM = {"R1": dict(annual=D("52800000"), hours=D("2112"))}

def equip_rate(code, include_depr=True, on=COSTING_DATE):
    e = EQUIP[code]
    end_year = e["in_service"].year + int(e["life"])
    expired = on >= date(end_year, e["in_service"].month, e["in_service"].day)
    depr = D("0") if (expired or not include_depr) else e["cost"] / e["life"]
    return depr, r4((depr + e["maint"] + e["calib"]) / (e["hours"] * e["util"]))
def room_rate(code, include_depr=True):
    r = ROOM[code]
    return D("0") if not include_depr else r4(r["annual"] / r["hours"])

# ---------------- Dinh muc (NC Norm Line) ----------------
@dataclass
class Line:
    line_id: str; step: str; comp: str; res: str
    qty: D; headcount: int = 1; authority: D = None; wastage: D = D("0"); excluded: bool = False
NORMS = {
 "DV-TEST-A": [
  Line("L01", "S001", "LABOR", "DD", D("10")),
  Line("L02", "S001", "SUPPLY", "GANG", D("2")),
  Line("L03", "S002", "LABOR", "BS", D("20"), authority=D("25")),
  Line("L04", "S002", "LABOR", "DD", D("20")),
  Line("L05", "S002", "DRUG", "THUOCX", D("1"), wastage=D("0.05")),
  Line("L06", "S002", "SUPPLY", "DUNGCU", D("1")),
  Line("L07", "S002", "EQUIPMENT", "EQ1", D("20")),
  Line("L08", "S002", "INFRA", "R1", D("30")),
  Line("L09", "S003", "LABOR", "DD", D("15"), authority=D("10")),
  Line("L10", "", "UTILITY", "DIEN", D("0.5")),
  Line("L11", "S002", "DRUG", "THUOCY", D("1"), excluded=True),
 ],
 "DV-TEST-B": [
  Line("L01", "S001", "LABOR", "DD", D("30")),
  Line("L02", "S001", "SUPPLY", "GANG", D("1")),
 ],
}
VOLUME = {"DV-TEST-A": D("4000"), "DV-TEST-B": D("6000")}      # san luong nam, khoa K01
CATEGORY = {"LABOR": "LABOR", "DRUG": "DRUG_SUPPLY", "SUPPLY": "DRUG_SUPPLY",
            "EQUIPMENT": "DEPRECIATION", "INFRA": "DEPRECIATION", "UTILITY": "UTILITY"}

# ---------------- So lieu ke toan (da gan loai chi phi) ----------------
ACCOUNTING = {  # trung tam chi phi -> loai -> so tien
 "K01": dict(LABOR=D("700000000"), DRUG_SUPPLY=D("260000000"), DEPRECIATION=D("300000000"),
             UTILITY=D("40000000"), MANAGEMENT=D("100000000")),
 "HC":  dict(LABOR=D("300000000"), MANAGEMENT=D("400000000")),   # trung tam ho tro
}
HEADCOUNT = {"K01": D("20"), "K02": D("30")}   # tieu chi cap 1 cua cac trung tam lam sang
L1_DRIVER = "HEADCOUNT"
L2_DRIVER = dict(LABOR="LABOR_MIN", DRUG_SUPPLY="VOLUME", DEPRECIATION="MACHINE_MIN",
                 UTILITY="VOLUME", MANAGEMENT="LABOR_MIN")

def applied_qty(l):                                   # BR-COST-007
    return l.qty if l.authority is None else min(l.qty, l.authority)

def direct_lines(svc, include_depr=True):
    out = []
    for l in NORMS[svc]:
        if l.excluded:
            out.append((l, D("0"), D("0"), D("0"))); continue
        q = applied_qty(l)
        if l.comp == "LABOR":                         # BR-COST-002
            rate = job_rate(l.res)[1]; amt = q / 60 * l.headcount * rate
        elif l.comp in ("DRUG", "SUPPLY"):            # BR-COST-003
            it = ITEM[l.res]; rate = it["price"]; amt = q * (1 + l.wastage) * rate / it["reuse"]
        elif l.comp == "EQUIPMENT":                   # BR-COST-004
            rate = equip_rate(l.res, include_depr)[1]; amt = q / 60 * rate
        elif l.comp == "INFRA":                       # BR-COST-005, BR-COST-016
            rate = room_rate(l.res, include_depr); amt = q / 60 * rate
        else:                                         # BR-COST-006
            rate = ITEM[l.res]["price"]; amt = q * rate
        out.append((l, q, rate, r2(amt)))
    return out

def run(include_depr=True):
    res = {}
    direct = {s: direct_lines(s, include_depr) for s in NORMS}
    by_cat = {s: {} for s in NORMS}
    for s, rows in direct.items():
        for l, q, rate, amt in rows:
            c = CATEGORY[l.comp]; by_cat[s][c] = by_cat[s].get(c, D("0")) + amt
    # tieu chi cap 2
    labor_min = {s: sum(applied_qty(l) * l.headcount for l in NORMS[s] if l.comp == "LABOR" and not l.excluded) * VOLUME[s] for s in NORMS}
    mach_min = {s: sum(applied_qty(l) for l in NORMS[s] if l.comp == "EQUIPMENT" and not l.excluded) * VOLUME[s] for s in NORMS}
    drv = dict(LABOR_MIN=labor_min, MACHINE_MIN=mach_min, VOLUME=dict(VOLUME))
    # cap 1 (BR-COST-010)
    share = HEADCOUNT["K01"] / sum(HEADCOUNT.values())
    recv = {c: r2(v * share) for c, v in ACCOUNTING["HC"].items()}
    # cap 2 (BR-COST-011) + doi soat (BR-COST-015)
    alloc = {s: {} for s in NORMS}; recon = []
    for cat, acc in ACCOUNTING["K01"].items():
        if cat == "DEPRECIATION" and not include_depr:
            recon.append((cat, None, None, None, None, None)); continue          # BR-COST-016
        pool_in = acc + recv.get(cat, D("0"))
        costed = sum(by_cat[s].get(cat, D("0")) * VOLUME[s] for s in NORMS)
        remainder = max(pool_in - costed, D("0"))
        d = drv[L2_DRIVER[cat]]; total = sum(d.values())
        for s in NORMS:
            alloc[s][cat] = r2(remainder * d[s] / total / VOLUME[s]) if total and VOLUME[s] else D("0")
        if cat == "MANAGEMENT":
            continue                                                             # BR-COST-015: khong doi soat MANAGEMENT
        pct = r2((costed - pool_in) / pool_in * 100)
        over = pct > PARAM["recon_tolerance"] or (cat == "DRUG_SUPPLY" and pct < -PARAM["recon_tolerance"])
        recon.append((cat, costed, pool_in, remainder, pct, over))
    for s in NORMS:
        dsum = sum(a for *_, a in direct[s]); asum = sum(alloc[s].values())
        full = dsum + asum                                                       # BR-COST-012
        rate = PARAM["accumulation_rate"]
        acc_amt = r2(full * rate) if PARAM["accumulation_mode"] == "ON_COST" else r2(full * rate / (1 - rate))
        calc = r2((full + acc_amt) / (1 - PARAM["obligation_rate"]))             # BR-COST-013
        u = PARAM["rounding_unit"]
        rounded = (calc / u).quantize(D("1"), rounding=ROUND_HALF_UP) * u        # BR-COST-014
        res[s] = dict(lines=direct[s], by_cat=by_cat[s], alloc=alloc[s], direct=dsum, alloc_sum=asum,
                      full=full, accumulation=acc_amt, calc=calc, rounded=rounded)
    return res, recon, recv

def fmt(x): return f"{x:,.2f}" if isinstance(x, D) else str(x)

if __name__ == "__main__":
    inc = "--no-depr" not in sys.argv
    res, recon, recv = run(inc)
    print("## Don gia");
    for j in JOB: a, r = job_rate(j); print(f"- {j}: chi phi nam {fmt(a)}; don gia gio {r}")
    print(f"- EQ1: khau hao nam {fmt(equip_rate('EQ1', inc)[0])}; don gia gio may {equip_rate('EQ1', inc)[1]}")
    print(f"- R1: don gia gio phong {room_rate('R1', inc)}")
    print(f"- Cap 1 nhan ve K01: {{{', '.join(k + ': ' + fmt(v) for k, v in recv.items())}}}")
    for s, r in res.items():
        print(f"\n## {s}  (san luong {VOLUME[s]})")
        for l, q, rate, amt in r["lines"]:
            print(f"| {l.line_id} | {l.step or 'chung'} | {l.comp} | {l.res} | {q} | {rate} | {fmt(amt)} |")
        print("truc tiep:", fmt(r["direct"]), "| theo loai:", {k: fmt(v) for k, v in r["by_cat"].items()})
        print("phan bo:", {k: fmt(v) for k, v in r["alloc"].items()}, "| tong:", fmt(r["alloc_sum"]))
        print("gia thanh:", fmt(r["full"]), "| tich luy:", fmt(r["accumulation"]), "| gia tinh toan:", fmt(r["calc"]), "| lam tron:", fmt(r["rounded"]))
    print("\n## Doi soat K01")
    for cat, costed, pool, rem, pct, over in recon:
        print(f"| {cat} | {fmt(costed)} | {fmt(pool)} | {fmt(rem)} | {pct} | {over} |")
