import mysql.connector
import pandas as pd
import streamlit as st
import json
import os
import time
from datetime import datetime
# Gọi trực tiếp các hàm logic chung từ file utils dùng chung
from utils import MYSQL_CONFIG, predict_online, tien_xu_ly

st.set_page_config(page_title="AI Spam Shield - Control Center", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #E5E7EB; padding: 1.2rem 1.5rem; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    button[data-baseweb="tab"] { font-size: 16px !important; font-weight: 600 !important; padding: 12px 24px !important; }
    .premium-card-ham { background: #F8FAFC; border: 1px solid #E2E8F0; border-left: 5px solid #10B981; padding: 1.2rem; border-radius: 12px; margin-bottom: 0.5rem; }
    .premium-card-spam { background: #FFF5F5; border: 1px solid #FED7D7; border-left: 5px solid #EF4444; padding: 1.2rem; border-radius: 12px; margin-bottom: 0.5rem; }
    </style>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if not st.session_state['authenticated']:
    _, col_center, _ = st.columns([1, 1.2, 1])
    with col_center:
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔒 AI SPAM SHIELD</h2>", unsafe_allow_html=True)
            mat_khau = st.text_input("Khóa bảo mật hệ thống:", type="password", placeholder="••••••••")
            if st.button("Đăng nhập hệ thống", use_container_width=True, type="primary"):
                if mat_khau == "admin123":
                    st.session_state['authenticated'] = True;
                    st.rerun()
                else:
                    st.error("Khóa bảo mật không chính xác.")
    st.stop()

st.sidebar.markdown(
    "<div style='text-align: center; padding: 10px; background-color: #F3F4F6; border-radius: 12px; margin-bottom: 20px;'>👨‍💼 <h4>Administrator</h4></div>",
    unsafe_allow_html=True)
if st.sidebar.button("🔒 Đăng xuất", use_container_width=True): st.session_state['authenticated'] = False; st.rerun()

st.markdown(
    "<div style='background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%); padding: 1.8rem; border-radius: 20px; color: white; margin-bottom: 2rem;'> <h1 style='color: white; margin: 0; font-size: 30px;'>🛡️ Hệ thống lọc thư rác dựa trên giải thuật Naive Bayes</h1> <p style='color: #E0E7FF; margin: 5px 0 0 0;'>Tích hợp mô hình toán học Naive Bayes cải tiến</p> </div>",
    unsafe_allow_html=True)


def thuc_hien_hoc_tang_cuong_online(msg_id, noi_dung, nhan_moi):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    c = conn.cursor()
    if msg_id is not None and msg_id > 0:
        if nhan_moi == 'spam':
            c.execute("UPDATE messages SET label='spam', spam_pct=100.0, ham_pct=0.0 WHERE id=%s", (msg_id,))
        else:
            c.execute("UPDATE messages SET label='ham', spam_pct=0.0, ham_pct=100.0 WHERE id=%s", (msg_id,))
        conn.commit()
    conn.close()

    if os.path.exists('model_knowledge.json'):
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
            diem_phe_cu = knowledge['word_counts'][nhan_cu].get(w, 0)
            diem_muon_bom = max(40, diem_phe_cu + 50)
            knowledge['word_counts'][nhan_moi][w] = knowledge['word_counts'][nhan_moi].get(w, 0) + diem_muon_bom
            knowledge['word_counts'][nhan_cu][w] = max(0, int(diem_phe_cu * 0.5))
            if w not in knowledge['vocab']: knowledge['vocab'].append(w)

        knowledge['class_counts'][nhan_moi] += 5
        with open('model_knowledge.json', 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=4)

    st.cache_resource.clear()
    st.toast(f"⚡ Đã thực thi Cân bằng động thành công!", icon="🚀")
    st.rerun()


def xoa_tin_nhan_don_le(msg_id):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        c = conn.cursor()
        c.execute("DELETE FROM messages WHERE id = %s", (msg_id,))
        conn.commit();
        conn.close()
        st.toast("🗑️ Đã xóa tin nhắn khỏi hệ thống!", icon="✅");
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi xóa dữ liệu: {e}")


def xoa_tat_ca_thu_rac():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        c = conn.cursor()
        c.execute("DELETE FROM messages WHERE label = 'spam'")
        conn.commit();
        conn.close()
        st.toast("💥 Đã dọn sạch hoàn toàn hòm thư rác!", icon="🔥");
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi khi xóa dữ liệu: {e}")


@st.dialog("⚠️ Xác nhận sửa đổi nhãn AI")
def hien_thi_hop_thoai_xac_nhan(msg_id, noi_dung, nhan_moi):
    st.write(f"Bạn đang yêu cầu ép hệ thống học tăng cường tin nhắn này sang nhóm **{nhan_moi.upper()}**.")
    st.markdown(
        f"<div style='background-color: #F3F4F6; padding: 10px; border-radius: 5px; font-style: italic;'>\"{noi_dung}\"</div>",
        unsafe_allow_html=True)
    if st.button("Xác nhận & Học trực tuyến", type="primary",
                 use_container_width=True): thuc_hien_hoc_tang_cuong_online(msg_id, noi_dung, nhan_moi)


@st.dialog("🗑️ Cảnh báo: Xóa vĩnh viễn tin nhắn")
def hien_thi_hop_thoai_xoa_don(msg_id, noi_dung):
    st.error("Hành động này sẽ xóa hoàn toàn bản ghi khỏi cơ sở dữ liệu MySQL và không thể khôi phục!")
    st.markdown(
        f"<div style='background-color: #FFF5F5; padding: 10px; border-radius: 5px; font-style: italic; color: #991B1B;'>\"{noi_dung}\"</div>",
        unsafe_allow_html=True)
    col_x1, col_x2 = st.columns(2)
    with col_x1:
        if st.button("Xóa vĩnh viễn", type="primary", use_container_width=True): xoa_tin_nhan_don_le(msg_id)
    with col_x2:
        if st.button("Hủy bỏ", use_container_width=True): st.rerun()


@st.dialog("🔥 CẢNH BÁO TỐI CAO: DỌN SẠCH THƯ RÁC")
def hien_thi_hop_thoai_xoa_sach_spam():
    st.error("Bạn đang chuẩn bị xóa TOÀN BỘ tin nhắn đang nằm trong Hộp thư rác!")
    col_all1, col_all2 = st.columns(2)
    with col_all1:
        if st.button("Đồng ý, dọn sạch sạch rác!", type="primary", use_container_width=True): xoa_tat_ca_thu_rac()
    with col_all2:
        if st.button("Hủy lệnh", use_container_width=True): st.rerun()


@st.cache_resource
def load_json_knowledge():
    if os.path.exists('model_knowledge.json'):
        with open('model_knowledge.json', 'r', encoding='utf-8') as f: return json.load(f)
    return None


try:
    knowledge_base = load_json_knowledge()
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    df_msg = pd.read_sql("SELECT * FROM messages ORDER BY id DESC", conn)
    df_blacklist = pd.read_sql("SELECT * FROM blacklist_keywords ORDER BY id DESC", conn)
    conn.close()

    total_msg, total_spam = len(df_msg), len(df_msg[df_msg['label'] == 'spam'])
    total_ham = len(df_msg[df_msg['label'] == 'ham'])
    spam_rate = (total_spam / total_msg * 100) if total_msg > 0 else 0

    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric(label="📥 Tổng lưu lượng tin", value=f"{total_msg} mẫu")
    with m_col2:
        st.metric(label="🟢 Hộp thư sạch (Ham)", value=f"{total_ham} tin")
    with m_col3:
        st.metric(label="🔴 Bộ lọc đã chặn (Spam)", value=f"{total_spam} tin")
    with m_col4:
        st.metric(label="📊 Tỷ lệ thư rác hiện tại", value=f"{spam_rate:.1f}%")

    st.write("")
    layout_left, layout_right = st.columns([1.6, 1])

    with layout_left:
        st.markdown(
            "<h3 style='color: #111827; font-weight: 700; margin-bottom: 15px;'>📥 Phân tách luồng thư & Sandbox Thuật toán</h3>",
            unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(
            [f"📥 Hộp thư chính ({total_ham})", f"🚨 Hộp thư rác ({total_spam})", "🧪 Test Nhanh AI Sandbox"])

        with tab1:
            ham_msgs = df_msg[df_msg['label'] == 'ham']
            if ham_msgs.empty: st.info("Hộp thư chính trống.")
            for _, row in ham_msgs.iterrows():
                st.markdown(
                    f"<div class='premium-card-ham'>Thư #{row['id']} | 👤 {row['name']} ({row['email']}) <span style='float:right; color:#9CA3AF;'>📅 {str(row['time'])[:19]}</span><br><br>{row['content']}</div>",
                    unsafe_allow_html=True)
                btn_c1, btn_c2, btn_c3 = st.columns([2.5, 1, 0.8])
                with btn_c1:
                    st.markdown(
                        f"🤖 Trọng số an toàn AI đánh giá: <span style='color: #10B981; font-weight: bold;'>{row['ham_pct']:.2f}%</span>",
                        unsafe_allow_html=True)
                with btn_c2:
                    if st.button("🚨 Gắn spam", key=f"spam_{row['id']}",
                                 use_container_width=True): hien_thi_hop_thoai_xac_nhan(row['id'], row['content'],
                                                                                        'spam')
                with btn_c3:
                    if st.button("🗑️ Xóa", key=f"del_ham_{row['id']}",
                                 use_container_width=True): hien_thi_hop_thoai_xoa_don(row['id'], row['content'])

        with tab2:
            spam_msgs = df_msg[df_msg['label'] == 'spam']
            if spam_msgs.empty:
                st.success("Không có thư rác.")
            else:
                st.button("🔥 DỌN SẠCH TOÀN BỘ THƯ RÁC HÀ LOẠT", use_container_width=True, type="primary",
                          on_click=hien_thi_hop_thoai_xoa_sach_spam)
                for _, row in spam_msgs.iterrows():
                    st.markdown(
                        f"<div class='premium-card-spam'>Item #{row['id']} | ⚠️ Nghi vấn từ: {row['name']} ({row['email']}) <span style='float:right; color:#9CA3AF;'>📅 {str(row['time'])[:19]}</span><br><br><i>{row['content']}</i></div>",
                        unsafe_allow_html=True)
                    btn_c1, btn_c2, btn_c3 = st.columns([2.5, 1, 0.8])
                    with btn_c1:
                        st.markdown(
                            f"🚨 Xác suất cấu trúc thư rác: <span style='color: #EF4444; font-weight: bold;'>{row['spam_pct']:.2f}%</span>",
                            unsafe_allow_html=True)
                    with btn_c2:
                        if st.button("✅Khôi phục", key=f"ham_{row['id']}", use_container_width=True,
                                     type="primary"): hien_thi_hop_thoai_xac_nhan(row['id'], row['content'], 'ham')
                    with btn_c3:
                        if st.button("🗑️ Xóa", key=f"del_spam_{row['id']}",
                                     use_container_width=True): hien_thi_hop_thoai_xoa_don(row['id'], row['content'])

        with tab3:
            st.markdown("#### 📝 Thử nghiệm nhanh mô hình phân loại (Môi trường Sandbox)")

            if knowledge_base is None:
                st.warning("⚠️ Không tìm thấy tệp tri thức 'model_knowledge.json'. Hãy khởi chạy Trang Chủ trước!")
            else:
                # Cơ chế khóa chuỗi qua Session State ngăn đơ nút bấm và văng con trỏ chuột
                if "o_nho_sandbox_co_dinh" not in st.session_state:
                    st.session_state["o_nho_sandbox_co_dinh"] = ""

                user_input = st.text_area("Nhập nội dung văn bản cần thẩm định ngay:",
                                          value=st.session_state["o_nho_sandbox_co_dinh"],
                                          height=130,
                                          key="sandbox_text_area_main",
                                          placeholder="Nhập thử các mẫu tin nhắn nghi ngờ lọt lưới...")
                st.session_state["o_nho_sandbox_co_dinh"] = user_input

                if st.button("🔍 Thực thi phân tích", type="primary", use_container_width=True, key="nut_doc_ban_check"):
                    pass  # Nút này chỉ kích hoạt reload form để lấy kết quả print phía dưới

                # ==================== KHU VỰC 2 NÚT HUẤN LUYỆN MỘT CHẠM ====================
                st.write("---")
                st.markdown("**🔧 Huấn luyện tăng cường trực tiếp (Incremental Learning)**")
                col_train1, col_train2 = st.columns(2)

                with col_train1:
                    if st.button("🚨 HUẤN LUYỆN LÀ SPAM", type="secondary", use_container_width=True,
                                 key="train_spam_btn"):
                        if user_input and user_input.strip() != "":
                            thuc_hien_hoc_tang_cuong_online(None, user_input, 'spam')
                        else:
                            st.warning("Vui lòng nhập nội dung trước khi huấn luyện!")

                with col_train2:
                    if st.button("✅ HUẤN LUYỆN LÀ HAM", type="primary", use_container_width=True, key="train_ham_btn"):
                        if user_input and user_input.strip() != "":
                            thuc_hien_hoc_tang_cuong_online(None, user_input, 'ham')
                        else:
                            st.warning("Vui lòng nhập nội dung trước khi huấn luyện!")

                # ==================== ĐỒNG BỘ IN TRỌNG SỐ THỜI GIAN THỰC ====================
                if user_input.strip() != "":
                    # 🌟 GIẢI PHÁP ĐỘT PHÁ: Đọc trực tiếp từ file JSON fresh vật lý để cập nhật trọng số mịn lập tức
                    with open('model_knowledge.json', 'r', encoding='utf-8') as f_fresh:
                        fresh_knowledge = json.load(f_fresh)

                    ket_qua, phan_tram_spam, phan_tram_ham = predict_online(user_input, fresh_knowledge)
                    st.markdown("##### 📊 Báo cáo phân tích:")
                    st.write(f"**Tỷ lệ Spam:** {phan_tram_spam:.2f}%")
                    st.progress(int(phan_tram_spam))
                    st.write(f"**Tỷ lệ Ham:** {phan_tram_ham:.2f}%")
                    st.progress(int(phan_tram_ham))

                    if ket_qua == 'spam':
                        st.error(f"🚨 HỆ THỐNG PHÁT HIỆN: THƯ RÁC ({phan_tram_spam:.2f}%)")
                    else:
                        st.success(f"✅ HỆ THỐNG XÁC NHẬN: THƯ THƯỜNG - HAM ({phan_tram_ham:.2f}%)")

    with layout_right:
        st.markdown(
            "<h3 style='color: #111827; font-weight: 700; margin-bottom: 15px;'>🛡️ Quy tắc cứng: MySQL Blacklist</h3>",
            unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("add_blacklist_form", clear_on_submit=True):
                new_kw = st.text_input("Nhập từ khóa muốn chặn đứng:")
                if st.form_submit_button("🚫 Thêm vào danh sách cấm", use_container_width=True):
                    if new_kw.strip() != "":
                        try:
                            conn = mysql.connector.connect(**MYSQL_CONFIG);
                            c = conn.cursor()
                            c.execute("INSERT INTO blacklist_keywords (keyword, created_at) VALUES (%s, %s)",
                                      (new_kw.strip().lower(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit();
                            conn.close();
                            st.rerun()
                        except:
                            st.error("Từ khóa này đã tồn tại!")
            st.write("---")
            if df_blacklist.empty:
                st.caption("Chưa có từ khóa cứng nào bị cấm.")
            else:
                for _, bl_row in df_blacklist.iterrows():
                    bl_col1, bl_col2 = st.columns([3, 1])
                    with bl_col1:
                        st.markdown(f"<code style='color: #EF4444; font-size: 14px;'>{bl_row['keyword']}</code>",
                                    unsafe_allow_html=True)
                    with bl_col2:
                        if st.button("🗑️ Xóa", key=f"del_kw_{bl_row['id']}", use_container_width=True):
                            conn = mysql.connector.connect(**MYSQL_CONFIG);
                            c = conn.cursor()
                            c.execute("DELETE FROM blacklist_keywords WHERE id=%s", (bl_row['id'],))
                            conn.commit();
                            conn.close();
                            st.rerun()

        st.write("")
        st.markdown("<h3 style='color: #111827; font-weight: 700; margin-bottom: 15px;'>📊 Phân tích lưu lượng</h3>",
                    unsafe_allow_html=True)
        with st.container(border=True):
            if total_msg > 0:
                chart_data = pd.DataFrame({'Số lượng': [total_ham, total_spam]},
                                          index=['Thư sạch (Ham)', 'Thư rác (Spam)'])
                st.bar_chart(chart_data, color="#3B82F6")
            else:
                st.info("Chưa có đủ chỉ số.")
except Exception as e:
    st.info("Hệ thống MySQL đang trống.")