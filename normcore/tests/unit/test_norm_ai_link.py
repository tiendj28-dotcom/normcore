import unittest

from normcore.norm import ai_link as a

CANDS = [
	{"doctype": "NC Item", "name": "I2", "label": "Lidocain 2%", "uom": "ống"},
	{"doctype": "NC Item", "name": "I1", "label": "Lidocain hydroclorid 2%", "uom": "ống"},
	{"doctype": "NC Item", "name": "I3", "label": "Găng tay", "uom": "đôi"},
]
EQ = {"doctype": "NC Equipment", "name": "E1", "label": "Máy siêu âm", "uom": None}


class TestAiLink(unittest.TestCase):
	def test_FR_AI_007_loc_ung_vien(self):
		self.assertEqual(a.pools_for("Thuốc"), ("NC Item",))
		self.assertEqual(a.pools_for("Thiết bị"), ("NC Equipment",))
		self.assertEqual(a.pools_for("Khác"), ("NC Item", "NC Equipment"))
		self.assertEqual(a.pools_for("Nhân lực"), ())
		self.assertEqual(a.pools_for("Phòng"), ())
		out = a.shortlist("LIDOCAIN  2%", CANDS)
		self.assertEqual([c["name"] for c in out], ["I2", "I1"])
		self.assertEqual(a.shortlist("Đặt ống", [{"name": "x", "label": "DAT ONG"}])[0]["name"], "x")
		self.assertEqual(a.shortlist("zzz", CANDS), [])
		self.assertEqual(a.shortlist("", CANDS), [])
		many = [{"name": f"N{i:02d}", "label": "kim"} for i in range(15)]
		out = a.shortlist("kim", many)
		self.assertEqual(len(out), 10)
		self.assertEqual(out[0]["name"], "N00")
		self.assertEqual(len(a.shortlist("kim", many, limit=3)), 3)

	def test_FR_AI_007_loc_de_xuat_lien_ket(self):
		lines = [
			{"line_id": "L1", "procedure_resource_row": "R1", "component": "DRUG"},
			{"line_id": "L2", "procedure_resource_row": "R2", "component": "EQUIPMENT"},
			{"line_id": "L3", "procedure_resource_row": "R3", "resource": "J1"},
			{"line_id": "L4", "procedure_resource_row": "R4", "ai_suggested": 1},
			{"line_id": "L5", "procedure_resource_row": "R5", "is_excluded": 1},
			{"line_id": "L6", "procedure_resource_row": "R6", "step_removed": 1},
			{"line_id": "L7"},
		]
		pend = a.pending_lines(lines)
		self.assertEqual([p["line_id"] for p in pend], ["L1", "L2"])
		res = {
			"R1": {"resource_type": "Thuốc", "resource_text": "Lidocain", "quantity": 1, "uom": "ống"},
			"R2": {"resource_type": "Thiết bị", "resource_text": "Siêu âm", "quantity": 5, "uom": "phút"},
		}
		v = a.request_variables(pend, res, {"R1": CANDS[:2], "R2": []})
		self.assertEqual([x["resource_row_id"] for x in v["lines"]], ["R1"])
		self.assertEqual(v["lines"][0]["candidates"][0], CANDS[0])
		self.assertIn("NC Equipment", v["components"])
		offered = {"R1": CANDS[:2], "R2": [EQ]}
		data = {
			"suggestions": [
				{
					"resource_row_id": "R1",
					"doctype": "NC Item",
					"name": "I2",
					"component": "DRUG",
					"confidence": 0.876,
				},
				{
					"resource_row_id": "R1",
					"doctype": "NC Item",
					"name": "I1",
					"component": "DRUG",
					"confidence": 0.5,
				},
				{
					"resource_row_id": "R1",
					"doctype": "NC Item",
					"name": "ZZ",
					"component": "DRUG",
					"confidence": 0.5,
				},
				{
					"resource_row_id": "R2",
					"doctype": "NC Equipment",
					"name": "E1",
					"component": "SUPPLY",
					"confidence": 0.5,
				},
				{
					"resource_row_id": "R2",
					"doctype": "NC Equipment",
					"name": "E1",
					"component": "EQUIPMENT",
					"confidence": 1.2,
				},
				{
					"resource_row_id": "R2",
					"doctype": "NC Equipment",
					"name": "E1",
					"component": "EQUIPMENT",
					"confidence": "0.9",
				},
				{
					"resource_row_id": "R2",
					"doctype": "NC Equipment",
					"name": "E1",
					"component": "EQUIPMENT",
					"confidence": True,
				},
				{
					"resource_row_id": "R9",
					"doctype": "NC Item",
					"name": "I1",
					"component": "DRUG",
					"confidence": 0.5,
				},
				{"resource_row_id": 5},
				"rác",
			]
		}
		acc, rej = a.parse_suggestions(data, offered)
		self.assertEqual(rej, 9)
		self.assertEqual(
			acc,
			{
				"R1": {
					"resource_doctype": "NC Item",
					"resource": "I2",
					"component": "DRUG",
					"ai_confidence": 88,
				}
			},
		)
		self.assertEqual(a.parse_suggestions({"mock": True}, offered), ({}, 0))
		acc["R3"] = {
			"resource_doctype": "NC Item",
			"resource": "I3",
			"component": "SUPPLY",
			"ai_confidence": 10,
		}
		done = a.apply_suggestions(lines, acc)
		self.assertEqual(done, ["L1"])
		self.assertEqual(
			(lines[0]["resource"], lines[0]["ai_suggested"], lines[0]["ai_confidence"]), ("I2", 1, 88)
		)
		self.assertEqual(lines[2]["resource"], "J1")
		self.assertEqual(a.original_component("Thuốc"), "DRUG")
		self.assertEqual(a.original_component("Lạ"), "SUPPLY")
