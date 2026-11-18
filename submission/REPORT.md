# Báo cáo Day 09 — Lê Đức Lương, 2A202603137

Báo cáo kết quả QC tự động trên lô 224 ảnh. Số liệu đối chiếu từ `submission/reports/`.

## 1. Kết luận trước
**Kết luận: HOLD** (mã thoát 10): chưa được phát hành.
- **Ảnh vào / ra:** 224 ảnh vào; 21 ảnh bị loại ở cửa vào (8 `DUP_IMAGE_EXACT`, 5 `LEAK_TEST`, 3 `BAD_SIZE`, 3 `DUP_IMAGE_NEAR`, 2 `CORRUPT_IMAGE`); **203 ảnh** vào QC và ra bản dataset **nháp** `submission/export/clean_v1/` (`manifest.json`: `n_images` = 203), ghi rõ là Hold nên chưa phát hành.
- **Lý do:** không còn lỗi bắt buộc nào (0 lỗi `ERROR` ở `07_error_list_v3`), nhưng **38/203 ảnh (18.7%)** còn cảnh báo chưa được người duyệt, vượt ngưỡng `warn_ratio_hold` = 10% nên cổng chặn ở Hold (`08_summary.json`: `n_warn_images` = 38, `warn_ratio` = 0.1872). Hàng đợi người duyệt có 125 ảnh nhưng ngân sách chỉ 80 ảnh (45 ảnh không ai xem).

## 2. Lỗi và phân việc
Số liệu từ `02_error_list_v1` (210 dòng lỗi trên 148 ảnh khác nhau). Cột số là **số dòng lỗi (số ảnh)**; mẫu số là 224 ảnh với 5 mã ở cửa vào, 203 ảnh với các mã còn lại.

| Mã lỗi | Số dòng lỗi (số ảnh) | Ai sửa (máy/người) | Vì sao |
|---|---:|---|---|
| `DUP_IMAGE_EXACT` | 8 (8) / 224 | máy (`remove_image`) | trùng từng byte, loại là an toàn |
| `DUP_IMAGE_NEAR` | 3 (3) / 224 | máy (`remove_image`) | phash ≤ 8; có rủi ro loại nhầm (xem mục 3) |
| `LEAK_TEST` | 5 (5) / 224 | máy (`remove_image`) | ảnh trùng với tập test/val, bắt buộc loại để không rò rỉ |
| `BAD_SIZE` | 3 (3) / 224 | máy (`remove_image`) | cạnh ngắn < 250px |
| `CORRUPT_IMAGE` | 2 (2) / 224 | máy (`remove_image`) | không mở được ảnh |
| `BAD_CLASS_NAME` | 2 (1, `data.yaml`) | máy (`rename_classes`) | tên lớp sai, ghi lại đúng `cfg["classes"]` |
| `BAD_FORMAT` | 3 (3) / 203 | máy (`drop_line`) | dòng nhãn hỏng cú pháp |
| `BAD_CLASS_ID` | 6 (6) / 203 | máy (`drop_line`) | id lớp ngoài 0..3 |
| `BOX_ZERO` | 4 (4) / 203 | máy (`drop_line`) | box rỗng, không có gì để sửa |
| `DUP_BOX` | 7 (7) / 203 | máy (`drop_line`) | box lặp cùng lớp, IoU cao |
| `BOX_OUT_OF_IMAGE` | 8 (8) / 203 | máy (`clip_box`) | cắt về trong [0,1], giữ nguyên lớp |
| `MISSING_LABEL_FILE` | 6 (6) / 203 | **người** (`needs_label`) | máy không được bịa nhãn; đẩy lên đầu hàng đợi |
| `EMPTY_LABEL` | 12 (12) / 203 | **người** | file rỗng có thể là ảnh nền hoặc thiếu nhãn, chỉ người phân biệt được |
| `BOX_TINY` | 6 (4) / 203 | **người** | cảnh báo, không có đáp án để máy tự sửa |
| `BOX_HUGE` | 3 (3) / 203 | **người** | cảnh báo box chiếm gần hết ảnh |
| `CLASS_RARE` | 4 (cấp dataset) | **người** | lớp ít box, là quyết định của dự án |
| `POSSIBLE_MISSING` | 53 (52) / 203 | **người** | model thấy vật nhãn không có |
| `POSSIBLE_LOOSE_BOX` | 28 (24) / 203 | **người** | box lỏng/lệch so với model |
| `POSSIBLE_FALSE_POS` | 29 (27) / 203 | **người** | box nhãn không khớp vật nào model thấy |
| `POSSIBLE_WRONG_CLASS` | 18 (18) / 203 | **người** | khác lớp so với model; model cũng có thể sai |

