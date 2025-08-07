# File: ai_bot.py (Revised to remove Sentiment Analysis)

import os
import json
import torch
import faiss
import numpy as np
import google.generativeai as genai
from sentence_transformers import SentenceTransformer, CrossEncoder
import re
from dotenv import load_dotenv
import sqlite3
import datetime

# ==============================================================================
# ส่วนที่ 1: โหลดทรัพยากรหลัก
# ==============================================================================
print("==========================================================")
print("⚙️ [1/5] กำลังเริ่มต้นการตั้งค่าและโหลดโมเดล...")
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"ใช้ Device (สำหรับ Embedding): {device.upper()}")

# --- โหลดโมเดลและฐานข้อมูลความรู้ (Knowledge Base) ---
print("⏳ [2/5] กำลังโหลดโมเดลและฐานข้อมูลความรู้ (หนังสือ)...")
embedder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device=device)
reranker = CrossEncoder("jinaai/jina-reranker-v1-turbo-en", device=device, trust_remote_code=True)
knowledge_index = faiss.read_index("./index/faiss.index")
with open("./index/mapping.json", "r", encoding="utf-8") as f:
    knowledge_entries = json.load(f)

# --- Cache โมเดล Gemini ---
print("🔥 [3/5] กำลังเชื่อมต่อ Gemini...")
try:
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash-latest')
        print("✅ [INFO] เชื่อมต่อและเตรียมโมเดล Gemini สำเร็จ")
    else:
        GEMINI_MODEL = None
        print("⚠️ [WARNING] ไม่พบ GOOGLE_API_KEY, ฟังก์ชัน AI จะไม่สามารถทำงานได้")
except Exception as e:
    GEMINI_MODEL = None
    print(f"❌ [ERROR] ไม่สามารถเชื่อมต่อกับ Gemini API ได้: {e}")

# ==============================================================================
# ส่วนที่ 2: โหลดข้อมูลตัวตน (Identity Loading)
# ==============================================================================
print("👤 [4/5] กำลังโหลดข้อมูลตัวตน...")

# --- 2.1 โปรไฟล์ผู้ใช้ ---
USER_PROFILE = {}
try:
    with open("data/user_profile.json", "r", encoding="utf-8") as f:
        USER_PROFILE = json.load(f)
    print(f"  - โหลดโปรไฟล์ผู้ใช้ '{USER_PROFILE.get('name', 'N/A')}' สำเร็จ")
except FileNotFoundError:
    print("  - ⚠️ [WARNING] ไม่พบไฟล์ data/user_profile.json")
except json.JSONDecodeError:
    print("  - ❌ [ERROR] รูปแบบไฟล์ data/user_profile.json ไม่ถูกต้อง")

# --- 2.2 โปรไฟล์ของ AI (เฟิง) ---
FENG_PROFILE = {}
try:
    with open("data/feng_profile.json", "r", encoding="utf-8") as f:
        FENG_PROFILE = json.load(f)
    print(f"  - โหลดโปรไฟล์ AI '{FENG_PROFILE.get('name', 'N/A')}' สำเร็จ")
except FileNotFoundError:
    print("  - ⚠️ [WARNING] ไม่พบไฟล์ data/feng_profile.json")
    FENG_PROFILE = {"name": "AI"}
except json.JSONDecodeError:
    print("  - ❌ [ERROR] รูปแบบไฟล์ data/feng_profile.json ไม่ถูกต้อง")
    FENG_PROFILE = {"name": "AI"}

print("🧠 [5/5] กำลังโหลดความทรงจำระยะสั้น...")

# --- 3.1 ความทรงจำระยะสั้น (จาก SQLite) ---
def init_short_term_memory_db():
    conn = sqlite3.connect('data/memory.db')
    cursor = conn.cursor()
    cursor.execute(''' CREATE TABLE IF NOT EXISTS conversation_history ( id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL ) ''')
    conn.commit()
    conn.close()
    print("  - 🗄️  ฐานข้อมูลความจำระยะสั้น (memory.db) พร้อมใช้งาน")

def add_to_short_term_memory(role, content):
    conn = sqlite3.connect('data/memory.db')
    cursor = conn.cursor()
    timestamp = datetime.datetime.now()
    try:
        cursor.execute("INSERT INTO conversation_history (timestamp, role, content) VALUES (?, ?, ?)", (timestamp, role, content))
        conn.commit()
    except Exception as e:
        print(f"❌ [ERROR] ไม่สามารถบันทึกความจำระยะสั้นได้: {e}")
    finally:
        conn.close()

def get_last_n_short_term_memories(n=15):
    try:
        conn = sqlite3.connect('data/memory.db')
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM conversation_history ORDER BY id DESC LIMIT ?", (n,))
        history = cursor.fetchall()
        conn.close()
        return list(reversed(history))
    except Exception as e:
        print(f"❌ [ERROR] ไม่สามารถดึงความจำระยะสั้นได้: {e}")
        return []

