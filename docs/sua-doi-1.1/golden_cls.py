"""Normcore - bo du lieu vang cho khoi can lam sang: cai dat tham chieu cua BR-CLS-001..016 (SRS 1.1).

Day la DAC TA CHAY DUOC, cung quy uoc voi docs/golden/golden_engine.py: ma thuan Python, khong phu
thuoc frappe, so thap phan chinh xac. Doi phat trien dung tep nay lam chuan doi chieu cho phan can lam
sang cua normcore/costing (ADR-003, ADR-017). Moi so lieu la SO THU NGHIEM, khong phai so thuc te.

Quy uoc lam tron (SRS muc 3.4.1 va 3.4.5): don gia giu 4 chu so thap phan (r4); thanh tien moi dong
cho mot ket qua lam tron 2 chu so (r2); he so k giu 6 chu so (r6); phep chia trung gian khong lam tron.

Pham vi: chi phi TRUC TIEP cua dich vu co he thong xet nghiem. Phan bo cap 1, cap 2, tich luy va lam
tron gia (BR-COST-010..014) khong doi va da co trong golden_engine.py.

Chay:  python3 golden_cls.py
"""
from decimal import Decimal as D, ROUND_HALF_UP
from datetime import date


def _q(x, p): return D(x).quantize(D(p), rounding=ROUND_HALF_UP)
def r0(x): return _q(x, "1")
def r2(x): return _q(x, "0.01")
def r4(x): return _q(x, "0.0001")
def r6(x): return _q(x, "0.000001")


# ---------------- Tham so ----------------
PARAM = dict(electricity_price=D("3000"), expired_mode="ZERO",       # ZERO | CONTINUE (FR-RES-007)
             material_tol=D("5"), volume_tol=D("2"))
COSTING_DATE = date(2026, 12, 31)
KTV_RATE = D("59644.8864")            # don gia gio cong, lay chuc danh DD cua golden_engine.py

# ---------------- Mat hang: gia don vi mua, so don vi dinh muc trong mot don vi mua ----------------
ITEM = {
    "HC_GLU": dict(price=D("6000000"), units=D("200"), nominal=D("200"), open_days=D("30")),  # hoa chat chinh
    "ONG":    dict(price=D("6000"), units=D("1")),      # ong lay mau
    "CUVET":  dict(price=D("1200"), units=D("1")),      # vat tu tieu hao theo test
    "DD_RUA": dict(price=D("50000"), units=D("1")),     # dung dich rua, dung theo me
    "HC_PT":  dict(price=D("120000"), units=D("1")),    # hoa chat phu tro, dung theo ngay-may
    "QC_L":   dict(price=D("900000"), units=D("5")),    # vat lieu noi kiem, lo 5 mL
}
def unit_price(code):                                   # BR-CLS-002: don gia mot don vi dinh muc
    return r4(ITEM[code]["price"] / ITEM[code]["units"])

# ---------------- Thiet bi ----------------
EQUIP = {
    "EQ_A": dict(dept="XN", mode="MUA", cost=D("3600000000"), life=10, in_service=date(2022, 1, 1),
                 maint=D("120000000"), maint_vendor=False, basis="RESULT", dept_share=D("1"),
                 asset_value=D("3600000000"),
                 parts=[dict(name="Den", cost=D("24000000"), basis="MONTH", life=D("12"), vendor=False),
                        dict(name="Dien cuc", cost=D("9000000"), basis="RESULT", life=D("30000"), vendor=False)],
                 power=dict(run_kw=D("2"), run_h=D("8"), standby_kw=D("0.5"), standby_h=D("16"), continuous=True),
                 compliance=[dict(cost=D("8000000"), cycle=D("12"))]),
    "EQ_B": dict(dept="XN", mode="DAT", maint=D("40000000"), maint_vendor=True, basis="RESULT",
                 dept_share=D("1"), asset_value=D("1200000000"), parts=[], power=None,
                 compliance=[dict(cost=D("6000000"), cycle=D("12"))]),
    "EQ_C": dict(dept="K3", mode="THUE", contract=D("450000000"), maint=D("0"), maint_vendor=False,
                 basis="RESULT", dept_share=D("1"), asset_value=None, parts=[], power=None, compliance=[]),
    "EQ_CT": dict(dept="CDHA", mode="MUA", cost=D("28000000000"), life=8, in_service=date(2024, 1, 1),
                  maint=D("140000000"), maint_vendor=False, basis="MINUTE", dept_share=D("1"),
                  asset_value=D("28000000000"), parts=[], power=None, compliance=[]),
}
USAGE = {"EQ_A": dict(qtb=D("300000")), "EQ_B": dict(qtb=D("100000")),
         "EQ_C": dict(qtb=D("300000")), "EQ_CT": dict(mtb=D("180000"))}


