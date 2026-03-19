# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import docx
import re
from collections import Counter
import io

# ---------------------------------------------------------
# Section 1: การตั้งค่าหน้าเว็บและกำหนด Stopwords
# ---------------------------------------------------------
st.set_page_config(page_title="เครื่องมือวิเคราะห์คำศัพท์สำหรับนักแปล", layout="wide")

# รายการ Stopwords ภาษาอังกฤษเบื้องต้น (สามารถเพิ่มคำที่ต้องการละเว้นได้ที่นี่)
STOPWORDS = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", 
    "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", 
    "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", 
    "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", 
    "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", 
    "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", 
    "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", 
    "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", 
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", 
    "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
])

# ---------------------------------------------------------
# Section 2: ฟังก์ชันสำหรับอ่านไฟล์และประมวลผลข้อความ
# ---------------------------------------------------------
def read_text_file(uploaded_file):
    """อ่านเนื้อหาจากไฟล์ .txt"""
    return uploaded_file.getvalue().decode("utf-8")

def read_docx_file(uploaded_file):
    """อ่านเนื้อหาจากไฟล์ .docx"""
    doc = docx.Document(uploaded_file)
    full_text = [para.text for para in doc.paragraphs]
    return '\n'.join(full_text)

def process_text(text):
    """ทำความสะอาดข้อความ แยกคำ และนับความถี่"""
    # ทำให้เป็นตัวพิมพ์เล็กทั้งหมด
    text = text.lower()
    # ดึงมาเฉพาะคำที่เป็นภาษาอังกฤษ (ตัวอักษร a-z)
    words = re.findall(r'\b[a-z]+\b', text)
    # กรอง stopwords ออก
    filtered_words = [word for word in words if word not in STOPWORDS]
    # นับจำนวนคำ
    return Counter(filtered_words)

# ---------------------------------------------------------
# Section 3: ส่วนแสดงผล UI บน Streamlit
# ---------------------------------------------------------
st.title("📝 ผู้ช่วยวิเคราะห์คำศัพท์สำหรับนักแปล (Vocabulary Analyzer)")
st.write("อัปโหลดไฟล์งานแปลของคุณ (.txt หรือ .docx) เพื่อดูคำศัพท์ที่ใช้บ่อยที่สุด พร้อมตัวอย่างบริบทการใช้งาน")

# 1. ให้ user upload ไฟล์
uploaded_file = st.file_uploader("เลือกไฟล์เอกสาร (.txt หรือ .docx)", type=["txt", "docx"])

if uploaded_file is not None:
    # ตรวจสอบประเภทไฟล์และดึงข้อความ
    if uploaded_file.name.endswith(".txt"):
        text_data = read_text_file(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        text_data = read_docx_file(uploaded_file)
    
    if text_data:
        # ประมวลผลและดึง Top 30 คำศัพท์
        word_counts = process_text(text_data)
        top_30_words = word_counts.most_common(30)
        
        if not top_30_words:
            st.warning("ไม่พบคำศัพท์ภาษาอังกฤษในไฟล์นี้ หรือมีแต่ Stopwords ครับ")
        else:
            # สร้าง Pandas DataFrame
            df = pd.DataFrame(top_30_words, columns=['คำศัพท์ (Word)', 'ความถี่ (Frequency)'])
            
            # สร้าง URL ของ Cambridge Dictionary สำหรับแต่ละคำ
            df['อ้างอิงและตัวอย่าง (Cambridge Dictionary)'] = "https://dictionary.cambridge.org/dictionary/english/" + df['คำศัพท์ (Word)']

            st.markdown("---")
            
            # ---------------------------------------------------------
            # Section 4: สร้างและแสดง Bar Chart (Matplotlib)
            # ---------------------------------------------------------
            st.subheader("📊 กราฟแสดง Top 30 คำศัพท์ที่ใช้บ่อยที่สุด")
            
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(df['คำศัพท์ (Word)'], df['ความถี่ (Frequency)'], color='#4C83EE')
            plt.xticks(rotation=45, ha='right')
            ax.set_ylabel('ความถี่ (ครั้ง)')
            ax.set_title('Top 30 Most Frequent Words')
            # ตัดขอบกราฟให้สวยงาม
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            st.pyplot(fig)
            
            st.markdown("---")
            
            # ---------------------------------------------------------
            # Section 5: ตารางข้อมูลและปุ่ม Download
            # ---------------------------------------------------------
            st.subheader("📋 รายละเอียดคำศัพท์และบริบท")
            
            # แสดง DataFrame พร้อมทำให้คอลัมน์ลิงก์กดได้
            st.dataframe(
                df,
                column_config={
                    "อ้างอิงและตัวอย่าง (Cambridge Dictionary)": st.column_config.LinkColumn("คลิกเพื่อดู Context (Cambridge Dictionary)")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # ปุ่ม Download ผลลัพธ์เป็น .csv
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 ดาวน์โหลดข้อมูลเป็นไฟล์ .CSV",
                data=csv,
                file_name='top_30_vocabulary.csv',
                mime='text/csv',
            )
