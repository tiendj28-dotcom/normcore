#!/usr/bin/env python3
"""Smoke test FEAT-000 trên staging qua REST (chỉ thư viện chuẩn).

Biến môi trường bắt buộc: SMOKE_URL, SMOKE_API_KEY, SMOKE_API_SECRET.
Luồng: dịch vụ -> quy trình một bước -> "Đã ban hành" -> bộ định mức -> khóa -> lần tính giá
-> một dòng LABOR truy về mã bước (dữ liệu vàng test-cases.md mục 2.1, dòng L01).
Không bao giờ in khóa. Thoát 0 nếu đạt, khác 0 nếu sai.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REQUIRED = ("SMOKE_URL", "SMOKE_API_KEY", "SMOKE_API_SECRET")
DEPT = "K01"
JOB = "DD"
EXPECT = {
	"step_id": "S001",
	"norm_line_id": "L001",
	"applied_qty": 10,
	"unit_rate": 59644.8864,
	"amount": 9940.81,
}


class SmokeError(Exception):
	pass


class Api:
	def __init__(self, base, key, secret):
		self.base = base.rstrip("/")
		self.token = f"token {key}:{secret}"
		self.secrets = (key, secret)

	def _scrub(self, text):
		for s in self.secrets:
			if s:
				text = text.replace(s, "***")
		return text

	def call(self, step, method, path, body=None, query=None):
		url = self.base + path
		if query:
			url += "?" + urllib.parse.urlencode(query)
		data = json.dumps(body).encode() if body is not None else None
		req = urllib.request.Request(url, data=data, method=method)
		req.add_header("Authorization", self.token)
		req.add_header("Accept", "application/json")
		if data is not None:
			req.add_header("Content-Type", "application/json")
		try:
			with urllib.request.urlopen(req, timeout=60) as resp:
				raw = resp.read().decode()
		except urllib.error.HTTPError as e:
			raise SmokeError(f"{step}: HTTP {e.code}: {self._scrub(self._server_message(e))}") from None
		except urllib.error.URLError as e:
			raise SmokeError(f"{step}: không gọi được máy chủ: {self._scrub(str(e.reason))}") from None
		try:
			return json.loads(raw)
		except ValueError:
			raise SmokeError(f"{step}: phản hồi không phải JSON") from None

	@staticmethod
	def _server_message(err):
		raw = err.read().decode(errors="replace")
		try:
			d = json.loads(raw)
		except ValueError:
			return raw[:500]
		msgs = d.get("_server_messages")
		if msgs:
			try:
				return "; ".join(json.loads(m).get("message", "") for m in json.loads(msgs))[:500]
			except (ValueError, AttributeError):
				pass
		return str(d.get("exception") or d.get("message") or raw)[:500]

	def get_doc(self, step, doctype, name):
		path = f"/api/resource/{urllib.parse.quote(doctype)}/{urllib.parse.quote(name, safe='')}"
		return self.call(step, "GET", path)["data"]

	def exists(self, doctype, name):
		path = f"/api/resource/{urllib.parse.quote(doctype)}/{urllib.parse.quote(name, safe='')}"
		try:
			self.call("exists", "GET", path)
			return True
		except SmokeError as e:
			if "HTTP 404" in str(e):
				return False
			raise

	def create(self, step, doctype, doc):
		path = f"/api/resource/{urllib.parse.quote(doctype)}"
		return self.call(step, "POST", path, doc)["data"]

	def run_method(self, step, doctype, name, method):
		return self.call(
			step, "POST", "/api/method/run_doc_method", {"dt": doctype, "dn": name, "method": method}
		)


def check(label, actual, expected):
	if isinstance(expected, float):
		ok = actual is not None and abs(float(actual) - expected) < 1e-6
	else:
		ok = actual == expected
	if not ok:
		raise SmokeError(f"kiểm kết quả: {label} = {actual!r}, mong đợi {expected!r}")


def run(api):
	suffix = time.strftime("%Y%m%d%H%M%S")
	service = f"SMOKE-{suffix}"

	if not api.exists("NC Department", DEPT):
		api.create(
			"1 khoa",
			"NC Department",
			{"department_code": DEPT, "department_name": "Khoa K01", "department_type": "Lâm sàng"},
		)
	if not api.exists("NC Job Title", JOB):
		api.create("2 chức danh", "NC Job Title", {"job_title_code": JOB, "job_title_name": "Điều dưỡng"})
	api.create(
		"3 dịch vụ", "NC Technical Service", {"service_code": service, "service_name": f"Smoke {suffix}"}
	)

	ps = api.create(
		"4 bộ tham số",
		"NC Costing Parameter Set",
		{
			"title": f"Smoke {suffix}",
			"effective_from": "2026-01-01",
			"base_salary": 2500000,
			"employer_contribution_rate": 23.5,
			"working_days_per_year": 264,
			"working_hours_per_day": 8,
			"job_title_rates": [{"job_title": JOB, "salary_coefficient": 3.0, "allowance_coefficient": 0.4}],
		},
	)
	rate = next((r for r in ps.get("job_title_rates", []) if r["job_title"] == JOB), None)
	if rate is None:
		raise SmokeError("4 bộ tham số: không có dòng DD")
	check("annual_cost DD", rate.get("annual_cost"), 125970000.0)
	check("rate_per_hour DD", rate.get("rate_per_hour"), 59644.8864)
	ps_name = ps["name"]

	proc = api.create(
		"5 quy trình",
		"NC Clinical Procedure",
		{
			"technical_service": service,
			"department": DEPT,
			"version_no": 1,
			"decision_no": f"QD-SMOKE-{suffix}",
			"effective_date": "2026-01-01",
			"steps": [
				{
					"phase": "Thực hiện",
					"step_title": "Thực hiện kỹ thuật",
					"description": "Bước smoke FEAT-000",
				}
			],
			"resources": [
				{
					"step_id": "S001",
					"resource_type": "Nhân lực",
					"resource_text": "Điều dưỡng",
					"linked_doctype": "NC Job Title",
					"linked_name": JOB,
					"quantity": 10,
					"uom": "phút",
					"headcount": 1,
				}
			],
		},
	)
	proc_name = proc["name"]

	api.run_method("6 ban hành", "NC Clinical Procedure", proc_name, "publish")
	check(
		"workflow_state",
		api.get_doc("6 ban hành", "NC Clinical Procedure", proc_name).get("workflow_state"),
		"Đã ban hành",
	)

	ns = api.call(
		"7 bộ định mức",
		"POST",
		"/api/method/normcore.nc_costing.doctype.nc_norm_set.nc_norm_set.make_norm_set",
		{"procedure": proc_name},
	)["message"]

	api.run_method("8 khóa", "NC Norm Set", ns, "lock")
	check("norm_set.status", api.get_doc("8 khóa", "NC Norm Set", ns).get("status"), "Đã khóa")

	run_doc = api.create(
		"9 lần tính",
		"NC Costing Run",
		{
			"title": f"Smoke {suffix}",
			"fiscal_year": 2026,
			"costing_date": "2026-12-31",
			"parameter_set": ps_name,
		},
	)
	run_name = run_doc["name"]
	api.run_method("9 chạy tính", "NC Costing Run", run_name, "run_costing")
	check(
		"costing_run.status", api.get_doc("9 chạy tính", "NC Costing Run", run_name).get("status"), "Đã tính"
	)

	costs = api.call(
		"10 đọc kết quả",
		"GET",
		"/api/resource/NC Service Cost".replace(" ", "%20"),
		query={
			"filters": json.dumps([["costing_run", "=", run_name], ["norm_set", "=", ns]]),
			"fields": json.dumps(["name"]),
			"limit_page_length": 10,
		},
	)["data"]
	check("số NC Service Cost", len(costs), 1)
	sc = api.get_doc("10 đọc kết quả", "NC Service Cost", costs[0]["name"])
	check("calc_status", sc.get("calc_status"), "Thành công")
	lines = sc.get("lines") or []
	check("số dòng", len(lines), 1)
	line = lines[0]
	check("line_type", line.get("line_type"), "Trực tiếp")
	check("component", line.get("component"), "LABOR")
	for k, v in EXPECT.items():
		check(k, line.get(k), v)
	check("rate_source", line.get("rate_source"), ps_name)
	check("direct_labor", sc.get("direct_labor"), 9940.81)

	print(f"Dịch vụ:      {service}")
	print(f"Bộ tham số:   {ps_name}")
	print(f"Quy trình:    {proc_name}")
	print(f"Bộ định mức:  {ns}")
	print(f"Lần tính giá: {run_name}")
	print(f"Kết quả:      {sc['name']} calc_status={sc['calc_status']} direct_labor={sc['direct_labor']}")
	print(
		"Dòng LABOR:   "
		f"step_id={line['step_id']} norm_line_id={line['norm_line_id']} applied_qty={line['applied_qty']} "
		f"unit_rate={line['unit_rate']} amount={line['amount']} rate_source={line['rate_source']}"
	)
	print("SMOKE FEAT-000: ĐẠT")


def main():
	missing = [v for v in REQUIRED if not os.environ.get(v)]
	if missing:
		print("Thiếu biến môi trường: " + ", ".join(missing), file=sys.stderr)
		return 2
	api = Api(os.environ["SMOKE_URL"], os.environ["SMOKE_API_KEY"], os.environ["SMOKE_API_SECRET"])
	try:
		run(api)
	except SmokeError as e:
		print(f"SMOKE FEAT-000: LỖI tại bước {e}", file=sys.stderr)
		return 1
	return 0


if __name__ == "__main__":
	sys.exit(main())