def _own_compliance(e):                                  # BR-CLS-011: quy ve nam
    return sum((c["cost"] * 12 / c["cycle"] for c in e["compliance"]), D("0"))

def compliance_annual(code, mode):                       # mode: ASSET | DIRECT
    e = EQUIP[code]
    if mode == "DIRECT" or e["asset_value"] is None:
        return _own_compliance(e)
    peers = [x for x in EQUIP.values() if x["dept"] == e["dept"] and x["asset_value"] is not None]
    pool = sum((_own_compliance(x) for x in peers), D("0"))
    return pool * e["asset_value"] / sum(x["asset_value"] for x in peers)

def machine_annual(code, include_depr=True, on=None, expired_mode=None):   # BR-CLS-009, BR-COST-004
    e = EQUIP[code]; on = on or COSTING_DATE; expired_mode = expired_mode or PARAM["expired_mode"]
    if e["mode"] == "DAT":
        return D("0")
    if e["mode"] in ("THUE", "LDLK"):
        return e["contract"]
    if not include_depr:                                  # BR-COST-016
        return D("0")
    s = e["in_service"]
    expired = on >= date(s.year + e["life"], s.month, s.day)
    return D("0") if (expired and expired_mode == "ZERO") else e["cost"] / e["life"]

def equipment_annual(code, mode="ASSET", **kw):          # BR-CLS-009: chi phi thiet bi nam cua khoa
    e = EQUIP[code]
    vendor = e["mode"] == "DAT"
    maint = D("0") if (vendor and e["maint_vendor"]) else e["maint"]
    parts = sum((p["cost"] * 12 / p["life"] for p in e["parts"]
                 if p["basis"] == "MONTH" and not (vendor and p["vendor"])), D("0"))   # BR-CLS-010
    return (machine_annual(code, **kw) + maint + parts + compliance_annual(code, mode)) * e["dept_share"]

def per_result(code, annual, m=None):                    # chia theo tieu chi chia cua thiet bi
    e = EQUIP[code]
    if e["basis"] == "RESULT":
        return r2(annual / USAGE[code]["qtb"])
    if e["basis"] == "MINUTE":
        return r2(r4(annual / USAGE[code]["mtb"]) * m)
    raise ValueError("Tieu chi Gio ke hoach: dung BR-COST-004 trong golden_engine.py")

def part_per_result(code, m=None):                       # BR-CLS-010: linh kien theo so ket qua, gio chay
    e = EQUIP[code]; out = D("0")
    for p in e["parts"]:
        if e["mode"] == "DAT" and p["vendor"]:
            continue
        if p["basis"] == "RESULT":
            out += r2(p["cost"] / p["life"])
        elif p["basis"] == "HOUR":
            out += r2(p["cost"] / p["life"] * m / 60)
    return out

def power_per_result(code, run_days, m=None):            # BR-CLS-012
    e = EQUIP[code]; p = e["power"]
    if not p:
        return D("0")
    day = (p["run_kw"] * p["run_h"] + p["standby_kw"] * p["standby_h"]) * PARAM["electricity_price"]
    days = D("365") if p["continuous"] else run_days
    return per_result(code, day * days * e["dept_share"], m)


# ---------------- He thong xet nghiem, ke hoach chat luong, san luong ----------------
IQC = [dict(item="QC_L", levels=D("2"), runs=D("1"), qty=D("0.2"), shared=D("20"))]
CAL = [dict(points=D("2"), reps=D("2"), per_year=D("12"), cost=D("400000"))]
EQA = dict(fee=D("24000000"), ship=D("1200000"), rounds=D("3"), samples=D("4"), n_services=D("21"))

SYSTEMS = {
    "GLU-A": dict(service="GLU", equip="EQ_A", qbn=D("12000"), run_days=D("300"), batch=D("40"),
                  tests_per_tube=D("4"), est=dict(rerun=D("0.02"), h=D("0.03")),
                  actual=dict(qnk=D("600"), qcal=D("48"), qrerun=D("240"), qeqa=D("12"), h=D("0.03"))),
    "GLU-B": dict(service="GLU", equip="EQ_B", qbn=D("4000"), run_days=D("300"), batch=D("40"),
                  tests_per_tube=D("4"), est=dict(rerun=D("0.02"), h=D("0.03")), actual=None),
}
# Bo dinh muc (giong nhau cho hai he thong): (ma dong, cap phat sinh, cau phan, nguon luc, luong, nhan k, gan voi)
NORM = [
    ("L01", "TUBE",   "SUPPLY",    "ONG",    D("1"),   False, None),
    ("L02", "RESULT", "DRUG",      "HC_GLU", D("1"),   True,  None),
    ("L03", "RESULT", "SUPPLY",    "CUVET",  D("1"),   True,  None),
    ("L04", "BATCH",  "DRUG",      "DD_RUA", D("1"),   False, None),
    ("L05", "DAY",    "DRUG",      "HC_PT",  D("1"),   False, "EQUIP"),
    ("L06", "RESULT", "LABOR",     "KTV",    D("1.5"), False, None),
    ("L07", "RESULT", "EQUIPMENT", None,     D("1"),   False, None),
]


