# Nghiệm thu NORM-65 (trả nợ ASM-046: NC Procedure Citation dùng Link)

Commit đã kiểm: `e925d1926f9e6d6075b250183821b70e6cf4ae50` (PR #68, nhánh `fix/NORM-65-citation-link`, đã chứa origin/develop).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| `legal_section` Link NC Legal Section, `legal_document` Link NC Legal Document (data-model.md) | Đọc `nc_procedure_citation.json`; `test_NORM_65_trich_dan_link_van_ban_muc` (chỉ văn bản, chỉ mục, mục lệch văn bản, chuỗi tự do bị `LinkValidationError`) | Đạt |
| Patch: khớp được đổi sang tên bản ghi | `test_patch_khop_duoc_doi_sang_ten_ban_ghi` | Đạt |
| Patch: không khớp không mất, vào `[Căn cứ cũ: …]`, Link để trống | `test_patch_khong_khop_khong_mat_gia_tri`; `test_citation_link.py` (18 test, phủ 100%, gồm hai nhánh văn bản lệch/không khớp sau khi Reviewer trả về) | Đạt |
| Patch chạy lại không đổi | `test_patch_chay_lai_khong_doi_gi` | Đạt |
| TC-PROC-09 xanh, giữ chặt | `test_TC_PROC_09_trich_dan` chạy xanh trên site sạch; soát diff: chỉ đổi dữ liệu vào sang bản ghi thật, assertion cùng loại, không xóa/skip/nới (ASM-NORM65-05) | Đạt |
| API/Vue khớp | `api/procedure.py` (`list_legal_documents/sections`, `_align_legal`), `ProcedureEditor.vue`; quyền đọc qua test API; NC Auditor chỉ đọc, DocType không đổi quyền | Đạt |
| Phạm vi, tài liệu chỉ đọc | 13 file, đều thuộc issue; không chạm `docs/srs.md`… `.claude/`, `.github/`; không sửa `procedure/review.py`, `api/review.py` | Đạt |
| Site sạch, toàn bộ test | `normcore-verify.test` mới, cài app, `run-tests --app normcore`: Ran 1671 tests, OK, rc=0; site đã xóa | Đạt |
| pytest unit+golden+độ phủ | 967 passed; `costing`+`benchmark` phủ 99% | Đạt |
| golden, RTM, quy ước | `golden_engine.py`, `golden_cls.py` chạy được; `build_rtm.py` báo 0 vấn đề liên quan; `check_conventions.py` rc=0 | Đạt |
| CI PR #68 | Cả hai job `pass` | Đạt |

Ghi chú: chưa kiểm giao diện Playwright vì staging (:8100) chưa chứa mã của PR này; luồng Link được phủ bằng test API trên site sạch.