Máy tự sửa 29 thay đổi ở `03_fixes.csv`: 20 `drop_line`, 8 `clip_box`, 1 `rename_classes` (cộng 6 dòng `needs_label` là chuyển người, không phải sửa). Sau khi sửa, `04_error_list_v2` không còn lỗi cú pháp nào, chỉ còn 6 `MISSING_LABEL_FILE` chờ người.

**Hàng đợi người duyệt (`05_review_queue.csv`, 125 ảnh):** điểm ưu tiên = tổng trọng số `review.weights` của từng cảnh báo (nhân với `1 + conf`) cộng điểm cho ảnh vừa bị máy sửa. Vì thế 6 ảnh `NEEDS_LABEL` (trọng số 10, chỉ người mới gán được) đứng gần đầu; `img_0020` đứng đầu với 11.5 vì cộng dồn `FIXED_DROP_LINE`, `POSSIBLE_MISSING` và `POSSIBLE_WRONG_CLASS` (loại lỗi ngữ nghĩa nặng nhất, trọng số 3). Với ngân sách 80 ảnh, người xem được 80/125 ảnh (64%): lỗi ngữ nghĩa `POSSIBLE_*` giảm từ 123 (`04_error_list_v2`) xuống 57 (`07_error_list_v3`), tức xử lý được 66 lỗi (54%); 45 ảnh không ai xem. **Lưu ý:** người duyệt là **mô phỏng** (`scripts/human_review_sim.py`: cả 80 ảnh đều được "thay bằng nhãn người"), nên con số v3 là lạc quan hơn người thật: người thật có thể sót hoặc sửa sai.

## 3. Calibration (2 ngưỡng)
| Tham số | Khởi đầu | Đã chọn | Precision / Recall (trước → sau) | Lý do (đánh đổi) |
|---|---|---|---|---|
| `duplicates.phash_dist` | 2 | 8 | `DUP_IMAGE_NEAR` P/R: 1.00 / 0.50 → 1.00 / 0.67 (3/6 → 4/6 lỗi chèn); `DUP_IMAGE_EXACT` giữ 1.00 / 1.00 | Đây là lỗi tự xoá ảnh nên ưu tiên **precision** (cờ sai = xoá nhầm ảnh tốt). Từ 4 đến 14 precision luôn 1.00 và recall đứng yên 0.67 (bình nguyên), nên chọn 8 nằm giữa bình nguyên cho an toàn. Không chọn 16 dù F1 cao nhất (0.91): sát "vách đá" ở 20, nơi `DUP_IMAGE_EXACT` tụt còn 0.33 recall |
| `second_opinion.conf` | 0.25 | 0.6 | `WRONG_CLASS` P/R: 0.56 / 0.83 → 0.62 / 0.83; `MISSING`: 0.50 / 1.00 → 0.57 / 1.00 | 0.6 là mức conf cao nhất mà `MISSING` vẫn giữ recall 1.00 (ở 0.7 tụt còn 0.88, ở 0.8 còn 0.75: bỏ sót lỗi). Đây là cảnh báo cho người nên chấp nhận precision thấp để giữ recall; chọn 0.8 dù `WRONG_CLASS` đạt P 1.00 sẽ làm mất 2/8 ca thiếu nhãn. Tăng conf cũng giảm bớt cảnh báo giả cho hàng đợi duyệt |

Số liệu lấy từ `submission/calibration/calibration_report.md`. `POSSIBLE_LOOSE_BOX` rất kém ở mọi mức conf (P ≤ 0.50, R ≤ 0.60) và `POSSIBLE_FALSE_POS` không phụ thuộc `conf` (P 0.31 / R 1.00, dùng `fp_conf` cố định), nên hai loại này không điều chỉnh được bằng ngưỡng đang calibrate.