def k_factor(code):                                      # BR-CLS-001
    s = SYSTEMS[code]; a = s["actual"]; qbn = s["qbn"]
    if a:
        qnk, qcal, qrerun, qeqa, h = a["qnk"], a["qcal"], a["qrerun"], a["qeqa"], a["h"]
    else:                                                # FR-QC-006: uoc tinh tu ke hoach
        qnk = sum(i["levels"] * i["runs"] * s["run_days"] for i in IQC)
        qcal = sum(c["per_year"] * c["points"] * c["reps"] for c in CAL)
        qeqa = EQA["rounds"] * EQA["samples"]
        qrerun = r0(s["est"]["rerun"] * qbn); h = s["est"]["h"]
    total = qbn + qnk + qcal + qrerun + qeqa
    return r6(total / ((1 - h) * qbn)), total, a is None

def system_lines(code, mode="ASSET", **kw):
    s = SYSTEMS[code]; eq = s["equip"]; qbn = s["qbn"]; k, total, est = k_factor(code)
    out = []
    for lid, level, comp, res, qty, apply_k, attach in NORM:
        if comp == "LABOR":                              # BR-COST-002
            amt = r2(qty / 60 * KTV_RATE); note = "BR-COST-002"
        elif comp == "EQUIPMENT":                        # BR-CLS-009
            amt = per_result(eq, equipment_annual(eq, mode, **kw)); note = "BR-CLS-009 may, bao tri, linh kien thang, kiem dinh"
        elif level == "RESULT":                          # BR-CLS-002
            amt = r2(qty * unit_price(res) * (k if apply_k else 1)); note = "BR-CLS-002" + (" x k" if apply_k else "")
        elif level == "TUBE":                            # BR-CLS-003
            amt = r2(qty * unit_price(res) / s["tests_per_tube"]); note = "BR-CLS-003"
        elif level == "BATCH":                           # BR-CLS-004
            amt = r2(qty * unit_price(res) / s["batch"]); note = "BR-CLS-004"
        else:                                            # BR-CLS-005: DAY, PERIOD
            annual = qty * unit_price(res) * (s["run_days"] if level == "DAY" else 1)
            amt = per_result(eq, annual) if attach == "EQUIP" else r2(annual / qbn); note = "BR-CLS-005"
        out.append((lid, level, comp, res or eq, amt, note))
    out.append(("EQ-P", "RESULT", "EQUIPMENT", eq, part_per_result(eq), "BR-CLS-010 linh kien theo so ket qua"))
    out.append(("EQ-E", "DAY", "UTILITY", eq, power_per_result(eq, s["run_days"]), "BR-CLS-012 dien"))
    for i in IQC:                                        # BR-CLS-006
        amt = r2(i["qty"] * i["levels"] * i["runs"] * s["run_days"] * unit_price(i["item"]) / i["shared"] / qbn)
        out.append(("QC-N", "PERIOD", "DRUG", i["item"], amt, "BR-CLS-006 noi kiem"))
    for c in CAL:                                        # BR-CLS-007
        out.append(("QC-C", "PERIOD", "DRUG", "CAL", r2(c["cost"] * c["per_year"] / qbn), "BR-CLS-007 chat chuan"))
    return out, k, total, est

def service_direct(service="GLU", mode="ASSET", **kw):   # BR-CLS-008, BR-CLS-013
    codes = [c for c, s in SYSTEMS.items() if s["service"] == service]
    qsum = sum(SYSTEMS[c]["qbn"] for c in codes)
    per = {c: sum(a for *_, a, _n in system_lines(c, mode, **kw)[0]) for c in codes}
    weighted = r2(sum(SYSTEMS[c]["qbn"] / qsum * per[c] for c in codes))
    eqa = r2((EQA["fee"] + EQA["ship"]) / EQA["n_services"] / qsum)
    return per, weighted, eqa, weighted + eqa, qsum

