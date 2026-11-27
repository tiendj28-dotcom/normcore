"""FEAT-030: API phương án giá (FR-PRICE-001..010, FR-OUT-007)."""

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.api import price_compare
from normcore.api import price_proposal as api
from normcore.benchmark import proposal as pr
from normcore.tests import proposal_fixtures as pf
from normcore.tests.utils import make_user

DT = "NC Price Proposal"


class ProposalCase(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.fin = make_user(pf.FIN_USER, "NC Finance")
		self.aud = make_user("aud.n84@normcore.test", "NC Auditor")
		self.dir = make_user("dir.n84@normcore.test", "NC Director")
		self.head = make_user("head.n84@normcore.test", "NC Department Head")
		self.cons = make_user("cons.n84@normcore.test", "NC Consultant")
		self.run, self.params, self.dept = pf.make_locked_golden_run(self.fin)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _create(self, **kw):
		frappe.set_user(self.fin)
		name = api.create_proposal(self.run.name, **kw)["name"]
		frappe.set_user("Administrator")
		return name

	def _item(self, name, service):
		return next(i for i in frappe.get_doc(DT, name).items if i.technical_service == service)


class TestProposalCreate(ProposalCase):
	def test_TC_PRICE_01_lap_tu_lan_tinh_khoa(self):
		name = self._create()
		frappe.set_user(self.fin)
		data = api.get_proposal(name)
		frappe.set_user("Administrator")
		items = {i["technical_service"]: i for i in data["items"]}
		self.assertEqual(len(items), 2)
		self.assertEqual(float(items["DV-TEST-A"]["proposed_price"]), 302100)
		self.assertEqual(float(items["DV-TEST-B"]["proposed_price"]), 92600)
		self.assertEqual(float(items["DV-TEST-A"]["full_cost"]), 287745.46)
		for i in items.values():
			self.assertEqual(float(i["proposed_price"]), float(i["rounded_price"]))
			self.assertEqual(i["below_cost"], 0)
		self.assertEqual(data["doc"]["workflow_state"], pr.DRAFT)
		self.assertEqual(data["approval_authority"], "Bệnh viện")
		# trung vị tham chiếu khớp thống kê của Bàn so sánh giá (FEAT-028)
		frappe.set_user(self.fin)
		cmp = {r["technical_service"]: r for r in price_compare.get_comparison(self.run.name)["rows"]}
		frappe.set_user("Administrator")
		for svc, i in items.items():
			self.assertEqual(i["benchmark_count"], cmp[svc]["count"])
			self.assertEqual(i["benchmark_median"] or None, cmp[svc]["median"])  # Currency rỗng lưu 0
		self.assertEqual(data["summary"], {"count": 2, "adjusted": 0, "below_cost": 0, "unacked": 0})

	def test_TC_PRICE_01_lan_tinh_chua_khoa_bi_tu_choi(self):
		frappe.db.set_value("NC Costing Run", self.run.name, "status", "Đã tính")
		frappe.set_user(self.fin)
		with self.assertRaises(frappe.ValidationError):
			api.create_proposal(self.run.name)

	def test_tao_phuong_an_can_quyen(self):
		for user in (self.aud, self.dir, self.cons, self.head):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.create_proposal(self.run.name)

	def test_get_proposal_can_quyen_doc(self):
		name = self._create()
		clin = make_user("clin.n84@normcore.test", "NC Clinician")
		frappe.set_user(clin)
		with self.assertRaises(frappe.PermissionError):
			api.get_proposal(name)


class ActionCase(ProposalCase):
	"""Dựng phương án có hai khoa (ASM-030-16) hoặc một khoa."""

	def setUp(self):
		super().setUp()
		self.head2 = make_user("head2.n84@normcore.test", "NC Department Head")
		self.head3 = make_user("head3.n84@normcore.test", "NC Department Head")
		from normcore.core import permissions
		from normcore.tests.utils import make_base

		make_base("DV-N84-Z", "KHOA-TEST-2")
		make_base("DV-N84-Y", "KHOA-N84-Y")
		permissions.assign_department(self.head, self.dept)
		permissions.assign_department(self.head2, "KHOA-TEST-2")
		permissions.assign_department(self.head3, "KHOA-N84-Y")
		frappe.db.set_value("NC Department", self.dept, "head_user", self.head)
		frappe.db.set_value("NC Department", "KHOA-TEST-2", "head_user", self.head2)

	def _two_departments(self):
		cost = frappe.db.get_value("NC Service Cost", {"costing_run": self.run.name, "technical_service": "DV-TEST-B"})
		frappe.db.set_value("NC Service Cost", cost, "department", "KHOA-TEST-2")

	def _act(self, user, name, action, **kw):
		frappe.set_user(user)
		try:
			return api.apply_action(name, action, **kw)
		finally:
			frappe.set_user("Administrator")

	def _state(self, name):
		return frappe.db.get_value(DT, name, "workflow_state")

	def _submitted(self, apply_from="2027-01-01", edit=None):
		name = self._create(apply_from=apply_from)
		if edit:
			doc = frappe.get_doc(DT, name)
			for row in doc.items:
				if row.technical_service in edit:
					row.proposed_price, row.adjustment_basis = edit[row.technical_service]
			frappe.set_user(self.fin)
			doc.save()
			frappe.set_user("Administrator")
		self._act(self.fin, name, "Gửi duyệt")
		return name

	def _to_director(self, **kw):
		name = self._submitted(**kw)
		self._act(self.head, name, "Xác nhận")
		self.assertEqual(self._state(name), pr.WAIT_DIRECTOR)
		return name

	def _logs(self, user, name):
		return frappe.get_all(
			"Notification Log", {"for_user": user, "document_name": name}, pluck="subject"
		)


class TestProposalActions(ActionCase):
	def test_TC_PRICE_02_thieu_can_cu_tu_choi_gui(self):
		name = self._create(apply_from="2027-01-01")
		doc = frappe.get_doc(DT, name)
		doc.items[0].proposed_price = 295000
		frappe.set_user(self.fin)
		doc.save()
		with self.assertRaises(frappe.ValidationError) as cm:
			api.apply_action(name, "Gửi duyệt")
		frappe.set_user("Administrator")
		msg = str(cm.exception)
		self.assertIn("DV-TEST-A", msg)
		self.assertIn("căn cứ", msg)
		self.assertEqual(self._state(name), pr.DRAFT)
		doc = frappe.get_doc(DT, name)
		doc.items[0].adjustment_basis = "Theo hội đồng giá"
		frappe.set_user(self.fin)
		doc.save()
		frappe.set_user("Administrator")
		self.assertEqual(self._act(self.fin, name, "Gửi duyệt"), {"workflow_state": pr.WAIT_DEPT})
		self.assertEqual(self._state(name), pr.WAIT_DEPT)

	def test_gui_duyet_loai_benh_vien_can_ngay_ap_dung(self):
		name = self._create()
		with self.assertRaises(frappe.ValidationError) as cm:
			self._act(self.fin, name, "Gửi duyệt")
		self.assertIn("ngày áp dụng", str(cm.exception))

	def test_TC_PRICE_03_duoi_gia_thanh_can_xac_nhan_dong(self):
		name = self._to_director(edit={"DV-TEST-A": (280000, "Giá cạnh tranh theo vùng")})
		row_a = self._item(name, "DV-TEST-A")
		self.assertEqual(row_a.below_cost, 1)
		self.assertAlmostEqual(row_a.full_cost, 287745.46, places=2)
		with self.assertRaises(frappe.ValidationError) as cm:
			self._act(self.dir, name, "Phê duyệt")
		self.assertIn("DV-TEST-A", str(cm.exception))
		self.assertEqual(self._state(name), pr.WAIT_DIRECTOR)
		self.assertEqual(self._item(name, "DV-TEST-A").director_ack, 0)
		# xác nhận nhầm dòng không dưới giá thành thì vẫn bị từ chối
		with self.assertRaises(frappe.ValidationError):
			self._act(self.dir, name, "Phê duyệt", acknowledged=[self._item(name, "DV-TEST-B").name])
		self._act(self.dir, name, "Phê duyệt", acknowledged=[row_a.name])
		self.assertEqual(self._state(name), pr.APPROVED)
		self.assertEqual(self._item(name, "DV-TEST-A").director_ack, 1)

	def test_TC_PRICE_04_hai_khoa_xac_nhan_lan_luot(self):
		self._two_departments()
		name = self._submitted()
		self.assertEqual(self._state(name), pr.WAIT_DEPT)
		self.assertEqual(len(frappe.get_doc(DT, name).department_confirmations), 2)
		self.assertTrue(any("chờ khoa xác nhận" in s for s in self._logs(self.head, name)))
		self.assertTrue(any("chờ khoa xác nhận" in s for s in self._logs(self.head2, name)))
		# trưởng khoa của khoa không có dòng, Finance: không xác nhận được
		for user in (self.head3, self.fin, self.dir):
			with self.assertRaises(frappe.PermissionError):
				self._act(user, name, "Xác nhận")
		self._act(self.head, name, "Xác nhận", note="Đồng ý")
		self.assertEqual(self._state(name), pr.WAIT_DEPT)
		done = [c for c in frappe.get_doc(DT, name).department_confirmations if c.confirmed_by]
		self.assertEqual([c.department for c in done], [self.dept])
		with self.assertRaises(frappe.PermissionError):  # khoa đã xác nhận rồi
			self._act(self.head, name, "Xác nhận")
		self.assertFalse(self._logs(self.dir, name))
		self._act(self.head2, name, "Xác nhận")
		self.assertEqual(self._state(name), pr.WAIT_DIRECTOR)
		self.assertTrue(any("chờ phê duyệt" in s for s in self._logs(self.dir, name)))

	def test_TC_PRICE_05_duyet_ghi_lich_su_gia(self):
		svc = frappe.get_doc("NC Technical Service", "DV-TEST-A")
		svc.flags.price_history_write = True
		svc.append(
			"approved_prices",
			{"price_category": "PC-GOLD", "price": 290000, "effective_date": "2026-01-01", "price_proposal": self._create()},
		)
		svc.save(ignore_permissions=True)
		name = self._to_director(apply_from="2027-01-01")
		self._act(self.dir, name, "Phê duyệt")
		self.assertEqual(self._state(name), pr.APPROVED)
		hist = frappe.get_doc("NC Technical Service", "DV-TEST-A").approved_prices
		self.assertEqual(len(hist), 2)
		old, new = sorted(hist, key=lambda r: str(r.effective_date))
		self.assertEqual((float(old.price), str(old.effective_date)), (290000.0, "2026-01-01"))
		self.assertEqual((float(new.price), str(new.effective_date), new.price_proposal), (302100.0, "2027-01-01", name))
		b = frappe.get_doc("NC Technical Service", "DV-TEST-B").approved_prices
		self.assertEqual([float(r.price) for r in b], [92600.0])
		# khóa: sửa dòng bị chặn
		doc = frappe.get_doc(DT, name)
		doc.items[0].proposed_price = 1
		frappe.set_user(self.fin)
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_TC_PRICE_06_cap_tham_quyen_ghi_ket_qua(self):
		frappe.db.set_value("NC Price Category", "PC-GOLD", "approval_authority", pr.AUTHORITY)
		name = self._to_director(apply_from=None)
		self._act(self.dir, name, "Phê duyệt")
		self.assertEqual(self._state(name), pr.WAIT_AUTHORITY)
		self.assertEqual(frappe.get_doc("NC Technical Service", "DV-TEST-A").approved_prices, [])
		self.assertTrue(any("chờ trình" in s for s in self._logs(self.fin, name)))
		rows = {i.technical_service: i.name for i in frappe.get_doc(DT, name).items}
		prices = {rows["DV-TEST-A"]: 300000, rows["DV-TEST-B"]: 90000}
		for user in (self.dir, self.aud, self.cons):
			frappe.set_user(user)
			with self.assertRaises(frappe.PermissionError):
				api.record_authority_result(name, "QD-01", "2027-02-01", prices)
		frappe.set_user(self.fin)
		with self.assertRaises(frappe.ValidationError):
			api.record_authority_result(name, "", "2027-02-01", {rows["DV-TEST-A"]: 300000})
		out = api.record_authority_result(name, "QD-01/2027", "2027-02-01", prices)
		frappe.set_user("Administrator")
		self.assertEqual(out, {"workflow_state": pr.AUTHORITY_APPROVED})
		a = self._item(name, "DV-TEST-A")
		self.assertEqual((float(a.proposed_price), float(a.authority_price)), (302100.0, 300000.0))
		doc = frappe.get_doc(DT, name)
		self.assertEqual(doc.authority_doc_no, "QD-01/2027")
		hist = frappe.get_doc("NC Technical Service", "DV-TEST-A").approved_prices
		self.assertEqual(len(hist), 1)
		self.assertEqual(
			(float(hist[0].price), str(hist[0].effective_date), hist[0].authority_doc_no),
			(300000.0, "2027-02-01", "QD-01/2027"),
		)

	def test_TC_PRICE_07_tu_choi_ve_nhap_bao_tai_chinh(self):
		name = self._submitted()
		with self.assertRaises(frappe.ValidationError):
			self._act(self.head, name, "Từ chối")
		with self.assertRaises(frappe.ValidationError):
			self._act(self.head, name, "Từ chối", reason="  ")
		self._act(self.head, name, "Từ chối", reason="Giá cao hơn mặt bằng của khoa")
		self.assertEqual(self._state(name), pr.DRAFT)
		doc = frappe.get_doc(DT, name)
		self.assertEqual(doc.department_confirmations, [])
		logs = self._logs(self.fin, name)
		self.assertTrue(any("Giá cao hơn mặt bằng của khoa" in s and "trưởng khoa" in s for s in logs))
		# lại gửi được; Giám đốc từ chối ở cấp phê duyệt cũng về Nháp, bỏ xác nhận dòng
		self._act(self.fin, name, "Gửi duyệt")
		self._act(self.head, name, "Xác nhận")
		self._act(self.dir, name, "Từ chối", reason="Chưa phù hợp")
		self.assertEqual(self._state(name), pr.DRAFT)

	def test_quyen_hanh_dong(self):
		name = self._create(apply_from="2027-01-01")
		for user in (self.dir, self.head, self.aud, self.cons):
			with self.assertRaises(frappe.PermissionError):
				self._act(user, name, "Gửi duyệt")
		self._act(self.fin, name, "Gửi duyệt")
		for user in (self.aud, self.cons, self.fin, self.head3):
			with self.assertRaises(frappe.PermissionError):
				self._act(user, name, "Xác nhận")
		for user in (self.aud, self.cons, self.fin, self.head3):
			with self.assertRaises(frappe.PermissionError):
				self._act(user, name, "Từ chối", reason="x")
		self._act(self.head, name, "Xác nhận")
		for user in (self.aud, self.cons, self.fin, self.head):
			with self.assertRaises(frappe.PermissionError):
				self._act(user, name, "Phê duyệt")
		with self.assertRaises(frappe.ValidationError):  # hành động sai trạng thái
			self._act(self.fin, name, "Gửi duyệt")
		frappe.set_user(self.fin)
		acts = api.get_proposal(name)["actions"]
		frappe.set_user(self.dir)
		dacts = api.get_proposal(name)["actions"]
		frappe.set_user("Administrator")
		self.assertEqual(acts, [])
		self.assertEqual(sorted(dacts), ["Phê duyệt", "Từ chối"])

	def test_FR_PRICE_010_lich_su_chi_them(self):
		name = self._to_director()
		# trùng (dịch vụ, loại giá, ngày): chặn phê duyệt, trạng thái không đổi
		prior = self._create()
		svc = frappe.get_doc("NC Technical Service", "DV-TEST-A")
		svc.flags.price_history_write = True
		svc.append(
			"approved_prices",
			{"price_category": "PC-GOLD", "price": 1, "effective_date": "2027-01-01", "price_proposal": prior},
		)
		svc.save(ignore_permissions=True)
		with self.assertRaises(frappe.ValidationError) as cm:
			self._act(self.dir, name, "Phê duyệt")
		self.assertIn("DV-TEST-A", str(cm.exception))
		self.assertEqual(self._state(name), pr.WAIT_DIRECTOR)
		self.assertEqual(len(frappe.get_doc("NC Technical Service", "DV-TEST-B").approved_prices), 0)
		# sửa, xóa, thêm tay bị chặn
		svc = frappe.get_doc("NC Technical Service", "DV-TEST-A")
		svc.approved_prices[0].price = 5
		with self.assertRaises(frappe.ValidationError):
			svc.save(ignore_permissions=True)
		svc = frappe.get_doc("NC Technical Service", "DV-TEST-A")
		svc.set("approved_prices", [])
		with self.assertRaises(frappe.ValidationError):
			svc.save(ignore_permissions=True)
		svc = frappe.get_doc("NC Technical Service", "DV-TEST-A")
		svc.append("approved_prices", {"price_category": "PC-GOLD", "price": 2, "effective_date": "2030-01-01", "price_proposal": prior})
		with self.assertRaises(frappe.ValidationError):
			svc.save(ignore_permissions=True)
		# sửa tên dịch vụ (không đụng lịch sử) vẫn được
		svc = frappe.get_doc("NC Technical Service", "DV-TEST-A")
		svc.service_name = "Tên mới"
		svc.save(ignore_permissions=True)

	def test_FR_NOTI_003_viec_cho(self):
		self._two_departments()
		name = self._submitted()
		got = {user: api.pending_for(user) for user in (self.head, self.head2, self.head3, self.dir, self.fin)}
		self.assertEqual([p["name"] for p in got[self.head]], [name])
		self.assertEqual(got[self.head][0]["state"], pr.WAIT_DEPT)
		self.assertEqual([p["name"] for p in got[self.head2]], [name])
		self.assertEqual(got[self.head3], [])
		self.assertEqual(got[self.dir], [])
		self.assertEqual(got[self.fin], [])
		self._act(self.head, name, "Xác nhận")
		self.assertEqual(api.pending_for(self.head), [])
		self._act(self.head2, name, "Xác nhận")
		self.assertEqual([p["name"] for p in api.pending_for(self.dir)], [name])
		self.assertEqual(api.pending_for(self.head2), [])
		self.assertEqual(api.pending_for(self.aud), [])
