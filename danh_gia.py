import json
import math
import pandas as pd

# Nhập lại các hàm xử lý ngôn ngữ từ file utils của bạn
from utils import tien_xu_ly, kiem_tra_tu_vo_nghia

print("Đang tiến hành đọc dữ liệu và chấm bài (Sẽ mất vài giây)...")

# 1. Tải trí thức AI đã học từ file JSON
with open('model_knowledge.json', 'r', encoding='utf-8') as f:
    knowledge = json.load(f)

word_counts = knowledge['word_counts']
class_counts = knowledge['class_counts']
vocab_size = len(knowledge['vocab'])
total_docs_trained = sum(class_counts.values())

# 2. Đọc file dữ liệu gốc
try:
    df = pd.read_csv('sms_spam.csv', encoding='utf-8').iloc[:, [0, 1]]
except:
    df = pd.read_csv('sms_spam.csv', encoding='latin1', on_bad_lines='skip').iloc[:, [0, 1]]
df.columns = ['label', 'text']

correct = 0
total_docs = len(df)

# 3. Vòng lặp chấm điểm
for index, row in df.iterrows():
    true_label = row['label']
    text = str(row['text'])

    # Bỏ qua bước kiểm tra Blacklist MySQL để tránh mở/đóng Database 5000 lần gây treo máy
    # Chỉ kiểm tra bẫy từ vô nghĩa và Toán học Naive Bayes
    if kiem_tra_tu_vo_nghia(text):
        pred_label = 'spam'
    else:
        words = tien_xu_ly(text, n_gram=2)
        log_prob = {}
        for label in ['spam', 'ham']:
            log_prob[label] = math.log(class_counts[label] / total_docs_trained)
            total_words = sum(word_counts[label].values())
            for w in words:
                prob = (word_counts[label].get(w, 0) + 1) / (total_words + vocab_size)
                log_prob[label] += math.log(prob)

        # Chốt kết quả
        pred_label = 'spam' if log_prob['spam'] > log_prob['ham'] else 'ham'

    # Đối chiếu
    if pred_label == true_label:
        correct += 1

# 4. In kết quả đúng 3 dòng bạn cần
accuracy = 100 * correct / total_docs if total_docs > 0 else 0

print("\n" + "-" * 50)
print(f"Tổng số tin nhắn kiểm tra : {total_docs}")
print(f"Số lượng dự đoán chính xác: {correct}")
print(f"Độ chính xác (Accuracy)   : {accuracy:.2f}%")