"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""
from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line  # noqa: F401


def run(ds, cfg):
    c = cfg["label_format"]
    tol, min_px, max_frac, dup_iou = c["overflow_tol"], c["min_box_px"], c["max_box_frac"], c["dup_box_iou"]
    n_classes = len(ds.classes)
    issues = []

    def add(sev, code, stem, line, msg, **extra):
        issues.append(Issue("label_format", sev, code, stem, msg, line=line, extra=extra))

    for path in ds.label_files():
        stem = path.stem
        size = None            # chỉ mở ảnh khi thật sự cần (BOX_TINY)
        seen = []              # [(class_id, (cx, cy, w, h))] các dòng hợp lệ phía trước
        # read_label_lines bỏ dòng trống nhưng GIỮ số dòng gốc
        for line_no, text in ds.read_label_lines(stem) or []:
            try:
                cid, cx, cy, w, h = parse_yolo_line(text)
            except ValueError as e:
                add(ERROR, "BAD_FORMAT", stem, line_no, f"dòng sai định dạng: {e}")
                continue
            if not 0 <= cid < n_classes:
                add(ERROR, "BAD_CLASS_ID", stem, line_no, f"id lớp {cid} ngoài 0..{n_classes - 1}", class_id=cid)
                continue
            if w <= 0 or h <= 0:
                add(ERROR, "BOX_ZERO", stem, line_no, f"box rỗng: w={w}, h={h}")
                continue

            box = (cx, cy, w, h)
            overflow = max(-(cx - w / 2), cx + w / 2 - 1, -(cy - h / 2), cy + h / 2 - 1)
            if overflow > tol:
                add(ERROR, "BOX_OUT_OF_IMAGE", stem, line_no, f"box tràn ảnh {overflow:.4f}", overflow=overflow)

            if any(pc == cid and iou_xywh(pb, box) > dup_iou for pc, pb in seen):
                add(ERROR, "DUP_BOX", stem, line_no, "box lặp (cùng lớp, IoU cao với dòng trước)")
            seen.append((cid, box))

            if size is None:
                size = ds.image_size(stem) or False
            if size and min(w * size[0], h * size[1]) < min_px:
                add(WARN, "BOX_TINY", stem, line_no, f"box quá nhỏ (cạnh ngắn {min(w * size[0], h * size[1]):.1f}px)")
            if w * h > max_frac:
                add(WARN, "BOX_HUGE", stem, line_no, f"box quá lớn (chiếm {w * h:.2f} diện tích ảnh)")
    return issues
