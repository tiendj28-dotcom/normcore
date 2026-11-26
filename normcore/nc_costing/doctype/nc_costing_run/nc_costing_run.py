import frappe
from frappe import _
from frappe.model.document import Document

from normcore.costing import allocation, reconcile, runner, snapshot, test_systems
from normcore.nc_costing.doctype.nc_costing_run import loader, writer

DRAFT, CALCULATING, CALCULATED, FAILED, LOCKED = "Nháp", "Đang tính", "Đã tính", "Tính lỗi", "Đã khóa"
IMPORT_FINAL = "Đã chốt"
RUNNABLE = (DRAFT, FAILED, CALCULATED)
EDITABLE_INPUTS = (DRAFT, FAILED)
INPUT_FIELDS = (
	"fiscal_year",
	"costing_date",
	"parameter_set",
	"accounting_import",
	"price_category",
	"volume_scenario",
	"compliance_allocation_mode",
)
EXECUTE = "normcore.nc_costing.doctype.nc_costing_run.nc_costing_run.execute_costing"
PROGRESS_EVENT = "normcore_costing_progress"


class NCCostingRun(Document):
	def validate(self):
		"""FR-COST-001: đầu vào bắt buộc (reqd), lần nhập "Đã chốt", khóa đầu vào ngoài Nháp, Tính lỗi."""
		if not self.status:
			self.status = DRAFT
		if self.accounting_import:
			status = frappe.db.get_value("NC Accounting Import", self.accounting_import, "status")
			if status != IMPORT_FINAL:
				frappe.throw(_("Lần nhập kế toán {0} chưa chốt").format(self.accounting_import))
		prev = None if self.is_new() else self.get_doc_before_save()
		if prev is None:
			self.snapshot_file = self.snapshot_hash = None  # chỉ thao tác Khóa ghi (FR-COST-011)
		elif prev.status == LOCKED and self._changed_since(prev):
			frappe.throw(
				_("Lần tính giá {0} đã khóa, không sửa được. Dùng Nhân bản để tạo lần tính mới.").format(self.name)
			)
		elif (self.snapshot_file, self.snapshot_hash) != (prev.snapshot_file, prev.snapshot_hash):
			frappe.throw(_("Ảnh chụp chỉ do thao tác Khóa ghi"))
		if prev is not None and prev.status not in EDITABLE_INPUTS and self._inputs_changed(prev):
			frappe.throw(_("Lần tính giá ở trạng thái {0}, không sửa được đầu vào").format(prev.status))

	def _changed_since(self, prev) -> bool:
		"""FR-COST-012: có trường nào khác bản trong CSDL (bỏ qua `modified`, `modified_by`)."""
		skip = {"modified", "modified_by"}
		for df in self.meta.fields:
			if df.fieldtype in frappe.model.table_fields or df.fieldname in skip:
				continue
			if self.get(df.fieldname) != prev.get(df.fieldname):
				return True
		return self._inputs_changed(prev)

	def on_trash(self):
		if self.status == LOCKED:
			frappe.throw(_("Lần tính giá {0} đã khóa, không xóa được").format(self.name))

	def _inputs_changed(self, prev) -> bool:
		if any(self.get(f) != prev.get(f) for f in INPUT_FIELDS):
			return True
		same = lambda a, b: sorted(a) == sorted(b)  # noqa: E731
		return not (
			same(
				[r.department for r in self.scope_departments], [r.department for r in prev.scope_departments]
			)
			and same(
				[r.technical_service for r in self.scope_services],
				[r.technical_service for r in prev.scope_services],
			)
		)

	def scope(self) -> dict:
		"""FR-COST-002: {"eligible": [...], "ineligible": [(dịch vụ, khoa)], "background": bool}."""
		info = loader.scope_info(self)
		info["background"] = runner.needs_background(len(info["eligible"]))
		return info

	@frappe.whitelist()
	def run_costing(self, confirm_ineligible=0):
		"""FR-COST-003: tính cho mọi bộ định mức "Đã khóa" trong phạm vi (DI-06). Việc tính nằm ở normcore.costing."""
		frappe.has_permission("NC Costing Run", "write", doc=self, throw=True)
		if self.status == LOCKED:
			frappe.throw(
				_("Lần tính giá {0} đã khóa, không tính lại được. Dùng Nhân bản để tạo lần tính mới.").format(
					self.name
				)
			)
		if self.status not in RUNNABLE:
			frappe.throw(_("Chỉ chạy được lần tính giá ở trạng thái Nháp, Tính lỗi hoặc Đã tính"))
		info = self.scope()
		eligible, ineligible = info["eligible"], info["ineligible"]
		listed = "; ".join(f"{s} ({d or '—'})" for s, d in ineligible)
		if ineligible and not frappe.utils.cint(confirm_ineligible):
			frappe.throw(
				_(
					"Có {0} dịch vụ chưa có bộ định mức Đã khóa: {1}. Xác nhận để chỉ tính các dịch vụ còn lại."
				).format(len(ineligible), listed)
			)
		if ineligible:
			self.add_comment(
				"Comment",
				_("Bỏ qua {0} dịch vụ chưa có bộ định mức Đã khóa: {1}").format(len(ineligible), listed),
			)
		if info["background"]:
			self.db_set({"status": CALCULATING, "progress": 0})
			frappe.enqueue(
				EXECUTE,
				queue="long",
				timeout=1500,
				run=self.name,
				eligible=eligible,
				enqueue_after_commit=True,
			)
			return self.status
		execute_costing(self.name, eligible, background=False)
		self.reload()
		return self.status

	def _run(self, eligible, progress=None):
		"""Pha tính (chỉ đọc): nạp dữ liệu, tính từng dịch vụ rồi phân bổ; trả danh sách `ServiceResult`."""
		ctx = loader.load_context(self, eligible)
		self.flags.run_warnings = loader.run_warnings(ctx, eligible)
		actx = loader.allocation_context(self, ctx)

		def load(e):
			inp = loader.load_service(ctx, e)
			actx.drivers[(e["service"], e["department"])] = allocation.service_drivers(
				inp, actx.dept_center.get(e["department"])
			)
			return inp

		results = runner.run(
			eligible,
			load,
			ctx.pricing,
			progress=progress,
			allocate=lambda rs: allocate_pools(rs, actx),
		)
		self._allocation = actx
		return [allocation.mark_volume(r) for r in results]

	@frappe.whitelist()
	def lock_costing(self):
		"""Khóa lần tính giá (UC-012 bước 8, data-model 5.4): từ chối khi còn dòng vượt ngưỡng chưa giải trình.
		FEAT-018 (FR-COST-011): tính lại từ ảnh chụp đầu vào, trùng kết quả đã lưu mới lưu tệp, mã băm và khóa."""
		frappe.has_permission("NC Costing Run", "write", doc=self, throw=True)
		if self.status != CALCULATED:
			frappe.throw(_("Chỉ khóa được lần tính giá ở trạng thái Đã tính"))
		lines = frappe.get_all(
			"NC Reconciliation Line",
			{"costing_run": self.name},
			["cost_center", "cost_category", "over_tolerance", "explanation"],
		)
		blockers = reconcile.lock_blockers(lines)
		if blockers:
			frappe.throw(
				_("Còn {0} dòng đối soát vượt ngưỡng chưa có giải trình: {1}").format(
					len(blockers), "; ".join(blockers)
				)
			)
		eligible = loader.eligible_from_results(self)
		snap = loader.capture_snapshot(self, eligible)
		rec = snapshot.recompute(snap)
		diffs = snapshot.diff_rows(
			writer.expected_rows(self.name, rec.results, rec.recon_rows), loader.stored_rows(self)
		)
		if diffs:
			frappe.throw(
				_(
					"Đầu vào đã thay đổi sau lần tính ({0} khác biệt, ví dụ: {1}). Chạy tính giá lại rồi khóa."
				).format(len(diffs), "; ".join(diffs[:3]))
			)
		blob, digest = snapshot.pack(snap)
		frappe.db.savepoint("nc_costing_lock")
		try:
			file = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": f"{self.name}-anh-chup-v{snapshot.VERSION}.json.gz",
					"content": blob,
					"is_private": 1,
					"attached_to_doctype": "NC Costing Run",
					"attached_to_name": self.name,
					"attached_to_field": "snapshot_file",
				}
			).insert(ignore_permissions=True)
			self.flags.audit_detail = f"Ảnh chụp {digest[:12]}"
			self.db_set({"snapshot_file": file.file_url, "snapshot_hash": digest, "status": LOCKED})
		except Exception:
			frappe.db.rollback(save_point="nc_costing_lock")
			frappe.log_error(title=f"Khóa lỗi: {self.name}")
			frappe.throw(_("Không lưu được ảnh chụp đầu vào; lần tính chưa khóa"))
		return LOCKED

	@frappe.whitelist()
	def verify_snapshot(self):
		"""NFR-REL-001: tính lại từ tệp ảnh chụp đã lưu (không đọc dữ liệu sống), so từng trường. Chỉ đọc."""
		frappe.has_permission("NC Costing Run", "read", doc=self, throw=True)
		if self.status != LOCKED or not self.snapshot_file:
			frappe.throw(_("Lần tính giá chưa khóa, chưa có ảnh chụp"))
		try:
			content = frappe.get_doc("File", {"file_url": self.snapshot_file}).get_content()
		except Exception:
			return {"ok": False, "diffs": [_("Không tìm thấy tệp ảnh chụp")], "diff_count": 1, "hash": self.snapshot_hash}
		blob = content.encode() if isinstance(content, str) else content
		try:
			snap = snapshot.unpack(blob, self.snapshot_hash)
		except ValueError as e:
			return {"ok": False, "diffs": [str(e)], "diff_count": 1, "hash": self.snapshot_hash}
		rec = snapshot.recompute(snap)
		stored = loader.stored_rows(self)
		diffs = snapshot.diff_rows(writer.expected_rows(self.name, rec.results, rec.recon_rows), stored)
		kinds = [r["key"][0] for r in stored]
		return {
			"ok": not diffs,
			"version": snap.get("version"),
			"hash": self.snapshot_hash,
			"services": kinds.count("cost"),
			"lines": kinds.count("line"),
			"recon_lines": kinds.count("recon"),
			"diffs": diffs[:50],
			"diff_count": len(diffs),
		}

	@frappe.whitelist()
	def duplicate_run(self):
		"""FR-COST-012: lần tính mới ở "Nháp", cùng đầu vào và phạm vi, không mang kết quả, đối soát, ảnh chụp."""
		frappe.has_permission("NC Costing Run", "read", doc=self, throw=True)
		frappe.has_permission("NC Costing Run", "create", throw=True)
		if self.status == CALCULATING:
			frappe.throw(_("Lần tính giá đang tính, chưa nhân bản được"))
		new = frappe.copy_doc(self)
		new.title = _("{0} (bản sao)").format(self.title)
		new.status, new.progress = DRAFT, 0
		for f in ("snapshot_file", "snapshot_hash", "allocation_warnings", "run_warnings", "based_on_run"):
			if new.meta.has_field(f):
				new.set(f, None)
		new.insert()
		new.add_comment("Comment", _("Nhân bản từ {0}").format(self.name))
		return new.name

	def test_systems_in_scope(self):
		"""FR-CLS-006, DI-06 [1.1]: mã các hệ thống xét nghiệm "Đang dùng" cho lần tính mới."""
		systems = frappe.get_all("NC Test System", fields=["name", "status"])
		return test_systems.in_costing_scope(systems)


