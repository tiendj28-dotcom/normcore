"""FR-NORM-001: ánh xạ dòng nguồn lực → dòng định mức."""

import unittest

from normcore.norm.init_from_procedure import (
	COMPONENT_BY_RESOURCE_TYPE,
	RESOURCE_DOCTYPE_BY_COMPONENT,
	lines_from_resources,
)


def res(row, rtype, doctype=None, name=None, step="S001", qty=10, uom="phút", headcount=None):
	return {
		"resource_row_id": row,
		"step_id": step,
		"resource_type": rtype,
		"linked_doctype": doctype,
		"linked_name": name,
		"quantity": qty,
		"uom": uom,
		"headcount": headcount,
	}


class TestNormInit(unittest.TestCase):
	def test_anh_xa_cau_phan(self):
		self.assertEqual(COMPONENT_BY_RESOURCE_TYPE["Nhân lực"], "LABOR")
		for t in ("Thuốc", "Hóa chất", "Dịch truyền"):
			self.assertEqual(COMPONENT_BY_RESOURCE_TYPE[t], "DRUG")
		self.assertEqual(COMPONENT_BY_RESOURCE_TYPE["Vật tư"], "SUPPLY")
		self.assertEqual(COMPONENT_BY_RESOURCE_TYPE["Khác"], "SUPPLY")
		self.assertEqual(RESOURCE_DOCTYPE_BY_COMPONENT["INFRA"], "NC Room")

	def test_sau_dong_nguon_luc_ra_sau_dong(self):
		rows = [
			res("R1", "Nhân lực", "NC Job Title", "BS", headcount=2),
			res("R2", "Nhân lực", "NC Job Title", "DD"),
			res("R3", "Thuốc"),
			res("R4", "Vật tư", "NC Item", "GANG"),
			res("R5", "Thiết bị", "NC Equipment", "EQ1"),
			res("R6", "Phòng"),
		]
		lines, errors = lines_from_resources(rows)
		self.assertEqual(errors, [])
		self.assertEqual([x["procedure_resource_row"] for x in lines], ["R1", "R2", "R3", "R4", "R5", "R6"])
		self.assertEqual(
			[x["component"] for x in lines], ["LABOR", "LABOR", "DRUG", "SUPPLY", "EQUIPMENT", "INFRA"]
		)
		self.assertEqual(lines[0]["headcount"], 2)
		self.assertEqual(lines[1]["headcount"], 1)
		self.assertIsNone(lines[2]["headcount"])
		self.assertIsNone(lines[2]["resource"])  # chưa liên kết
		self.assertEqual(lines[2]["resource_doctype"], "NC Item")
		self.assertEqual(lines[3]["resource"], "GANG")
		self.assertTrue(all(x["basis"] == "Quy trình" and x["step_id"] == "S001" for x in lines))

	def test_lien_ket_sai_loai_coi_la_chua_lien_ket(self):
		lines, _ = lines_from_resources([res("R1", "Vật tư", "NC Equipment", "EQ1")])
		self.assertIsNone(lines[0]["resource"])

	def test_nhan_luc_chua_gan_chuc_danh_bao_loi(self):
		lines, errors = lines_from_resources([res("R1", "Nhân lực")])
		self.assertEqual(len(lines), 1)
		self.assertIn("R1", errors[0])
