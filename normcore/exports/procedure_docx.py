"""Xuất DOCX quy trình (FR-PROC-011, ADR-015): dựng bằng mã, cùng ngữ cảnh với bản PDF."""

import io
import re


def _plain(html):
	return re.sub(r"<[^>]+>", "", (html or "").replace("<br>", "\n").replace("</p>", "\n")).strip()


def build_docx(ctx):
	from docx import Document  # import trễ: thiếu thư viện chỉ hỏng DOCX, không hỏng app

	d = Document()
	if ctx["is_draft"]:
		d.add_paragraph(ctx["watermark"]).runs[0].bold = True
	d.add_heading(ctx["title"], 0)
	d.add_paragraph(
		f"{ctx['service_name']} ({ctx['service_code']})" if ctx["service_code"] else ctx["service_name"]
	)
	d.add_paragraph(f"Khoa chủ trì: {ctx['department']}")
	if ctx["status_note"]:
		d.add_paragraph(ctx["status_note"])
	t = d.add_table(rows=0, cols=2)
	for k, v in (
		("Số hiệu", ctx["number"]),
		("Phiên bản", ctx["version"]),
		("Số quyết định", ctx["decision_no"]),
		("Ngày hiệu lực", ctx["effective_date"]),
		("Trạng thái", ctx["state"]),
	):
		row = t.add_row().cells
		row[0].text, row[1].text = k, v
	for sec in ctx["sections"]:
		d.add_heading(sec["heading"], 1)
		if sec["is_steps"]:
			for ph in ctx["phases"]:
				d.add_heading(ph["phase"], 2)
				tb = d.add_table(rows=1, cols=4)
				for c, h in zip(tb.rows[0].cells, ("Mã", "Tên bước", "Mô tả", "Phút"), strict=False):
					c.text = h
				for s in ph["steps"]:
					cells = tb.add_row().cells
					cells[0].text, cells[1].text = s["step_id"] or "", s["title"]
					cells[2].text = s["description"]
					cells[3].text = "" if s["minutes"] is None else str(s["minutes"])
			if ctx["resources"]:
				d.add_heading("Nguồn lực", 2)
				tb = d.add_table(rows=1, cols=4)
				for c, h in zip(tb.rows[0].cells, ("Bước", "Nguồn lực", "Số lượng", "Đơn vị"), strict=False):
					c.text = h
				for r in ctx["resources"]:
					cells = tb.add_row().cells
					cells[0].text = r.get("step_id") or ""
					cells[1].text = r.get("resource_text") or r.get("linked_name") or ""
					cells[2].text = "" if r.get("quantity") is None else str(r["quantity"])
					cells[3].text = r.get("uom") or ""
		else:
			d.add_paragraph(_plain(sec["text"]))
	d.add_heading("Chữ ký", 1)
	tb = d.add_table(rows=3, cols=len(ctx["signatures"]))
	for i, s in enumerate(ctx["signatures"]):
		tb.rows[0].cells[i].text = s["label"]
		tb.rows[1].cells[i].text = s["user"]
		tb.rows[2].cells[i].text = s["date"]
	buf = io.BytesIO()
	d.save(buf)
	return buf.getvalue()


def docx_text(data):
	"""Đọc lại mọi chuỗi trong DOCX (đoạn và ô bảng); dùng cho test."""
	from docx import Document

	d = Document(io.BytesIO(data))
	out = [p.text for p in d.paragraphs]
	for t in d.tables:
		for row in t.rows:
			out += [c.text for c in row.cells]
	return "\n".join(out)
