"""BƯỚC 2/4 — Sửa tự động những lỗi bắt buộc mà máy sửa được AN TOÀN.   ★★

Test:  pytest tests/test_autofix.py -q

`fix(ds, issues, cfg) -> list[dict]`: duyệt `issues` (chỉ lỗi severity ERROR), sửa thẳng vào thư mục `ds`,
và trả về danh sách thay đổi; mỗi phần tử có khoá: image, line, action, before, after
(đây chính là file `03_fixes.csv` — bằng chứng pipeline đã làm gì, người có thể kiểm lại).

| code lỗi                                       | cách sửa                                    | action           |
|------------------------------------------------|---------------------------------------------|------------------|
| BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO, DUP_BOX    | xoá dòng đó khỏi file nhãn                  | "drop_line"      |
| BOX_OUT_OF_IMAGE                               | cắt box về trong [0,1] (giữ nguyên lớp)     | "clip_box"       |
| MISSING_LABEL_FILE                             | KHÔNG sửa file (máy không thể bịa nhãn): ghi 1 dòng fix, before="(không có file)", after="chuyển người gán" | "needs_label" |
| BAD_CLASS_NAME                                 | ghi lại `names` trong data.yaml đúng `cfg["classes"]` | "rename_classes" |
| DUP_IMAGE_*, LEAK_TEST, CORRUPT_IMAGE, BAD_SIZE| xoá ảnh + nhãn khỏi `ds`                    | "remove_image"   |

Bẫy cần nghĩ tới (có test cho từng cái)
- Một file có NHIỀU dòng lỗi: số dòng trong `issues` là số dòng GỐC. Nếu xoá từng dòng một thì số dòng lệch.
  Gom theo file, rồi ghi lại MỘT lần.
- Sau khi cắt, box có thể không còn diện tích (nằm hẳn ngoài ảnh): lúc đó xoá dòng thay vì ghi box rỗng.
- Một dòng có 2 lỗi (vd. BOX_OUT_OF_IMAGE + DUP_BOX): xoá dòng thắng, chỉ ghi 1 fix `drop_line`, không ghi thêm `clip_box`. Dòng trống ở giữa file vẫn đếm vào số dòng gốc.
- Ảnh vừa bị xoá (DUP_IMAGE_*...) mà còn issue dòng của chính nó: bỏ qua êm, không được báo lỗi/chết.
- Không động tới lỗi WARN (cảnh báo là việc của người). Không sửa file ở `data/raw/` — chỉ sửa `ds`.
- Chạy lần 2 trên dữ liệu đã sửa phải không làm gì thêm (idempotent) — NGOẠI LỆ duy nhất: `needs_label` được ghi lại mỗi lần còn lỗi `MISSING_LABEL_FILE` (vì ảnh vẫn chưa có nhãn).

- `needs_label` KHÔNG tạo file nhãn rỗng (rỗng = "ảnh nền", khác với "chưa gán"). `review_queue` sẽ đẩy ảnh này lên đầu hàng đợi cho người.

Gợi ý: `yaml.safe_load / safe_dump`.
"""
from collections import defaultdict  # noqa: F401

import yaml  # noqa: F401

from ..common import ERROR, parse_yolo_line  # noqa: F401


DROP_CODES = {"BAD_FORMAT", "BAD_CLASS_ID", "BOX_ZERO", "DUP_BOX"}         # xoá dòng
REMOVE_IMAGE_CODES = {"DUP_IMAGE_EXACT", "DUP_IMAGE_NEAR", "LEAK_TEST", "CORRUPT_IMAGE", "BAD_SIZE"}   # xoá ảnh + nhãn


def _clip(text):
    """Cắt box về trong [0,1]. Trả về dòng mới, hoặc None nếu sau khi cắt box không còn diện tích."""
    cid, cx, cy, w, h = parse_yolo_line(text)
    x1, x2 = max(0.0, cx - w / 2), min(1.0, cx + w / 2)
    y1, y2 = max(0.0, cy - h / 2), min(1.0, cy + h / 2)
    nw, nh = x2 - x1, y2 - y1
    if nw <= 0 or nh <= 0:
        return None
    return f"{cid} {(x1 + x2) / 2:.6f} {(y1 + y2) / 2:.6f} {nw:.6f} {nh:.6f}"


def fix(ds, issues, cfg):
    fixes = []

    def log(image, line, action, before, after):
        fixes.append({"image": image, "line": line, "action": action, "before": before, "after": after})

    errors = [i for i in issues if i.severity == ERROR]      # cảnh báo là việc của người: không đụng tới

    # 1) Xoá ảnh (+ nhãn): làm trước để các issue dòng của ảnh đó bị bỏ qua êm.
    removed = set()
    for stem in sorted({i.image for i in errors if i.code in REMOVE_IMAGE_CODES}):
        img = ds.image_path(stem)
        lbl = ds.label_path(stem)
        if img is None and not lbl.exists():
            continue
        name = img.name if img else stem
        if img is not None:
            img.unlink()
        if lbl.exists():
            lbl.unlink()
        ds._size_cache.pop(stem, None)
        removed.add(stem)
        log(stem, "", "remove_image", name, "(đã xoá ảnh + nhãn)")

    # 2) Sửa dòng nhãn: gom theo file, dùng số dòng GỐC, ghi lại MỘT lần.
    drops, clips = defaultdict(set), defaultdict(set)
    for i in errors:
        if i.image in removed or i.line is None:
            continue
        if i.code in DROP_CODES:
            drops[i.image].add(i.line)
        elif i.code == "BOX_OUT_OF_IMAGE":
            clips[i.image].add(i.line)

    for stem in sorted(set(drops) | set(clips)):
        path = ds.label_path(stem)
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        new, changes = list(lines), []
        delete = set()
        for n in sorted(drops[stem] | clips[stem]):
            if not 1 <= n <= len(lines):
                continue
            before = lines[n - 1]
            if n in drops[stem]:                       # xoá thắng cắt
                delete.add(n)
                changes.append((n, "drop_line", before, "(đã xoá dòng)"))
                continue
            try:
                clipped = _clip(before)
            except ValueError:
                clipped = None
            if clipped is None:
                delete.add(n)
                changes.append((n, "drop_line", before, "(đã xoá dòng)"))
            else:
                new[n - 1] = clipped
                changes.append((n, "clip_box", before, clipped))
        if changes:
            kept = [ln for k, ln in enumerate(new, 1) if k not in delete]
            path.write_text("".join(ln + "\n" for ln in kept), encoding="utf-8")
            for n, action, before, after in changes:
                log(stem, n, action, before, after)

    # 3) Ảnh chưa có file nhãn: KHÔNG bịa nhãn (cũng không tạo file rỗng), chuyển người gán.
    for stem in sorted({i.image for i in errors if i.code == "MISSING_LABEL_FILE"} - removed):
        log(stem, "", "needs_label", "(không có file)", "chuyển người gán")

    # 4) Tên lớp: ghi lại names đúng cfg["classes"], giữ các khoá khác của data.yaml.
    if any(i.code == "BAD_CLASS_NAME" for i in errors):
        old = ds.yaml_names()
        data = {}
        if ds.yaml_path.exists():
            data = yaml.safe_load(ds.yaml_path.read_text(encoding="utf-8")) or {}
        data["names"] = {k: n for k, n in enumerate(cfg["classes"])}
        ds.yaml_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        log("data.yaml", "", "rename_classes", str([old[k] for k in sorted(old)]), str(list(cfg["classes"])))

    return fixes
