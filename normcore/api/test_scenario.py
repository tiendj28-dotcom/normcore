"""FEAT-029: kịch bản điều chỉnh và yêu cầu sửa quy trình (FR-ADJ-006, 007, 009; UC-014 4 đến 6, 4b; UC-007 1c)."""

import time

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import price_compare as pc
from normcore.api import scenario as api
from normcore.core import permissions
from normcore.tests import costing_fixtures as cf
from normcore.tests.utils import make_base, make_user, publish_procedure

COST, ADJ, PCR, NS, RUN, PROC = (
	"NC Service Cost",
	"NC Adjustment Suggestion",
	"NC Procedure Change Request",
	"NC Norm Set",
	"NC Costing Run",
	"NC Clinical Procedure",
)
GOLDEN_PRICE = 302132.73


class ScenarioBase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fin = make_user("fin.n83b@normcore.test", "NC Finance")
		self.aud = make_user("aud.n83b@normcore.test", "NC Auditor")
		self.dir = make_user("dir.n83b@normcore.test", "NC Director")
		self.head = make_user("head.n83b@normcore.test", "NC Department Head")
		self.cons = make_user("cons.n83b@normcore.test", "NC Consultant")
		self.adm = make_user("adm.n83b@normcore.test", "NC Admin")
		self.params, self.dept, self.sets = cf.make_golden_world()
		frappe.db.set_value("NC Department", self.dept, "head_user", self.head)
		permissions.assign_department(self.head, self.dept)
		# TC-ADJ-05: EQ1 hệ số 0,4 trước khi tính lần gốc (golden dùng 0,5)
		frappe.db.set_value("NC Equipment", "EQ1", "utilization_rate", 0.4)
		self.imp = cf.make_golden_allocation(self.dept)
		self.run = cf.make_golden_run(self.params, accounting_import=self.imp)
		self.assertEqual(self.run.run_costing(), "Đã tính")
		self.cost = frappe.get_value(COST, {"costing_run": self.run.name, "technical_service": "DV-TEST-A"})
		self.base_price = frappe.db.get_value(COST, self.cost, "calculated_price")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def suggestion(self, rule, target, current, suggested, proc=False, **kw):
		doc = frappe.get_doc(
			{
				"doctype": ADJ,
				"service_cost": self.cost,
				"rule_code": rule,
				"direction": "Giảm",
				"component": kw.pop("component", "EQUIPMENT"),
				"target_ref": target,
				"current_value": current,
				"suggested_value": suggested,
				"requires_procedure_change": 1 if proc else 0,
				**kw,
			}
		)
		doc.flags.adj_system = True
		return doc.insert(ignore_permissions=True).name

	def origin_state(self):
		rows = frappe.get_all(
			COST, {"costing_run": self.run.name}, ["name", "calculated_price", "full_cost", "modified"]
		)
		run = frappe.db.get_value(RUN, self.run.name, ["status", "modified"])
		return sorted((r.name, r.calculated_price, r.full_cost, r.modified) for r in rows), run

	def locked_set(self):
		return frappe.get_value(
			NS, {"technical_service": "DV-TEST-A", "department": self.dept, "status": "Đã khóa"}
		)

	def drafts(self):
		return frappe.get_all(
			NS, {"technical_service": "DV-TEST-A", "department": self.dept, "status": "Nháp"}, pluck="name"
		)

	def scenario_price(self, scenario):
		return frappe.db.get_value(
			COST, {"costing_run": scenario, "technical_service": "DV-TEST-A"}, "calculated_price"
		)


