"""NORM-9: /app không lặp vô hạn khi setup_complete = true mà desktop:home_page = setup-wizard."""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from normcore.setup import fix_home_page

KEY = "desktop:home_page"


class TestFixHomePage(FrappeTestCase):
	def setUp(self):
		self._orig = frappe.db.get_default(KEY)

	def tearDown(self):
		frappe.db.set_default(KEY, self._orig)
		frappe.clear_cache()

	def test_NORM_9_setup_xong_va_setup_wizard_thi_doi_sang_workspace(self):
		frappe.db.set_default(KEY, "setup-wizard")
		with patch("frappe.is_setup_complete", return_value=True):
			fix_home_page()
		self.assertEqual(frappe.db.get_default(KEY), "workspace")

	def test_NORM_9_setup_chua_xong_thi_giu_setup_wizard(self):
		frappe.db.set_default(KEY, "setup-wizard")
		with patch("frappe.is_setup_complete", return_value=False):
			fix_home_page()
		self.assertEqual(frappe.db.get_default(KEY), "setup-wizard")

	def test_NORM_9_home_page_khac_thi_giu_nguyen(self):
		frappe.db.set_default(KEY, "private/app")
		with patch("frappe.is_setup_complete", return_value=True):
			fix_home_page()
		self.assertEqual(frappe.db.get_default(KEY), "private/app")
