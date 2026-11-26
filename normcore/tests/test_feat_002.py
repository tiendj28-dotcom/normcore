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
		end = src.index('// Bộ lọc "Tình trạng chuỗi"')
		script = (
			textwrap.dedent(
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
			)
			% src[start:end]
		)
		out = subprocess.run([node, "-e", script], capture_output=True, text=True, check=True).stdout
		r = json.loads(out)
		self.assertEqual(r["taken"], {"nc_chain_stage": "no_procedure", "nc_department": "K01"})
		self.assertEqual(r["ro"], {"status": "x"})
		self.assertEqual(r["url"], "/app/nc-technical-service?a=1")

	def test_FR_OUT_010_lan_vao_thu_hai_khi_list_view_da_cache(self):
		"""Frappe giữ list view trong cache: before_refresh phải nhận tham số mới ở mỗi lần list hiện ra."""
		import shutil
		import subprocess
		import textwrap

		src = open(self.JS).read()
		body = src[src.index("const NC_MAX_FILTER") : src.index('// Cột "Tình trạng chuỗi"')]
		script = (
			textwrap.dedent(
				"""
			const log = [];
			const __ = (s) => s;
			const frappe = {
				route_options: null,
				xcall: (m) => Promise.resolve(m.endsWith("get_home") ? {stages: [{stage: "a", label: "A"}, {stage: "b", label: "B"}]} : []),
			};
			let url = "";
			const window = {
				location: {search: "", pathname: "/app/nc-technical-service", hash: ""},
				history: {state: null, replaceState(s, t, u) { url = u; window.location.search = u.includes("?") ? "?" + u.split("?")[1] : ""; }},
			};
			const mk = (name) => ({df: {fieldname: name}, v: "", get_value() { return this.v; },
				set_value(v) { this.v = v; log.push(name + "=" + v); }, refresh() {}});
			const dept = mk("department");
			const std = [["NC Technical Service", "nc_chain_stage", "=", "a"], ["NC Technical Service", "department", "=", "K01"]];
			const listview = {
				doctype: "NC Technical Service",
				page: {fields_dict: {department: dept}, add_field(df) { const f = mk(df.fieldname); f.df = df; return f; }},
				filter_area: {get_standard_filters: () => std, remove() {}, add() {}, debounced_refresh_list_view() {}},
				before_refresh() { log.push("orig"); return Promise.resolve(); },
			};
			%s
			(async () => {
				normcore_chain_filter(listview);
				await new Promise((r) => setTimeout(r, 10));
				// lần vào 1: mức a, khoa K01
				frappe.route_options = {nc_chain_stage: "a", nc_department: "K01"};
				window.location.search = "?nc_chain_stage=a&nc_department=K01";
				await listview.before_refresh();
				const first = {log: log.splice(0), ro: frappe.route_options, url};
				// lần vào 2 (list cache, onload không chạy lại): mức b, khoa K02
				frappe.route_options = {nc_chain_stage: "b", nc_department: "K02"};
				window.location.search = "?nc_chain_stage=b&nc_department=K02";
				await listview.before_refresh();
				const second = {log: log.splice(0), ro: frappe.route_options, url};
				console.log(JSON.stringify({first, second, std: listview.filter_area.get_standard_filters()}));
			})();
			"""
			)
			% body
		)
		out = subprocess.run(
			[shutil.which("node"), "-e", script], capture_output=True, text=True, check=True
		).stdout
		r = json.loads(out)
		self.assertEqual(r["first"]["log"], ["department=K01", "nc_chain_stage=a", "orig"])
		self.assertEqual(r["second"]["log"], ["department=K02", "nc_chain_stage=b", "orig"])
		for k in ("first", "second"):
			self.assertEqual(r[k]["ro"], {})
			self.assertEqual(r[k]["url"], "/app/nc-technical-service")
		# ô chọn mức bị loại khỏi bộ lọc chuẩn, khoa vẫn giữ
		self.assertEqual([f[1] for f in r["std"]], ["department"])
