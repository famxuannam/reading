#!/usr/bin/env python3
"""Dựng dữ liệu cho trang tra cứu đọc sách.

Đọc:
  data/reading-master.csv   bảng chủ (Calibre + Goodreads)
  data/doc-rieng.csv        bảng theo dõi riêng (tuỳ chọn) — sách không có trên Goodreads
  reports/*.pdf             báo cáo tháng, đặt tên YYYY-MM.pdf (vd 2026-10.pdf)
Ghi:
  site/books.json, site/reports.json, site/reports/*.pdf

Chỉ dùng thư viện chuẩn của Python, chạy được trên Cloudflare Pages không cần cài gì.
Nếu tên cột trong CSV khác, sửa danh sách COLS bên dưới.
"""
import csv, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).parent
DATA, REPORTS, SITE = ROOT / "data", ROOT / "reports", ROOT / "site"

# Mỗi trường: danh sách tên cột có thể có, thử lần lượt (không phân biệt hoa thường).
COLS = {
    "title":     ["title", "Title", "tua", "tựa"],
    "author":    ["author", "authors", "Author", "tac_gia"],
    "date_read": ["date_read", "Date Read", "finished", "ngay_doc_xong", "end_date", "ngày gần nhất", "ngay_gan_nhat"],
    "rating":    ["rating", "my_rating", "My Rating", "diem"],
    "topic":     ["topic", "chu_de", "chủ đề"],
    "pages":     ["pages", "#pages", "Number of Pages", "so_trang"],
    "year_pub":  ["year_pub", "Original Publication Year", "year", "pubyear", "nam_xb"],
    "days":      ["days", "so_ngay_doc", "số ngày đọc"],
    "language":  ["language", "languages", "ngon_ngu"],
}

def pick(row, field):
    lower = {k.strip().lower(): v for k, v in row.items() if k}
    for name in COLS[field]:
        v = lower.get(name.lower())
        if v not in (None, ""):
            return v.strip()
    return ""

def to_int(v):
    m = re.search(r"-?\d+", v or "")
    return int(m.group()) if m else None

def to_date(v):
    """Chuẩn hoá về YYYY-MM-DD; chấp nhận 2026/08/30, 30/08/2026, 2026-08-30."""
    v = (v or "").strip()
    if not v:
        return ""
    m = re.match(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", v)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    m = re.match(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", v)
    if m:
        d, mo, y = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    return ""

def sane_pages(n):
    """Bỏ số trang vô lý (vd Business Adventures ghi 150.820 trang trong Calibre)."""
    return n if n and 0 < n <= 5000 else None

def era(year):
    if year is None or year < 100:      # năm 0101 và năm trống trong Calibre
        return ""
    if year < 1800: return "Trước 1800"
    if year < 1900: return "1800–1899"
    if year < 1980: return "1900–1979"
    if year < 2010: return "1980–2009"
    return "2010 trở đi"

def load(path, source):
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        print(f"{path.name}: các cột = {reader.fieldnames}")
        books = []
        for row in reader:
            date = to_date(pick(row, "date_read"))
            if not date:                 # chưa đọc xong → không vào danh mục
                continue
            year = to_int(pick(row, "year_pub"))
            books.append({
                "title": pick(row, "title"),
                "author": pick(row, "author"),
                "date": date,
                "rating": to_int(pick(row, "rating")) or None,
                "topic": pick(row, "topic"),
                "pages": sane_pages(to_int(pick(row, "pages"))),
                "year": year if year and year >= 100 else None,
                "era": era(year),
                "days": to_int(pick(row, "days")),
                "source": source,
            })
        return books

def key(b):
    return (re.sub(r"\W+", "", b["title"].lower()), b["date"][:7])

def main():
    master = load(DATA / "reading-master.csv", "chu")
    if not master:
        sys.exit("Không tìm thấy sách đã đọc trong data/reading-master.csv — kiểm tra file và tên cột ngày đọc xong.")
    private = load(DATA / "doc-rieng.csv", "rieng")

    books = {key(b): b for b in master}
    for b in private:                    # bảng riêng bổ sung sách thiếu, và số ngày đọc nếu bảng chủ không có
        k = key(b)
        if k in books:
            for f in ("days", "rating", "pages", "topic", "year", "era"):
                if not books[k].get(f) and b.get(f):
                    books[k][f] = b[f]
        else:
            books[k] = b

    out = sorted(books.values(), key=lambda b: b["date"], reverse=True)
    for b in out:
        b.pop("source", None)

    SITE.mkdir(exist_ok=True)
    (SITE / "books.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    (SITE / "reports").mkdir(exist_ok=True)
    reports = []
    for pdf in sorted(REPORTS.glob("*.pdf"), reverse=True):
        m = re.match(r"(\d{4})-(\d{2})", pdf.stem)
        if not m:
            print(f"Bỏ qua {pdf.name}: tên file phải dạng YYYY-MM.pdf")
            continue
        shutil.copy2(pdf, SITE / "reports" / pdf.name)
        reports.append({"year": int(m[1]), "month": int(m[2]), "file": f"reports/{pdf.name}"})
    (SITE / "reports.json").write_text(json.dumps(reports, ensure_ascii=False), encoding="utf-8")

    print(f"Xong: {len(out)} sách đã đọc ({len(private)} dòng từ bảng riêng), {len(reports)} báo cáo.")

if __name__ == "__main__":
    main()
