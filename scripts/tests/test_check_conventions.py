import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_conventions as cc

GOOD = {
	"doctype": "DocType",
	"name": "NC Quy Trinh",
	"track_changes": 1,
	"fields": [
		{"fieldname": "ma_buoc", "fieldtype": "Data", "label": "Mã bước"},
		{"fieldname": "sec_1", "fieldtype": "Section Break"},
	],
	"permissions": [
		{"role": "NC Auditor", "read": 1},
		{"role": "System Manager", "read": 1, "write": 1, "create": 1},
	],
}


def make(tmp_path, data, folder="nc_quy_trinh", base="app/mod"):
	d = tmp_path / base / "doctype" / folder
	d.mkdir(parents=True, exist_ok=True)
	(d / f"{folder}.json").write_text(json.dumps(data), encoding="utf-8")


def codes(tmp_path):
	return {e.split("[")[1].split("]")[0] for e in cc.run(tmp_path)}


def variant(**kw):
	d = copy.deepcopy(GOOD)
	d.update(kw)
	return d


def test_hop_le(tmp_path):
	make(tmp_path, GOOD)
	assert cc.run(tmp_path) == []
	assert cc.main([str(tmp_path)]) == 0


def test_khong_co_doctype_thoat_0(tmp_path):
	assert cc.main([str(tmp_path)]) == 0


def test_loi_thoat_1_va_dinh_dang_dong(tmp_path, capsys):
	make(tmp_path, variant(name="Quy Trinh"))
	assert cc.main([str(tmp_path)]) == 1
	out = capsys.readouterr().out.strip().splitlines()
	assert len(out) == 1 and ": [NC-01] " in out[0] and out[0].startswith("app/mod/doctype/")


def test_luat1_tien_to(tmp_path):
	make(tmp_path, variant(name="Quy Trinh"))
	assert codes(tmp_path) == {"NC-01"}


def test_luat2_fieldname(tmp_path):
	d = variant(fields=[{"fieldname": "MaBuoc", "fieldtype": "Data", "label": "x"}])
	make(tmp_path, d)
	assert codes(tmp_path) == {"NC-02"}


def test_luat2_fieldname_trung(tmp_path):
	f = {"fieldname": "ma", "fieldtype": "Data", "label": "Mã"}
	make(tmp_path, variant(fields=[f, dict(f)]))
	assert codes(tmp_path) == {"NC-02"}


def test_luat2_fieldname_tieng_viet_co_dau(tmp_path):
	make(tmp_path, variant(fields=[{"fieldname": "mã_bước", "fieldtype": "Data", "label": "x"}]))
	assert codes(tmp_path) == {"NC-02"}


def test_luat3_thieu_label(tmp_path):
	make(tmp_path, variant(fields=[{"fieldname": "ma", "fieldtype": "Data"}]))
	assert codes(tmp_path) == {"NC-03"}


def test_luat3_layout_khong_can_label(tmp_path):
	fields = [
		{"fieldname": n, "fieldtype": t}
		for n, t in [
			("a", "Section Break"),
			("b", "Column Break"),
			("c", "Tab Break"),
			("d", "HTML"),
			("e", "Button"),
		]
	]
	make(tmp_path, variant(fields=fields))
	assert cc.run(tmp_path) == []


def test_luat4_track_changes(tmp_path):
	d = variant()
	d["track_changes"] = 0
	make(tmp_path, d)
	assert codes(tmp_path) == {"NC-04"}


def test_luat4_bang_con_khong_can(tmp_path):
	make(tmp_path, variant(istable=1, track_changes=0, permissions=[]))
	assert cc.run(tmp_path) == []


def test_luat5_permissions_rong(tmp_path):
	make(tmp_path, variant(permissions=[]))
	assert codes(tmp_path) == {"NC-05"}


