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
from pythainlp.tokenize import word_tokenize  # เพิ่มตัวตัดคำภาษาไทย
from pythainlp.corpus import thai_stopwords  # เพิ่ม Stopwords ภาษาไทย

# ---------------------------------------------------------
# Section 1: ระบบจัดการ 2 ภาษา (Language Mapping)
# ---------------------------------------------------------
LANG_TEXTS = {
    "TH": {
        "title": "📝 ผู้ช่วยวิเคราะห์คำศัพท์ (รองรับไทย-อังกฤษ)",
        "desc": "วิเคราะห์คำศัพท์จากไฟล์ (.txt, .docx, .pdf) รองรับทั้งภาษาไทยและอังกฤษ",
        "upload_label": "เลือกไฟล์เอกสาร",
        "processing": "กำลังตัดคำและประมวลผล...",
        "summary_title": "📌 สรุปใจความสำคัญ",
        "time_title": "⏳ การประเมินเวลาทำงาน",
        "speed_label": "ความเร็วการแปล (คำต่อชั่วโมง)",
        "total_words": "จำนวนคำทั้งหมด:",
        "est_time": "เวลาที่คาดว่าต้องใช้:",
        "chart_title": "📊 กราฟแสดง Top 30 คำที่ใช้บ่อย",
        "table_title": "📋 ตาราง Glossary",
        "col_word": "คำศัพท์",
        "col_freq": "ความถี่",
        "col_trans": "คำแปล (EN <-> TH)",
        "col_context": "บริบท",
        "col_collocate": "คำที่ใช้คู่กัน",
        "btn_download": "📥 ดาวน์โหลดไฟล์ Excel (.xlsx)",
        "no_word_warn": "ไม่พบคำศัพท์ในไฟล์นี้",
    },
    "EN": {
        "title": "📝 Multi-lang Vocab Analyzer",
        "desc": "Analyze vocab from files (.txt, .docx, .pdf) supporting both Thai and English.",
        "upload_label": "Choose a document file",
        "processing": "Processing and tokenizing...",
        "summary_title": "📌 Key Sentence Summary",
        "time_title": "⏳ Workload Estimation",
        "speed_label": "Translation Speed (Words/Hour)",
        "total_words": "Total Word Count:",
        "est_time": "Estimated Time:",
        "chart_title": "📊 Top 30 Most Frequent Words",
        "table_title": "📋 Glossary Table",
        "col_word": "Word",
        "col_freq": "Frequency",
        "col_trans": "Translation",
        "col_context": "Context",
        "col_collocate": "Collocates",
        "btn_download": "📥 Download Excel (.xlsx)",
        "no_word_warn": "No words found in this file.",
    }
}

# ---------------------------------------------------------
# Section 2: ฟังก์ชันการประมวลผล
# ---------------------------------------------------------
ENG_STOPWORDS = set(["i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they", "them", "a", "an", "the", "and", "but", "if", "or", "as", "of", "at", "by", "for", "with", "about", "to", "from", "in", "on", "is", "are", "was", "were", "be", "been", "do", "does", "did", "can", "will", "should", "not", "this", "that"])
TH_STOPWORDS = set(thai_stopwords())

def get_text_from_file(uploaded_file):
    try:
        if uploaded_file.name.endswith(".txt"):
            return uploaded_file.getvalue().decode("utf-8")
        elif uploaded_file.name.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            return '\n'.join([p.text for p in doc.paragraphs])
        elif uploaded_file.name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(uploaded_file)
            return '\n'.join([page.extract_text() for page in reader.pages])
    except: return ""
    return ""

def custom_tokenize(text):
    """ฟังก์ชันตัดคำที่รองรับทั้งไทยและอังกฤษ"""
    # ตัดคำภาษาไทยและอังกฤษผสมกัน
    tokens = word_tokenize(text, engine="newmm")
    clean_tokens = []
    for t in tokens:
        t = t.strip().lower()
        # กรองเอาเฉพาะคำ (ไม่ใช่สัญลักษณ์หรือตัวเลขตัวเดียว) และไม่อยู่ใน Stopwords
        if len(t) > 1 and t not in ENG_STOPWORDS and t not in TH_STOPWORDS and not re.match(r'^\d+$', t):
            clean_tokens.append(t)
    return clean_tokens