def allocate_pools(results, actx=None):
	"""Điểm cắm phân bổ cấp 1, cấp 2: trả {(dịch vụ, khoa): [CostLine "Phân bổ"]} (BR-COST-010, 011).
	`actx` None (hoặc hàm bị vá trong test) thì không phân bổ."""
	if actx is None:
		return {}
	actx.outcome = allocation.allocate(results, actx.drivers, actx.input)
	return actx.outcome.lines


def _fail(doc):
	frappe.log_error(title=f"Tính giá lỗi: {doc.name}")
	doc.db_set("status", FAILED)
	frappe.msgprint(_("Lần tính giá lỗi, xem Error Log"), indicator="red", alert=True)
	return FAILED


def execute_costing(run, eligible, background=True):
	"""Pha tính (chỉ đọc) rồi pha ghi trong savepoint. Lỗi → bỏ kết quả dở, "Tính lỗi" (data-model 5.4).
	Không raise: lỗi sẽ rollback cả request và trạng thái "Tính lỗi" không được lưu."""
	doc = frappe.get_doc("NC Costing Run", run)

	def progress(i, n):
		pct = int(i * 100 / n)
		doc.db_set("progress", pct, update_modified=False)
		frappe.publish_realtime(PROGRESS_EVENT, {"run": run, "progress": pct}, after_commit=not background)
		if background:
			frappe.db.commit()  # pha tính chỉ đọc: commit tiến độ không commit kết quả dở

	try:
		results = doc._run(eligible, progress)
	except Exception:
		return _fail(doc)
	frappe.db.savepoint("nc_costing_run")
	try:
		frappe.db.delete(
			"NC Reconciliation Line", {"costing_run": run}
		)  # giải trình cũ mất theo (ASM-017-08)
		for name in frappe.get_all("NC Service Cost", {"costing_run": run}, pluck="name"):
			frappe.delete_doc("NC Service Cost", name, force=True, ignore_permissions=True)
		writer.write_results(doc, results)
		warnings = []
		actx = getattr(doc, "_allocation", None)
		if actx is not None and actx.outcome is not None:
			depr = reconcile.depreciation_centers(actx.accounting, actx.outcome.pools)
			writer.write_reconciliation(
				doc, reconcile.reconcile(actx.outcome.pools, actx.tolerance, actx.include_depreciation, depr)
			)
			warnings = actx.outcome.warnings
		doc.db_set("run_warnings", "\n".join(doc.flags.run_warnings or []) or None, update_modified=False)
		doc.db_set("allocation_warnings", "\n".join(warnings) or None)
	except Exception:
		frappe.db.rollback(save_point="nc_costing_run")
		return _fail(doc)
	doc.db_set({"status": CALCULATED, "progress": 100})
	return CALCULATED