THAI_HOLIDAYS = { "01-01": "วันขึ้นปีใหม่", "04-13": "วันสงกรานต์", "04-14": "วันสงกรานต์", "04-15": "วันสงกรานต์", "05-01": "วันแรงงานแห่งชาติ", "07-28": "วันเฉลิมพระชนมพรรษา รัชกาลที่ 10", "08-12": "วันแม่แห่งชาติ", "10-13": "วันคล้ายวันสวรรคต รัชกาลที่ 9", "10-23": "วันปิยมหาราช", "12-05": "วันพ่อแห่งชาติ", "12-10": "วันรัฐธรรมนูญ", "12-31": "วันสิ้นปี" }

def get_daily_context():
    now = datetime.datetime.now()
    today_key = now.strftime("%m-%d")
    context = {
        "full_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M"),
        "day_of_week_thai": ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"][now.weekday()],
        "is_weekend": now.weekday() >= 5,
        "special_event": THAI_HOLIDAYS.get(today_key)
    }
    return context

def create_persona_block(profile: dict) -> str:
    if not profile:
        return "คุณคือ AI ผู้ช่วย"
    name = profile.get('name', 'AI')
    creator_name = profile.get('creator_info', {}).get('name', 'ผู้สร้าง')
    purpose = profile.get('relationship', {}).get('purpose_and_goal', 'เป็นผู้ช่วยที่มีประโยชน์')
    traits_list = profile.get('personality', {}).get('traits', [])
    traits_str = "\n".join([f"- {trait}" for trait in traits_list])
    persona = f"""คุณคือ "{name}", ปัญญาประดิษฐ์ที่ถูกสร้างโดย "{creator_name}"
**เป้าหมายและความสัมพันธ์ของคุณ:**
{purpose}

**บุคลิกและสไตล์การตอบของคุณ:**
{traits_str}
"""
    return persona.strip()

PERSONA_BLOCK = create_persona_block(FENG_PROFILE)
GEMINI_CONFIG = {"temperature": 0.3, "top_p": 0.95, "top_k": 40}
all_book_titles = sorted(list(set([entry.get("book_title", "").strip() for entry in knowledge_entries.values() if entry.get("book_title")])))
all_categories = sorted(list(set([entry.get("category", "").strip() for entry in knowledge_entries.values() if entry.get("category")])))
print(f"📚 พบหนังสือ {len(all_book_titles)} เล่ม ใน {len(all_categories)} หมวดหมู่")
print("🎉 All systems configured and loaded successfully!")
print("==========================================================")

def generate_context_with_sources_separated(relevant_keys, query, num_final_context=7, score_threshold=0.2):
    if not relevant_keys: return "ไม่มีข้อมูลเฉพาะเจาะจง", []
    candidate_data = [{'content': knowledge_entries.get(str(key), {}).get('embedding_text', '').strip(), 'source': knowledge_entries.get(str(key), {})} for key in relevant_keys]
    candidate_data = [data for data in candidate_data if data['content']]
    if not candidate_data: return "ไม่มีข้อมูลเฉพาะเจาะจง", []
    sentence_pairs = [[query, data['content']] for data in candidate_data]
    scores = reranker.predict(sentence_pairs)
    for i, score in enumerate(scores): candidate_data[i]['score'] = score
    ranked_results = sorted(candidate_data, key=lambda x: x['score'], reverse=True)
    context_parts, sources = [], []
    print("\n📈 [DEBUG] Reranker Scores (Threshold = 0.2):")
    for result in ranked_results:
        score, content, source_info = result['score'], result['content'], result['source']
        print(f"  Score: {score:.4f} | Book: {source_info.get('book_title', 'N/A')} | Text: {content[:60].replace(chr(10), ' ')}...")
        if score >= score_threshold:
            context_parts.append(content)
            sources.append({"book_title": source_info.get("book_title", "ไม่ระบุ"), "title": source_info.get("title", "ไม่ระบุหัวข้อ")})
        if len(context_parts) >= num_final_context: break
    if not context_parts: return "ไม่มีข้อมูลเฉพาะเจาะจง", []
    return "\n---\n".join(context_parts), sources

def clean_response(response_text):
    response_text = re.sub(r'\*\s*\*', '*', response_text)
    response_text = re.sub(r'(^|\n)\s*\*\s*', r'\1  * ', response_text)
    response_text = re.sub(r'\s*---\s*', '\n\n---\n\n', response_text)
    response_text = re.sub(r'\n{3,}', '\n\n', response_text)
    response_text = re.sub(r'<[^>]+>', '', response_text)
    return response_text.strip()