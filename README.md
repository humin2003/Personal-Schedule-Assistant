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
    * Tự động bắt yêu cầu nhắc nhở: *"Nhắc tôi trước 15 phút"*.
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
* **Giao diện (GUI):** Streamlit, Streamlit Option Menu, Streamlit Calendar.
* **NLP Engine:**
    * `Underthesea`: Nhận diện tên riêng, địa điểm (NER).
    * `Regex` & `Dateutil`: Xử lý logic thời gian, nhắc hẹn và quy tắc ngữ pháp tiếng Việt.
* **Database:** SQLite.
* **Đóng gói (Build):** PyInstaller (Chế độ One-dir tối ưu hóa).

---

## IV. Hướng dẫn Cài đặt
### Cách 1: Dành cho Người dùng (Khuyên dùng)
Bạn không cần cài đặt Python hay bất kỳ phần mềm nào khác.
1.  Truy cập mục **[Releases](../../releases)** bên phải giao diện GitHub này.
2.  Tải file nén `ScheduleAssistant.zip` của phiên bản mới nhất.
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

---

## V. Hướng dẫn Chức năng (Các Tabs)
Giao diện chính được chia thành 4 thẻ chức năng:

1.  **Thêm sự kiện (Add Event):**
    * Nhập câu lệnh tiếng Việt tự nhiên (Ví dụ: *"Đi xem phim với bạn lúc 19h tối nay"*).
    * Hệ thống tự động trích xuất thông tin và thêm vào lịch.

2.  **Xem Lịch Biểu (Calendar View):**
    * Quan sát trực quan các sự kiện theo Tháng/Tuần/Ngày.
    * Hỗ trợ chuyển đổi linh hoạt giữa giao diện Lịch và Danh sách (List View).

3.  **Quản lý Data (Data Management):**
    * **Sao lưu/Khôi phục:** Xuất dữ liệu ra file `.json` hoặc nạp lại dữ liệu từ file backup.
    * **Chỉnh sửa:** Tìm kiếm, sửa thông tin chi tiết hoặc xóa sự kiện theo ID.

4.  **Báo cáo Test (NLP Dashboard):**
    * Dành cho mục đích kiểm thử.
    * Tải lên file `.csv` trong Folder `tests` chứa các test case để hệ thống tự động chạy và chấm điểm độ chính xác của thuật toán NLP.

---

## VI. Cấu trúc thư mục
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
 ```

---

## VII. Kết quả kiểm thử NLP

Tổng số Test Case: Hơn 100 câu lệnh tiếng Việt đa dạng.

Độ chính xác (Accuracy): Trên 90%.

Khả năng xử lý:

✅ Thời gian tuyệt đối/tương đối (9h sáng, sáng mai, tuần sau).

✅ Nhắc nhở (nhắc trước 30p).

✅ Địa điểm (tại phòng 302, ở rạp CGV).

✅ Loại bỏ từ nối rác (với, của, đi, đến...).