"""FEAT-002: Workspace Normcore có block trang chủ, giữ lối tắt cũ (SCR-DSK-001)."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHomeWorkspace(FrappeTestCase):
	def test_workspace_co_block_trang_chu(self):
		ws = frappe.get_doc("Workspace", "Normcore")
		content = json.loads(ws.content)
		self.assertEqual(content[0]["type"], "header")
		self.assertEqual(content[1]["type"], "custom_block")  # đứng đầu, trước mọi lối tắt
		self.assertEqual(content[1]["data"]["custom_block_name"], "NC Trang chủ")
		self.assertEqual([c.custom_block_name for c in ws.custom_blocks], ["NC Trang chủ"])
		# mọi lối tắt cũ còn đủ
		labels = {s.label for s in ws.shortcuts}
		for label in ("Dịch vụ kỹ thuật", "Tham số vận hành", "Nhập dữ liệu từ Excel", "Nhật ký"):
			self.assertIn(label, labels)
		self.assertEqual(len([b for b in content if b["type"] == "shortcut"]), len(ws.shortcuts))

	def test_block_trang_chu_goi_get_home_va_cong_khai(self):
		block = frappe.get_doc("Custom HTML Block", "NC Trang chủ")
		self.assertEqual(block.private, 0)
		self.assertIn("normcore.api.home.get_home", block.script)


class TestChainStageRoute(FrappeTestCase):
	"""NORM-57: liên kết có nc_chain_stage/nc_department không được thành bộ lọc DocType (lỗi 417)."""

	JS = (
		frappe.get_app_path("normcore", "nc_procedure", "doctype", "nc_technical_service")
		+ "/nc_technical_service_list.js"
	)

	def test_FR_OUT_010_lien_ket_tham_so_khong_loi(self):
		import shutil
		import subprocess
		import textwrap

		node = shutil.which("node")
		self.assertTrue(node, "cần node để chạy kiểm tra JS")
		src = open(self.JS).read()
		start = src.index("const NC_ROUTE_PARAMS")
		end = src.index("// Bộ lọc \"Tình trạng chuỗi\"")
		script = textwrap.dedent(
			"""
			const frappe = {route_options: {nc_chain_stage: "no_procedure", nc_department: "K01", status: "x"}};
			let replaced = null;
			const window = {
				location: {search: "?nc_chain_stage=no_procedure&nc_department=K01&a=1", pathname: "/app/nc-technical-service", hash: ""},
				history: {state: null, replaceState(s, t, url) { replaced = url; }},
			};
			%s
			const taken = normcore_take_route_params();
			console.log(JSON.stringify({taken, ro: frappe.route_options, url: replaced}));
			"""
		) % src[start:end]
		out = subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout
		r = json.loads(out)
		self.assertEqual(r["taken"], {"nc_chain_stage": "no_procedure", "nc_department": "K01"})
		self.assertEqual(r["ro"], {"status": "x"})
		self.assertEqual(r["url"], "/app/nc-technical-service?a=1")
