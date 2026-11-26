import frappe
from frappe import _
from frappe.model.document import Document

from normcore.ai import prompts

IMMUTABLE = ("template_code", "version", "system_prompt", "user_prompt", "output_schema")


class NCPromptTemplate(Document):
	def before_insert(self):
		# FR-AI-014: phiên bản tự cấp = lớn nhất của mã + 1 khi trống
		if not self.version:
			current = frappe.db.sql(
				"select max(version) from `tabNC Prompt Template` where template_code = %s",
				self.template_code,
			)[0][0]
			self.version = (current or 0) + 1

	def validate(self):
		if not self.is_new():
			before = self.get_doc_before_save()
			for f in IMMUTABLE:
				if before is not None and self.get(f) != before.get(f):
					frappe.throw(
						_('Mẫu lệnh đã tạo không sửa được. Dùng "Tạo phiên bản mới".'),
						title=_("Mẫu lệnh"),
					)
		else:
			if frappe.db.exists(
				"NC Prompt Template", {"template_code": self.template_code, "version": self.version}
			):
				frappe.throw(
					_("Phiên bản {0} của mẫu {1} đã tồn tại").format(self.version, self.template_code)
				)
			try:
				prompts.check_syntax(self.user_prompt)
				prompts.parse_schema(self.output_schema)
			except prompts.PromptError as e:
				frappe.throw(_(str(e)), title=_("Mẫu lệnh"))

	def on_update(self):
		if self.is_active:
			others = frappe.get_all(
				"NC Prompt Template",
				filters={"template_code": self.template_code, "name": ["!=", self.name], "is_active": 1},
				pluck="name",
			)
			for name in others:
				frappe.db.set_value("NC Prompt Template", name, "is_active", 0, update_modified=False)
