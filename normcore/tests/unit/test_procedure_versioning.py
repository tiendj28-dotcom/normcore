"""Tạo phiên bản sửa đổi (FR-WF-009). Thuần Python."""

import unittest

from normcore.procedure import versioning as v


def _src():
	return {
		"name": "QT-1",
		"technical_service": "DV1",
		"department": "K1",
		"version_no": 1,
		"workflow_state": "Đã ban hành",
		"decision_no": "QD-1",
		"effective_date": "2026-01-01",
		"copied_from": "QT-0",
		"ai_log": "LOG-1",
		"doctor_request": "yêu cầu",
		"needs_review": 1,
		"overview": "đại cương",
		"indications": "chỉ định",
		"next_step_seq": 6,
		"next_resource_seq": 9,
		"steps": [
			{
				"step_id": "S001",
				"phase": "A",
				"step_title": "t1",
				"description": "d",
				"reference_minutes": 5,
				"ai_suggested": 1,
			},
			{
				"step_id": "S004",
				"phase": "B",
				"step_title": "t4",
				"description": "",
				"reference_minutes": 3,
				"ai_suggested": 1,
			},
		],
		"resources": [
			{
				"resource_row_id": "R002",
				"step_id": "S004",
				"resource_type": "Nhân lực",
				"quantity": 2,
				"uom": "phút",
				"ai_suggested": 1,
			}
		],
		"citations": [
			{"target_section": "overview", "relation": "Theo hướng dẫn", "quote": "q", "name": "x"}
		],
	}


class TestVersioning(unittest.TestCase):
	def test_giu_ma_va_bo_dem(self):
		d = v.build_revision(_src(), 1)
		self.assertEqual(d["version_no"], 2)
		self.assertEqual(d["previous_version"], "QT-1")
		self.assertEqual([s["step_id"] for s in d["steps"]], ["S001", "S004"])
		self.assertEqual(d["resources"][0]["resource_row_id"], "R002")
		self.assertEqual((d["next_step_seq"], d["next_resource_seq"]), (6, 9))
		self.assertEqual(d["overview"], "đại cương")
		self.assertEqual(d["doctor_request"], "yêu cầu")
		self.assertEqual(d["needs_review"], 1)

	def test_version_lay_tu_max_version(self):
		self.assertEqual(v.build_revision(_src(), 4)["version_no"], 5)

	def test_khong_sao_chep_truong_he_thong(self):
		d = v.build_revision(_src(), 1)
		for f in ("workflow_state", "decision_no", "effective_date", "copied_from", "ai_log", "name"):
			self.assertNotIn(f, d)

	def test_ai_suggested_ve_0(self):
		d = v.build_revision(_src(), 1)
		self.assertEqual([s["ai_suggested"] for s in d["steps"]], [0, 0])
		self.assertEqual(d["resources"][0]["ai_suggested"], 0)

	def test_trich_dan_khong_mang_name(self):
		self.assertNotIn("name", v.build_revision(_src(), 1)["citations"][0])

	def test_can_revise(self):
		self.assertTrue(v.can_revise("Đã ban hành"))
		for s in ("Nháp", "Đã thay thế", "Đã thu hồi", "Chờ ban hành"):
			self.assertFalse(v.can_revise(s))
