"""FEAT-032: số test ước tính khớp golden_cls.py (dòng 154-156) và test-cases.md (600, 48, 12)."""

import importlib.util
import pathlib
import sys
import unittest
from decimal import Decimal as D

from normcore.costing import qc_plans as qp

_P = pathlib.Path(__file__).resolve().parents[3] / "docs" / "golden" / "golden_cls.py"
_spec = importlib.util.spec_from_file_location("golden_cls", _P)
G = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("golden_cls", G)
_spec.loader.exec_module(G)


def _plan(run_days):
	return dict(
		run_days_per_year=run_days,
		iqc_lines=[dict(levels=i["levels"], runs_per_day=i["runs"]) for i in G.IQC],
		calibration_lines=[
			dict(points=c["points"], replicates=c["reps"], calibrations_per_year=c["per_year"]) for c in G.CAL
		],
	)


class TestQcPlansGolden(unittest.TestCase):
	def test_uoc_tinh_bang_golden(self):
		run_days = G.SYSTEMS["GLU-B"]["run_days"]
		iqc, cal = qp.estimated_tests(_plan(run_days))
		self.assertEqual(iqc, sum(i["levels"] * i["runs"] * run_days for i in G.IQC))
		self.assertEqual(cal, sum(c["per_year"] * c["points"] * c["reps"] for c in G.CAL))
		eqa = qp.eqa_samples_per_year(G.EQA["rounds"], G.EQA["samples"])
		self.assertEqual(eqa, G.EQA["rounds"] * G.EQA["samples"])

	def test_trung_so_thuc_te_glu_a(self):
		a = G.SYSTEMS["GLU-A"]["actual"]
		iqc, cal = qp.estimated_tests(_plan(G.SYSTEMS["GLU-A"]["run_days"]))
		self.assertEqual((iqc, cal), (a["qnk"], a["qcal"]))
		self.assertEqual(qp.eqa_samples_per_year(G.EQA["rounds"], G.EQA["samples"]), a["qeqa"])
		self.assertEqual((iqc, cal), (D("600"), D("48")))
