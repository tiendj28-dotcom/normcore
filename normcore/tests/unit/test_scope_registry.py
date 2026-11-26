"""NORM-37 phần B: sổ đăng ký phạm vi khoa đọc từ tệp; hooks sinh từ sổ; check_conventions NC-13."""

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import check_conventions as cc

from normcore.core import scope_registry as reg

SCOPED = {
	"NC Clinical Procedure",
	"NC Norm Set",
	"NC Test System",
	"NC Test System Volume",
	"NC Equipment Usage",
	"NC Stock Issue Actual",
	"NC QC Plan",  # FEAT-032, ASM-032-11
	"NC EQA Program",  # FEAT-032, ASM-032-11
	"NC Time Study",  # FEAT-014, ASM-014-11
}


def test_sau_doctype_hien_co_dung_nhu_truoc():
	rules = reg.load_scope_rules()
	assert set(rules) == SCOPED
	assert rules["NC Clinical Procedure"]["public_read"] == {"workflow_state": "Đã ban hành"}
	assert all(r["department_field"] == "department" for r in rules.values())
	assert all(r["public_read"] == {} for dt, r in rules.items() if dt != "NC Clinical Procedure")


def test_tep_scoped_false_khong_vao_so():
	assert "NC Equipment" in reg.load_declared_doctypes()
	assert "NC Equipment" not in reg.load_scope_rules()


def test_hooks_sinh_tu_so():
	import normcore.hooks as hooks

	assert set(hooks.has_permission) == SCOPED == set(hooks.permission_query_conditions)
	assert set(reg.load_delete_guard()) <= set(hooks.doc_events)
	assert len(reg.load_delete_guard()) == 9


def test_them_tep_la_them_doctype(tmp_path):
	(tmp_path / "nc_moi.json").write_text(
		json.dumps({"doctype": "NC Moi", "department_field": "khoa"}), encoding="utf-8"
	)
	assert reg.load_scope_rules(tmp_path) == {"NC Moi": {"department_field": "khoa", "public_read": {}}}


DOCTYPE = {
	"doctype": "DocType",
	"name": "NC Phieu Khoa",
	"track_changes": 1,
	"fields": [{"fieldname": "department", "fieldtype": "Link", "options": "NC Department", "label": "Khoa"}],
	"permissions": [
		{"role": "NC Auditor", "read": 1},
		{"role": "NC Department Head", "read": 1},
	],
}


def _make(tmp_path, data):
	d = tmp_path / "normcore" / "nc_x" / "doctype" / "nc_phieu_khoa"
	d.mkdir(parents=True)
	(d / "nc_phieu_khoa.json").write_text(json.dumps(data), encoding="utf-8")


def _codes(tmp_path):
	return [e for e in cc.run(tmp_path) if "[NC-13]" in e]


def test_thieu_tep_scope_rules_bao_loi(tmp_path):
	_make(tmp_path, DOCTYPE)
	errs = _codes(tmp_path)
	assert len(errs) == 1 and "nc_phieu_khoa.json" in errs[0]


def test_co_tep_scope_rules_sach(tmp_path):
	_make(tmp_path, DOCTYPE)
	d = tmp_path / cc.SCOPE_DIR
	d.mkdir(parents=True)
	(d / "nc_phieu_khoa.json").write_text(json.dumps({"doctype": "NC Phieu Khoa"}), encoding="utf-8")
	assert _codes(tmp_path) == []


def test_scoped_false_thieu_ly_do_bao_loi(tmp_path):
	_make(tmp_path, DOCTYPE)
	d = tmp_path / cc.SCOPE_DIR
	d.mkdir(parents=True)
	(d / "nc_phieu_khoa.json").write_text(
		json.dumps({"doctype": "NC Phieu Khoa", "scoped": False}), encoding="utf-8"
	)
	assert len(_codes(tmp_path)) == 1


def test_khong_co_vai_tro_khoa_thi_khong_can_tep(tmp_path):
	data = copy.deepcopy(DOCTYPE)
	data["permissions"] = [{"role": "NC Auditor", "read": 1}]
	_make(tmp_path, data)
	assert _codes(tmp_path) == []