**Chỗ calibration có thể đánh lừa:** `DUP_IMAGE_NEAR` trong calib chỉ có 6 lỗi chèn nên mỗi ảnh làm recall nhảy 0.17, và bảng cho thấy F1 cao nhất ở `phash_dist=16` (0.91) nhưng ngay sau đó ở 20 recall `DUP_IMAGE_EXACT` sập còn 0.33 — tối ưu theo F1 sẽ chọn đúng sát mép vách. Trên lô raw (`01_intake.csv`, `phash_dist=8`), pipeline loại 21/224 ảnh: 8 `DUP_IMAGE_EXACT`, 5 `LEAK_TEST`, 3 `BAD_SIZE`, 3 `DUP_IMAGE_NEAR`, 2 `CORRUPT_IMAGE`. Trong 3 ảnh `DUP_IMAGE_NEAR`, chỉ `img_0223` (so với `img_0077`, phash 6) cần ngưỡng > 2; hai ảnh còn lại phash 0. Nghĩa là phần lợi của ngưỡng cao hơn trên raw chỉ dựa vào **1 ảnh**. Tôi đã mở xem cặp `img_0223`/`img_0077`: hai ảnh **giống hệt nhau về nội dung**, chỉ khác độ nét (`img_0077` nét hơn, `img_0223` mờ hơn), tức là trùng thật nên việc loại `img_0223` là đúng và không phải xoá nhầm. Tuy nhiên đây mới là 1 trường hợp, chưa đủ để kết luận `phash_dist=8` an toàn trên toàn bộ dữ liệu: `phash_dist=2` sẽ bỏ sót đúng ca này (một bản sao mờ), còn ngưỡng cao hơn thì phải kiểm thêm xem có cặp ảnh khác nhau bị coi là trùng hay không. Ngoài ra calib không có ca `LEAK_TEST` còn raw có 5 ca, nên recall của calib không phản ánh lô raw.

## 4. Cửa chặn và điều pipeline KHÔNG bắt được
**3 lỗi tự nhìn thấy khi xem `work/viz/` (bằng mắt, trước khi chạy pipeline):**
1. `img_0001`: người lính mặc quân phục rằn ri ở giữa/bên phải ảnh **không có box** (chỉ có 2 box `person`: người cầm gậy và một người bị cắt ở mép phải) → **thiếu nhãn** (missed object), file nhãn có nhưng thiếu dòng.
2. `img_0020`: chiếc xe buýt Metro Local to bên trái được gán nhãn `1:truck` (xe tải) → **gán nhầm lớp** (đúng ra là `bus`). Box ôm khít xe nên lỗi này là lỗi ngữ nghĩa, máy khó bắt chắc, cần người duyệt hoặc `second_opinion`.
3. `img_0030`: ảnh rất đông người (~15 box), nhiều box **chồng lấn** (vd. cầu thủ phía trước bên phải có 2 box chồng nhau) và nhiều box sát mép trái ảnh bị cắt; một số nhãn hiển thị `Person` thay vì `person` → nghi **box trùng/dư**, **box tràn ảnh** và **tên lớp không nhất quán**.

*(Các nhận xét trên là quan sát bằng mắt; cần đối chiếu lại với `02_error_list_v1` sau khi chạy pipeline.)*

**(a) Cửa chặn thật sự chặn.** Chạy `python -m pipeline.run --budget 0 --reports work/rep_nb --export-dir work/exp_nb` (không có người duyệt nên ảnh thiếu file nhãn còn nguyên): sau khi máy tự sửa, hàng đợi vẫn còn 6 ảnh `MISSING_LABEL_FILE` (máy không bịa nhãn), nên cổng kết luận **REWORK** (`còn 6 lỗi bắt buộc (kể cả ở ảnh đã duyệt)`), **mã thoát 20**, log in `KHÔNG xuất: còn lỗi bắt buộc (Rework)` và thư mục `work/exp_nb` **không được tạo** (`Test-Path` = False). So với lần chạy chính (ngân sách 80 ảnh): 6 ảnh này nằm trong 80 ảnh được duyệt nên về 0 lỗi bắt buộc và ra Hold, có xuất bản nháp.

