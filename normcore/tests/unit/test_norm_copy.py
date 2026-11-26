"""FEAT-034 T01: sao chép bộ định mức (norm.copy). Dữ liệu dòng dựng từ golden_cls.NORM."""

import copy
import importlib.util
import pathlib
import unittest

from normcore.norm.copy import copy_lines

_spec = importlib.util.spec_from_file_location(
	"golden_cls", pathlib.Path(__file__).resolve().parents[3] / "docs" / "golden" / "golden_cls.py"
)
golden_cls = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(golden_cls)

COMPONENT_DOCTYPE = {"EQUIPMENT": "NC Equipment", "LABOR": "NC Job Title"}


def golden_lines():
	out = []
	for i, (code, level, comp, res, qty, k, attach) in enumerate(golden_cls.NORM, 1):
		out.append(
			{
				"line_id": code,
				"step_id": f"S{i:03d}" if code != "L05" else None,
				"service_level": 0 if code != "L05" else 1,
				"procedure_resource_row": f"R{i}",
				"component": comp,
				"resource_doctype": COMPONENT_DOCTYPE.get(comp, "NC Item"),
				"resource": res,
				"hospital_qty": float(qty),
				"cost_level": level,
				"apply_k": 1 if k else 0,
				"attach_to": "Thiết bị" if attach == "EQUIP" else None,
				"attach_equipment": "EQ_A" if attach == "EQUIP" else None,
				"confirmed_by": "a@b.c",
				"confirmed_on": "2026-01-01",
			}
		)
	return out


STEPS = {f"S{i:03d}" for i in range(1, 8)}
ROWS = {f"R{i}" for i in range(1, 8)}


class TestCopyLines(unittest.TestCase):
	def run_copy(self, **kw):
		args = {
			"lines": golden_lines(),
			"step_ids": STEPS,
			"resource_rows": ROWS,
			"equipment_map": {"EQ_A": "EQ_B"},
			"qc_items": set(),
		}
		args.update(kw)
		return copy_lines(**args)

	def test_TC_CLS_33_giu_dong_doi_thiet_bi_bo_xac_nhan(self):
		out, skipped = self.run_copy()
		self.assertEqual(skipped, [])
		self.assertEqual([o["line_id"] for o in out], [r[0] for r in golden_cls.NORM])
		l05 = next(o for o in out if o["line_id"] == "L05")
		self.assertEqual(l05["attach_equipment"], "EQ_B")
		self.assertEqual(l05["cost_level"], "DAY")
		self.assertTrue(all("confirmed_by" not in o and "confirmed_on" not in o for o in out))

	def test_khong_doi_dau_vao(self):
		lines = golden_lines()
		before = copy.deepcopy(lines)
		self.run_copy(lines=lines)
		self.assertEqual(lines, before)

	def test_ma_buoc_khong_con(self):
		out, skipped = self.run_copy(step_ids={"S001"})
		self.assertEqual(len(out), 2)  # L01 và L05 (chung cho cả dịch vụ)
		self.assertEqual(skipped[0], {"line_id": "L02", "reason": "Mã bước S002 không còn trong quy trình"})

	def test_dong_nguon_luc_khong_con_bo_lien_ket(self):
		out, _ = self.run_copy(resource_rows={"R1"})
		self.assertEqual(out[0]["procedure_resource_row"], "R1")
		self.assertIsNone(out[1]["procedure_resource_row"])

	def test_mat_hang_ke_hoach_bi_bo(self):
		out, skipped = self.run_copy(qc_items={"HC_PT"})
		self.assertEqual(
			skipped, [{"line_id": "L05", "reason": "Mặt hàng thuộc kế hoạch chất lượng của hệ thống đích"}]
		)
		self.assertEqual(len(out), 6)

	def test_thiet_bi_khac_giu_nguyen(self):
		out, _ = self.run_copy(equipment_map={})
		self.assertEqual(next(o for o in out if o["line_id"] == "L05")["attach_equipment"], "EQ_A")

	def test_chi_chep_truong_duoc_phep(self):
		out, _ = self.run_copy(inputs=("line_id", "step_id", "service_level", "component", "resource"))
		self.assertEqual(set(out[0]), {"line_id", "step_id", "service_level", "component", "resource"})
