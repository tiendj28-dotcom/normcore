import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import time_study as api
from normcore.nc_costing.doctype.nc_time_study.test_nc_time_study import make_four_step_procedure
from normcore.tests.utils import make_base, make_user


class TestTimeStudyApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _job = make_base("DV-BG", "K01")
		self.proc = make_four_step_procedure(self.service, self.dept)
		self.doc = frappe.get_doc(
			{"doctype": "NC Time Study", "technical_service": self.service, "department": self.dept}
		).insert()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_get_entry_co_buoc_va_nhan(self):
		r = api.get_entry(self.doc.name)
		self.assertEqual(len(r["steps"]), 4)
		self.assertEqual([s["step_title"] for s in r["steps"]], ["B1", "B2", "B3", "B4"])
		self.assertEqual(r["doc"]["procedure"], self.proc.name)
		labels = {
			(ln["job_title"], ln["equipment"]): (ln["job_title_label"], ln["equipment_label"])
			for ln in r["lines"]
		}
		self.assertEqual(labels[("BS", None)][0], "Bác sĩ")
		self.assertEqual(labels[(None, "EQ1")][1], "Thiết bị thử")
		self.assertTrue(r["can_write"])

	def test_get_entry_auditor_khong_ghi_duoc(self):
		frappe.set_user(make_user("auditor.tsapi@normcore.test", "NC Auditor"))
		r = api.get_entry(self.doc.name)
		self.assertFalse(r["can_write"])

	def test_get_entry_council_bi_tu_choi(self):
		frappe.set_user(make_user("council.tsapi@normcore.test", "NC Council Member"))
		self.assertRaises(frappe.PermissionError, api.get_entry, self.doc.name)


from normcore.core import permissions as access
from normcore.nc_costing.doctype.nc_norm_set.nc_norm_set import make_norm_set


