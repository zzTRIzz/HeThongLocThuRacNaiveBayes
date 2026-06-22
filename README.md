

# 🛡️ AI SPAM SHIELD - Hệ Thống Phân Loại Thư Rác Thông Minh (Naive Bayes)

> **Dự án:** Xây dựng hệ thống phân loại thư rác (Spam Classification) dựa trên giải thuật Naive Bayes cải tiến.
> **Giảng viên hướng dẫn:** GS. Trần Thanh Huân
> **Nhóm 4 - Sinh viên thực hiện:**
> 1. **Nguyễn Quốc Trí - 2025600645** (Trưởng nhóm / Lead)
> 2. Nguyễn Đăng Biển - 2025600492
> 3. Nguyễn Công Ninh - 2025600316
> 
> 

---

## 📊 Thông số & Độ chính xác của Mô hình

Hệ thống đã được huấn luyện và kiểm thử trên tập dữ liệu hỗn hợp (Đa ngôn ngữ), mang lại kết quả đánh giá cực kỳ ấn tượng nhờ các cải tiến thuật toán:

* **Tổng số tin nhắn kiểm tra:** `6304`
* **Số lượng dự đoán chính xác:** `6280`
* **Độ chính xác (Accuracy):** `99.62%`

 🌐 [Link hình ảnh giao diện sản phẩm](https://github.com/zzTRIzz/HeThongLocThuRacNaiveBayes/tree/main/H%C3%ACnh%20%E1%BA%A3nh%20giao%20di%E1%BB%87n)
---



## 📁 Chi tiết Tập dữ liệu (Dataset)

Để đảm bảo AI có khả năng nhận diện tốt các kịch bản lừa đảo thực tế tại Việt Nam lẫn quốc tế, tập dữ liệu (`sms_spam.csv`) chứa **6304** mẫu đã được nhóm tinh chỉnh và tổng hợp từ nhiều nguồn:

* **1.000 mẫu Spam Tiếng Việt:** Thu thập từ các kịch bản lừa đảo SMS, tin nhắn rác trúng thưởng, mạo danh ngân hàng thực tế tại Việt Nam.
* **1.000 mẫu Ham Tiếng Việt:** Các tin nhắn giao tiếp, trao đổi công việc, thông báo hợp lệ hàng ngày để làm mẫu tin sạch.
* **150 mẫu Spam cải tiến (Tùy biến):** Các mẫu rác do nhóm tự tinh chỉnh, chứa các thủ đoạn lách luật mới nhất (teencode, chèn icon, viết lóng, spam ký tự) để ép AI học cách chống lại các "Zero-day Spam".
* **Phần còn lại (hơn 4.000 mẫu):** Tập dữ liệu tin nhắn SMS quốc tế (Tiếng Anh) được tổng hợp từ các kho dữ liệu mở trên Internet, giúp mô hình đa dạng hóa vốn từ và mở rộng khả năng lọc thư rác đa ngôn ngữ.

---

## 🧠 Phân tích sâu: Sức mạnh của N-gram (Bigram) & Bộ não `model_knowledge.json`

Thuật toán Naive Bayes nguyên thủy có một điểm yếu chí mạng gọi là giả định **"Ngây thơ" (Naive)** – nó coi mọi từ trong câu là độc lập hoàn toàn với nhau. Điều này khiến AI dễ bị mù ngữ cảnh khi các từ đơn lẻ mang nghĩa sạch nhưng khi ghép lại thì là lừa đảo (ví dụ: chữ `"chuyển"` và chữ `"khoản"`, chữ `"trúng"` và chữ `"thưởng"`).

Để khắc phục, dự án đã can thiệp bằng cách thiết kế cơ chế **N-gram với cấu hình $n=2$ (Bigram)** chạy bằng Python thuần:

* **Bảo toàn ngữ cảnh:** Trong bước tiền xử lý, các từ đứng cạnh nhau sẽ được hệ thống tự động nối lại bằng dấu gạch dưới (VD: `chuyển_khoản`, `trúng_thưởng`, `nhận_tiền`).
* **Sự tiến hóa của `model_knowledge.json`:** Nhờ cơ chế này, "bộ não AI" (file `model_knowledge.json`) không chỉ lưu trữ tần suất của các từ đơn lẻ mà còn mở rộng tập từ vựng (`vocab`) để chứa hàng ngàn cụm từ ghép ngữ cảnh.
* **Tác động đến dự đoán:** Khi tra cứu điểm xác suất, hệ thống sẽ chấm điểm cả cụm từ `[chuyển_khoản]` thay vì chỉ chấm `[chuyển]` và `[khoản]` rời rạc. Điều này giúp mô hình bắt trọn vẹn các đặc trưng ngôn ngữ lừa đảo của tiếng Việt, giảm thiểu tối đa hiện tượng bắt nhầm tin nhắn sạch.

---

## 🌟 Nổi bật: Các Cải tiến Đột phá so với Naive Bayes gốc

Bên cạnh N-gram, dự án còn tích hợp **5 cải tiến kỹ thuật cốt lõi** khác để tối ưu hóa độ chính xác:

1. **Chống tràn số thực (Log-Sum-Exp Trick):** Thay vì nhân các xác suất lại với nhau (gây lỗi *Floating-point Underflow* làm sập hệ thống khi tin nhắn dài), mô hình sử dụng hàm Logarit (`math.log`) để chuyển phép nhân thành phép cộng. Cuối cùng, dùng kỹ thuật Log-Sum-Exp (`max_l`) để giải mã ra tỷ lệ phần trăm chính xác tuyệt đối.
2. **Làm mịn Laplace (Laplace Smoothing):** Triệt tiêu hoàn toàn lỗi "Xác suất bằng 0" khi người dùng nhập từ mới tinh (Out-of-Vocabulary) chưa từng có trong tập dữ liệu.
3. **Cơ chế Học tăng cường động (Heuristic Online Learning):** Đây là "vũ khí bí mật" của hệ thống. Thay vì đếm `+1` cực kỳ chậm chạp như thuật toán gốc, khi Admin báo cáo sai sót, hệ thống lập tức **chém đứt 50% điểm định kiến** của phe đoán sai và **bơm một lượng điểm mồi khổng lồ (tối thiểu 40, lên tới +50)** vào phe đúng. Giúp AI "quay xe" đoán đúng kịch bản lừa đảo mới chỉ trong 1 giây mà không cần tắt Server huấn luyện lại.
4. **Quy chuẩn hóa đặc trưng (Feature Normalization):** Tự động quy đổi các đường link lạ thành `token_url` và các con số thành `token_so`. Giúp AI không bị "học vẹt" mà nhận diện được bản chất "hành vi" lừa đảo (thường chứa nhiều link lạ và số tiền).
5. **Bộ lọc kết hợp Hybrid (Quy tắc cứng + AI):** Tích hợp kiểm tra Database Blacklist và thuật toán bẫy "gõ phím vô nghĩa" (kiểm tra tỷ lệ phụ âm, độ dài từ) để chặn đứng Spam ở vòng gửi xe trước khi đưa vào AI phân tích chuyên sâu.

---

## 📁 Cấu trúc Dự án

* `utils.py`: File chứa toàn bộ "linh hồn" của hệ thống (Kết nối DB, tiền xử lý NLP, thuật toán Naive Bayes, thuật toán Học tăng cường).
* `Lien_He.py`: Giao diện người dùng (Client) - Nơi khách hàng gửi tin nhắn.
* `Quan_Ly_Admin.py`: Giao diện Quản trị viên (Admin) - Nơi kiểm duyệt thư, biểu đồ thống kê, Sandbox thử nghiệm và sửa sai cho AI.
* `danh_gia.py`: Script dùng để chấm điểm độ chính xác của mô hình dựa trên tập dữ liệu.
* `sms_spam.csv`: Tập dữ liệu thô (Dataset) dùng để AI học lần đầu.
* `model_knowledge.json`: "Bộ não" tĩnh của AI, được hệ thống tự động sinh ra và cập nhật Real-time.

---

## ⚙️ Hướng dẫn Cài đặt & Vận hành

### Bước 1: Cài đặt Database (MySQL)

1. Hãy chắc chắn máy tính của bạn đã cài đặt MySQL (có thể dùng XAMPP, WAMP, hoặc MySQL Workbench).
2. Khởi động MySQL Server.
3. Không cần tự tạo Database, hệ thống sẽ tự động khởi tạo khi chạy code, bạn chỉ cần đảm bảo thông tin đăng nhập trong file `utils.py` khớp với máy bạn:
* **User:** `root`
* **Password:** `12345` *(Hãy sửa lại dòng 10 trong utils.py nếu mật khẩu máy bạn khác)*



### Bước 2: Cài đặt Thư viện Python

Mở Terminal / Command Prompt tại thư mục chứa dự án và chạy câu lệnh sau:

```bash
pip install pandas streamlit mysql-connector-python

```

### Bước 3: Khởi chạy Hệ thống

**1. Khởi chạy Giao diện Người dùng (Trang Liên hệ):**
Lần chạy đầu tiên, hệ thống sẽ tự động đọc file `sms_spam.csv` để tạo ra bộ não `model_knowledge.json` và thiết lập các bảng trong Database.

```bash
streamlit run Lien_He.py

```

**2. Khởi chạy Giao diện Quản trị viên (Trang Admin):**
Mở một tab Terminal mới và chạy:

```bash
streamlit run Quan_Ly_Admin.py

```

**3. Kiểm tra Độ chính xác của Mô hình:**
Chạy file python thuần này để in ra kết quả accuracy 99.62%:

```bash
python danh_gia.py

```

---

## 🔐 Thông tin Quản trị viên (Admin)

Khi truy cập vào trang `Quan_Ly_Admin.py`, hệ thống sẽ yêu cầu khóa bảo mật.

* **Mật khẩu Admin:** `admin123`

*Lưu ý: có thể thay đổi mật khẩu này tại dòng số 31 trong file `Quan_Ly_Admin.py`.*