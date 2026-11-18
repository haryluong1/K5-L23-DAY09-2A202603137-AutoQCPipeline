# Báo cáo Day 09 — <Họ và tên>, <MSHV>

> Xoá mọi `TODO(học viên)` và dòng gợi ý. Mỗi ý trả lời bằng **số lấy từ `submission/reports/`**, kèm mẫu số. Cả báo cáo ~1–2 trang.

## 1. Kết luận trước
TODO(học viên): pipeline kết luận **Release / Hold / Rework**? Bao nhiêu ảnh vào, bao nhiêu ảnh ra dataset? Lý do chính (1–3 câu).

## 2. Lỗi và phân việc
Lấy từ `02_error_list_v1` (gom theo mã lỗi). Cột "ai sửa": **máy** (autofix) hay **người** (hàng đợi); chỉ ghi những mã có mặt trong lô của bạn.

| Mã lỗi | Số ảnh/dòng | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
| TODO(học viên) | | | |

TODO(học viên): vì sao `05_review_queue.csv` xếp ảnh đầu hàng như vậy? Với ngân sách 80 ảnh, người xem được bao nhiêu lỗi ngữ nghĩa?

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | 8 | `DUP_IMAGE_NEAR` P/R: 1.00 / 0.50 → 1.00 / 0.67 (3/6 → 4/6 lỗi chèn); `DUP_IMAGE_EXACT` giữ 1.00 / 1.00 | Đây là lỗi tự xoá ảnh nên ưu tiên **precision** (cờ sai = xoá nhầm ảnh tốt). Từ 4 đến 14 precision luôn 1.00 và recall đứng yên 0.67 (bình nguyên), nên chọn 8 nằm giữa bình nguyên cho an toàn. Không chọn 16 dù F1 cao nhất (0.91): sát "vách đá" ở 20, nơi `DUP_IMAGE_EXACT` tụt còn 0.33 recall |
| `second_opinion.conf` | 0.25 | 0.6 | `WRONG_CLASS` P/R: 0.56 / 0.83 → 0.62 / 0.83; `MISSING`: 0.50 / 1.00 → 0.57 / 1.00 | 0.6 là mức conf cao nhất mà `MISSING` vẫn giữ recall 1.00 (ở 0.7 tụt còn 0.88, ở 0.8 còn 0.75: bỏ sót lỗi). Đây là cảnh báo cho người nên chấp nhận precision thấp để giữ recall; chọn 0.8 dù `WRONG_CLASS` đạt P 1.00 sẽ làm mất 2/8 ca thiếu nhãn. Tăng conf cũng giảm bớt cảnh báo giả cho hàng đợi duyệt |

Số liệu lấy từ `submission/calibration/calibration_report.md`. `POSSIBLE_LOOSE_BOX` rất kém ở mọi mức conf (P ≤ 0.50, R ≤ 0.60) và `POSSIBLE_FALSE_POS` không phụ thuộc `conf` (P 0.31 / R 1.00, dùng `fp_conf` cố định), nên hai loại này không điều chỉnh được bằng ngưỡng đang calibrate.

**Chỗ calibration có thể đánh lừa:** `DUP_IMAGE_NEAR` trong calib chỉ có 6 lỗi chèn nên mỗi ảnh làm recall nhảy 0.17, và bảng cho thấy F1 cao nhất ở `phash_dist=16` (0.91) nhưng ngay sau đó ở 20 recall `DUP_IMAGE_EXACT` sập còn 0.33 — tối ưu theo F1 sẽ chọn đúng sát mép vách. Trên lô raw (`01_intake.csv`, `phash_dist=8`), pipeline loại 21/224 ảnh: 8 `DUP_IMAGE_EXACT`, 5 `LEAK_TEST`, 3 `BAD_SIZE`, 3 `DUP_IMAGE_NEAR`, 2 `CORRUPT_IMAGE`. Trong 3 ảnh `DUP_IMAGE_NEAR`, chỉ `img_0223` (so với `img_0077`, phash 6) cần ngưỡng > 2; hai ảnh còn lại phash 0. Nghĩa là phần lợi của ngưỡng cao hơn trên raw chỉ dựa vào **1 ảnh**, và cần mở xem cặp `img_0223`/`img_0077` để chắc đó là trùng thật chứ không phải hai ảnh khác nhau trông giống nhau. Ngoài ra calib không có ca `LEAK_TEST` còn raw có 5 ca, nên recall của calib không phản ánh lô raw.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được
**3 lỗi tự nhìn thấy khi xem `work/viz/` (bằng mắt, trước khi chạy pipeline):**
1. `img_0001`: người lính mặc quân phục rằn ri ở giữa/bên phải ảnh **không có box** (chỉ có 2 box `person`: người cầm gậy và một người bị cắt ở mép phải) → **thiếu nhãn** (missed object), file nhãn có nhưng thiếu dòng.
2. `img_0020`: chiếc xe buýt Metro Local to bên trái được gán nhãn `1:truck` (xe tải) → **gán nhầm lớp** (đúng ra là `bus`). Box ôm khít xe nên lỗi này là lỗi ngữ nghĩa, máy khó bắt chắc, cần người duyệt hoặc `second_opinion`.
3. `img_0030`: ảnh rất đông người (~15 box), nhiều box **chồng lấn** (vd. cầu thủ phía trước bên phải có 2 box chồng nhau) và nhiều box sát mép trái ảnh bị cắt; một số nhãn hiển thị `Person` thay vì `person` → nghi **box trùng/dư**, **box tràn ảnh** và **tên lớp không nhất quán**.

*(Các nhận xét trên là quan sát bằng mắt; cần đối chiếu lại với `02_error_list_v1` sau khi chạy pipeline.)*

TODO(học viên): (a) chứng minh gate chặn đúng: chạy `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb` (không có người duyệt nên ảnh thiếu file nhãn còn nguyên), chỉ ra kết luận **Rework**, mã thoát 20 và việc **không xuất** dataset. (Đừng sửa tay `work/run/ds`: pipeline dựng lại thư mục này từ raw mỗi lần chạy.) (b) ≥ 2 điểm mù có bằng chứng (box lỏng nhẹ, nhầm lớp mà model lớn cũng nhầm, ảnh trùng biến đổi mạnh…).

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Chưa train: ghi "chưa chạy" và lý do, rồi bỏ qua phần còn lại của mục này. Nếu đã train: dán bảng từ `submission/results/comparison.md` (model, epoch, seed, số ảnh train mỗi biến thể).

TODO(học viên): chênh mAP50 (clean − raw) so với **độ lệch chuẩn giữa các seed**; kết luận **trung thực** (nằm trong nhiễu thì nói là chưa kết luận được); ≥ 2 giả thuyết giải thích (ảnh trùng/rò rỉ test trong `raw`, nhãn máy còn lại trong `clean`, test chỉ 100 ảnh…) và cách kiểm.

## 6. Quyết định và ghi chú AI
TODO(học viên): (a) quyết định cuối; nếu Hold/Rework cần làm gì để thành Release? (b) Dùng AI viết code? Ghi 3 dòng: prompt chính, cách bạn kiểm code AI, 1 lần AI sai. Không dùng: ghi "không dùng".

*(Thưởng +2, tùy chọn)* CVAT: lọc `width < 20`, ảnh/số box khớp, đối chiếu `BOX_TINY` (xem docs/CVAT_FILTER.md), 1 câu về `can_review`.
