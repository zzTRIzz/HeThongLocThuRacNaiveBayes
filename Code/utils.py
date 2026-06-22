import math
import re
import os
import json
import pandas as pd
import mysql.connector

# Cấu hình kết nối MySQL dùng chung cho toàn hệ thống
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '12345',
    "database": "loc_thu_rac"
}


def init_db():
    try:
        config_tho = MYSQL_CONFIG.copy()
        db_name = config_tho.pop("database")
        conn_tho = mysql.connector.connect(**config_tho)
        c_tho = conn_tho.cursor()
        c_tho.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn_tho.commit()
        c_tho.close()
        conn_tho.close()

        conn = mysql.connector.connect(**MYSQL_CONFIG)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INT AUTO_INCREMENT PRIMARY KEY, 
                        name VARCHAR(255), 
                        email VARCHAR(255), 
                        content TEXT, 
                        label VARCHAR(50), 
                        spam_pct DOUBLE, 
                        ham_pct DOUBLE, 
                        time DATETIME
                     )''')
        c.execute('''CREATE TABLE IF NOT EXISTS blacklist_keywords (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        keyword VARCHAR(255) UNIQUE NOT NULL,
                        created_at DATETIME
                     )''')
        conn.commit()
        c.close()
        conn.close()
    except mysql.connector.Error as err:
        pass


def kiem_tra_blacklist_mysql(text):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        c = conn.cursor()
        c.execute("SELECT keyword FROM blacklist_keywords")
        keywords = [row[0].strip().lower() for row in c.fetchall()]
        conn.close()
        text_lower = text.lower()
        for kw in keywords:
            if kw and kw in text_lower: return True
        return False
    except:
        return False


def chuan_hoa_thong_minh(text):
    if not isinstance(text, str): return ""
    # Chỉ thu gọn nếu ký tự đó xuất hiện liên tiếp từ 3 lần trở lên
    # Ví dụ: darlingggg (4 chữ g) -> darling, nhưng good (2 chữ o) -> giữ nguyên good
    text = re.sub(r'(.)\1{2,}', r'\1', text)
    return text


def kiem_tra_tu_vo_nghia(text):
    if not isinstance(text, str) or text.strip() == "":
        return False

    # Thực hiện chuẩn hóa co chữ kéo dài trước khi quét bẫy nhiễu
    text_chuan_hoa = chuan_hoa_thong_minh(text.lower())

    # Loại bỏ link/email trước khi test vô nghĩa để tránh bắt nhầm URL dài
    clean_text = re.sub(r'https?://\S+|www\.\S+|\S+@\S+', '', text_chuan_hoa)
    words = clean_text.split()
    if not words:
        return False

    so_tu_vo_nghia = 0

    for w in words:
        if len(w) <= 2:
            continue

        # 🌟 BẪY 1: Từ quá dài (Chuỗi ký tự dính liền không ngắt nghỉ)
        if len(w) > 15:
            so_tu_vo_nghia += 1
            continue

        # 🌟 BẪY 2: Spam phím vật lý theo chuỗi liên tiếp sát cạnh nhau trên bàn phím
        if re.search(r'asdf|jkl;|qwer|zxcv|qazw|edcr|rfvt|ghjk', w):
            so_tu_vo_nghia += 1
            continue

        # 🌟 BẪY 3: Lặp ký tự đặc biệt lặp phá hoại sâu luồng dữ liệu
        if re.search(r'(.)\1{3,}', w):
            so_tu_vo_nghia += 1
            continue

        # 🌟 BẪY 4: Từ rác không có nguyên âm (Chỉ toàn phụ âm đứng cạnh nhau từ 5 chữ trở lên)
        if len(w) >= 5 and not re.search(r'[aeiouyàáảãạăằắẳẵặâấầẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ]',
                                         w):
            so_tu_vo_nghia += 1
            continue

        # 🌟 BẪY 5: Tỷ lệ phụ âm quá dày đặc trong một từ đơn dài (Đã nới lỏng để bảo vệ từ tiếng Việt)
        phu_am = re.findall(r'[bcdfghjklmnpqrstvwxyzđ]', w)
        if len(phu_am) / len(w) > 0.85 and len(w) >= 7:
            so_tu_vo_nghia += 1
            continue

    # 🌟 BẪY TỔNG: Nếu tỉ lệ từ rác vượt quá ngưỡng 40% câu
    ty_le_rac = so_tu_vo_nghia / len(words)

    # Nếu câu ban đầu có chữ nhưng sau khi xóa ký tự đặc biệt/icon chỉ còn chuỗi trống rỗng -> Đích thị là spam icon
    text_chi_chu_va_so = re.sub(r'[^a-zA-Z0-9áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ\s]',
                                '', text_chuan_hoa).strip()
    if text_chi_chu_va_so == "":
        return True

    return ty_le_rac > 0.40


def tien_xu_ly(text, n_gram=2):
    if not isinstance(text, str): return []

    # Thực hiện chuẩn hóa co chữ kéo dài đầu luồng NLP
    text = chuan_hoa_thong_minh(text.lower())

    # Quy chuẩn hóa cấu trúc Link và Số biến động
    if "noibo-congty.com" in text or "ghn-tracking.vn" in text:
        text = re.sub(r'https?://\S+|www\.\S+', ' token_link_tin_cay ', text)
    else:
        text = re.sub(r'https?://\S+|www\.\S+', ' token_url ', text)

    text = re.sub(r'\b\d+[\d.,:]*\b', ' token_so ', text)

    # kửưký tự lách chữ gian lận
    text = re.sub(r'\bsh0p\b', 'shop', text)
    text = re.sub(r'¡', 'i', text)
    text = re.sub(r'¢', 'c', text)
    text = re.sub(r'£', 'l', text)

    # Loại bỏ các ký tự đặc biệt
    text = re.sub(r'[^a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđ0-9\s]', ' ', text)
    words = text.split()

    # Tập hợp Stopwords mở rộng toàn diện (Có dấu + Không dấu)
    stopwords = {
        'thì', 'thi', 'mà', 'ma', 'là', 'la', 'và', 'va', 'của', 'cua',
        'những', 'nhung', 'cái', 'cai', 'lên', 'len', 'vào', 'vao', 'để', 'de',
        'với', 'voi', 'đây', 'day', 'đang', 'dang', 'này', 'nay', 'làm', 'lam',
        'cho', 'được', 'duoc', 'từ', 'tu', 'ra', 'bởi', 'boi', 'tại', 'tai',
        'trong', 'ngoài', 'ngoai', 'như', 'nhu', 'hoặc', 'hoac', 'nhưng', 'bằng', 'bang',
        'tuy', 'cho nên', 'cho nen', 'vì', 'vi', 'do', 'đến', 'den', 'theo',
        'chúng', 'chung', 'tôi', 'toi', 'anh', 'em', 'bạn', 'ban', 'nó', 'no',
        'họ', 'ho', 'ta', 'mình', 'minh', 'ông', 'ong', 'bà', 'ba', 'cô', 'co',
        'chú', 'chu', 'bác', 'bac', 'người', 'nguoi', 'ai', 'gì', 'gi', 'nào', 'nao',
        'đã', 'da', 'sẽ', 'se', 'rồi', 'roi', 'cũng', 'cung', 'chỉ', 'chi',
        'quá', 'qua', 'lắm', 'lam', 'rất', 'rat', 'hơi', 'hoi', 'luôn', 'luon',
        'ngay', 'từng', 'tung', 'cứ', 'cu', 'đều', 'deu', 'tự', 'vừa', 'vua',
        'mới', 'moi', 'nữa', 'nua', 'xong', 'nhé', 'nhe', 'nha', 'ạ', 'a', 'ơi', 'oi',
        'đi', 'di', 'thôi', 'thoi', 'vậy', 'vay', 'chứ', 'chu', 'sao', 'đâu', 'dau', 'nhỉ', 'nhi',
        'các', 'cac', 'mọi', 'moi', 'mỗi', 'moi', 'tất cả', 'tat ca', 'hết', 'het',
        'nhiều', 'nhieu', 'ít', 'it', 'vài', 'vai', 'mấy', 'may',
        'the', 'to', 'is', 'and', 'a', 'an', 'of', 'for', 'in', 'on', 'at', 'by',
        'this', 'that', 'with', 'you', 'me', 'my', 'it', 'we', 'us'
    }
    words = [word for word in words if word not in stopwords]

    features = list(words)
    if n_gram >= 2 and len(words) >= 2:
        for i in range(len(words) - 1):
            features.append(f"{words[i]}_{words[i + 1]}")
    return features


def khoi_tao_tri_thuc_json():
    if not os.path.exists('model_knowledge.json'):
        try:
            df = pd.read_csv('sms_spam.csv', encoding='utf-8').iloc[:, [0, 1]]
        except:
            df = pd.read_csv('sms_spam.csv', encoding='latin1', on_bad_lines='skip').iloc[:, [0, 1]]
        df.columns = ['label', 'text']

        word_counts = {'spam': {}, 'ham': {}}
        class_counts = {'spam': 0, 'ham': 0}

        for row in df.itertuples(index=False):
            # DÒNG NÀY LÀM GÌ: Chạy vòng lặp quét qua từng dòng một của bảng dữ liệu CSV.
            # Cấu hình 'index=False' để loại bỏ số thứ tự dòng mặc định của Pandas, giúp vòng lặp chạy nhẹ hơn.

            label, text = row[0], str(row[1])
            # DÒNG NÀY LÀM GÌ: Rút dữ liệu của dòng hiện tại ra gán vào biến: nhãn nằm ở cột 0 gán vào 'label',
            # nội dung câu ở cột 1 ép sang kiểu chuỗi chữ gán vào 'text'.

            words = tien_xu_ly(text, n_gram=2)
            # DÒNG NÀY LÀM GÌ: Ném nội dung câu văn thô vào hàm sơ chế 'tien_xu_ly' để gọt rác, gom link/số, loại bỏ từ thừa.
            # Kết quả trả về là mảng 'words' chứa danh sách các từ đơn và cụm từ ghép (Bigram) sạch sẽ.

            class_counts[label] += 1
            # DÒNG NÀY LÀM GÌ: Cứ đọc được một tin nhắn thuộc phe nào (label là gì) thì cộng thêm 1 điểm vào tổng số lượng tin nhắn của phe đó.

            for w in words:
                # DÒNG NÀY LÀM GÌ: Chạy vòng lặp duyệt qua từng từ/cụm từ 'w' vừa bóc tách được từ tin nhắn hiện tại.

                word_counts[label][w] = word_counts[label].get(w, 0) + 1
                # DÒNG NÀY LÀM GÌ: Cập nhật sổ đếm chữ: Tìm từ 'w' trong danh mục của phe đó.
                # Lệnh '.get(w, 0)' nghĩa là nếu từ này mới tinh chưa từng gặp, cho nó giá trị khởi đầu bằng 0, sau đó cộng thêm 1.
                # Nếu từ đã có sẵn trong sổ rồi thì chỉ việc lấy số lần cũ cộng dồn thêm 1.

            # =====================================================================
            # 📦 BƯỚC 5: ĐÓNG GÓI TRI THỨC VÀ GHI VÀO FILE Ổ CỨNG
            # =====================================================================

        knowledge = {
            'word_counts': word_counts,  # Nhét bảng đếm tần suất của các từ vào gói tổng hợp 'knowledge'.
            'class_counts': class_counts,  # Nhét tổng số lượng tin nhắn rác/sạch vào gói tổng hợp.
            'vocab': list(set(list(word_counts['spam'].keys()) + list(word_counts['ham'].keys())))
            # DÒNG NÀY LÀM GÌ: Tạo danh sách từ vựng tổng thể duy nhất (|V|). Nó gộp tất cả các từ của phe 'spam' và phe 'ham' lại,
            # ném qua hàm 'set()' để tự động lọc bỏ các từ bị trùng lặp, rồi chuyển ngược về kiểu mảng 'list()' để lưu trữ.
        }

        with open('model_knowledge.json', 'w', encoding='utf-8') as f:
            # DÒNG NÀY LÀM GÌ: Mở file 'model_knowledge.json' ở chế độ ghi mới ('w'), ép cấu hình định dạng font chữ tiếng Việt 'utf-8',
            # và đặt tên đại diện cho file đang mở này là biến 'f'.

            json.dump(knowledge, f, ensure_ascii=False, indent=4)
            # DÒNG NÀY LÀM GÌ: Sử dụng thư viện JSON để chuyển toàn bộ từ điển tri thức 'knowledge' thành định dạng văn bản,
            # rồi đổ trực tiếp vào file 'f' trên ổ cứng. Cấu hình 'ensure_ascii=False' giúp giữ nguyên dấu tiếng Việt không bị lỗi hiển thị,
            # và 'indent=4' để tự động lùi đầu dòng các khối dữ liệu 4 khoảng trắng cho đẹp mắt, dễ đọc.


def predict_online(text, knowledge):
    if kiem_tra_blacklist_mysql(text): return 'spam', 100.0, 0.0
    # Nếu dính từ cấm, lập tức TRẢ VỀ kết quả phán quyết là 'spam', tỷ lệ rác 100%, tỷ lệ sạch 0% và THOÁT HÀM LUÔN.
    if kiem_tra_tu_vo_nghia(text): return 'spam', 100.0, 0.0

    words = tien_xu_ly(text, n_gram=2)
    # DÒNG NÀY LÀM GÌ: Ném tin nhắn mới vào hàm 'tien_xu_ly' để dọn rác, lọc từ thừa, đổi link thành 'token_url', đổi số thành 'token_so'.
    # Kết quả trả về gán vào biến 'words' - một mảng chứa các từ đơn và cụm từ ghép (Bigram) sạch sẽ.

    word_counts = knowledge['word_counts']
    # DÒNG NÀY LÀM GÌ: Truy cập vào bộ não JSON, lấy ra bảng đếm tần suất xuất hiện của các từ trong lịch sử gán vào biến 'word_counts'.

    class_counts = knowledge['class_counts']
    # DÒNG NÀY LÀM GÌ: Lấy ra tổng số lượng tin nhắn rác (spam) và sạch (ham) hệ thống đã từng học trong quá khứ gán vào biến 'class_counts'.

    vocab_size = len(knowledge['vocab'])
    # DÒNG NÀY LÀM GÌ: Đếm xem tổng cộng AI đang sở hữu bao nhiêu từ vựng KHÁC NHAU trong đầu (Ký hiệu toán học là |V|).

    total_docs = sum(class_counts.values())
    # DÒNG NÀY LÀM GÌ: Tính tổng tất cả tin nhắn đã từng học trong lịch sử bằng cách lấy (số tin nhắn spam + số tin nhắn ham).


    log_prob = {}

    # Chạy vòng lặp duyệt qua 2 nhãn. Lượt 1 tính điểm cho 'spam', lượt 2 tính điểm cho 'ham'.
    for label in ['spam', 'ham']:
        log_prob[label] = math.log(class_counts[label] / total_docs)
        # DÒNG NÀY LÀM GÌ: Áp dụng CÔNG THỨC LÀM MỊN LAPLACE SMOOTHING để tính xác suất xuất hiện của từ 'w'.
        # - Tử số: Tìm xem từ 'w' xuất hiện bao nhiêu lần trong phe này (nếu từ mới tinh thì cho bằng 0) rồi cộng thêm 1 bảo hiểm (+1).
        # - Mẫu số: Lấy (Tổng số chữ của riêng phe này + Tổng kích thước từ vựng hệ thống vocab_size).

        total_words = sum(word_counts[label].values())
        # DÒNG NÀY LÀM GÌ: Thay vì nhân các xác suất 'prob' với nhau (gây lỗi sập phần cứng do số quá nhỏ),
        # ta lấy Logarit tự nhiên của 'prob' (ra số âm) rồi CỘNG DỒN vào quỹ điểm tổng của phe đó.

        for w in words:
            prob = (word_counts[label].get(w, 0) + 1) / (total_words + vocab_size)
            log_prob[label] += math.log(prob)

    max_l = max(log_prob.values())
    # DÒNG NÀY LÀM GÌ: Tìm ra số điểm logarit lớn nhất giữa 2 bên (vì là số âm nên số nào gần mốc 0 nhất là lớn nhất).

    ps = math.exp(log_prob['spam'] - max_l)
    # DÒNG NÀY LÀM GÌ: Lấy điểm Spam trừ đi số lớn nhất 'max_l' để kéo điểm âm khổng lồ về sát mốc 0.
    # Sau đó dùng hàm số mũ math.exp() để giải mã ngược từ điểm Logarit về lại số dương thông thường (giá trị ps).

    ph = math.exp(log_prob['ham'] - max_l)
    # DÒNG NÀY LÀM GÌ: Làm tương tự như trên với phe Ham để giải mã ra giá trị số dương đại diện cho phe Ham (giá trị ph).

    return ('spam' if ps > ph else 'ham'), (ps / (ps + ph) * 100), (ph / (ps + ph) * 100)
    # DÒNG NÀY LÀM GÌ: Trả về đồng thời 3 kết quả phân loại:
    # 1. So sánh nếu ps lớn hơn ph thì phán câu này là 'spam', ngược lại là 'ham'.
    # 2. Tính tỷ lệ phần trăm % của phe Spam bằng công thức chia tỷ trọng: ps / (ps + ph) * 100.
    # 3. Tính tỷ lệ phần trăm % của phe Ham bằng công thức chia tỷ trọng: ph / (ps + ph) * 100.


def thuc_hien_hoc_tang_cuong_online(msg_id, noi_dung, nhan_moi):
    import time
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    # DÒNG NÀY LÀM GÌ: Sử dụng cấu hình chung để thiết lập kết nối đến cơ sở dữ liệu MySQL.

    c = conn.cursor()
    # DÒNG NÀY LÀM GÌ: Tạo một con trỏ (cursor) giúp hệ thống có thể thực thi các câu lệnh SQL xuống Database.
    if nhan_moi == 'spam':
        c.execute("UPDATE messages SET label='spam', spam_pct=100.0, ham_pct=0.0 WHERE id=%s", (msg_id,))
    else:
        c.execute("UPDATE messages SET label='ham', spam_pct=0.0, ham_pct=100.0 WHERE id=%s", (msg_id,))
    conn.commit()
    conn.close()

    if os.path.exists('model_knowledge.json'):
        # Cơ chế phòng vệ Spinlock chống xung đột tệp tin JSON khi lưu
        for _ in range(5):
            # DÒNG NÀY LÀM GÌ: Tạo một vòng lặp chạy tối đa 5 lần. Đây là cơ chế phòng vệ Spinlock để thử lại nếu file JSON đang bị bận.
            try:
                with open('model_knowledge.json', 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                    # DÒNG NÀY LÀM GÌ: Dùng thư viện JSON nạp toàn bộ dữ liệu thống kê từ file 'f' vào bộ nhớ RAM dưới dạng từ điển 'knowledge'.
                break
            except:
                time.sleep(0.05)

        words = tien_xu_ly(noi_dung, n_gram=2)
        # DÒNG NÀY LÀM GÌ: Ném nội dung câu văn bị đoán sai vào hàm sơ chế 'tien_xu_ly' để lấy ra danh sách từ đơn và từ ghép Bigram sạch sẽ.
        nhan_cu = 'ham' if nhan_moi == 'spam' else 'spam'

        for w in words:

            # 🌟 THUẬT TOÁN CÂN BẰNG ĐỘNG: Đọc định kiến lịch sử của từ ở phe cũ
            diem_phe_cu = knowledge['word_counts'][nhan_cu].get(w, 0)
            # DÒNG NÀY LÀM GÌ: Tra cứu xem từ khóa 'w' này đang sở hữu sẵn bao nhiêu điểm định kiến ở bên phe bị đoán sai trong bộ não JSON.
            # Lệnh '.get(w, 0)' nghĩa là nếu từ này mới tinh chưa từng học, mặc định lấy giá trị bằng 0.


            # Tính toán lượng điểm mồi: Đảm bảo phe mới luôn đè bẹp phe cũ tối thiểu 50 điểm
            diem_muon_bom = max(40, diem_phe_cu + 50)
            # DÒNG NÀY LÀM GÌ: CÔNG THỨC ĐIỂM MỒI: Tính toán lượng điểm thưởng nạp vào phe đúng phải lớn hơn phe cũ ít nhất 50 điểm.
            # Hàm 'max(40, ...)' là chốt chặn bảo hiểm, đảm bảo lượng điểm thưởng bơm vào luôn đạt tối thiểu là 40 điểm để không bị loãng.

            # Bơm mạnh trọng số cho phe mới để AI quay xe ngay lập tức ở lượt test sau
            knowledge['word_counts'][nhan_moi][w] = knowledge['word_counts'][nhan_moi].get(w, 0) + diem_muon_bom
            # DÒNG NÀY LÀM GÌ: Lấy số điểm hiện tại của từ 'w' ở phe đúng (nhan_moi), cộng thêm lượng điểm mồi khổng lồ vừa tính để bơm sức mạnh.

            # Triệt tiêu mạnh 50% sức mạnh định kiến cũ của phe đoán sai
            knowledge['word_counts'][nhan_cu][w] = max(0, int(diem_phe_cu * 0.5))
            # DÒNG NÀY LÀM GÌ: CÔNG THỨC PHẠT: Ép phạt phe sai bằng cách chém bay 50% số điểm định kiến cũ (nhân với 0.5 và ép về kiểu số nguyên int).
            # Hàm 'max(0, ...)' làm nhiệm vụ bảo hiểm, giữ cho điểm số của từ khóa không bao giờ bị âm.

            if w not in knowledge['vocab']:
                knowledge['vocab'].append(w)

        # Cân bằng lại xác suất tiên nghiệm lớp P(Class) để triệt tiêu độ lệch dữ liệu tĩnh
        knowledge['class_counts'][nhan_moi] += 5

        with open('model_knowledge.json', 'w', encoding='utf-8') as f:
            # DÒNG NÀY LÀM GÌ: Mở lại file 'model_knowledge.json' ở chế độ ghi đè mới ('w'), hỗ trợ font chữ tiếng Việt 'utf-8', đại diện là biến 'f'.

            json.dump(knowledge, f, ensure_ascii=False, indent=4)
            # DÒNG NÀY LÀM GÌ: Chuyển toàn bộ dữ liệu bộ não 'knowledge' đã thông minh hơn sau khi cập nhật thành định dạng văn bản JSON,
            # ghi đè trực tiếp xuống ổ cứng file 'f'. Giữ nguyên dấu tiếng Việt ('ensure_ascii=False') và lùi dòng 4 khoảng trắng cho đẹp ('indent=4').