# Sổ đọc sách

Trang tra cứu báo cáo đọc sách hằng tháng và danh mục sách đã đọc.
Dữ liệu gốc nằm trong repo này; Cloudflare Pages dựng trang, Cloudflare Access khoá bằng email.

## Cấu trúc

```
data/reading-master.csv   bảng chủ (chép từ thư mục đọc sách)
data/doc-rieng.csv        bảng theo dõi riêng — tuỳ chọn
reports/2026-10.pdf       báo cáo tháng, tên file bắt buộc dạng YYYY-MM.pdf
build.py                  chuyển dữ liệu thành site/books.json, site/reports.json
site/                     trang web (index.html)
```

Chạy thử trên máy: `python3 build.py && cd site && python3 -m http.server`, rồi mở http://localhost:8000.
Lần chạy đầu, `build.py` in ra tên các cột nó đọc được. Nếu danh mục trống hay thiếu trường nào,
sửa danh sách `COLS` ở đầu `build.py` cho khớp tên cột thật.

Một cuốn vào danh mục khi có **ngày đọc xong**. Bảng riêng bổ sung những cuốn không có trong bảng chủ,
và điền số ngày đọc cho những cuốn đã có (khớp theo tên sách + tháng đọc xong).

## Cài đặt lần đầu (khoảng 20 phút)

### 1. GitHub
Tạo repo **private** (ví dụ `doc-sach`), đưa toàn bộ thư mục này lên, kèm hai file CSV và PDF tháng 10.

### 2. Cloudflare Pages
1. dash.cloudflare.com → **Workers & Pages** → **Create** → tab **Pages** → **Connect to Git** → chọn repo.
2. Build settings:
   - Framework preset: **None**
   - Build command: `python3 build.py`
   - Build output directory: `site`
3. **Save and Deploy**. Trang sẽ ở `doc-sach.pages.dev` (hoặc tên tương tự).

### 3. Cloudflare Access — khoá trang
1. Trong project Pages → **Settings** → **General** → **Access policy** → **Enable** (bật cho bản xem trước).
2. Vào **Zero Trust** (lần đầu phải chọn tên team và gói **Free**, tới 50 người dùng).
3. **Access → Applications → Add an application → Self-hosted**:
   - Domain: `doc-sach.pages.dev` (thêm dòng thứ hai `*.doc-sach.pages.dev` để khoá cả bản xem trước)
   - Session duration: **1 month** để không phải đăng nhập lại thường xuyên
   - Policy: Action **Allow**, Include → **Emails** → email của anh
4. Đăng nhập bằng **One-time PIN**: Cloudflare gửi mã về email, nhập là vào.

Mở trang trong cửa sổ ẩn danh để chắc chắn nó đòi đăng nhập.
Làm vậy trên mỗi máy và điện thoại một lần; phiên đăng nhập giữ theo thời hạn đã đặt.

## Mỗi tháng

1. Xuất báo cáo từ Claude Design ra PDF, đặt tên `YYYY-MM.pdf`, bỏ vào `reports/`.
2. Chép `reading-master.csv` (và `doc-rieng.csv`) mới nhất vào `data/`.
3. Commit và push. Cloudflare tự dựng lại trong khoảng một phút.