**(b) Điểm pipeline KHÔNG bắt được** (bằng chứng từ `calibration_report.md` ở cấu hình đã chọn `phash_dist=8`, `conf=0.6`):
1. **Box lỏng nhẹ:** `POSSIBLE_LOOSE_BOX` có precision 0.20 / recall 0.20 (chỉ bắt 1/5 lỗi chèn) và không mức `conf` nào cải thiện được cả hai: recall cao nhất là 0.60 nhưng precision chỉ 0.38 (conf 0.1), còn precision 0.50 thì recall chỉ 0.20 (conf 0.7–0.8). Ngưỡng `iou_loose` bị cố định và model cũng có thể vẽ box lệch nhẹ so với vật, nên box lệch vài pixel dễ lọt vào dataset mà không ai biết.
2. **Ảnh trùng bị biến đổi mạnh:** `DUP_IMAGE_NEAR` chỉ đạt recall 0.67 (bắt 4/6 ảnh trùng chèn); nhiều khả năng 2 ảnh còn lại bị biến đổi mạnh nên phash xa hơn ngưỡng. Nới `phash_dist` lên 20 làm recall của `DUP_IMAGE_EXACT` sụp còn 0.33, nên không thể "bắt hết" bằng cách tăng ngưỡng. Ảnh bị cắt 80% rồi thu nhỏ là điểm mù đã biết.
3. **Nhầm lớp mà model lớn cũng nhầm:** `second_opinion` chỉ so với một model (yolo26l); `POSSIBLE_WRONG_CLASS` đạt recall 0.83 (bỏ sót 1/6) và precision chỉ 0.62, nên khi nhãn và model cùng nhầm (ví dụ `truck`/`bus`/`car` trông giống nhau) thì không có cờ nào. `POSSIBLE_FALSE_POS` còn kém hơn: precision 0.31, tức khoảng 2/3 cờ là báo động giả.
4. **Ảnh `EMPTY_LABEL`:** file nhãn rỗng được báo là cảnh báo (12 ảnh), nhưng máy không phân biệt được ảnh nền hợp lệ với ảnh bị thiếu nhãn.

## 5. Train: raw vs clean (tùy chọn, chấm riêng)
Thí nghiệm huấn luyện đối đầu giữa dữ liệu gốc (`raw`) và dữ liệu sau pipeline (`clean`) được thực hiện trên Google Colab (GPU T4) với mô hình `yolo26n.pt`, 20 epochs, batch 16, imgsz 640 trên 2 seed (0 và 1). Tập đánh giá là `data/test` (100 ảnh chuẩn).

Kết quả từ `submission/results/comparison.md`:

| biến thể | #ảnh train | số seed | map50 (TB ± độ lệch) | map50_95 (TB ± độ lệch) | precision (TB ± độ lệch) | recall (TB ± độ lệch) |
|---|---|---|---|---|---|---|
| raw | 224 | 2 | 0.726 ± 0.000 | 0.512 ± 0.004 | 0.764 ± 0.061 | 0.649 ± 0.028 |
| clean | 203 | 2 | 0.699 ± 0.025 | 0.486 ± 0.013 | 0.796 ± 0.050 | 0.596 ± 0.049 |

Chênh mAP50 (clean − raw) = **-0.027** (-2.7%).

**Phân tích và kết luận trung thực:**
1. **So sánh chênh lệch với độ nhiễu giữa các seed:**
   - Mức chênh lệch trung bình giữa `clean` và `raw` là -0.027. Tuy nhiên, độ lệch chuẩn giữa các seed của `clean` lên tới **± 0.025** (ở seed 0, `clean` đạt 0.6813; nhưng ở seed 1 vọt lên 0.7163, biến thiên 0.035).
   - Vì khoảng chênh lệch nằm trọn trong biên độ nhiễu ngẫu nhiên giữa các lần khởi tạo seed, **chưa đủ bằng chứng thống kê** để kết luận tập dữ liệu nào cho mô hình tốt hơn nếu chỉ nhìn vào mAP50 tổng thể.
2. **Precision vs Recall:**
   - `clean` cho **Precision trung bình cao hơn** rõ rệt (0.796 ± 0.050 so với 0.764 ± 0.061 của `raw`), đặc biệt ở seed 0 đạt tới 0.8310. Điều này chứng minh việc dọn dẹp nhãn sai, lọc box tràn viền và bỏ ảnh hỏng giúp mô hình ít bị dự đoán sai/dự đoán nhầm hơn.
   - Nhưng Recall của `clean` thấp hơn (0.596 so với 0.649), làm mAP50 trung bình bị giảm nhẹ.
