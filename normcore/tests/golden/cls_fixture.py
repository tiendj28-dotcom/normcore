"""Dựng đầu vào của costing/cls.py từ docs/golden/golden_cls.py (không chép số): FEAT-036."""

import sys
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "docs" / "golden"))
import golden_cls as g

from normcore.costing import cls, engine, resources

MODE = {"MUA": resources.BUY, "DAT": resources.VENDOR, "THUE": resources.RENT, "LDLK": resources.JOINT}
BASIS = {"RESULT": resources.BASIS_RESULT, "MINUTE": resources.BASIS_MINUTE}
LIFE = {"MONTH": "Tháng", "RESULT": cls.LIFE_RESULT, "HOUR": cls.LIFE_HOUR}
COMPONENT = {"TUBE": "SUPPLY"}


def equipment(code, **override):
	e = g.EQUIP[code]
	u = g.USAGE[code]
	p = e["power"]
	kw = dict(
		code=code,
		department=e["dept"],
		mode=MODE[e["mode"]],
		basis=BASIS[e["basis"]],
		original_cost=e.get("cost"),
		life_years=D(e["life"]) if "life" in e else None,
		in_service=e.get("in_service"),
		contract_cost=e.get("contract"),
		maintenance=e["maint"],
		maintenance_vendor_paid=e["maint_vendor"],
		components=tuple(
			cls.ComponentInput(x["cost"], LIFE[x["basis"]], x["life"], x["vendor"]) for x in e["parts"]
		),
		dept_share=e["dept_share"],
		asset_value=e["asset_value"],
		power=cls.PowerInput(p["run_kw"], p["run_h"], p["standby_kw"], p["standby_h"], p["continuous"])
		if p
		else None,
		manual_calibration=D("0"),
		records=tuple(cls.RecordInput(c["cost"], c["cycle"], True) for c in e["compliance"]),
		qtb=u.get("qtb"),
		mtb=u.get("mtb"),
	)
	kw.update(override)
	return cls.EquipmentInput(**kw)


def system(code, **override):
	s = g.SYSTEMS[code]
	a = s["actual"]
	norm_lines, rates = [], {}
	for lid, level, comp, res, qty, apply_k, attach in g.NORM:
		line = engine.NormLine(lid, "", comp, res or "", res or "", qty, wastage_rate=D("0"))
		norm_lines.append(
			cls.ClsNormLine(
				line,
				level,
				apply_k,
				cls.ATTACH_EQUIP if attach == "EQUIP" else "",
				"",
				res == "HC_GLU",
				g.ITEM["HC_GLU"]["nominal"] if res == "HC_GLU" else None,
				g.ITEM["HC_GLU"]["open_days"] if res == "HC_GLU" else None,
			)
		)
		if comp == "LABOR":
			rates[lid] = engine.LineRate(g.KTV_RATE, "KTV")
		elif comp != "EQUIPMENT":
			rates[lid] = engine.LineRate(g.unit_price(res), res)
	iqc = tuple(
		cls.IqcLine(
			i["item"],
			i["levels"],
			i["runs"],
			i["qty"],
			i["shared"],
			engine.LineRate(g.unit_price(i["item"]), i["item"]),
		)
		for i in g.IQC
	)
	cal = tuple(cls.CalLine(c["points"], c["reps"], c["per_year"], c["cost"]) for c in g.CAL)
	kw = dict(
		code=code,
		norm_set="NS-" + code,
		equipment=s["equip"],
		qbn=s["qbn"],
		actual=cls.AuxCounts(a["qnk"], a["qcal"], a["qrerun"], a["qeqa"], a["h"]) if a else cls.AuxCounts(),
		est_rerun_rate=s["est"]["rerun"],
		est_h=s["est"]["h"],
		est_qnk=sum((i["levels"] * i["runs"] * s["run_days"] for i in g.IQC), D("0")),
		est_qcal=sum((c["per_year"] * c["points"] * c["reps"] for c in g.CAL), D("0")),
		eqa_tests_est=g.EQA["rounds"] * g.EQA["samples"],
		run_days=s["run_days"],
		batch=s["batch"],
		tests_per_tube=s["tests_per_tube"],
		lines=tuple(norm_lines),
		rates=rates,
		iqc=iqc,
		cal=cal,
	)
	kw.update(override)
	return cls.TestSystemInput(**kw)


def service_input(
	codes=("GLU-A", "GLU-B"), mode=cls.ALLOC_ASSET, on=None, expired_mode=None, include_depr=True, **override
):
	kw = dict(
		scenario="Thực tế 12 tháng",
		fiscal_year=2026,
		systems=tuple(system(c) for c in codes),
		equipment={c: equipment(c) for c in g.EQUIP},
		eqa=(cls.EqaInput("EQA", g.EQA["fee"], g.EQA["ship"], D(1) / g.EQA["n_services"]),),
		allocation_mode=mode,
		expired_mode=expired_mode or g.PARAM["expired_mode"],
		on=on or g.COSTING_DATE,
		include_depr=include_depr,
		electricity_price=g.PARAM["electricity_price"],
	)
	kw.update(override)
	return cls.ClsServiceInput(**kw)


def service(inp=None, **kw):
	inp = inp or service_input(**kw)
	return engine.ServiceInput("GLU", "XN", "", (), {}, None, inp)


PARAMS = engine.PricingParams(None, D("0"), D("0"), D("100"), True)


def cost(**kw):
	return cls.cost_service(service(**kw), PARAMS)
