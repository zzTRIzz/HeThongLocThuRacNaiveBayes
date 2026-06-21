import os
import json
import mysql.connector
import streamlit as st
from datetime import datetime
# Gọi trực tiếp các hàm logic chung từ file utils độc lập
from utils import MYSQL_CONFIG, init_db, khoi_tao_tri_thuc_json, predict_online

st.set_page_config(page_title="Trang Chủ - Doanh nghiệp", layout="wide")

# Khởi chạy hạ tầng cơ sở dữ liệu và tri thức AI ban đầu
init_db()
khoi_tao_tri_thuc_json()


def lay_thoi_gian_json():
    return os.path.getmtime('model_knowledge.json') if os.path.exists('model_knowledge.json') else 0


@st.cache_resource
def load_json_knowledge():
    with open('model_knowledge.json', 'r', encoding='utf-8') as f:
        return json.load(f)


# Cơ chế tự động xóa bộ nhớ Cache nếu Admin thực hiện học tăng cường online ở trang kia
if 'last_json_time' not in st.session_state or st.session_state['last_json_time'] != lay_thoi_gian_json():
    st.cache_resource.clear()
    st.session_state['knowledge'] = load_json_knowledge()
    st.session_state['last_json_time'] = lay_thoi_gian_json()

st.title("🏢 LIÊN HỆ")
st.write("Chào mừng quý khách đến với website chính thức của chúng tôi. Hãy để lại lời nhắn nếu cần hỗ trợ!")

with st.form("contact_form", clear_on_submit=True):
    name = st.text_input("Họ và tên:")
    email = st.text_input("Địa chỉ Email:")
    content = st.text_area("Nội dung liên hệ:", height=150)
    submitted = st.form_submit_button("Gửi thông tin")

    if submitted:
        if name.strip() == "" or email.strip() == "" or content.strip() == "":
            st.warning("Vui lòng nhập đầy đủ thông tin!")
        else:
            # Thuật toán lõi thực thi dự đoán từ file utils dùng chung
            label, ps, ph = predict_online(content, st.session_state['knowledge'])

            conn = mysql.connector.connect(**MYSQL_CONFIG)
            c = conn.cursor()
            sql = "INSERT INTO messages (name, email, content, label, spam_pct, ham_pct, time) VALUES (%s,%s,%s,%s,%s,%s,%s)"
            c.execute(sql, (name, email, content, label, ps, ph, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            st.success("Gửi liên hệ thành công! Chúng tôi sẽ phản hồi sớm nhất.")