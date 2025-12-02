# Trợ Lý Quản Lý Lịch Trình Cá Nhân (Personal Schedule Assistant)

## I. Giới thiệu
Ứng dụng quản lý lịch trình thông minh trên Desktop, tích hợp xử lý ngôn ngữ tự nhiên (NLP) tiếng Việt, giúp người dùng thêm sự kiện nhanh chóng bằng các câu lệnh đời thường thay vì nhập liệu thủ công.

**Sinh viên thực hiện:** Minh
**Môn học:** Đồ án chuyên ngành (2025-2026)
**Trạng thái:** Hoàn thiện (Production Ready)

---

## II. Tính năng nổi bật
* **Nhập liệu tự nhiên:** Hiểu các câu lệnh phức tạp tiếng Việt.
    * *Ví dụ:* "Họp team lúc 9h sáng mai tại phòng 302, nhắc trước 15 phút".
* **Nhắc nhở thông minh:** Hệ thống chạy ngầm và hiển thị thông báo (Pop-up System Tray) ngay cả khi ứng dụng bị thu nhỏ.
* **Quản lý trực quan:** Xem lịch dưới dạng đồ họa (Calendar View) hoặc danh sách chi tiết.
* **Tìm kiếm & Lọc:** Tìm kiếm sự kiện theo tên, địa điểm hoặc nội dung gốc.
* **An toàn dữ liệu:** Tự động lưu trữ cục bộ (SQLite) và hỗ trợ Sao lưu/Khôi phục (JSON).

---

## III. Công nghệ sử dụng
* **Ngôn ngữ:** Python 3.8+
* **Giao diện (GUI):** Streamlit, Streamlit Calendar
* **NLP Engine:**
    * `Underthesea`: Trích xuất thực thể tên riêng, địa điểm (NER).
    * `Regex` & `Dateutil`: Xử lý logic thời gian và quy tắc ngữ pháp.
* **Database:** SQLite.
* **Đóng gói:** PyInstaller.

---

## IV. Cấu trúc thư mục
```text
📦 Personal-Schedule-Assistant
 ┣ 📂 data/               # Chứa database (schedule.db)
 ┣ 📂 dist/               # Chứa file .EXE sau khi build
 ┣ 📂 src/                # Mã nguồn chính
 ┃ ┣ 📂 nlp/              # Module xử lý ngôn ngữ (Core Engine)
 ┃ ┣ 📜 app.py            # Giao diện chính
 ┃ ┗ 📜 database.py       # Quản lý lưu trữ
 ┣ 📂 tests/              # Bộ Test Case & Báo cáo độ chính xác
 ┣ 📜 requirements.txt    # Danh sách thư viện
 ┣ 📜 schedule_app.spec   # Cấu hình đóng gói PyInstaller
 ┗ 📜 README.md           # Hướng dẫn sử dụng

 V. Hướng dẫn cài đặt & Sử dụng
Cách 1: Chạy từ Mã nguồn (Dành cho Dev/Giám khảo)
Yêu cầu: Đã cài đặt Python và Git.

Cài đặt thư viện: Mở CMD/Terminal tại thư mục gốc và chạy:

pip install -r requirements.txt
Khởi chạy ứng dụng:

streamlit run src/app.py
Ứng dụng sẽ tự động mở trên trình duyệt tại địa chỉ: http://localhost:8501

Cách 2: Chạy file thực thi (.EXE)
Yêu cầu: Không cần cài Python.

Truy cập thư mục dist/.

Chạy file ScheduleAssistant.exe.

(Lần đầu khởi động có thể mất khoảng 10-15s để giải nén tài nguyên).

VI. Hướng dẫn đóng gói (Build .EXE)
Nếu bạn muốn tự đóng gói lại ứng dụng thành file .exe, hãy làm theo các bước sau:

Đảm bảo đã cài pyinstaller:


pip install pyinstaller
Chạy lệnh build dựa trên file cấu hình có sẵn:



pyinstaller schedule_app.spec --clean
File .exe sẽ được tạo ra trong thư mục dist/.

VII. Kết quả kiểm thử (NLP)
Tổng số test case: 40 câu lệnh tiếng Việt.

Độ chính xác (Accuracy): 100%.

Chi tiết: Xem file tests/test_report_final2.csv.
