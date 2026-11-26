"""FEAT-018 trên site: khóa kèm ảnh chụp đầu vào, tái lập, nhân bản, bản ghi đã khóa (technical-design 6)."""

import sys

import frappe
from frappe.tests.utils import FrappeTestCase

sys.path.insert(0, frappe.get_app_path("normcore", "..", "docs", "golden"))
import golden_engine as g

from normcore.costing import snapshot
from normcore.tests import cls_fixtures as fx
from normcore.tests import costing_fixtures as cf
from normcore.tests.golden import test_costing_golden as tg

LOCKED = "Đã khóa"


class TestCostingRunLock(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.params, self.dept, self.sets = cf.make_golden_world()
		self.imp = cf.make_golden_allocation(self.dept)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _run(self, **kw):
		run = cf.make_golden_run(self.params, accounting_import=self.imp, **kw)
		self.assertEqual(run.run_costing(), "Đã tính")
		return run

	def _explain(self, run):
		name = frappe.db.get_value(
			"NC Reconciliation Line", {"costing_run": run.name, "cost_category": "DRUG_SUPPLY"}
		)
		frappe.db.set_value("NC Reconciliation Line", name, "explanation", "Nhập thuốc chưa xuất kho")

	def _locked_run(self):
		run = self._run()
		self._explain(run)
		self.assertEqual(run.lock_costing(), LOCKED)
		return run.reload()

	def _set_gang_price(self, price):
		frappe.db.set_value("NC Item Price", {"price_code": "DG-GANG"}, "unit_price", price)

	def _unpack(self, run):
		file = frappe.get_doc("File", {"file_url": run.snapshot_file})
		content = file.get_content()
		return file, snapshot.unpack(
			content.encode() if isinstance(content, str) else content, run.snapshot_hash
		)

	def _l02(self, run):
		sc = frappe.get_doc("NC Service Cost", {"costing_run": run.name, "technical_service": "DV-TEST-A"})
		return next(ln.amount for ln in sc.lines if ln.norm_line_id == "L02")

	def test_TC_COST_09_tinh_lai_tu_anh_chup_trung_moi_truong(self):
		run = self._run()
		self._explain(run)
		before = self._stored(run)
		self.assertEqual(run.lock_costing(), LOCKED)
		run.reload()
		file, snap = self._unpack(run)
		self.assertEqual(file.is_private, 1)
		self.assertEqual((file.attached_to_doctype, file.attached_to_name), ("NC Costing Run", run.name))
		self.assertEqual(len(run.snapshot_hash), 64)
		self.assertEqual(run.snapshot_hash, snapshot.digest(snapshot.dumps(snap)))
		event = frappe.get_all(
			"NC Audit Event",
			{"ref_doctype": "NC Costing Run", "ref_name": run.name, "event_type": "Khóa"},
			["detail"],
		)
		self.assertTrue(event and run.snapshot_hash[:12] in event[0].detail)
		self.assertEqual(self._l02(run), 6000.0)
		self._set_gang_price(5000)
		res = run.verify_snapshot()
		self.assertTrue(res["ok"], res)
		self.assertEqual((res["diff_count"], res["services"]), (0, 2))
		by = {r.service: r for r in snapshot.recompute(snap).results}
		g_res = g.run()[0]
		self.assertEqual(float(by["DV-TEST-A"].direct_total), 183963.06)
		self.assertEqual(by["DV-TEST-A"].price.full_cost, g_res["DV-TEST-A"]["full"])
		self.assertEqual(float(by["DV-TEST-A"].price.full_cost), 287745.46)
		self.assertEqual(self._stored(run), before)
		dup = frappe.get_doc("NC Costing Run", run.duplicate_run())
		self.assertEqual(dup.run_costing(), "Đã tính")
		self.assertEqual(self._l02(dup), 10000.0)
		self.assertEqual(self._l02(run), 6000.0)

	def _stored(self, run):
		from normcore.nc_costing.doctype.nc_costing_run import loader

		return sorted((r["key"], sorted(r["values"].items(), key=str)) for r in loader.stored_rows(run))

	def test_khoa_tu_choi_khi_dau_vao_doi_sau_lan_tinh(self):
		run = self._run()
		self._explain(run)
		files = frappe.db.count("File", {"attached_to_name": run.name})
		self._set_gang_price(5000)
		with self.assertRaises(frappe.ValidationError) as cm:
			run.lock_costing()
		self.assertIn("Đầu vào đã thay đổi", str(cm.exception))
		self.assertIn("khác biệt", str(cm.exception))
		self.assertIn("≠", str(cm.exception))
		self.assertEqual(frappe.db.get_value("NC Costing Run", run.name, "status"), "Đã tính")
		self.assertFalse(frappe.db.get_value("NC Costing Run", run.name, "snapshot_hash"))
		self.assertEqual(frappe.db.count("File", {"attached_to_name": run.name}), files)
		run.reload()
		self.assertEqual(run.run_costing(), "Đã tính")
		self._explain(run)
		self.assertEqual(run.lock_costing(), LOCKED)

	def test_kiem_tra_tai_lap_phat_hien_tep_bi_sua(self):
		run = self._locked_run()
		other, _ = snapshot.pack(snapshot.build([], tg._params()))
		file = frappe.get_doc("File", {"file_url": run.snapshot_file})
		with open(file.get_full_path(), "wb") as fh:
			fh.write(other)
		res = run.verify_snapshot()
		self.assertFalse(res["ok"])
		self.assertIn("mã băm không khớp", res["diffs"][0])

	def test_TC_COST_11_da_khoa_tu_choi_tinh_nhan_ban_ra_nhap(self):
		from normcore.api import costing as api

		run = self._locked_run()
		costs = frappe.db.count("NC Service Cost", {"costing_run": run.name})
		for call in (lambda: run.run_costing(), lambda: api.start_costing(run.name)):
			with self.assertRaises(frappe.ValidationError) as cm:
				call()
			self.assertIn("đã khóa, không tính lại được", str(cm.exception))
			self.assertIn("Nhân bản", str(cm.exception))
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": run.name}), costs)
		new = frappe.get_doc("NC Costing Run", run.duplicate_run())
		self.assertEqual((new.status, new.progress), ("Nháp", 0))
		for f in ("fiscal_year", "costing_date", "parameter_set", "accounting_import", "price_category"):
			self.assertEqual(new.get(f), run.get(f), f)
		self.assertFalse(new.snapshot_file or new.snapshot_hash or new.allocation_warnings)
		self.assertEqual(frappe.db.count("NC Service Cost", {"costing_run": new.name}), 0)
		self.assertEqual(frappe.db.count("NC Reconciliation Line", {"costing_run": new.name}), 0)
		self.assertTrue(
			frappe.db.exists(
				"Comment",
				{
					"reference_doctype": "NC Costing Run",
					"reference_name": new.name,
					"content": ["like", f"%{run.name}%"],
				},
			)
		)
		run.reload()
		self.assertEqual((run.status, bool(run.snapshot_file)), (LOCKED, True))
		self.assertEqual(new.run_costing(), "Đã tính")

	def test_ban_ghi_da_khoa_khong_sua_khong_xoa(self):
		run = self._locked_run()
		run.title = "x"
		with self.assertRaises(frappe.ValidationError):
			run.save()
		with self.assertRaises(frappe.ValidationError):
			frappe.client.set_value("NC Costing Run", run.name, "snapshot_hash", "x")
		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("NC Costing Run", run.name)
		self.assertTrue(frappe.db.exists("NC Costing Run", run.name))
		new = frappe.get_doc(
			{
				**run.as_dict(),
				"name": None,
				"status": LOCKED,
				"title": "Chèn thẳng",
				"snapshot_file": "x",
				"snapshot_hash": "y",
			}
		)
		new.insert(ignore_permissions=True)
		self.assertEqual(new.status, LOCKED)
		self.assertFalse(new.snapshot_hash)


class TestCostingRunLockCls(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.addCleanup(frappe.db.rollback)
		self.world = fx.make_cls_golden()

	def test_TC_CLS_38_khoa_that_tai_lap_tu_anh_chup(self):
		run = fx.make_run(self.world)
		run.run_costing(confirm_ineligible=1)
		run.reload()
		for name in frappe.get_all(
			"NC Reconciliation Line", {"costing_run": run.name, "over_tolerance": 1}, pluck="name"
		):
			frappe.db.set_value("NC Reconciliation Line", name, "explanation", "Giải trình")
		self.assertEqual(run.lock_costing(), LOCKED)
		frappe.db.set_value("NC QC IQC Line", {"parent": "KHCL-GLU-A"}, "levels", 3)
		frappe.db.set_value("NC Equipment Compliance", {"equipment": "EQ_A"}, "cost_per_time", 16000000)
		res = run.reload().verify_snapshot()
		self.assertTrue(res["ok"], res)