def test_luat6_auditor_ghi(tmp_path):
	for right in cc.AUDITOR_FORBIDDEN:
		d = variant(permissions=[{"role": "NC Auditor", "read": 1, right: 1}])
		make(tmp_path, d)
		assert codes(tmp_path) == {"NC-06"}, right


def test_luat6_vai_tro_khac_duoc_ghi(tmp_path):
	make(tmp_path, variant(permissions=[{"role": "NC Admin", "write": 1, "delete": 1}]))
	assert cc.run(tmp_path) == []


def test_bo_qua_docs_va_tham_khao(tmp_path):
	bad = variant(name="Sai")
	make(tmp_path, bad, base="docs/x")
	make(tmp_path, bad, base="tham-khao/y")
	assert cc.run(tmp_path) == []


def test_json_phu_canh_doctype_bi_bo_qua(tmp_path):
	make(tmp_path, GOOD)
	d = tmp_path / "app/mod/doctype/nc_quy_trinh"
	(d / "test_records.json").write_text(json.dumps([{"doctype": "NC Quy Trinh"}]))
	(d / "phu.json").write_text(json.dumps({"name": "sai", "doctype": "Report"}))
	assert cc.run(tmp_path) == []


def test_file_doctype_khac_loai_bi_bo_qua(tmp_path):
	make(tmp_path, {"doctype": "Report", "name": "sai"})
	assert cc.run(tmp_path) == []


def test_json_doctype_hong_van_bao_nc00(tmp_path):
	d = tmp_path / "app/mod/doctype/nc_x"
	d.mkdir(parents=True)
	(d / "nc_x.json").write_text("{hong")
	assert codes(tmp_path) == {"NC-00"}


def test_fields_va_permissions_null_khong_van(tmp_path):
	d = variant(fields=None, permissions=None)
	make(tmp_path, d)
	assert codes(tmp_path) == {"NC-05"}


def test_fieldname_khong_phai_chuoi(tmp_path):
	make(tmp_path, variant(fields=[{"fieldname": 123, "fieldtype": "Data", "label": "x"}]))
	assert codes(tmp_path) == {"NC-02"}


# --- NORM-32: chống conflict ---
import build_workspace as bw


def _ws(tmp_path, lines, stale=False):
	d = tmp_path / bw.REL
	d.mkdir(parents=True)
	(d / "shortcuts.txt").write_text("# c\n" + "\n".join(lines) + "\n", encoding="utf-8")
	out = bw.render(bw.read_shortcuts(d / "shortcuts.txt"))
	(d / "normcore.json").write_text(out + (" " if stale else ""), encoding="utf-8")


def test_workspace_khop_nguon(tmp_path):
	_ws(tmp_path, ["a-s|Nhãn A|NC A|DocType|List"])
	assert cc.run(tmp_path) == []


def test_workspace_lech_nguon_bi_bao(tmp_path):
	_ws(tmp_path, ["a-s|Nhãn A|NC A|DocType|List"], stale=True)
	assert codes(tmp_path) == {"NC-11"}


def test_workspace_sinh_tat_dinh_va_bo_dong_trung(tmp_path):
	_ws(tmp_path, ["a-s|A|NC A|DocType|List", "a-s|A|NC A|DocType|List", "b-s|B|NC B|DocType|List"])
	data = json.loads((tmp_path / bw.REL / "normcore.json").read_text(encoding="utf-8"))
	assert [s["label"] for s in data["shortcuts"]] == ["A", "B"]


def test_asm_trung_ma_bi_bao(tmp_path):
	p = tmp_path / "docs/decisions"
	p.mkdir(parents=True)
	(p / "assumptions.md").write_text("| ASM-001 | x |\n| ASM-002 | y |\n| ASM-001 | z |\n", encoding="utf-8")
	assert codes(tmp_path) == {"NC-12"}
	(p / "assumptions.md").write_text("| ASM-001 | x |\n| ASM-002 | y |\n", encoding="utf-8")
	assert cc.run(tmp_path) == []
