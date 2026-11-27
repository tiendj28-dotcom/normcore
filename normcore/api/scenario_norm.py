"""Bộ định mức nháp sau điều chỉnh giá (FEAT-029; FR-ADJ-009, FR-NORM-009..011).

Không sửa `api/norm.py` (ba test cũ FEAT-025, FEAT-038, bấm giờ khóa tệp đó không đổi so với develop;
ASM-029-18). Tái dùng `norm._open_set` và `nc_norm_set` (`LINE_INPUTS`, `next_version`).
"""

import frappe
from frappe import _

from normcore.api import norm as norm_api
from normcore.core import notify
from normcore.nc_costing.doctype.nc_norm_set import nc_norm_set as ctl

NS = norm_api.NS
DRAFT, CONFIRMED, LOCKED = norm_api.DRAFT, norm_api.CONFIRMED, norm_api.LOCKED
ADJUSTABLE_FIELDS = ("hospital_qty", "wastage_rate")


def _build_next_version(src):
	"""Bộ "Nháp" kế tiếp của `src` cùng quy trình, giữ line_id, chưa insert (như `norm._new_version_same_procedure`)."""
	new = frappe.new_doc(NS)
	new.update(
		{
			"technical_service": src.technical_service,
			"department": src.department,
			"procedure": src.procedure,
			"test_system": src.test_system,
			"tests_per_tube": src.tests_per_tube,
			"norm_template": src.norm_template,
			"version_no": ctl.next_version(src.technical_service, src.department, src.test_system),
			"previous_version": src.name,
			"status": DRAFT,
			"next_line_seq": src.next_line_seq,
		}
	)
	for r in src.lines:  # giữ line_id; bỏ xác nhận
		new.append("lines", {f: r.get(f) for f in ctl.LINE_INPUTS})
	new.flags.from_procedure = True  # dòng giữ chỗ chưa sửa không bị kiểm đầy đủ (ASM-034-05)
	return new


def version_for_adjustment(service, department, test_system, line_id, field, value, note):
	"""Đặt `field` của dòng `line_id` ở bộ định mức "Nháp" kế tiếp, bỏ xác nhận dòng đó để chờ xác nhận lại.
	Không whitelisted; API kịch bản đã kiểm quyền (ASM-029-08, 17). Trả {"name", "created": 0|1}."""
	if field not in ADJUSTABLE_FIELDS:
		frappe.throw(_("Trường {0} không đổi được qua kịch bản điều chỉnh").format(field))
	open_name = norm_api._open_set(service, department, test_system)
	created = 0
	if open_name:
		doc = frappe.get_doc(NS, open_name)
		if doc.status == CONFIRMED:
			frappe.throw(
				_("Bộ định mức {0} đang chờ khóa; khóa hoặc trả về trước khi áp thay đổi").format(open_name)
			)
	else:
		src_name = frappe.get_all(
			NS,
			{
				"technical_service": service,
				"department": department,
				"test_system": test_system or ["is", "not set"],
				"status": LOCKED,
			},
			pluck="name",
			order_by="version_no desc, name desc",
			limit=1,
		)
		if not src_name:
			frappe.throw(_("Chưa có bộ định mức Đã khóa của {0}").format(service))
		doc = _build_next_version(frappe.get_doc(NS, src_name[0]))
		doc.insert(ignore_permissions=True)  # NC Finance chỉ có R, A trên bộ định mức; bộ do hệ thống tạo
		created = 1
	row = next((r for r in doc.lines if r.line_id == line_id), None)
	if row is None:
		frappe.throw(_("Dòng {0} không còn trong bộ định mức mới").format(line_id))
	row.set(field, value)
	row.confirmed_by = row.confirmed_on = None
	doc.flags.norm_action = "adjustment"
	doc.flags.from_procedure = True
	doc.save(ignore_permissions=True)
	doc.add_comment("Info", note)
	head = frappe.db.get_value("NC Department", department, "head_user")
	notify.notify(
		[head],
		_("Bộ định mức {0} cần xác nhận lại sau điều chỉnh giá").format(doc.name),
		NS,
		doc.name,
	)
	return {"name": doc.name, "created": created}
