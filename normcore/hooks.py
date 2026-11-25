from normcore.core import scope_registry

app_name = "normcore"
app_title = "Normcore"
app_publisher = "Medcons"
app_description = "Normcore app"
app_email = "info@medcons.vn"
app_license = "Proprietary"

# Apps
# ------------------

required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "normcore",
# 		"logo": "/assets/normcore/logo.png",
# 		"title": "Normcore",
# 		"route": "/normcore",
# 		"has_permission": "normcore.api.permission.has_app_permission"
# 	}
# ]

# Fixtures: 10 vai trò (FR-ACC-002) và hai Workflow State của skeleton
fixtures = [
	{"dt": "Role", "filters": [["name", "like", "NC %"]]},
	{
		"dt": "Workflow State",
		"filters": [
			[
				"name",
				"in",
				[
					"Nháp",
					"Chờ trưởng khoa duyệt",
					"Chờ hội đồng thẩm định",
					"Chờ ban hành",
					"Đã ban hành",
					"Đã thay thế",
					"Đã thu hồi",
				],
			]
		],
	},
	{
		"dt": "Workflow Action Master",
		"filters": [["name", "in", ["Gửi duyệt", "Đồng ý", "Thông qua", "Ban hành", "Từ chối"]]],
	},
	{"dt": "Workflow", "filters": [["name", "=", "NC Clinical Procedure"]]},
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/normcore/css/normcore.css"
# app_include_js = "/assets/normcore/js/normcore.js"

# include js, css files in header of web template
# web_include_css = "/assets/normcore/css/normcore.css"
# web_include_js = "/assets/normcore/js/normcore.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "normcore/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "normcore/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {"methods": ["normcore.api.procedure_workflow.get_print_context"]}  # FR-PROC-010

# Installation
# ------------

before_install = "normcore.install.before_install"
after_install = [
	"normcore.install.after_install",
	"normcore.setup.fix_home_page",
	"normcore.setup.ensure_list_view_settings",
]

# Migration
# ------------
after_migrate = ["normcore.setup.fix_home_page", "normcore.setup.ensure_list_view_settings"]

# Uninstallation
# ------------

# before_uninstall = "normcore.uninstall.before_uninstall"
# after_uninstall = "normcore.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "normcore.utils.before_app_install"
# after_app_install = "normcore.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "normcore.utils.before_app_uninstall"
# after_app_uninstall = "normcore.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "normcore.build.after_build"

# To hook into the build process of other apps
# The list of apps being built is passed as an argument

# after_app_build = "normcore.build.after_app_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "normcore.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["normcore.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# Phạm vi theo khoa (FR-ACC-003): sinh từ normcore/core/scope_rules/*.json (NORM-37), không liệt kê tay
permission_query_conditions = {
	dt: "normcore.core.permissions.permission_query_conditions" for dt in scope_registry.scope_doctypes()
}

has_permission = {dt: "normcore.core.permissions.has_permission" for dt in scope_registry.scope_doctypes()}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# FR-ADM-005: từ chối xóa danh mục đang được tham chiếu, nêu bản ghi tham chiếu
doc_events = {
	dt: {"on_trash": "normcore.core.references.check_not_referenced"}
	for dt in scope_registry.load_delete_guard()  # normcore/core/delete_guard/*.json (NORM-37)
}
# FR-AUD-001 (ADR-014): hook chung ghi sự kiện chuyển trạng thái, khóa, xóa; không sửa controller từng DocType
doc_events["*"] = {
	"validate": "normcore.core.audit.on_doc_validate",
	"on_change": "normcore.core.audit.on_doc_change",
	"after_delete": "normcore.core.audit.on_doc_delete",
}
# Dynamic Link `ref_name` của sổ sự kiện không được chặn xóa bản ghi nguồn
ignore_links_on_delete = ["NC Audit Event"]

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"normcore.api.compliance.daily_job",  # FR-CMP-005
		"normcore.api.procedure_workflow.daily_job",  # FR-WF-006, FR-WF-013
		"normcore.api.library.daily_job",  # FR-LIB-006
	]
}

# scheduler_events = {
# 	"all": [
# 		"normcore.tasks.all"
# 	],
# 	"daily": [
# 		"normcore.tasks.daily"
# 	],
# 	"hourly": [
# 		"normcore.tasks.hourly"
# 	],
# 	"weekly": [
# 		"normcore.tasks.weekly"
# 	],
# 	"monthly": [
# 		"normcore.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "normcore.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "normcore.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "normcore.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["normcore.utils.before_request"]
# after_request = ["normcore.utils.after_request"]

# Job Events
# ----------
# before_job = ["normcore.utils.before_job"]
# after_job = ["normcore.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"normcore.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
