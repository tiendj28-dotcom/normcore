import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import cls_volume

KEY = ("fiscal_year", "scenario", "test_system")  # DI-14


class NCTestSystemVolume(Document):
	def validate(self):
		# FR-ACCT-012..014, DI-14
		# thiếu "Số kết quả trả": để Frappe báo MandatoryError
		errors = [
			_(m)
			for f, m in cls_volume.volume_errors(self.get)
			if f != "patient_results" or self.patient_results not in (None, "")
		]
		if errors:
			frappe.throw("<br>".join(errors), title=_("Sản lượng chưa hợp lệ"))
		dup = frappe.db.exists(
			"NC Test System Volume", {**{k: self.get(k) for k in KEY}, "name": ("!=", self.name)}
		)
		if dup:
			frappe.throw(
				_("Đã có sản lượng năm {0}, kịch bản {1} của hệ thống {2}").format(
					self.fiscal_year, self.scenario, self.test_system
				)
			)

	def as_dict(self, *args, **kwargs):
		# Frappe ép Float NULL thành 0 khi tuần tự hóa (lúc tải, lúc lưu, lúc tạo mới); form sẽ hiện 0 và lưu 0 thật.
		# Giá trị thô trống nghĩa là chưa có số thực tế: trả NULL (ASM-035-04). Nhập 0 thì giữ 0.
		d = super().as_dict(*args, **kwargs)
		for f in cls_volume.NON_NEGATIVE[1:]:
			if f in d and self.__dict__.get(f) in (None, ""):
				d[f] = None
		return d

	def on_update(self):
		# Frappe ghi 0 cho ô số để trống; FR-QC-006 cần NULL để FEAT-036 ước tính từ kế hoạch (ASM-035-04)
		blanks = [f for f in cls_volume.NON_NEGATIVE[1:] if self.get(f) in (None, "")]
		if blanks:
			sets = ", ".join(f"`{f}` = NULL" for f in blanks)
			frappe.db.sql(f"update `tabNC Test System Volume` set {sets} where name = %s", self.name)


def on_doctype_update():
	# Cột số của Frappe luôn "not null default 0"; ô test phụ trống phải là NULL (FR-QC-006, ASM-035-04, ASM-035-12)
	cols = {
		c["Field"]: c["Type"]
		for c in frappe.db.sql("show columns from `tabNC Test System Volume`", as_dict=True)
	}
	mods = [f"modify column `{f}` {cols[f]} null default null" for f in cls_volume.NON_NEGATIVE[1:]]
	frappe.db.sql_ddl("alter table `tabNC Test System Volume` " + ", ".join(mods))
	frappe.db.add_unique("NC Test System Volume", list(KEY), constraint_name="unique_nc_test_system_volume")
