# File: main.py

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import os
import traceback
import re
import random
from rapidfuzz import process, fuzz
from contextlib import asynccontextmanager

# --- Imports from local modules ---
from ai_bot import (
    GEMINI_MODEL, PERSONA_BLOCK, GEMINI_CONFIG,
    all_book_titles, all_categories,
    knowledge_entries, knowledge_index,
    embedder, reranker,
    generate_context_with_sources_separated,
    clean_response,
    USER_PROFILE, FENG_PROFILE,
    init_short_term_memory_db, add_to_short_term_memory, get_last_n_short_term_memories,
    get_daily_context,
)
from quick_responses import QUICK_RESPONSES
from modules.reporter import handle_reporter_query
from modules.system_tools import handle_system_tool_query
from modules.image_search import search_for_image
from modules.super_advisor import handle_super_advisor_query

# --- Lifespan Manager for Startup and Shutdown Events ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    # Code to run on startup
    print("🚀 FastAPI is starting up...")
    init_short_term_memory_db()
    print("✅ Memory system initialized.")
    
    yield  # The application runs here
    
    # Code to run on shutdown
    print("🌙 FastAPI is shutting down...")

# --- FastAPI App Initialization ---
app = FastAPI(title="Personal AI Assistant API", lifespan=lifespan)
web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
app.mount("/web", StaticFiles(directory=web_dir), name="web")


# --- Pydantic Models ---
class ImageInfo(BaseModel):
    url: str
    description: str
    photographer: str
    profile_url: str

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    history: list
    image: Optional[ImageInfo] = None


def get_emergency_help_response(user_name: str) -> str:
    return f"""แน่นอนครับคุณ{user_name}, ผมสามารถช่วยคุณทำสิ่งเหล่านี้ได้ครับ:

- **บอกวันและเวลา:** "วันนี้วันอะไร", "ตอนนี้กี่โมง"
- **เปิดโปรแกรม:** "เปิด notepad"
- **เปิดเว็บไซต์:** "เปิด youtube"
- **จัดการคลิปบอร์ด:** "อ่านคลิปบอร์ด", "คัดลอก 'ข้อความ'"
- **ควบคุมเสียง:** "เพิ่มเสียง", "ลดเสียง"
- **ค้นหารูปภาพ:** "หารูป [สิ่งของ]"

ลองใช้คำสั่งเหล่านี้ได้เลยครับ"""

def get_quick_response_safely(query: str, response_list: list, score_cutoff=90, max_words=4) -> Optional[str]:
    if len(query.split()) > max_words:
        return None
    for item in response_list:
        result = process.extractOne(query, item["questions"], scorer=fuzz.ratio)
        if result and result[1] >= score_cutoff:
            matched_question, score, _ = result
            print(f"⚡️ [Quick Response] Found a safe match: '{matched_question}' (Score: {score:.2f})")
            return random.choice(item["answers"])
    return None


# --- API Endpoints ---
@app.get("/", response_class=FileResponse)
async def read_root():
    return FileResponse(os.path.join(web_dir, 'index.html'))

@app.post("/ask", response_model=ChatResponse)
async def ask_question(chat_request: ChatRequest):
    query = chat_request.query
    ai_answer = "ขออภัยครับ มีบางอย่างผิดพลาดในการประมวลผล"
    is_non_ai_module_used = False
    image_to_display = None

    try:
        add_to_short_term_memory('user', query)
        short_term_memory = get_last_n_short_term_memories(n=15)
        user_name = USER_PROFILE.get('name', 'เพื่อน')
        q_lower = query.lower()

        # Flow 0 & 0.5: Check for Help and Quick Responses
        if any(keyword in q_lower for keyword in ["ทำอะไรได้บ้าง", "ใช้ทำอะไรได้"]):
            ai_answer = get_emergency_help_response(user_name)
            is_non_ai_module_used = True
        
        if not is_non_ai_module_used:
            quick_response = get_quick_response_safely(q_lower, QUICK_RESPONSES)
            if quick_response:
                ai_answer = quick_response.replace("{user_name}", user_name)
                is_non_ai_module_used = True

        # Flow 1-4: Check for Rule-Based Tools
        if not is_non_ai_module_used:
            # Reporter
            reporter_keywords = ["วันนี้วันอะไร", "วันที่เท่าไหร่", "ตอนนี้กี่โมง", "เวลาอะไร"]
            if any(keyword in q_lower for keyword in reporter_keywords):
                ai_answer = handle_reporter_query(q_lower, get_daily_context(), user_name)
                is_non_ai_module_used = True
            
            # System Tools
            if not is_non_ai_module_used:
                system_tool_response = handle_system_tool_query(query)
                if system_tool_response:
                    ai_answer = system_tool_response
                    is_non_ai_module_used = True

            # Image Search
            if not is_non_ai_module_used:
                image_search_match = re.search(r"(หารูป|ขอดูรูป|สร้างภาพ|หาภาพ)\s+(.+)", query, re.IGNORECASE)
                if image_search_match:
                    search_term = image_search_match.group(2).strip()
                    print(f"🖼️ [Image Search] User requested: '{search_term}'")
                    image_to_display = search_for_image(search_term)
                    ai_answer = f"นี่คือรูป '{search_term}' ที่ผมหามาให้ครับ" if image_to_display else f"ขออภัยครับ, ผมหารูป '{search_term}' ไม่เจอ"
                    is_non_ai_module_used = True

        # Flow 5: The One and Only Super Advisor
        if not is_non_ai_module_used:
            print("🚀 [Flow Control] Handing over to Super Advisor...")
            daily_context = get_daily_context()

            if not GEMINI_MODEL:
                ai_answer = "ขออภัยครับ ตอนนี้ผมไม่สามารถเชื่อมต่อกับระบบ AI หลักได้"
            else:
                final_ai_answer = handle_super_advisor_query(
                    query=query, q_lower=q_lower, persona_block=PERSONA_BLOCK,
                    gemini_model=GEMINI_MODEL, config=GEMINI_CONFIG, clean_func=clean_response,
                    user_profile=USER_PROFILE, short_term_memory=short_term_memory,
                    daily_context=daily_context,
                    all_book_titles=all_book_titles, all_categories=all_categories,
                    knowledge_index=knowledge_index, knowledge_entries=knowledge_entries,
                    embedder=embedder, generate_context_func=generate_context_with_sources_separated
                )
                
                if final_ai_answer:
                    ai_answer = final_ai_answer
                else:
                    ai_answer = f"เรื่องนี้ผมอาจจะยังไม่มีข้อมูลที่แน่ชัดครับคุณ{user_name} ลองถามผมในหัวข้ออื่นได้นะครับ"

        add_to_short_term_memory('model', ai_answer)
        
        final_history = get_last_n_short_term_memories(n=16) 
        updated_history_for_display = [{"role": role, "parts": content} for role, content in final_history]

        return ChatResponse(answer=ai_answer, history=updated_history_for_display, image=image_to_display)

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดร้ายแรงใน Endpoint /ask: {e}")
        traceback.print_exc()
        user_name = USER_PROFILE.get('name', 'เพื่อน')
        error_message = f"ขออภัยครับคุณ{user_name} เกิดข้อผิดพลาดร้ายแรงในระบบ โปรดลองอีกครั้งในภายหลัง"
        add_to_short_term_memory('model', error_message)
        final_history = get_last_n_short_term_memories(n=16)
        updated_history_for_display = [{"role": r, "parts": c} for r, c in final_history]
        return ChatResponse(answer=error_message, history=updated_history_for_display, image=None)