3. **Hai nguyên nhân chính giải thích kết quả:**
   - **Giả thuyết 1: `raw` bị rò rỉ dữ liệu kiểm tra (`LEAK_TEST`) và có ảnh trùng.** Pipeline ở Bước 1 phát hiện `raw` chứa 5 ảnh rò rỉ từ tập test và 8 ảnh trùng lặp tuyệt đối. Mô hình `raw` đã được huấn luyện trên chính các ảnh có mặt trong tập test (data leakage), dẫn đến điểm số mAP của `raw` bị thổi phồng giả tạo (overestimated). *Cách kiểm:* Đánh giá lại cả hai mô hình trên một tập test hoàn toàn độc lập nằm ngoài bộ COCO hiện tại, hoặc loại bỏ 5 ảnh leak khỏi `raw` rồi train lại.
   - **Giả thuyết 2: Số lượng ảnh train của `clean` bị giảm (203 vs 224 ảnh) và các lớp hiếm bị ảnh hưởng nặng.** `clean` bị loại 21 ảnh ở cửa vào. Với tập dữ liệu nhỏ (~200 ảnh), việc mất 21 ảnh làm giảm độ đa dạng của các lớp ít dữ liệu: cụ thể lớp `truck` (chỉ có 41 box) bị sụt giảm AP50 từ 0.6574 xuống 0.4841 (seed 0). Ngược lại, ở các lớp có nhiều dữ liệu hơn như `person` và `bus`, `clean` đều có AP50 cao hơn hoặc tương đương `raw` (ở seed 0: `person` tăng từ 0.8126 lên 0.8341, `bus` tăng từ 0.6811 lên 0.6972). *Cách kiểm:* Thu thập thêm dữ liệu bổ sung cho lớp hiếm (`truck`, `bus`) để bù lại số ảnh bị loại.
4. **Kết luận trung thực & việc tiếp theo:**
   - Không kết luận "clean tốt hơn raw" về mAP thô khi chưa có đủ số lượng seed lớn hơn (cần 5 seed để làm kiểm định t-test).
   - Tuy nhiên, `clean` mang lại giá trị thực tế quan trọng: loại bỏ hoàn toàn nguy cơ rò rỉ dữ liệu test, tăng Precision dự đoán, và đảm bảo tính minh bạch cho quy trình ML.
   - Bước tiếp theo: Bổ sung thêm ảnh cho các lớp hiếm (`truck`), tăng ngân sách duyệt người lên 125 ảnh để gỡ bỏ trạng thái Hold sang Release.

## 6. Quyết định và ghi chú AI
**(a) Quyết định cuối:** Giữ nguyên kết luận **HOLD** (mã thoát 10) trung thực theo số liệu kiểm tra của pipeline (38/203 ảnh còn cảnh báo, tức 18.7% ≥ ngưỡng 10%).

Để chuyển thành **Release**:
- Cần cấp thêm ngân sách cho người duyệt (`budget_images` trong `review`) từ 80 lên tối thiểu 125 ảnh để người duyệt xem xét hết 45 ảnh còn lại trong hàng đợi `05_review_queue.csv`.
- Sau khi người duyệt xử lý dứt điểm các cảnh báo ngữ nghĩa nghi vấn (`POSSIBLE_MISSING`, `POSSIBLE_WRONG_CLASS`, `POSSIBLE_LOOSE_BOX`), số lượng ảnh còn cảnh báo sẽ giảm xuống dưới 20 ảnh (< 10%), khi đó cổng gate sẽ chuyển sang **Release** và cho phép phát hành chính thức.

**(b) Ghi chú dùng AI:**
1. **Prompt chính:** "Viết logic cho các module QC (`label_format`, `gate`, `autofix`, `second_opinion`) bám sát docstring và định dạng YOLO; dùng try/except bắt lỗi dòng hỏng, lấy ngưỡng từ cfg, không hardcode giá trị, tuân thủ TDD để pass toàn bộ test suite."
2. **Cách kiểm code AI:** Chạy `pytest tests/test_<module>.py -q` theo từng bước TDD; kiểm tra mã sha1 các file gốc không bị sửa đổi (`scripts/_protected.json`); chạy `python -m pipeline.run` kiểm tra tính tái lập và đối chiếu trực tiếp các file output (`03_fixes.csv`, `07_error_list_v3.csv`).
3. **1 lần AI sai:** Khi dùng lệnh PowerShell để cập nhật ngưỡng trong `configs/pipeline.yaml`, script PowerShell làm hỏng encoding UTF-8 (mất dấu tiếng Việt của các comment trong file), làm bẩn git diff toàn bộ file. Cách khắc phục: khôi phục file gốc từ git và dùng thao tác edit từng dòng chính xác để giữ nguyên encoding.