class TestTimeStudyResult(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _job = make_base("DV-BG", "K01")
		self.proc = make_four_step_procedure(self.service, self.dept)
		self.s1, self.s2 = (self.proc.steps[0].step_id, self.proc.steps[1].step_id)
		frappe.db.set_single_value("NC Settings", "min_time_study_cases", 5)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _case(self, day, bs, eq=None, dept=None):
		lines = [{"step_id": self.s2, "job_title": "BS", "headcount": 1, "labor_minutes": bs}]
		if eq is not None:
			lines.append({"step_id": self.s1, "equipment": "EQ1", "machine_minutes": eq})
		return frappe.get_doc(
			{
				"doctype": "NC Time Study",
				"technical_service": self.service,
				"department": dept or self.dept,
				"observed_on": f"2026-11-{day:02d}",
				"lines": lines,
			}
		).insert()

	def _norm_set(self):
		return frappe.get_doc("NC Norm Set", make_norm_set(self.proc.name))

	def _line(self, ns, step, resource):
		return next(r for r in ns.lines if r.step_id == step and r.resource == resource)

	def test_get_result_trung_vi(self):
		for i, m in enumerate([18, 22, 20, 25, 19]):
			self._case(i + 1, m)
		r = api.get_result(self.service, self.dept)
		self.assertEqual((r["n_cases"], r["min_cases"], r["sufficient"]), (5, 5, True))
		self.assertEqual(r["procedure"], self.proc.name)
		row = r["rows"][0]
		self.assertEqual(
			(row["step_id"], row["kind"], row["resource"], row["median_minutes"]),
			(self.s2, "labor", "BS", 20),
		)
		self.assertEqual((row["step_title"], row["resource_label"]), ("B2", "Bác sĩ"))
		self._case(6, 21)
		self.assertEqual(api.get_result(self.service, self.dept)["rows"][0]["median_minutes"], 20.5)

	def test_get_result_khong_co_quy_trinh_ban_hanh(self):
		frappe.db.set_value("NC Clinical Procedure", self.proc.name, "workflow_state", "Nháp")
		self.assertRaises(frappe.ValidationError, api.get_result, self.service, self.dept)

	def test_TC_TS_02_ap_ket_qua_vao_bo_nhap(self):
		for i, m in enumerate([18, 22, 20, 25, 19]):
			self._case(i + 1, m, eq=10 + i)
		ns = self._norm_set()
		other = self._line(ns, self.s2, "DD")
		other_qty = other.hospital_qty
		r = api.apply_to_norm_set(ns.name)
		self.assertTrue(r["applied"])
		self.assertEqual(r["n_cases"], 5)
		ns.reload()
		bs = self._line(ns, self.s2, "BS")
		eq = self._line(ns, self.s1, "EQ1")
		self.assertEqual((bs.hospital_qty, bs.basis), (20, "Bấm giờ"))
		self.assertEqual((eq.hospital_qty, eq.basis), (12, "Bấm giờ"))
		self.assertIn("5 ca bấm giờ", bs.basis_ref)
		self.assertIn("01/11/2026", bs.basis_ref)
		self.assertEqual(self._line(ns, self.s2, "DD").hospital_qty, other_qty)
		self.assertEqual(sorted(r["updated"]), sorted([bs.line_id, eq.line_id]))

	def test_ap_khoa_khong_khop_di_vao_unmatched(self):
		for i in range(5):
			self._case(i + 1, 20, eq=10)
		ns = self._norm_set()
		for r in list(ns.lines):
			if r.resource == "EQ1":
				ns.remove(r)
		ns.save()
		res = api.apply_to_norm_set(ns.name)
		self.assertEqual(res["unmatched"], [{"step_id": self.s1, "kind": "equipment", "resource": "EQ1"}])

	def test_TC_TS_03_thieu_ca_canh_bao_xac_nhan(self):
		for i in range(3):
			self._case(i + 1, 20)
		ns = self._norm_set()
		before = self._line(ns, self.s2, "BS").hospital_qty
		r = api.apply_to_norm_set(ns.name)
		self.assertEqual(
			(r["applied"], r["needs_confirm"], r["n_cases"], r["min_cases"]), (False, True, 3, 5)
		)
		ns.reload()
		self.assertEqual(self._line(ns, self.s2, "BS").hospital_qty, before)
		self.assertTrue(api.apply_to_norm_set(ns.name, confirm=1)["applied"])
		ns.reload()
		self.assertEqual(self._line(ns, self.s2, "BS").hospital_qty, 20)

	def test_TC_ADM_03_ket_qua_bam_gio_3_ca(self):
		for i in range(3):
			self._case(i + 1, 20)
		self.assertFalse(api.get_result(self.service, self.dept)["sufficient"])
		frappe.db.set_single_value("NC Settings", "min_time_study_cases", 3)
		r = api.get_result(self.service, self.dept)
		self.assertEqual((r["sufficient"], r["min_cases"], r["rows"][0]["median_minutes"]), (True, 3, 20))
		ns = self._norm_set()
		self.assertTrue(api.apply_to_norm_set(ns.name)["applied"])

	def test_chua_co_ca_nao_bi_tu_choi(self):
		ns = self._norm_set()
		self.assertRaises(frappe.ValidationError, api.apply_to_norm_set, ns.name)

	def test_ap_chi_vao_bo_nhap(self):
		for i in range(5):
			self._case(i + 1, 20)
		ns = self._norm_set()
		frappe.db.set_value("NC Norm Set", ns.name, "status", "Đã khóa")
		self.assertRaises(frappe.ValidationError, api.apply_to_norm_set, ns.name)

	def test_ap_mat_xac_nhan_dong_bi_doi(self):
		for i in range(5):
			self._case(i + 1, 20)
		ns = self._norm_set()
		bs = self._line(ns, self.s2, "BS")
		bs.confirmed_by, bs.confirmed_on = "Administrator", "2026-11-26 08:00:00"
		ns.flags.ignore_permissions = True
		ns.save()
		api.apply_to_norm_set(ns.name)
		ns.reload()
		self.assertFalse(self._line(ns, self.s2, "BS").confirmed_by)

	def test_quyen_apply_va_result(self):
		for i in range(5):
			self._case(i + 1, 20)
		ns = self._norm_set()
		aud = make_user("aud.res@normcore.test", "NC Auditor")
		con = make_user("con.res@normcore.test", "NC Consultant")
		council = make_user("council.res@normcore.test", "NC Council Member")
		make_base("DV-BG", "K02")
		other = make_user("clin.k02.res@normcore.test", "NC Clinician")
		own = make_user("clin.k01.res@normcore.test", "NC Clinician")
		access.assign_department(other, "K02")
		access.assign_department(own, "K01")
		for user in (aud, con):
			frappe.set_user(user)
			self.assertRaises(frappe.PermissionError, api.apply_to_norm_set, ns.name)
			self.assertEqual(api.get_result(self.service, self.dept)["n_cases"], 5)
		frappe.set_user(council)
		self.assertRaises(frappe.PermissionError, api.get_result, self.service, self.dept)
		frappe.set_user(other)
		self.assertRaises(frappe.PermissionError, api.apply_to_norm_set, ns.name)
		frappe.set_user(own)
		self.assertTrue(api.apply_to_norm_set(ns.name)["applied"])
