"""FEAT-039: NC Auditor chỉ đọc (FR-ACC-007, TC-CLS-44, TC-AUD-03)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.core import permissions as perms


class TestQuetQuyen(FrappeTestCase):
	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()
		# Workflow, Custom DocPerm có thể đã commit ngầm: dọn rõ ràng để không làm bẩn site test
		for name in frappe.get_all("Workflow", {"name": ["like", "FEAT39%"]}, pluck="name"):
			frappe.delete_doc("Workflow", name, force=True, ignore_permissions=True)
		for name in frappe.get_all(
			"Custom DocPerm", {"parent": "NC Norm Set", "role": "NC Auditor"}, pluck="name"
		):
			frappe.delete_doc("Custom DocPerm", name, force=True, ignore_permissions=True)
		# Frappe tự tạo Custom Field cho trường trạng thái của Workflow (ALTER TABLE, commit ngầm)
		for name in frappe.get_all("Custom Field", {"name": ["like", "NC Norm Set-feat39%"]}, pluck="name"):
			frappe.delete_doc("Custom Field", name, force=True, ignore_permissions=True)
		for name in frappe.get_all("Workflow State", {"name": ["like", "FEAT39%"]}, pluck="name"):
			frappe.delete_doc("Workflow State", name, force=True, ignore_permissions=True)
		for name in frappe.get_all("Workflow Action Master", {"name": ["like", "FEAT39%"]}, pluck="name"):
			frappe.delete_doc("Workflow Action Master", name, force=True, ignore_permissions=True)
		frappe.clear_cache(doctype="NC Norm Set")
		frappe.db.commit()

	def test_TC_CLS_44_quet_quyen_sach(self):
		self.assertEqual(perms.read_only_violations(), [])
		self.assertIn("NC Norm Set", perms.nc_doctypes())

	def test_TC_CLS_44_quet_bat_custom_docperm(self):
		frappe.get_doc(
			{
				"doctype": "Custom DocPerm",
				"parent": "NC Norm Set",
				"parenttype": "DocType",
				"parentfield": "permissions",
				"role": "NC Auditor",
				"permlevel": 0,
				"read": 1,
				"write": 1,
			}
		).insert(ignore_permissions=True)
		frappe.clear_cache(doctype="NC Norm Set")
		out = perms.read_only_violations()
		self.assertTrue(any("NC Norm Set" in v and "write" in v for v in out), out)

	def test_TC_CLS_44_quet_bat_workflow(self):
		frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": "FEAT39 Nháp"}).insert(
			ignore_if_duplicate=True
		)
		frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": "FEAT39 Duyệt"}).insert(
			ignore_if_duplicate=True
		)
		frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": "FEAT39 Duyệt"}).insert(
			ignore_if_duplicate=True
		)
		frappe.get_doc(
			{
				"doctype": "Workflow",
				"workflow_name": "FEAT39 Thử",
				"document_type": "NC Norm Set",
				"is_active": 0,
				"workflow_state_field": "feat39_state",
				"states": [
					{"state": "FEAT39 Nháp", "doc_status": 0, "allow_edit": "NC Auditor"},
					{"state": "FEAT39 Duyệt", "doc_status": 0, "allow_edit": "NC Admin"},
				],
				"transitions": [
					{
						"state": "FEAT39 Nháp",
						"action": "FEAT39 Duyệt",
						"next_state": "FEAT39 Duyệt",
						"allowed": "NC Auditor",
					}
				],
			}
		).insert(ignore_permissions=True)
		out = perms.read_only_violations()
		self.assertTrue(any("FEAT39 Thử" in v and "chuyển" in v for v in out), out)
		self.assertTrue(any("FEAT39 Thử" in v and "allow_edit" in v for v in out), out)


# --- TC-CLS-44, kịch bản UC-026 -----------------------------------------------------------

from normcore.api import access as access_api
from normcore.api import audit as audit_api
from normcore.api import importer as importer_api
from normcore.api import item as item_api
from normcore.api import procedure as procedure_api
from normcore.core import audit
from normcore.core import import_sets as _import_sets
from normcore.core import importer as importer_core
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set
from normcore.tests.utils import (
	costing_run_inputs,
	ensure,
	make_base,
	make_chain_data,
	make_param_set,
	make_user,
)

AUDITOR = "NC Auditor"
PRICE_SOURCE = "Hóa đơn"


def _snapshot(doctypes):
	"""Số bản ghi và `modified` lớn nhất của từng DocType: thao tác bị từ chối không được đổi."""
	return {
		dt: (
			frappe.db.count(dt),
			frappe.db.get_value(dt, {}, "max(modified)") if dt != "NC Audit Event" else None,
		)
		for dt in doctypes
	}


WATCH = (
	"NC Norm Set",
	"NC Clinical Procedure",
	"NC Costing Run",
	"NC Service Cost",
	"NC Costing Parameter Set",
	"NC Item Price",
)


class TestTCCLS44(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()
		self.chain = make_chain_data(self.service, self.dept)
		self.service2, self.dept2, _ = make_base(service="DV-TEST-B", department="KHOA-TEST-2")
		self.chain2 = make_chain_data(self.service2, self.dept2)
		self.auditor = make_user("auditor.f39@normcore.test", AUDITOR)
		self.finance = make_user("fin.f39@normcore.test", "NC Finance")
		audit.log_event("Xuất tệp", "NC Department", self.dept, detail="f39")
		frappe.get_doc(
			{
				"doctype": "NC AI Log",
				"purpose": "DRAFT_PROCEDURE",
				"status": "Thành công",
				"user": "Administrator",
			}
		).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_CLS_44_doc_so_lieu_nhat_ky(self):
		frappe.set_user(self.auditor)
		for dt in ("NC Costing Run", "NC Service Cost", "NC Audit Event", "NC AI Log", "NC Norm Set"):
			self.assertTrue(frappe.has_permission(dt, "read"), dt)
			self.assertTrue(frappe.get_list(dt, limit_page_length=1), dt)
		frappe.get_doc("NC Costing Run", self.chain.run)
		frappe.get_doc("NC Service Cost", self.chain.cost)
		self.assertTrue(audit_api.get_events(ref_name=self.dept))
		# bộ định mức của hai khoa khác nhau: Auditor không bị hẹp theo khoa
		names = {r.name for r in frappe.get_list("NC Norm Set", fields=["name"])}
		self.assertTrue({self.chain.norm_set, self.chain2.norm_set} <= names)

	def test_TC_CLS_44_sua_bo_dinh_muc_bi_tu_choi(self):
		before = frappe.db.get_value("NC Norm Set", self.chain.norm_set, ["modified", "status"])
		count = frappe.db.count("NC Norm Set")
		frappe.set_user(self.auditor)
		ns = frappe.get_doc("NC Norm Set", self.chain.norm_set)
		ns.lines[0].hospital_qty = 999
		with self.assertRaises(frappe.PermissionError):
			ns.save()
		with self.assertRaises(frappe.PermissionError):
			frappe.delete_doc("NC Norm Set", self.chain.norm_set)
		frappe.set_user("Administrator")
		self.assertEqual(
			frappe.db.get_value("NC Norm Set", self.chain.norm_set, ["modified", "status"]), before
		)
		self.assertEqual(frappe.db.count("NC Norm Set"), count)
		self.assertNotEqual(frappe.get_doc("NC Norm Set", self.chain.norm_set).lines[0].hospital_qty, 999)

	def test_TC_CLS_44_ghi_xoa_duyet_bi_tu_choi(self):
		ns = frappe.get_doc("NC Norm Set", self.chain.norm_set)
		proc = frappe.get_doc("NC Clinical Procedure", self.chain.procedure)
		param = make_param_set()
		run = frappe.get_doc(
			{
				"doctype": "NC Costing Run",
				"title": "Lần tính f39",
				"fiscal_year": 2026,
				"costing_date": "2026-10-02",
				"parameter_set": param.name,
				**costing_run_inputs(),
			}
		).insert(ignore_permissions=True)
		ensure("NC Item", "item_code", "F39-ITEM", item_name="Mặt hàng f39", item_type="Thuốc", uom="viên")
		price = frappe.get_doc(
			{
				"doctype": "NC Item Price",
				"item": "F39-ITEM",
				"unit_price": 1000,
				"price_source": PRICE_SOURCE,
				"document_no": "CT-F39",
				"document_date": "2026-01-01",
				"valid_from": "2026-01-01",
			}
		).insert(ignore_permissions=True)
		set_key = next(iter(importer_core.REGISTRY))
		events_before = frappe.db.count("NC Audit Event")
		before = _snapshot(WATCH)
		frappe.set_user(self.auditor)
		new_ns = frappe.get_doc("NC Norm Set", self.chain.norm_set)

		ops = {
			"make_norm_set": lambda: make_norm_set(self.chain.procedure),
			"lock": new_ns.lock,
			"publish": proc.publish,
			"create_procedure": lambda: procedure_api.create_procedure(self.service2, self.dept2),
			"save_sections": lambda: procedure_api.save_sections(self.chain.procedure, "{}"),
			"add_step": lambda: procedure_api.add_step(self.chain.procedure, "Thực hiện", "B", "d"),
			"run_costing": run.run_costing,
			"duplicate": param.duplicate,
			"import_file": lambda: importer_api.import_file(set_key, "/private/files/none.xlsx", "ghi"),
			"assign_department": lambda: access_api.assign_department(self.auditor, self.dept),
			"client.set_value": lambda: frappe.client.set_value(
				"NC Norm Set", self.chain.norm_set, "status", "Nháp"
			),
			"client.insert": lambda: frappe.client.insert(
				{
					"doctype": "NC Costing Run",
					"title": "x",
					"fiscal_year": 2026,
					"parameter_set": param.name,
					**costing_run_inputs(),
				}
			),
			"client.delete": lambda: frappe.client.delete("NC Costing Run", run.name),
			"client.delete_event": lambda: frappe.client.delete(
				"NC Audit Event", frappe.get_all("NC Audit Event", pluck="name", limit=1)[0]
			),
		}
		ops["verify_price"] = lambda: item_api.verify_price(price.name)
		for label, op in ops.items():
			with self.subTest(op=label):
				with self.assertRaises(frappe.PermissionError):
					op()
		frappe.set_user("Administrator")
		self.assertEqual(_snapshot(WATCH), before)
		self.assertEqual(frappe.db.count("NC Audit Event"), events_before)
		self.assertEqual(frappe.db.get_value("NC Norm Set", ns.name, "status"), "Đã khóa")

	def test_TC_CLS_44_vai_tro_khac_khong_bi_hep(self):
		both = make_user("both.f39@normcore.test", AUDITOR, "NC Finance")
		param = make_param_set()
		frappe.set_user(both)
		self.assertTrue(frappe.has_permission("NC Costing Parameter Set", "write"))
		doc = frappe.get_doc("NC Costing Parameter Set", param.name)
		doc.title = "Đổi tên f39"
		doc.save()
		self.assertEqual(frappe.db.get_value("NC Costing Parameter Set", param.name, "title"), "Đổi tên f39")
		frappe.set_user(self.finance)  # Finance không có NC Auditor: ghi được như trước
		self.assertTrue(frappe.has_permission("NC Costing Parameter Set", "write"))


class TestTCAUD03Auditor(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, self.job = make_base()
		self.auditor = make_user("auditor.f39b@normcore.test", AUDITOR)
		self.director = make_user("dir.f39b@normcore.test", "NC Director")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_TC_AUD_03_auditor_loc_theo_quy_trinh(self):
		from normcore.tests.utils import make_procedure, publish_procedure

		p1 = make_procedure(self.service, self.dept)
		p2 = make_procedure(self.service, self.dept, version=2)
		frappe.set_user(self.director)
		publish_procedure(p1, "QĐ-39", "2026-12-01")
		frappe.set_user(self.auditor)
		rows = audit_api.get_events(ref_doctype="NC Clinical Procedure", ref_name=p1.name)
		self.assertEqual([r["to_state"] for r in rows], ["Nháp", "Đã ban hành"])
		self.assertEqual({r["ref_name"] for r in rows}, {p1.name})
		times = [r["event_time"] for r in rows]
		self.assertEqual(times, sorted(times))
		other = audit_api.get_events(ref_doctype="NC Clinical Procedure", ref_name=p2.name)
		self.assertEqual({r["ref_name"] for r in other}, {p2.name})