class TestScenario(ScenarioBase):
	def test_TC_ADJ_05_kich_ban_tinh_lai_goc_khong_doi(self):
		adj = self.suggestion("BR-ADJ-001", "EQ1", "0,4", "0,5")
		before = self.origin_state()
		frappe.set_user(self.fin)
		t0 = time.monotonic()
		out = api.accept_suggestion(adj)
		print(f"\n[ASM-029-16] accept_suggestion trên bộ vàng: {time.monotonic() - t0:.2f} s")
		self.assertEqual(out["outcome"], "scenario")
		sc = frappe.get_doc(RUN, out["scenario"])
		self.assertEqual(sc.based_on_run, self.run.name)
		self.assertEqual(len(sc.scenario_changes), 1)
		ch = sc.scenario_changes[0]
		self.assertEqual(
			(ch.change_type, ch.target_ref, ch.field, ch.old_value, ch.new_value, ch.source_suggestion),
			("Thiết bị", "EQ1", "utilization_rate", "0.4", "0.5", adj),
		)
		self.assertNotEqual(self.base_price, GOLDEN_PRICE)
		self.assertAlmostEqual(float(self.scenario_price(sc.name)), GOLDEN_PRICE, places=2)
		self.assertAlmostEqual(float(out["scenario_price"]), GOLDEN_PRICE, places=2)
		self.assertEqual(sc.status, "Đã tính")
		self.assertEqual(self.origin_state(), before)  # lần gốc không đổi
		self.assertEqual(frappe.db.get_value(ADJ, adj, "status"), "Chấp nhận")
		with self.assertRaises(frappe.ValidationError):  # kịch bản không sinh gợi ý
			pc.generate_suggestions(frappe.get_value(COST, {"costing_run": sc.name}))

	def test_TC_ADJ_06_yeu_cau_sua_quy_trinh(self):
		adj = self.suggestion(
			"BR-ADJ-003", "L05", "THUOCX", "THUOCZ", proc=True, component="DRUG", estimated_impact=-1000
		)
		sets_before = frappe.db.count(NS)
		lines_before = frappe.get_all("NC Norm Line", {"parent": self.locked_set()}, ["name", "hospital_qty"])
		frappe.set_user(self.fin)
		out = api.accept_suggestion(adj)
		frappe.set_user("Administrator")
		self.assertEqual(out["outcome"], "procedure_request")
		self.assertEqual(frappe.db.count(NS), sets_before)
		self.assertEqual(
			frappe.get_all("NC Norm Line", {"parent": self.locked_set()}, ["name", "hospital_qty"]),
			lines_before,
		)
		self.assertIsNone(frappe.get_value(RUN, {"based_on_run": self.run.name}))
		req = frappe.get_doc(PCR, out["change_request"])
		proc = frappe.get_value(
			PROC, {"technical_service": "DV-TEST-A", "department": self.dept, "workflow_state": "Đã ban hành"}
		)
		self.assertEqual(
			(req.status, req.procedure, req.source_suggestion, req.requested_by),
			("Mới", proc, adj, self.fin),
		)
		self.assertIn("BR-ADJ-003", req.proposed_change)
		self.assertIn("THUOCZ", req.proposed_change)
		self.assertEqual(out["notified"], [self.head])
		self.assertTrue(
			frappe.db.exists(
				"Notification Log", {"for_user": self.head, "document_type": PCR, "document_name": req.name}
			)
		)
		self.assertEqual(frappe.db.get_value(ADJ, adj, "status"), "Đã chuyển yêu cầu sửa quy trình")

	def test_TC_ADJ_07_bo_dinh_muc_nhap_so_phut_moi(self):
		adj = self.suggestion(
			"BR-ADJ-002", "L04", "20 phút", "15 phút", component="LABOR", estimated_impact=-5000
		)
		locked = self.locked_set()
		before = frappe.get_doc(NS, locked)
		frappe.set_user(self.fin)
		out = api.accept_suggestion(adj)
		frappe.set_user("Administrator")
		self.assertEqual((out["outcome"], out["norm_set_created"]), ("scenario", 1))
		draft = frappe.get_doc(NS, out["norm_set"])
		self.assertEqual(
			(draft.status, draft.previous_version, draft.version_no), ("Nháp", locked, before.version_no + 1)
		)
		l04 = next(r for r in draft.lines if r.line_id == "L04")
		self.assertEqual(l04.hospital_qty, 15)
		self.assertFalse(l04.confirmed_by)
		self.assertEqual(
			next(r for r in frappe.get_doc(NS, locked).lines if r.line_id == "L04").hospital_qty, 20
		)
		self.assertEqual(frappe.get_doc(NS, locked).status, "Đã khóa")
		sc = frappe.get_doc(RUN, out["scenario"])
		self.assertEqual(
			(sc.scenario_changes[0].change_type, sc.scenario_changes[0].target_ref),
			("Dòng định mức", "L04"),
		)
		self.assertLess(float(self.scenario_price(sc.name)), float(self.base_price))
		self.assertTrue(
			frappe.db.exists(
				"Notification Log", {"for_user": self.head, "document_type": NS, "document_name": draft.name}
			)
		)

	def test_FR_ADJ_006_cong_don_va_ghi_de(self):
		a1 = self.suggestion("BR-ADJ-001", "EQ1", "0,4", "0,5")
		a2 = self.suggestion("BR-ADJ-005", self.params.name, "5%", "4%", component="PARAMETER")
		frappe.set_user(self.fin)
		o1 = api.accept_suggestion(a1)
		o2 = api.accept_suggestion(a2)
		self.assertEqual(o1["scenario"], o2["scenario"])
		self.assertEqual(frappe.db.count(RUN, {"based_on_run": self.run.name}), 1)
		sc = frappe.get_doc(RUN, o1["scenario"])
		self.assertEqual([c.change_type for c in sc.scenario_changes], ["Thiết bị", "Tham số"])
		self.assertEqual(sc.scenario_changes[1].new_value, "4")
		# cùng khóa: ghi đè new_value, giữ old_value đầu tiên
		frappe.set_user("Administrator")
		a3 = self.suggestion("BR-ADJ-001", "EQ1", "0,5", "0,6")
		frappe.set_user(self.fin)
		api.accept_suggestion(a3)
		sc.reload()
		self.assertEqual(len(sc.scenario_changes), 2)
		eq = sc.scenario_changes[0]
		self.assertEqual((eq.old_value, eq.new_value, eq.source_suggestion), ("0.4", "0.6", a3))
		view = api.get_open_scenario(self.run.name)
		self.assertEqual(view["change_count"], 2)
		row = next(r for r in view["rows"] if r["technical_service"] == "DV-TEST-A")
		self.assertEqual(row["base_price"], self.base_price)
		self.assertEqual(row["scenario_price"], self.scenario_price(sc.name))
		self.assertAlmostEqual(row["diff"], row["scenario_price"] - row["base_price"], places=2)
		self.assertTrue(view["can_create"])
		# kịch bản mới bắt đầu từ lần gốc, không mang thay đổi cũ
		new = api.create_scenario(self.run.name)["name"]
		self.assertNotEqual(new, sc.name)
		self.assertEqual(api.get_open_scenario(self.run.name)["name"], new)
		self.assertEqual(api.get_open_scenario(self.run.name)["change_count"], 0)

	def test_FR_ADJ_006_decide_cung_ghi_kich_ban(self):
		adj = self.suggestion("BR-ADJ-001", "EQ1", "0,4", "0,5")
		proc = self.suggestion("BR-ADJ-003", "L05", "THUOCX", "THUOCZ", proc=True, component="DRUG")
		frappe.set_user(self.fin)
		d = pc.decide_suggestion(adj, "Chấp nhận")
		self.assertEqual(d["status"], "Chấp nhận")
		sc = frappe.get_value(RUN, {"based_on_run": self.run.name})
		self.assertTrue(sc)
		self.assertAlmostEqual(float(self.scenario_price(sc)), GOLDEN_PRICE, places=2)
		with self.assertRaises(frappe.ValidationError) as ctx:
			pc.decide_suggestion(proc, "Chấp nhận")
		self.assertIn("sửa quy trình", str(ctx.exception))
		self.assertEqual(frappe.db.get_value(ADJ, proc, "status"), "Mới")
		detail = pc.get_service_detail(self.cost)
		self.assertFalse(detail["is_scenario"])
		self.assertTrue(detail["can_request_change"])

	def test_FR_ADJ_009_dung_bo_nhap_dang_co(self):
		a1 = self.suggestion("BR-ADJ-002", "L04", "20 phút", "15 phút", component="LABOR")
		a2 = self.suggestion("BR-ADJ-002", "L03", "20 phút", "18 phút", component="LABOR")
		frappe.set_user(self.fin)
		o1 = api.accept_suggestion(a1)
		o2 = api.accept_suggestion(a2)
		frappe.set_user("Administrator")
		self.assertEqual((o1["norm_set_created"], o2["norm_set_created"]), (1, 0))
		self.assertEqual(o1["norm_set"], o2["norm_set"])
		self.assertEqual(self.drafts(), [o1["norm_set"]])
		lines = {r.line_id: r.hospital_qty for r in frappe.get_doc(NS, o1["norm_set"]).lines}
		self.assertEqual((lines["L04"], lines["L03"]), (15, 18))

	def test_FR_ADJ_009_bo_cho_khoa_chan(self):
		a1 = self.suggestion("BR-ADJ-002", "L04", "20 phút", "15 phút", component="LABOR")
		a2 = self.suggestion("BR-ADJ-002", "L03", "20 phút", "18 phút", component="LABOR")
		frappe.set_user(self.fin)
		o1 = api.accept_suggestion(a1)
		frappe.db.set_value(NS, o1["norm_set"], "status", "Đã xác nhận chuyên môn")
		with self.assertRaises(frappe.ValidationError) as ctx:
			api.accept_suggestion(a2)
		self.assertIn("chờ khóa", str(ctx.exception))
		self.assertEqual(frappe.db.get_value(ADJ, a2, "status"), "Mới")
		sc = frappe.get_doc(RUN, o1["scenario"])
		self.assertEqual([c.target_ref for c in sc.scenario_changes], ["L04"])  # L03 đã hoàn tác

	def test_FR_ADJ_007_de_xuat_nguoi_dung(self):
		frappe.set_user(self.fin)
		for reason in (None, "  "):
			with self.assertRaises(frappe.ValidationError):
				api.request_procedure_change(self.cost, "Thêm bước kiểm tra", reason)
		with self.assertRaises(frappe.ValidationError):
			api.request_procedure_change(self.cost, " ", "Giảm thời gian")
		out = api.request_procedure_change(self.cost, "Thêm bước kiểm tra", "Giảm thời gian")
		frappe.set_user("Administrator")
		req = frappe.get_doc(PCR, out["change_request"])
		self.assertFalse(req.source_suggestion)
		self.assertIn("Thêm bước kiểm tra", req.proposed_change)
		self.assertIn("Giảm thời gian", req.proposed_change)
		self.assertEqual(out["notified"], [self.head])
		frappe.set_user(self.aud)
		with self.assertRaises(frappe.PermissionError):
			api.request_procedure_change(self.cost, "x", "y")

	def _request(self):
		adj = self.suggestion("BR-ADJ-003", "L05", "THUOCX", "THUOCZ", proc=True, component="DRUG")
		frappe.set_user(self.fin)
		name = api.accept_suggestion(adj)["change_request"]
		frappe.set_user("Administrator")
		return name

	def test_UC_007_1c_tiep_nhan_tao_ban_nhap(self):
		name = self._request()
		make_base("DV-N83-X", "KHOA-N83-X")
		head2 = make_user("head2.n83b@normcore.test", "NC Department Head")
		permissions.assign_department(head2, "KHOA-N83-X")
		for user in (head2, self.fin, self.aud, self.cons):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.act_on_change_request(name, "Tiếp nhận")
		frappe.set_user(self.head)
		self.assertEqual(api.change_request_actions(name), ["Tiếp nhận", "Từ chối"])
		out = api.act_on_change_request(name, "Tiếp nhận")
		frappe.set_user("Administrator")
		rev = frappe.get_doc(PROC, out["revision"])
		self.assertEqual(rev.workflow_state, "Nháp")
		self.assertEqual(frappe.db.get_value(PCR, name, "status"), "Đã tiếp nhận")
		note = frappe.db.get_value(PCR, name, "proposed_change")
		comments = frappe.get_all(
			"Comment",
			{"reference_doctype": PROC, "reference_name": rev.name, "comment_type": "Info"},
			pluck="content",
		)
		self.assertTrue(any(note in c or "BR-ADJ-003" in c for c in comments))

	def test_FR_ADJ_007_luong_trang_thai(self):
		name = self._request()
		frappe.set_user(self.head)
		for action, reason in (("Từ chối", None), ("Từ chối", " "), ("Đã thực hiện", None), ("Lạ", None)):
			with self.assertRaises(frappe.ValidationError):
				api.act_on_change_request(name, action, reason)
		out = api.act_on_change_request(name, "Tiếp nhận")
		with self.assertRaises(frappe.ValidationError):
			api.act_on_change_request(name, "Tiếp nhận")
		with self.assertRaises(frappe.ValidationError) as ctx:  # chưa ban hành phiên bản mới
			api.act_on_change_request(name, "Đã thực hiện")
		self.assertIn("chưa ban hành", str(ctx.exception))
		frappe.set_user("Administrator")
		publish_procedure(frappe.get_doc(PROC, out["revision"]), "QĐ-2", "2026-12-01")
		frappe.set_user(self.head)
		self.assertEqual(api.change_request_actions(name), ["Từ chối", "Đã thực hiện"])
		self.assertEqual(api.act_on_change_request(name, "Đã thực hiện")["status"], "Đã thực hiện")
		self.assertEqual(api.change_request_actions(name), [])
		# từ chối có lý do
		frappe.set_user("Administrator")
		name2 = self._request_again()
		frappe.set_user(self.head)
		self.assertEqual(api.act_on_change_request(name2, "Từ chối", "Không khả thi")["status"], "Từ chối")
		frappe.set_user("Administrator")
		self.assertTrue(
			frappe.db.exists(
				"Notification Log", {"for_user": self.fin, "document_type": PCR, "document_name": name2}
			)
		)

	def _request_again(self):
		frappe.set_user(self.fin)
		out = api.request_procedure_change(self.cost, "Bỏ bước 2", "Trùng lặp")
		frappe.set_user("Administrator")
		return out["change_request"]

	def test_quyen_chap_nhan_va_xem_kich_ban(self):
		adj = self.suggestion("BR-ADJ-001", "EQ1", "0,4", "0,5")
		make_base("DV-N83-Y", "KHOA-N83-Y")
		head2 = make_user("head2.n83c@normcore.test", "NC Department Head")
		permissions.assign_department(head2, "KHOA-N83-Y")
		for user in (head2, self.cons, self.adm, self.aud):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.accept_suggestion(adj)
		self.assertEqual(frappe.db.get_value(ADJ, adj, "status"), "Mới")
		frappe.set_user(self.head)  # Trưởng khoa khoa mình được
		self.assertEqual(api.accept_suggestion(adj)["outcome"], "scenario")
		view = api.get_open_scenario(self.run.name)
		self.assertEqual([r["technical_service"] for r in view["rows"]], ["DV-TEST-A", "DV-TEST-B"])
		self.assertFalse(view["can_create"])
		frappe.set_user(head2)  # khoa khác: thấy kịch bản nhưng không có dòng nào của khoa kia
		self.assertEqual(api.get_open_scenario(self.run.name)["rows"], [])
		frappe.set_user(self.aud)
		self.assertEqual(len(api.get_open_scenario(self.run.name)["rows"]), 2)
		with self.assertRaises(frappe.PermissionError):
			api.create_scenario(self.run.name)
		frappe.set_user(self.dir)
		a2 = self.suggestion("BR-ADJ-005", self.params.name, "5%", "4%", component="PARAMETER")
		self.assertEqual(api.accept_suggestion(a2)["outcome"], "scenario")
