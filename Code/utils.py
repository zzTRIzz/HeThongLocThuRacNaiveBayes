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

    # Khử ký tự lách chữ gian lận
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
            label, text = row[0], str(row[1])
            words = tien_xu_ly(text, n_gram=2)
            class_counts[label] += 1
            for w in words:
                word_counts[label][w] = word_counts[label].get(w, 0) + 1

        knowledge = {
            'word_counts': word_counts,
            'class_counts': class_counts,
            'vocab': list(set(list(word_counts['spam'].keys()) + list(word_counts['ham'].keys())))
        }
        with open('model_knowledge.json', 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=4)


def predict_online(text, knowledge):
    if kiem_tra_blacklist_mysql(text): return 'spam', 100.0, 0.0
    if kiem_tra_tu_vo_nghia(text): return 'spam', 100.0, 0.0

    words = tien_xu_ly(text, n_gram=2)
    word_counts = knowledge['word_counts']
    class_counts = knowledge['class_counts']
    vocab_size = len(knowledge['vocab'])
    total_docs = sum(class_counts.values())

    log_prob = {}
    for label in ['spam', 'ham']:
        log_prob[label] = math.log(class_counts[label] / total_docs)
        total_words = sum(word_counts[label].values())
        for w in words:
            prob = (word_counts[label].get(w, 0) + 1) / (total_words + vocab_size)
            log_prob[label] += math.log(prob)

    max_l = max(log_prob.values())
    ps = math.exp(log_prob['spam'] - max_l)
    ph = math.exp(log_prob['ham'] - max_l)
    return ('spam' if ps > ph else 'ham'), (ps / (ps + ph) * 100), (ph / (ps + ph) * 100)


# =====================================================================
# 🚀 THUẬT TOÁN CÂN BẰNG ĐỘNG (MỘT PHÁT ĐỔI Ý LUÔN) DÙNG CHUNG CHO ADMIN
# =====================================================================
def thuc_hien_hoc_tang_cuong_online(msg_id, noi_dung, nhan_moi):
    import time
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    c = conn.cursor()
    if nhan_moi == 'spam':
        c.execute("UPDATE messages SET label='spam', spam_pct=100.0, ham_pct=0.0 WHERE id=%s", (msg_id,))
    else:
        c.execute("UPDATE messages SET label='ham', spam_pct=0.0, ham_pct=100.0 WHERE id=%s", (msg_id,))
    conn.commit()
    conn.close()

    if os.path.exists('model_knowledge.json'):
        # Cơ chế phòng vệ Spinlock chống xung đột tệp tin JSON khi lưu
        for _ in range(5):
            try:
                with open('model_knowledge.json', 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                break
            except:
                time.sleep(0.05)

        words = tien_xu_ly(noi_dung, n_gram=2)
        nhan_cu = 'ham' if nhan_moi == 'spam' else 'spam'

        for w in words:
            # 🌟 THUẬT TOÁN CÂN BẰNG ĐỘNG: Đọc định kiến lịch sử của từ ở phe cũ
            diem_phe_cu = knowledge['word_counts'][nhan_cu].get(w, 0)

            # Tính toán lượng điểm mồi: Đảm bảo phe mới luôn đè bẹp phe cũ tối thiểu 50 điểm
            diem_muon_bom = max(40, diem_phe_cu + 50)

            # Bơm mạnh trọng số cho phe mới để AI quay xe ngay lập tức ở lượt test sau
            knowledge['word_counts'][nhan_moi][w] = knowledge['word_counts'][nhan_moi].get(w, 0) + diem_muon_bom

            # Triệt tiêu mạnh 50% sức mạnh định kiến cũ của phe đoán sai
            knowledge['word_counts'][nhan_cu][w] = max(0, int(diem_phe_cu * 0.5))

            if w not in knowledge['vocab']:
                knowledge['vocab'].append(w)

        # Cân bằng lại xác suất tiên nghiệm lớp P(Class) để triệt tiêu độ lệch dữ liệu tĩnh
        knowledge['class_counts'][nhan_moi] += 5

        with open('model_knowledge.json', 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=4)