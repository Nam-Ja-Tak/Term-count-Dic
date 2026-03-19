# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import docx
import PyPDF2
import re
from collections import Counter
import io
from deep_translator import GoogleTranslator

# ---------------------------------------------------------
# Section 1: การตั้งค่าหน้าเว็บและกำหนด Stopwords
# ---------------------------------------------------------
st.set_page_config(page_title="เครื่องมือวิเคราะห์คำศัพท์สำหรับนักแปล", layout="wide")

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
    return uploaded_file.getvalue().decode("utf-8")

def read_docx_file(uploaded_file):
    doc = docx.Document(uploaded_file)
    full_text = [para.text for para in doc.paragraphs]
    return '\n'.join(full_text)

def read_pdf_file(uploaded_file):
    reader = PyPDF2.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def process_text(text):
    text_lower = text.lower()
    words = re.findall(r'\b[a-z]+\b', text_lower)
    filtered_words = [word for word in words if word not in STOPWORDS]
    return Counter(filtered_words)

@st.cache_data(show_spinner=False)
def translate_words(words_list):
    translator = GoogleTranslator(source='en', target='th')
    translations = []
    for word in words_list:
        try:
            translated = translator.translate(word)
            translations.append(translated)
        except Exception as e:
            translations.append("แปลไม่ได้")
    return translations

def get_word_context(word, full_text):
    """ฟังก์ชันดึงประโยคตัวอย่างจากข้อความต้นฉบับ"""
    # แทนที่การขึ้นบรรทัดใหม่ด้วยช่องว่าง เพื่อไม่ให้ประโยคขาดตอน
    clean_text = full_text.replace('\n', ' ')
    # แยกข้อความออกเป็นประโยคๆ โดยใช้จุด, เครื่องหมายตกใจ, เครื่องหมายคำถาม
    sentences = re.split(r'(?<=[.!?])\s+', clean_text)
    
    # สร้าง Pattern ค้นหาคำแบบเจาะจงเป็นคำๆ (ไม่ให้ไปซ้ำกับส่วนหนึ่งของคำอื่น)
    pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
    
    # วนลูปหาประโยคแรกที่มีคำศัพท์นี้อยู่
    for sentence in sentences:
        if pattern.search(sentence):
            return sentence.strip()
    return "ไม่พบบริบทชัดเจน"

# ---------------------------------------------------------
# Section 3: ส่วนแสดงผล UI บน Streamlit
# ---------------------------------------------------------
st.title("📝 ผู้ช่วยวิเคราะห์คำศัพท์สำหรับนักแปล (Vocabulary Analyzer)")
st.write("อัปโหลดไฟล์งานแปลของคุณ (.txt, .docx หรือ .pdf) เพื่อดูคำศัพท์ที่ใช้บ่อยที่สุด คำแปล และประโยคบริบทต้นฉบับ")

uploaded_file = st.file_uploader("เลือกไฟล์เอกสาร (.txt, .docx, .pdf)", type=["txt", "docx", "pdf"])

if uploaded_file is not None:
    text_data = ""
    if uploaded_file.name.endswith(".txt"):
        text_data = read_text_file(uploaded_file)
    elif uploaded_file.name.endswith(".docx"):
        text_data = read_docx_file(uploaded_file)
    elif uploaded_file.name.endswith(".pdf"):
        text_data = read_pdf_file(uploaded_file)
    
    if text_data:
        word_counts = process_text(text_data)
        top_30_words = word_counts.most_common(30)
        
        if not top_30_words:
            st.warning("ไม่พบคำศัพท์ภาษาอังกฤษในไฟล์นี้ หรือมีแต่ Stopwords ครับ")
        else:
            df = pd.DataFrame(top_30_words, columns=['คำศัพท์ (Word)', 'ความถี่ (Frequency)'])
            
            with st.spinner('กำลังแปลคำศัพท์และดึงประโยคบริบท กรุณารอสักครู่...'):
                # แปลภาษา
                df['คำแปล (Translation)'] = translate_words(df['คำศัพท์ (Word)'].tolist())
                # ดึงบริบทประโยค (Context)
                df['บริบทจากต้นฉบับ (Context)'] = df['คำศัพท์ (Word)'].apply(lambda w: get_word_context(w, text_data))

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
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            st.pyplot(fig)
            
            st.markdown("---")
            
            # ---------------------------------------------------------
            # Section 5: ตารางข้อมูล Glossary และปุ่ม Download (Excel)
            # ---------------------------------------------------------
            st.subheader("📋 ตารางคำศัพท์ คำแปล และบริบท (Glossary)")
            
            # จัดเรียงคอลัมน์ใหม่ให้มี Context ด้วย
            df_display = df[['คำศัพท์ (Word)', 'คำแปล (Translation)', 'บริบทจากต้นฉบับ (Context)', 'ความถี่ (Frequency)']]
            st.dataframe(df_display, hide_index=True, use_container_width=True)
            
            # แปลง DataFrame เป็นไฟล์ Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_display.to_excel(writer, index=False, sheet_name='Glossary')
            
            # ปุ่ม Download ผลลัพธ์เป็น .xlsx
            st.download_button(
                label="📥 ดาวน์โหลดข้อมูลเป็นไฟล์ Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name='top_30_vocabulary_with_context.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
