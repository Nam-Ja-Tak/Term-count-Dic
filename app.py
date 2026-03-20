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
# Section 1: ระบบจัดการ 2 ภาษา (Language Mapping)
# ---------------------------------------------------------
LANG_TEXTS = {
    "TH": {
        "title": "📝 ผู้ช่วยวิเคราะห์คำศัพท์สำหรับนักแปล",
        "desc": "อัปโหลดไฟล์ (.txt, .docx, .pdf) เพื่อดูคำศัพท์, คำแปล, บริบท และคำที่ใช้คู่กัน (Collocations)",
        "upload_label": "เลือกไฟล์เอกสาร",
        "processing": "กำลังประมวลผลและแปลภาษา...",
        "chart_title": "📊 กราฟแสดง Top 30 คำศัพท์ที่ใช้บ่อยที่สุด",
        "table_title": "📋 ตาราง Glossary พร้อม Collocations",
        "col_word": "คำศัพท์ (Word)",
        "col_freq": "ความถี่ (Freq)",
        "col_trans": "คำแปล (Translation)",
        "col_context": "บริบท (Context)",
        "col_collocate": "คำที่มักใช้คู่กัน (Collocates)",
        "btn_download": "📥 ดาวน์โหลดไฟล์ Excel (.xlsx)",
        "no_word_warn": "ไม่พบคำศัพท์ภาษาอังกฤษในไฟล์นี้",
    },
    "EN": {
        "title": "📝 Vocabulary Analyzer for Translators",
        "desc": "Upload files (.txt, .docx, .pdf) to see vocabulary, translations, context, and collocations.",
        "upload_label": "Choose a document file",
        "processing": "Processing and translating...",
        "chart_title": "📊 Top 30 Most Frequent Words",
        "table_title": "📋 Glossary Table with Collocations",
        "col_word": "Word",
        "col_freq": "Frequency",
        "col_trans": "Translation",
        "col_context": "Context",
        "col_collocate": "Common Collocates",
        "btn_download": "📥 Download Excel (.xlsx)",
        "no_word_warn": "No English vocabulary found in this file.",
    }
}

# ---------------------------------------------------------
# Section 2: ฟังก์ชันการประมวลผล (Processing Functions)
# ---------------------------------------------------------
STOPWORDS = set(["i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they", "them", "a", "an", "the", "and", "but", "if", "or", "as", "of", "at", "by", "for", "with", "about", "to", "from", "in", "on", "is", "are", "was", "were", "be", "been", "do", "does", "did", "can", "will", "should", "not", "this", "that"])

def get_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".txt"):
        return uploaded_file.getvalue().decode("utf-8")
    elif uploaded_file.name.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        return '\n'.join([p.text for p in doc.paragraphs])
    elif uploaded_file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        return '\n'.join([page.extract_text() for page in reader.pages])
    return ""

def find_collocates(target_word, all_words, window=2):
    """หาคำที่ปรากฏข้างๆ target_word (Collocations)"""
    collocates = []
    for i, word in enumerate(all_words):
        if word == target_word:
            # ดึงคำก่อนหน้าและคำถัดไปภายในช่วง window
            start = max(0, i - window)
            end = min(len(all_words), i + window + 1)
            context_words = all_words[start:end]
            for w in context_words:
                if w != target_word and w not in STOPWORDS:
                    collocates.append(w)
    # คืนค่า Top 3 คำที่มาคู่กันบ่อยที่สุด
    most_common = [c[0] for c in Counter(collocates).most_common(3)]
    return ", ".join(most_common) if most_common else "-"

# ---------------------------------------------------------
# Section 3: ส่วนแสดงผล UI
# ---------------------------------------------------------
st.set_page_config(page_title="Translator Tool", layout="wide")

# Sidebar สำหรับเลือกภาษา UI
with st.sidebar:
    st.header("Settings")
    ui_lang = st.radio("เลือกภาษา UI / Select UI Language", ("ไทย", "English"))
    lang_key = "TH" if ui_lang == "ไทย" else "EN"
    txt = LANG_TEXTS[lang_key]

st.title(txt["title"])
st.write(txt["desc"])

uploaded_file = st.file_uploader(txt["upload_label"], type=["txt", "docx", "pdf"])

if uploaded_file:
    full_text = get_text_from_file(uploaded_file)
    
    if full_text:
        # เตรียมข้อมูลคำศัพท์
        raw_words = re.findall(r'\b[a-z]+\b', full_text.lower())
        filtered_words = [w for w in raw_words if w not in STOPWORDS and len(w) > 1]
        word_counts = Counter(filtered_words)
        top_30 = word_counts.most_common(30)
        
        if not top_30:
            st.warning(txt["no_word_warn"])
        else:
            with st.spinner(txt["processing"]):
                df = pd.DataFrame(top_30, columns=[txt["col_word"], txt["col_freq"]])
                
                # แปลภาษา
                translator = GoogleTranslator(source='en', target='th' if lang_key=="TH" else 'en')
                df[txt["col_trans"]] = [translator.translate(w) for w in df[txt["col_word"]]]
                
                # หา Context (ดึงจากประโยคแรกที่เจอ)
                sentences = re.split(r'(?<=[.!?])\s+', full_text.replace('\n', ' '))
                contexts = []
                for word in df[txt["col_word"]]:
                    match = next((s.strip() for s in sentences if re.search(rf'\b{word}\b', s, re.I)), "-")
                    contexts.append(match)
                df[txt["col_context"]] = contexts
                
                # หา Collocates (ฟีเจอร์ใหม่!)
                df[txt["col_collocate"]] = [find_collocates(w, raw_words) for w in df[txt["col_word"]]]

            # แสดงกราฟ
            st.subheader(txt["chart_title"])
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.bar(df[txt["col_word"]], df[txt["col_freq"]], color='#4C83EE')
            plt.xticks(rotation=45)
            st.pyplot(fig)
            
            st.markdown("---")
            
            # แสดงตาราง
            st.subheader(txt["table_title"])
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # ดาวน์โหลด Excel
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Glossary')
            
            st.download_button(
                label=txt["btn_download"],
                data=buffer.getvalue(),
                file_name='translator_glossary.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
