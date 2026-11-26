import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.core import permissions as access
from normcore.tests.utils import ensure, make_base, make_equipment, make_user, publish_procedure

FORBIDDEN_WORDS = ("patient", "benh_nhan", "bệnh nhân", "ho_ten", "mrn", "bhyt", "birth", "ngay_sinh")


def make_four_step_procedure(service, dept, equipment="EQ1", state="published"):
	"""Quy trình 4 bước: S001 có BS và EQ1, S002 có BS và DD, bước 3 và 4 không có nguồn lực."""
	ensure("NC Job Title", "job_title_code", "BS", job_title_name="Bác sĩ", job_group="Bác sĩ")
	make_equipment(equipment, dept)
	proc = frappe.get_doc(
		{
			"doctype": "NC Clinical Procedure",
			"technical_service": service,
			"department": dept,
			"version_no": 1,
			"steps": [
				{"phase": "Chuẩn bị", "step_title": "B1", "description": "Thực hiện"},
				{"phase": "Thực hiện", "step_title": "B2", "description": "Thực hiện"},
				{"phase": "Thực hiện", "step_title": "B3", "description": "Thực hiện"},
				{"phase": "Kết thúc", "step_title": "B4", "description": "Thực hiện"},
			],
		}
	)
	proc.flags.ignore_single_active = True
	proc.insert(ignore_permissions=True)
	s = [x.step_id for x in proc.steps]
	for sid, kind, doctype, name in (
		(s[0], "Nhân lực", "NC Job Title", "BS"),
		(s[0], "Thiết bị", "NC Equipment", equipment),
		(s[1], "Nhân lực", "NC Job Title", "BS"),
		(s[1], "Nhân lực", "NC Job Title", "DD"),
	):
		proc.append(
			"resources",
			{
				"step_id": sid,
				"resource_type": kind,
				"resource_text": name,
				"linked_doctype": doctype,
				"linked_name": name,
				"quantity": 10,
				"uom": "phút",
				"headcount": 1,
			},
		)
	proc.save(ignore_permissions=True)
	if state == "published":
		publish_procedure(proc)
	return proc