def get_statistical_summary(text, top_words_dict, n=3):
    sentences = re.split(r'(?<=[.!?\n])\s+', text)
    scores = {}
    for i, s in enumerate(sentences):
        for word, freq in top_words_dict.items():
            if word in s.lower():
                scores[i] = scores.get(i, 0) + freq
    top_indices = sorted(scores, key=scores.get, reverse=True)[:n]
    top_indices.sort()
    return " ... ".join([sentences[i].strip() for i in top_indices if sentences[i].strip()])

# ---------------------------------------------------------
# Section 3: UI
# ---------------------------------------------------------
st.set_page_config(page_title="Multi-lang Translator Tool", layout="wide")

with st.sidebar:
    st.header("Settings")
    ui_lang = st.radio("เลือกภาษา UI / Select UI Language", ("ไทย", "English"))
    lang_key = "TH" if ui_lang == "ไทย" else "EN"
    txt = LANG_TEXTS[lang_key]
    st.markdown("---")
    trans_speed = st.slider(txt["speed_label"], 100, 1000, 250)

st.title(txt["title"])
st.write(txt["desc"])

uploaded_file = st.file_uploader(txt["upload_label"], type=["txt", "docx", "pdf"])

if uploaded_file:
    full_text = get_text_from_file(uploaded_file)
    if full_text:
        with st.spinner(txt["processing"]):
            # ตัดคำทั้งหมด
            all_tokens = custom_tokenize(full_text)
            total_word_count = len(all_tokens)
            
            # 1. Estimation
            st.subheader(txt["time_title"])
            est_hours = total_word_count / trans_speed
            c1, c2 = st.columns(2)
            c1.metric(txt["total_words"], f"{total_word_count:,}")
            c2.metric(txt["est_time"], f"{est_hours:.1f} hrs", f"{est_hours/8:.1f} days")

            word_counts = Counter(all_tokens)
            top_30 = word_counts.most_common(30)
            
            if top_30:
                # 2. Summary
                st.subheader(txt["summary_title"])
                summary = get_statistical_summary(full_text, dict(top_30))
                st.info(summary if summary else "ไม่สามารถสรุปได้")

                # 3. Table & Translation
                df = pd.DataFrame(top_30, columns=[txt["col_word"], txt["col_freq"]])
                
                # ระบบสลับทิศทางการแปลอัตโนมัติ
                def smart_translate(word):
                    # ถ้าเป็นภาษาอังกฤษ ให้แปลเป็นไทย | ถ้าเป็นไทย ให้แปลเป็นอังกฤษ
                    is_english = bool(re.match(r'^[a-zA-Z]+$', word))
                    source_lang = 'en' if is_english else 'th'
                    target_lang = 'th' if is_english else 'en'
                    try:
                        return GoogleTranslator(source=source_lang, target=target_lang).translate(word)
                    except: return "-"

                df[txt["col_trans"]] = [smart_translate(w) for w in df[txt["col_word"]]]
                
                # Context & Collocates
                sentences = re.split(r'(?<=[.!?\n])\s+', full_text)
                df[txt["col_context"]] = [next((s.strip() for s in sentences if w in s.lower()), "-") for w in df[txt["col_word"]]]
                
                def quick_col(target, tokens):
                    near = []
                    for i, v in enumerate(tokens):
                        if v == target:
                            start, end = max(0, i-2), min(len(tokens), i+3)
                            near.extend(tokens[start:i] + tokens[i+1:end])
                    res = [c[0] for c in Counter(near).most_common(2)]
                    return ", ".join(res) if res else "-"
                df[txt["col_collocate"]] = [quick_col(w, all_tokens) for w in df[txt["col_word"]]]

                st.subheader(txt["chart_title"])
                # แก้ไขฟอนต์กราฟให้รองรับภาษาไทย (เลือกฟอนต์พื้นฐานในระบบ)
                plt.rcParams['font.family'] = 'Tahoma' # หรือ 'Arial Unicode MS' สำหรับ Mac
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(df[txt["col_word"]], df[txt["col_freq"]], color='#4C83EE')
                plt.xticks(rotation=45)
                st.pyplot(fig)

                st.subheader(txt["table_title"])
                st.dataframe(df, use_container_width=True, hide_index=True)

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(txt["btn_download"], buffer.getvalue(), "glossary.xlsx")
