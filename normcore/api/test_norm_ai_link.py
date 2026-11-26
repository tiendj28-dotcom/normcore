"""FEAT-025: đề xuất liên kết định mức (FR-AI-007). Chỉ dùng provider giả lập (CLAUDE.md mục 3 luật 6)."""

import json
from unittest.mock import patch

import frappe

from normcore.ai.providers.base import ProviderError
from normcore.api import norm as api
from normcore.api.test_norm import DEPT, NormBase
from normcore.api.test_procedure_ai import FakeProvider, enable_ai
from normcore.tests.utils import ensure, make_equipment, make_procedure, publish_procedure


class TestAiLinkController(NormBase):
	def _suggest(self, name, comp="DRUG", resource="TH-N12", conf=80):
		ns = frappe.get_doc("NC Norm Set", name)
		row = next(r for r in ns.lines if r.component == comp and not r.resource)
		row.resource, row.ai_suggested, row.ai_confidence = resource, 1, conf
		ns.flags.norm_action = "ai_link"
		ns.save(ignore_permissions=True)
		return row.line_id

	def _row(self, name, line_id):
		return next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.line_id == line_id)

	def test_FR_AI_007_chap_nhan_bo_sua_de_xuat_controller(self):
		name = self.make_set()
		lid = self._suggest(name)
		r = self._row(name, lid)
		self.assertEqual((r.resource, r.ai_suggested, r.ai_confidence), ("TH-N12", 1, 80))
		# đường khác (form, client): không đổi được ai_suggested / ai_confidence
		ns = frappe.get_doc("NC Norm Set", name)
		row = next(x for x in ns.lines if x.line_id == lid)
		row.ai_suggested, row.ai_confidence = 0, 5
		ns.save(ignore_permissions=True)
		r = self._row(name, lid)
		self.assertEqual((r.ai_suggested, r.ai_confidence), (1, 80))
		# dòng thêm mới không tự mang đề xuất
		ns = frappe.get_doc("NC Norm Set", name)
		ns.append(
			"lines",
			{
				"service_level": 1,
				"component": "UTILITY",
				"resource_doctype": "NC Item",
				"resource": "DIEN-N12",
				"hospital_qty": 1,
				"uom": "cái",
				"basis": "Ước tính",
				"ai_suggested": 1,
				"ai_confidence": 99,
			},
		)
		ns.save(ignore_permissions=True)
		new = frappe.get_doc("NC Norm Set", name).lines[-1]
		self.assertEqual((new.ai_suggested, new.ai_confidence), (0, 0))
		# "ai_link" trả dòng về trống không đòi nguồn lực (không phải sửa dòng)
		ns = frappe.get_doc("NC Norm Set", name)
		row = next(x for x in ns.lines if x.line_id == lid)
		row.resource, row.ai_suggested, row.ai_confidence = None, 0, 0
		ns.flags.norm_action = "ai_link"
		ns.save(ignore_permissions=True)
		r = self._row(name, lid)
		self.assertEqual((r.resource, r.ai_suggested, r.ai_confidence), (None, 0, 0))
		# "ai_link" không làm đổi trạng thái
		self.assertEqual(frappe.db.get_value("NC Norm Set", name, "status"), "Nháp")