class TestNCTimeStudy(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.service, self.dept, _job = make_base("DV-BG", "K01")
		self.proc = make_four_step_procedure(self.service, self.dept)
		self.steps = [s.step_id for s in self.proc.steps]

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _new(self, **kw):
		return frappe.get_doc(
			{"doctype": "NC Time Study", "technical_service": self.service, "department": self.dept, **kw}
		)

	def test_TC_TS_04_nap_4_buoc_theo_quy_trinh(self):
		doc = self._new()
		doc.insert()
		self.assertEqual(doc.procedure, self.proc.name)
		ids = [ln.step_id for ln in doc.lines]
		self.assertEqual(
			ids, [self.steps[0], self.steps[0], self.steps[1], self.steps[1], self.steps[2], self.steps[3]]
		)
		self.assertEqual(list(dict.fromkeys(ids)), self.steps)
		self.assertEqual(doc.observer, "Administrator")

	def test_TC_TS_04_quy_trinh_chua_ban_hanh_bi_tu_choi(self):
		frappe.db.set_value("NC Clinical Procedure", self.proc.name, "workflow_state", "Nháp")
		self.assertRaises(frappe.ValidationError, self._new().insert)
		self.assertRaises(frappe.ValidationError, self._new(procedure=self.proc.name).insert)

	def test_luu_phieu_moi_khi_chua_chon_procedure(self):
		"""QA: Desk chặn khi procedure bắt buộc; nay trường không bắt buộc, controller tự điền khi lưu."""
		self.assertFalse(frappe.get_meta("NC Time Study").get_field("procedure").reqd)
		doc = frappe.get_doc(
			{"doctype": "NC Time Study", "technical_service": self.service, "department": self.dept}
		)
		doc.insert()
		self.assertEqual(doc.procedure, self.proc.name)
		self.assertEqual(len(doc.lines), 6)

	def test_luu_phieu_moi_thieu_quy_trinh_bao_loi_tieng_viet(self):
		frappe.db.set_value("NC Clinical Procedure", self.proc.name, "workflow_state", "Nháp")
		with self.assertRaises(frappe.ValidationError) as cm:
			self._new().insert()
		self.assertIn("chưa có quy trình đã ban hành", str(cm.exception))

	def test_quy_trinh_khong_khop_khoa_bi_tu_choi(self):
		make_base("DV-BG", "K02")
		self.assertRaises(
			frappe.ValidationError,
			frappe.get_doc(
				{
					"doctype": "NC Time Study",
					"technical_service": self.service,
					"department": "K02",
					"procedure": self.proc.name,
				}
			).insert,
		)

	def test_TC_TS_05_luu_theo_buoc_khong_dinh_danh_nguoi_benh(self):
		s2 = self.steps[1]
		doc = self._new(
			lines=[
				{"step_id": s2, "job_title": "BS", "headcount": 1, "labor_minutes": 20},
				{"step_id": s2, "job_title": "DD", "headcount": 1, "labor_minutes": 20},
				{"step_id": s2, "equipment": "EQ1", "machine_minutes": 20},
			]
		)
		doc.insert()
		doc = frappe.get_doc("NC Time Study", doc.name)
		got = [
			(ln.step_id, ln.job_title, ln.headcount, ln.labor_minutes, ln.equipment, ln.machine_minutes)
			for ln in doc.lines
		]
		self.assertEqual(
			got,
			[(s2, "BS", 1, 20, None, 0), (s2, "DD", 1, 20, None, 0), (s2, None, 0, 0, "EQ1", 20)],
		)
		for dt in ("NC Time Study", "NC Time Study Line"):
			for f in frappe.get_meta(dt).fields:
				text = f"{f.fieldname} {f.label} {f.options or ''}".lower()
				for w in FORBIDDEN_WORDS:
					self.assertNotIn(w, text, f"{dt}.{f.fieldname}")

	def test_dong_sai_bi_tu_choi_qua_save(self):
		doc = self._new()
		doc.insert()
		doc.lines[0].labor_minutes = -5
		self.assertRaises(frappe.ValidationError, doc.save)
		doc.reload()
		doc.append("lines", {"step_id": "KHONG-CO", "job_title": "BS"})
		self.assertRaises(frappe.ValidationError, doc.save)

	def test_docperm_khop_bang(self):
		perms = {
			p.role: (p.read, p.write, p.create, p.delete)
			for p in frappe.get_meta("NC Time Study").permissions
		}
		rw = (1, 1, 1, 0)
		ro = (1, 0, 0, 0)
		self.assertEqual(
			perms,
			{
				"NC Clinician": rw,
				"NC Department Head": rw,
				"NC Consultant": rw,
				"NC Finance": ro,
				"NC Director": ro,
				"NC Admin": ro,
				"NC Auditor": ro,
			},
		)

	def test_quyen_time_study_council_khong_quyen(self):
		doc = self._new()
		doc.insert()
		council = make_user("council.ts@normcore.test", "NC Council Member")
		frappe.set_user(council)
		self.assertFalse(frappe.has_permission("NC Time Study", "read", doc))
		self.assertRaises(
			frappe.PermissionError, frappe.get_doc("NC Time Study", doc.name).check_permission, "read"
		)
		self.assertRaises(frappe.PermissionError, self._new().insert)

	def test_quyen_time_study_auditor_chi_doc(self):
		doc = self._new()
		doc.insert()
		aud = make_user("auditor.ts@normcore.test", "NC Auditor")
		frappe.set_user(aud)
		self.assertTrue(frappe.has_permission("NC Time Study", "read", doc))
		self.assertTrue(frappe.get_doc("NC Time Study", doc.name))
		self.assertRaises(frappe.PermissionError, self._new().insert)
		got = frappe.get_doc("NC Time Study", doc.name)
		got.observer = aud
		self.assertRaises(frappe.PermissionError, got.save)

	def test_quyen_time_study_clinician_theo_khoa(self):
		doc = self._new()
		doc.insert()
		make_base("DV-BG", "K02")
		own = make_user("clin.k01.ts@normcore.test", "NC Clinician")
		other = make_user("clin.k02.ts@normcore.test", "NC Clinician")
		access.assign_department(own, "K01")
		access.assign_department(other, "K02")
		frappe.set_user(other)
		self.assertNotIn(doc.name, frappe.get_list("NC Time Study", pluck="name"))
		self.assertFalse(frappe.has_permission("NC Time Study", "write", doc))
		frappe.set_user(own)
		self.assertIn(doc.name, frappe.get_list("NC Time Study", pluck="name"))
		mine = frappe.get_doc("NC Time Study", doc.name)
		mine.lines[0].labor_minutes = 7
		mine.save()
		self.assertTrue(frappe.has_permission("NC Time Study", "create"))

	def test_quyen_time_study_consultant_tao_duoc(self):
		con = make_user("cons.ts@normcore.test", "NC Consultant")
		frappe.set_user(con)
		doc = self._new()
		doc.insert()
		self.assertTrue(doc.name.startswith("BG-DV-BG-K01-"))
