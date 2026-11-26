"""Hàng đợi rà soát (FEAT-021: TC-LIB-07, FR-LIB-009, FR-WF-009, SCR-DSK-012)."""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, today

from normcore.api import access, library, review
from normcore.api import procedure as proc_api
from normcore.api import procedure_workflow as wf
from normcore.api.test_library_supersession import _notified, _pair, make_cited
from normcore.tests.utils import make_base, make_user, to_state

DT = "NC Clinical Procedure"


class TestReviewQueue(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.head = make_user("hd_q21@example.com", "NC Department Head")
		self.head2 = make_user("hd2_q21@example.com", "NC Department Head")
		self.clin = make_user("cl_q21@example.com", "NC Clinician")
		self.aud = make_user("au_q21@example.com", "NC Auditor")
		self.norole = make_user("nr_q21@example.com", "Blogger")
		self.director = make_user("dr_q21@example.com", "NC Director")
		self.a, self.b, self.secs = _pair("TT/QA", "TT/QB")
		self.p = make_cited(
			"DV-Q1",
			"KHOA-Q1",
			self.head,
			[{"legal_document": self.b.name, "legal_section": self.secs["2"].name}],
		)
		make_base("DV-Q2", "KHOA-Q2")
		access.assign_department(self.head, "KHOA-Q1")
		access.assign_department(self.clin, "KHOA-Q1")
		access.assign_department(self.head2, "KHOA-Q2")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _expire(self, day="2099-07-01"):
		library.declare_supersession(self.a.name, self.b.name, "Một phần", day, "2")
		return library.refresh_validity(today=getdate(day))

	def test_TC_LIB_07_gan_co_thong_bao_hang_doi(self):
		other = make_cited(
			"DV-Q3",
			"KHOA-Q3",
			self.head,
			[{"legal_document": self.b.name, "legal_section": self.secs["3"].name}],
		)
		draft = make_cited(
			"DV-Q4",
			"KHOA-Q4",
			self.head,
			[{"legal_document": self.b.name, "legal_section": self.secs["2"].name}],
			state="Nháp",
		)
		self._expire()
		self.assertEqual(frappe.db.get_value(DT, self.p.name, "needs_review"), 1)
		self.assertEqual(frappe.db.get_value(DT, other.name, "needs_review"), 0)
		self.assertEqual(frappe.db.get_value(DT, draft.name, "needs_review"), 0)
		subjects = _notified(self.head, self.p.name)
		self.assertEqual(len(subjects), 1)
		self.assertIn("TT/QB", subjects[0])
		frappe.set_user(self.head)
		q = review.get_review_queue()
		self.assertEqual([r["name"] for r in q["rows"]], [self.p.name])
		row = q["rows"][0]
		self.assertEqual(row["can_act"], 1)
		self.assertIsNone(row["pending_revision"])
		cit = row["citations"][0]
		self.assertEqual(cit["reason"], "Mục hết hiệu lực")
		self.assertEqual(cit["section_no"], "2")
		self.assertEqual(cit["validity_status"], "Hết hiệu lực")
		self.assertEqual([x["document"] for x in cit["replacements"]], [self.a.name])

	def test_FR_LIB_009_khong_can_sua_go_co(self):
		self._expire()
		frappe.set_user(self.head)
		with self.assertRaises(frappe.ValidationError):
			review.dismiss_review(self.p.name, "  ")
		self.assertEqual(
			review.dismiss_review(self.p.name, "Nội dung mục mới giống mục cũ"), {"needs_review": 0}
		)
		self.assertEqual(frappe.db.get_value(DT, self.p.name, "needs_review"), 0)
		self.assertTrue(
			frappe.db.exists(
				"Comment",
				{
					"reference_doctype": DT,
					"reference_name": self.p.name,
					"content": ["like", "%Không cần sửa: Nội dung mục mới giống mục cũ%"],
				},
			)
		)
		self.assertEqual(review.get_review_queue()["rows"], [])
		with self.assertRaises(frappe.ValidationError):  # không còn cờ
			review.dismiss_review(self.p.name, "lý do")

	def test_FR_WF_009_sua_doi_tu_hang_doi(self):
		self._expire()
		frappe.set_user(self.head)
		rev = proc_api.create_revision(self.p.name)
		self.assertEqual(frappe.db.get_value(DT, rev["name"], "needs_review"), 1)
		q = review.get_review_queue()
		self.assertEqual(q["rows"][0]["pending_revision"], rev["name"])
		# ban hành bản mới gỡ cờ
		frappe.set_user("Administrator")
		to_state(frappe.get_doc(DT, rev["name"]), "Chờ ban hành")
		frappe.set_user(self.director)
		wf.apply_action(
			rev["name"], "Ban hành", decision_no="9/QĐ", effective_date=str(add_days(today(), 30))
		)
		self.assertEqual(frappe.db.get_value(DT, rev["name"], "needs_review"), 0)
		frappe.set_user("Administrator")
		to_state(frappe.get_doc(DT, self.p.name), "Đã thay thế")
		frappe.set_user(self.head)
		self.assertEqual(review.get_review_queue()["rows"], [])

	def test_SCR_DSK_012_quyen_hang_doi(self):
		self._expire()
		frappe.set_user(self.norole)
		with self.assertRaises(frappe.PermissionError):
			review.get_review_queue()
		frappe.set_user(self.aud)
		q = review.get_review_queue()
		self.assertEqual([r["name"] for r in q["rows"]], [self.p.name])
		self.assertEqual(q["rows"][0]["can_act"], 0)
		for user in (self.aud, self.clin, self.head2, self.norole):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				review.dismiss_review(self.p.name, "lý do")
		self.assertEqual(frappe.db.get_value(DT, self.p.name, "needs_review"), 1)
		frappe.set_user(self.head2)  # trưởng khoa khoa khác chỉ thấy quy trình khoa mình
		self.assertEqual(review.get_review_queue()["rows"], [])
		frappe.set_user(self.clin)
		self.assertEqual([r["name"] for r in review.get_review_queue()["rows"]], [self.p.name])
		self.assertEqual(review.get_review_queue()["rows"][0]["can_act"], 0)

	def test_SCR_DSK_012_loc_khoa_khi_co_hai_khoa(self):
		"""Trưởng khoa được gán hai khoa: bộ lọc Khoa chỉ ra quy trình của khoa đó."""
		self.p2 = make_cited(
			"DV-Q5",
			"KHOA-Q5",
			self.head,
			[{"legal_document": self.b.name, "legal_section": self.secs["2"].name}],
		)
		access.assign_department(self.head, "KHOA-Q5")
		self._expire()
		frappe.set_user(self.head)
		names = lambda **kw: sorted(r["name"] for r in review.get_review_queue(**kw)["rows"])  # noqa: E731
		self.assertEqual(names(), sorted([self.p.name, self.p2.name]))
		self.assertEqual(names(department="KHOA-Q1"), [self.p.name])
		self.assertEqual(names(department="KHOA-Q5"), [self.p2.name])
		self.assertEqual(review.get_review_queue(department="KHOA-Q5")["total"], 1)
		self.assertEqual(names(department="KHOA-Q2"), [])  # khoa không được gán