class TestAiLinkApi(NormBase):
	def setUp(self):
		super().setUp()
		ensure("NC Item", "item_code", "TH-LIDO", item_name="Lidocain 2%", item_type="Thuốc", uom="ống", norm_units_per_purchase_unit=1)
		ensure("NC Item", "item_code", "VT-KIM", item_name="Kim tiêm 23G", item_type="Vật tư tiêu hao", uom="cái", norm_units_per_purchase_unit=1)
		ensure("NC Item", "item_code", "CC-NOIKIEM", item_name="Kim tiêm nội kiểm", item_type="Vật liệu nội kiểm", uom="cái", norm_units_per_purchase_unit=1)
		make_equipment("TB-SA", department=DEPT, equipment_name="Máy siêu âm tim")
		enable_ai(1)

	def proc3(self):
		"""Quy trình ban hành: Nhân lực (đã gắn), Thuốc, Vật tư, Thiết bị (chưa gắn)."""
		proc = make_procedure(self.service, DEPT, minutes=10)
		step = proc.steps[0].step_id
		for rtype, text, qty, uom in (
			("Thuốc", "Lidocain 2%", 1, "ống"),
			("Vật tư", "Kim tiêm 23G", 2, "cái"),
			("Thiết bị", "Máy siêu âm tim", 20, "phút"),
		):
			proc.append(
				"resources",
				{"step_id": step, "resource_type": rtype, "resource_text": text, "quantity": qty, "uom": uom},
			)
		proc.save(ignore_permissions=True)
		return publish_procedure(proc)

	def rows(self, proc):
		return {r.resource_type: r.resource_row_id for r in frappe.get_doc("NC Clinical Procedure", proc.name).resources}

	def full_reply(self, proc):
		r = self.rows(proc)
		sug = lambda row, dt, n, comp, c: {"resource_row_id": r[row], "doctype": dt, "name": n, "component": comp, "confidence": c}
		return {
			"suggestions": [
				sug("Thuốc", "NC Item", "TH-LIDO", "DRUG", 0.93),
				sug("Vật tư", "NC Item", "VT-KIM", "SUPPLY", 0.8),
				sug("Thiết bị", "NC Equipment", "TB-SA", "EQUIPMENT", 0.71),
			]
		}

	def create(self, proc, provider):
		frappe.set_user(self.clin)
		with patch("normcore.ai.gateway.get_provider", return_value=provider):
			return api.create_norm_set(proc.name)

	def logs(self):
		return frappe.get_all("NC AI Log", {"ref_doctype": "NC Norm Set"}, pluck="name")

	def lines(self, name):
		return {r.component + (r.procedure_resource_row or ""): r for r in frappe.get_doc("NC Norm Set", name).lines}

	def suggested_set(self):
		proc = self.proc3()
		prov = FakeProvider(self.full_reply(proc))
		out = self.create(proc, prov)
		return proc, out["name"], prov

	def test_FR_AI_007_khoi_tao_de_xuat_lien_ket(self):
		proc = self.proc3()
		before = len(self.logs())
		prov = FakeProvider(self.full_reply(proc))
		out = self.create(proc, prov)
		self.assertTrue(out["link_job"])
		ns = frappe.get_doc("NC Norm Set", out["name"])
		by_type = {r.procedure_resource_row: r for r in ns.lines}
		rows = self.rows(proc)
		for rtype, (dt, name, comp) in {
			"Thuốc": ("NC Item", "TH-LIDO", "DRUG"),
			"Vật tư": ("NC Item", "VT-KIM", "SUPPLY"),
			"Thiết bị": ("NC Equipment", "TB-SA", "EQUIPMENT"),
		}.items():
			ln = by_type[rows[rtype]]
			self.assertEqual((ln.resource_doctype, ln.resource, ln.component), (dt, name, comp))
			self.assertEqual(ln.ai_suggested, 1)
			self.assertTrue(0 <= ln.ai_confidence <= 100)
		self.assertEqual(by_type[rows["Thuốc"]].ai_confidence, 93)
		labor = by_type[rows["Nhân lực"]]
		self.assertEqual((labor.resource, labor.ai_suggested), ("DD", 0))
		st = api.get_link_suggestion_status(out["link_job"])
		self.assertEqual((st["status"], st["suggested"]), ("done", 3))
		self.assertEqual(len(self.logs()) - before, 1)
		# ứng viên gửi AI: không có vật liệu nội kiểm (FR-NORM-024)
		sent = json.dumps(prov.calls[0]["variables"], ensure_ascii=False)
		self.assertNotIn("CC-NOIKIEM", sent)
		got = api.get_norm_set(ns.name)
		self.assertEqual(got["ai_pending"], 3)
		self.assertTrue(got["ai_enabled"])
		self.assertIn("suggest_links", got["actions"])
		self.assertIn("accept_link", got["actions"])
		self.assertEqual(
			sorted(x["ai_confidence"] for g in got["groups"] for x in g["lines"] if x["ai_suggested"]), [71, 80, 93]
		)

	def test_UC009_8a_de_xuat_chua_xu_ly_chan_xac_nhan(self):
		proc, name, _prov = self.suggested_set()
		ln = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.ai_suggested)
		with self.assertRaises(frappe.ValidationError) as cm:
			api.confirm_line(name, ln.line_id)
		self.assertIn("đề xuất AI", str(cm.exception))
		frappe.set_user(self.head)
		with self.assertRaises(frappe.ValidationError) as cm:
			api.confirm_set(name)
		self.assertIn("Còn đề xuất AI chưa xử lý", str(cm.exception))
		frappe.set_user(self.clin)
		out = api.accept_link_suggestions(name, all=1)
		self.assertEqual(out["ai_pending"], 0)
		self.confirm_all(name)
		frappe.set_user(self.head)
		api.confirm_set(name)
		self.assertEqual(frappe.db.get_value("NC Norm Set", name, "status"), "Đã xác nhận chuyên môn")

	def test_FR_AI_007_chap_nhan_bo_sua_de_xuat(self):
		proc, name, _prov = self.suggested_set()
		lines = frappe.get_doc("NC Norm Set", name).lines
		a, b, c = [r for r in lines if r.ai_suggested]
		# Chấp nhận theo danh sách dòng: giữ liên kết, hết nhãn
		out = api.accept_link_suggestions(name, [a.line_id])
		self.assertEqual(out["ai_pending"], 2)
		row = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.line_id == a.line_id)
		self.assertEqual((row.resource, row.ai_suggested, row.ai_confidence), (a.resource, 0, 0))
		with self.assertRaises(frappe.ValidationError):
			api.reject_link_suggestion(name, a.line_id)  # không còn là đề xuất
		with self.assertRaises(frappe.ValidationError):
			api.accept_link_suggestions(name, ["L999"])
		# Bỏ: dòng về chưa liên kết, cấu phần như lúc khởi tạo, không lỗi "Nguồn lực"
		out = api.reject_link_suggestion(name, b.line_id)
		row = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.line_id == b.line_id)
		self.assertEqual((row.resource, row.ai_suggested, row.ai_confidence), (None, 0, 0))
		self.assertIn(row.component, ("SUPPLY", "EQUIPMENT", "DRUG"))
		self.assertEqual(out["ai_pending"], 1)
		# sửa liên kết của dòng đề xuất = đã xử lý; sửa lượng thì giữ đề xuất
		api.save_line(name, {"hospital_qty": 7}, c.line_id)
		row = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.line_id == c.line_id)
		self.assertEqual((row.hospital_qty, row.ai_suggested, row.ai_confidence), (7, 1, c.ai_confidence))
		other = "TB-SA" if row.resource != "TB-SA" else None
		if other:
			api.save_line(name, {"resource": other}, c.line_id)
		else:  # dòng thiết bị: đổi sang thiết bị khác
			make_equipment("TB-SA2", department=DEPT, equipment_name="Máy khác")
			api.save_line(name, {"resource": "TB-SA2"}, c.line_id)
		row = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.line_id == c.line_id)
		self.assertEqual((row.ai_suggested, row.ai_confidence), (0, 0))
		# client không tự đặt được đề xuất hay độ tin cậy
		for field in ("ai_suggested", "ai_confidence"):
			with self.assertRaises(frappe.ValidationError):
				api.save_line(name, {field: 1}, c.line_id)

	def test_FR_AI_007_ai_tat_hoac_loi_khong_de_xuat(self):
		proc = self.proc3()
		before = len(self.logs())
		enable_ai(0)
		prov = FakeProvider(self.full_reply(proc))
		out = self.create(proc, prov)
		self.assertIsNone(out["link_job"])
		self.assertEqual(prov.calls, [])
		self.assertEqual(len(self.logs()), before)
		with self.assertRaises(frappe.ValidationError):
			api.start_link_suggestion(out["name"])
		ns = frappe.get_doc("NC Norm Set", out["name"])
		self.assertFalse(any(r.ai_suggested for r in ns.lines))
		# provider lỗi: trạng thái failed, bộ không đổi
		enable_ai(1)
		with patch("normcore.ai.gateway.get_provider", return_value=FakeProvider(exc=ProviderError("hỏng"))):
			job = api.start_link_suggestion(out["name"])["job_id"]
		st = api.get_link_suggestion_status(job)
		self.assertEqual(st["status"], "failed")
		self.assertTrue(st["message"])
		self.assertFalse(any(r.ai_suggested for r in frappe.get_doc("NC Norm Set", out["name"]).lines))
		# không còn dòng chờ
		with patch("normcore.ai.gateway.get_provider", return_value=FakeProvider(self.full_reply(proc))):
			job = api.start_link_suggestion(out["name"])["job_id"]
			self.assertEqual(api.get_link_suggestion_status(job)["suggested"], 3)
			self.assertIsNone(api.start_link_suggestion(out["name"])["job_id"])
		# mã tác vụ lạ
		self.assertEqual(api.get_link_suggestion_status("khong-co")["status"], "unknown")

	def test_FR_AI_007_quyen_de_xuat_lien_ket(self):
		proc, name, _prov = self.suggested_set()
		line = next(r for r in frappe.get_doc("NC Norm Set", name).lines if r.ai_suggested).line_id
		for user in (self.aud, self.fin, self.clin2):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.start_link_suggestion(name)
			with self.assertRaises(frappe.PermissionError):
				api.accept_link_suggestions(name, all=1)
			with self.assertRaises(frappe.PermissionError):
				api.reject_link_suggestion(name, line)
		frappe.set_user(self.clin)
		with patch("normcore.ai.gateway.get_provider", return_value=FakeProvider({"suggestions": []})):
			api.accept_link_suggestions(name, all=1)
			ns = frappe.get_doc("NC Norm Set", name)
			ns.reload()
			frappe.db.set_value("NC Norm Line", ns.lines[2].name, {"resource": None, "ai_suggested": 0})
			job = api.start_link_suggestion(name)["job_id"]
		for user in (self.aud, self.clin2):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.get_link_suggestion_status(job)
		frappe.set_user(self.aud)
		got = api.get_norm_set(name)
		self.assertIn("ai_confidence", got["groups"][0]["lines"][0])
		self.assertNotIn("suggest_links", got["actions"])
		self.assertNotIn("accept_link", got["actions"])

	def test_FR_AI_011_payload_kiem_tra_va_de_xuat(self):
		proc, name, prov = self.suggested_set()
		blob = json.dumps(prov.calls[0], ensure_ascii=False)
		for forbidden in ("NC Norm", "NC Room", "price", "unit_cost", "hospital_qty", "authority"):
			self.assertNotIn(forbidden, blob)
		cand = prov.calls[0]["variables"]["lines"][0]["candidates"][0]
		self.assertEqual(set(cand), {"doctype", "name", "label", "uom"})