def material_recon(item, issued_purchase_units):         # BR-CLS-014
    calc = D("0")
    for c, s in SYSTEMS.items():
        k = k_factor(c)[0]
        for lid, level, comp, res, qty, apply_k, attach in NORM:
            if res == item and level == "RESULT":
                calc += qty * (k if apply_k else 1) * s["qbn"]
    issued = issued_purchase_units * ITEM[item]["units"]
    pct = r2((issued - calc) / issued * 100)
    return calc, issued, pct, abs(pct) > PARAM["material_tol"]

def volume_recon(results, his):                          # BR-CLS-015
    pct = r2((results - his) / his * 100)
    return pct, abs(pct) > PARAM["volume_tol"]

def low_volume(total_tests, item="HC_GLU"):              # BR-CLS-016
    used = total_tests * ITEM[item]["open_days"] / 365
    return r2(used), used < ITEM[item]["nominal"]


def fmt(x): return f"{x:,.2f}" if isinstance(x, D) else str(x)

if __name__ == "__main__":
    print("## Don gia mot don vi dinh muc (BR-CLS-002)")
    for c in ITEM: print(f"- {c}: {unit_price(c)}")
    print("\n## Chi phi thiet bi nam, cach phan bo Theo gia tri tai san (BR-CLS-009..011)")
    for c in ("EQ_A", "EQ_B"):
        print(f"- {c}: may {fmt(machine_annual(c))}; kiem dinh {fmt(compliance_annual(c, 'ASSET'))}; "
              f"tong nam {fmt(equipment_annual(c))}; mot ket qua {fmt(per_result(c, equipment_annual(c)))}")
    for code in SYSTEMS:
        lines, k, total, est = system_lines(code)
        print(f"\n## He thong {code}: Qbn {SYSTEMS[code]['qbn']}; tong test {total}; k = {k}"
              f"{' (Uoc tinh tu ke hoach)' if est else ''}")
        for lid, level, comp, res, amt, note in lines:
            print(f"| {lid} | {level} | {comp} | {res} | {fmt(amt)} | {note} |")
        print("chi phi truc tiep mot ket qua:", fmt(sum(a for *_, a, _n in lines)))
    per, weighted, eqa, direct, qsum = service_direct()
    print(f"\n## Dich vu GLU (tong Qbn {qsum})")
    print("binh quan gia quyen:", fmt(weighted), "| ngoai kiem:", fmt(eqa), "| chi phi truc tiep cua dich vu:", fmt(direct))

    print("\n## Bien the")
    print("V1 cach phan bo Gan truc tiep thiet bi:",
          {c: (fmt(compliance_annual(c, 'DIRECT')), fmt(per_result(c, equipment_annual(c, 'DIRECT')))) for c in ("EQ_A", "EQ_B")},
          "| dich vu:", fmt(service_direct(mode="DIRECT")[3]))
    late = date(2033, 1, 1)
    print("V2 EQ_A het thoi gian su dung (ngay tinh 01/01/2033): ZERO ->",
          fmt(per_result("EQ_A", equipment_annual("EQ_A", on=late, expired_mode="ZERO"))),
          "| CONTINUE ->", fmt(per_result("EQ_A", equipment_annual("EQ_A", on=late, expired_mode="CONTINUE"))))
    print("V3 EQ_C may thue 450.000.000/nam, Qtb 300.000:", fmt(per_result("EQ_C", equipment_annual("EQ_C"))))
    a = equipment_annual("EQ_CT")
    print("V4 EQ_CT chia theo Phut chiem may: chi phi nam", fmt(a), "| don gia phut", r4(a / USAGE["EQ_CT"]["mtb"]),
          "| m=10 ->", fmt(per_result("EQ_CT", a, D("10"))), "| m=20 ->", fmt(per_result("EQ_CT", a, D("20"))))
    print("V5 loai gia khong ket cau khau hao: EQ_A ->", fmt(per_result("EQ_A", equipment_annual("EQ_A", include_depr=False))),
          "| EQ_C (tien thue van tinh, cho TBD-14) ->", fmt(per_result("EQ_C", equipment_annual("EQ_C", include_depr=False))))
    for boxes in (D("94"), D("100")):
        calc, issued, pct, over = material_recon("HC_GLU", boxes)
        print(f"V6 doi soat vat chat HC_GLU, xuat {boxes} hop: tinh duoc {calc}; xuat kho {issued}; lech {pct}%; vuot nguong {over}")
    for his in (D("15800"), D("15500")):
        print(f"V7 doi soat san luong: 16000 ket qua, HIS {his}: lech {volume_recon(D('16000'), his)}")
    for t in (D("12900"), D("4740"), D("1900")):
        print(f"V8 canh bao san luong thap, tong test {t}: {low_volume(t)}")
