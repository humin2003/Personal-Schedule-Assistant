# Trợ Lý Quản Lý Lịch Trình Cá Nhân (Personal Schedule Assistant)

## I. Giới thiệu
Ứng dụng quản lý lịch trình thông minh trên Desktop (Windows), tích hợp **Xử lý Ngôn ngữ Tự nhiên (NLP) tiếng Việt**, giúp người dùng thêm sự kiện nhanh chóng bằng các câu lệnh đời thường thay vì nhập liệu thủ công phức tạp.

**Sinh viên thực hiện:** Trần Hữu Minh
**MSSV:** 3121410323
**Môn học:** Đồ án chuyên ngành (2025-2026)
**Trạng thái:** Hoàn thiện (v1.0 - Production Ready)

---

## II. Tính năng nổi bật
* **Nhập liệu ngôn ngữ tự nhiên (NLP):**
    * Hiểu các câu lệnh phức tạp: *"Họp team lúc 9h sáng mai tại phòng 302"*.
    * **MỚI:** Tự động bắt yêu cầu nhắc nhở: *"Nhắc tôi trước 15 phút"*.
    * Xử lý linh hoạt thời gian kết thúc (End Time) và dọn dẹp các từ nối dư thừa.
* **Hệ thống nhắc nhở (System Tray):** Ứng dụng chạy ngầm và hiển thị thông báo Pop-up trên Windows khi đến giờ hẹn.
* **Giao diện trực quan:** Tích hợp Lịch (Calendar View) và Danh sách (List View).
* **Kiểm tra xung đột:** Tự động cảnh báo nếu bạn thêm sự kiện trùng giờ với lịch cũ.
* **An toàn dữ liệu:**
    * Lưu trữ cục bộ (SQLite).
    * Hỗ trợ Sao lưu (Export) và Khôi phục (Import) dữ liệu ra file JSON.

---

## III. Công nghệ sử dụng
* **Core:** Python 3.8+
* **Giao diện (GUI):** Streamlit, Streamlit Calendar.
* **NLP Engine:**
    * `Underthesea`: Nhận diện tên riêng, địa điểm (NER).
    * `Regex` & `Dateutil`: Xử lý logic thời gian, nhắc hẹn và quy tắc ngữ pháp tiếng Việt.
* **Database:** SQLite.
* **Đóng gói (Build):** PyInstaller (Chế độ One-dir tối ưu hóa).

---

## IV. Hướng dẫn Cài đặt & Sử dụng

### Cách 1: Dành cho Người dùng (Khuyên dùng)
Bạn không cần cài đặt Python hay bất kỳ phần mềm nào khác.

1.  Truy cập mục **[Releases](../../releases)** bên phải giao diện GitHub này.
2.  Tải file nén `ScheduleAssistant.zip` (hoặc file `.exe`) của phiên bản mới nhất.
3.  Giải nén và chạy file `ScheduleAssistant.exe`.
    *(Lưu ý: Lần đầu khởi động có thể mất khoảng 10-15s để hệ thống giải nén tài nguyên).*

### Cách 2: Dành cho Lập trình viên (Chạy từ Source Code)
Yêu cầu máy đã cài đặt Python và Git.

1.  **Clone dự án:**
    ```bash
    git clone <link-repo-cua-ban>
    cd Personal-Schedule-Assistant
    ```

2.  **Cài đặt thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Khởi chạy ứng dụng:**
    ```bash
    streamlit run src/app.py
    ```
    Ứng dụng sẽ mở trên trình duyệt tại: `http://localhost:8501`

---

## V. Cấu trúc thư mục
```text
📦 Personal-Schedule-Assistant
 ┣ 📂 data/                 # Chứa database (schedule.db)
 ┣ 📂 src/                  # Mã nguồn chính
 ┃ ┣ 📂 nlp/                # Module xử lý ngôn ngữ (NLP Engine)
 ┃ ┣ 📜 app.py              # Giao diện chính (Streamlit)
 ┃ ┗ 📜 database.py         # Quản lý lưu trữ SQLite
 ┣ 📂 tests/                # Bộ Test Case & Báo cáo độ chính xác
 ┣ 📜 run.py                # File mồi để khởi động Streamlit trong môi trường EXE
 ┣ 📜 schedule_app.spec     # Cấu hình đóng gói PyInstaller (Quan trọng)
 ┣ 📜 requirements.txt      # Danh sách thư viện
 ┗ 📜 README.md             # Hướng dẫn sử dụng
