# Nghiệm thu NORM-75 (lọc khoa gõ tay + Tab không tính lại danh sách NC Technical Service)

Commit đã kiểm: `34ba3b5a32d520cc9e57d2303fc1e6ce69fb5a90` (PR #76 đã merge vào develop; staging chạy mã này). Kiểm trên `origin/develop` f1542ed (chứa 34ba3b5).

| Tiêu chí | Bằng chứng | Kết quả |
| :-- | :-- | :-- |
| Tái hiện trên staging (:8100), tài khoản Clinician Test (không phải Administrator): "Chưa có quy trình" → khoa K01 chọn gợi ý → gõ `THU-K02` + Tab | Bước 1: 2 dòng (THU-F002-A/B). Bước 2 sau Tab: bộ lọc mã dịch vụ đổi thành THU-K02-A1/A2/A3, danh sách "3 trong số 3" gồm THU-K02-A3, A2, A1. Ảnh: qa-norm75-step1-k01.png, qa-norm75-step3-after-wait.png | Đạt |
| Chọn từ gợi ý vẫn đúng (không hồi quy) | Bước K01 chọn gợi ý ra đúng 2 dòng | Đạt |
| Test tái hiện có và đỏ trước khi sửa | `test_service_list_behavior.py` 2 passed; Reviewer đã chạy harness với bản a1dc233 cho kết quả sai | Đạt |
| Site sạch, toàn bộ test | `normcore-verify.test` mới, `run-tests --app normcore`: Ran 1928 tests, OK; site đã xóa | Đạt |
| pytest unit+golden+độ phủ | 1142 passed; `costing`+`benchmark` phủ 99% | Đạt |
| Quy ước | `check_conventions.py` rc=0 | Đạt |
| Soát diff test, phạm vi, tài liệu chỉ đọc | PR chỉ 3 tệp: `nc_technical_service_list.js` (+14), harness, test mới; không xóa/skip/nới test; không chạm docs chỉ đọc, `.github/` | Đạt |
| CI PR #76 | Cả hai job pass | Đạt |
| Quyền / NC Auditor | Không đổi quyền DocType, không đổi API; sửa chỉ ở JS danh sách | Không áp dụng |

Ghi chú: khi chụp ngay sau Tab, danh sách còn hiện 2 dòng cũ vài giây ("Làm mới…") rồi cập nhật thành 3 dòng. Đây là độ trễ tải, không phải lỗi. Cửa sổ console có 1 lỗi 404 tải `/assets/normcore/js/nc_technical_service_list.js` (có từ trước, tệp được nạp theo đường doctype list nên không ảnh hưởng chức năng; không chặn). Chưa kiểm bằng tài khoản NC Auditor trên trình duyệt vì không đổi phân quyền.
