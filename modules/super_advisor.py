# File: modules/super_advisor.py (Revised for Logic-Focused Consultation)

import re

def handle_super_advisor_query(
    query, q_lower, persona_block, gemini_model, config, clean_func,
    user_profile, short_term_memory, daily_context,
    all_book_titles, all_categories,
    knowledge_index, knowledge_entries, embedder, generate_context_func
):
    """
    จัดการคำถามทุกรูปแบบในฐานะ "Super Advisor" ที่เน้นการให้คำปรึกษาเชิงตรรกะและเหตุผล
    """
    user_name = user_profile.get('name', 'เพื่อน')

    if "มีหนังสืออะไรบ้าง" in q_lower or "รายชื่อหนังสือ" in q_lower:
        print("✅ [Super Advisor] Responding with book list (Librarian task).")
        if not all_book_titles:
            return "ยังไม่มีข้อมูลหนังสือในระบบครับ"
        return "ตอนนี้ผมมีข้อมูลหนังสือดังนี้ครับ:\n- " + "\n- ".join(all_book_titles)

    if "มีหมวดหมู่อะไรบ้าง" in q_lower or "หมวดหมู่ทั้งหมด" in q_lower:
        print("✅ [Super Advisor] Responding with category list (Librarian task).")
        if not all_categories:
            return "ยังไม่มีข้อมูลหมวดหมู่ในระบบครับ"
        return "หมวดหมู่ทั้งหมดที่มีอยู่คือ:\n- " + "\n- ".join(all_categories)

    print("⏳ [Super Advisor] Searching for deep knowledge (RAG)...")
    query_embedding = embedder.encode(query, convert_to_tensor=True).cpu().numpy().astype('float32')
    _, indices = knowledge_index.search(query_embedding.reshape(1, -1), 20)
    relevant_keys = [str(idx) for idx in indices[0] if 0 <= idx < len(knowledge_entries)]
    context_from_books, _ = generate_context_func(relevant_keys, query, num_final_context=7)

    short_term_context = "\n".join([f"{role}: {content}" for role, content in short_term_memory])

    print("🧠 [Super Advisor] Constructing LOGIC-FOCUSED Master Prompt for Gemini...")
    master_prompt = f"""{persona_block}

    **[PART 1: CONTEXTUAL DATA - ข้อมูลประกอบการวิเคราะห์]**

    **1.1 Daily Context:**
    - วันนี้คือ: {daily_context['day_of_week_thai']}, {daily_context['full_date']}
    - เวลาปัจจุบัน: {daily_context['current_time']} น.

    **1.2 User Profile:**
    - ชื่อ: {user_name}

    **1.3 Recent Conversation (Short-term Memory):**
    <ประวัติล่าสุด>
    {short_term_context if short_term_context else "นี่คือการสนทนาแรก"}
    </ประวัติล่าสุด>
    
    **1.4 User's Latest Query:** "{query}"

    ---

    **[PART 2: KNOWLEDGE BASE - ข้อมูลดิบจากคลังความรู้]**

    **2.1 Relevant Information from Books (RAG):**
    <ข้อมูลอ้างอิง>
    {context_from_books}
    </ข้อมูลอ้างอิง>
    
    ---

    **[PART 3: YOUR MISSION - ภารกิจของคุณ]**

    คุณคือ "เฟิง", ที่ปรึกษาผู้ใช้ตรรกะและเหตุผลเป็นหลัก (Logic-Driven Consultant) ภารกิจของคุณคือการวิเคราะห์คำถามของผู้ใช้โดยใช้ข้อมูลจาก PART 1 และ PART 2 เพื่อสร้างคำตอบที่เฉียบคม, มีโครงสร้าง, และอ้างอิงหลักการได้อย่างชัดเจน โดยปฏิบัติตามกฎต่อไปนี้:

    **RULE #1: STRUCTURED REASONING (การให้เหตุผลเชิงโครงสร้าง)**
    - วิเคราะห์ปัญหาอย่างเป็นระบบ
    - หากเป็นไปได้ ให้เสนอทางเลือกหลายๆ ทาง พร้อมชี้แจงข้อดี-ข้อเสียของแต่ละทางเลือกตามหลักการที่อ้างอิงมา
    - สรุปใจความสำคัญในตอนท้ายเพื่อให้ผู้ใช้เห็นภาพรวมที่ชัดเจน

    **RULE #2: EVIDENCE-BASED SYNTHESIS (การสังเคราะห์โดยอิงหลักฐาน)**
    - **ถ้ามีข้อมูลใน <ข้อมูลอ้างอิง>:** จงใช้ข้อมูลนั้นเป็นแกนหลักในการตอบคำถามอย่างเคร่งครัด ห้ามแสดงความคิดเห็นส่วนตัวที่ไม่มีข้อมูลสนับสนุน
    - **ถ้า <ข้อมูลอ้างอิง> คือ "ไม่มีข้อมูลเฉพาะเจาะจง":** ให้ตอบอย่างตรงไปตรงมาว่า "เรื่องนี้ผมยังไม่มีข้อมูลที่เฉพาะเจาะจงจากคลังความรู้ครับ" และอาจจะถามคำถามกลับเพื่อช่วยให้ผู้ใช้จำกัดขอบเขตของปัญหาให้แคบลง เพื่อให้การค้นหาครั้งต่อไปมีประสิทธิภาพมากขึ้น

    **RULE #3: MAINTAIN A PROFESSIONAL PERSONA (คงบุคลิกของผู้เชี่ยวชาญ)**
    - ตอบในฐานะ "เฟิง" ที่ปรึกษาผู้สุขุมและยึดมั่นในหลักการ
    - ใช้ภาษาที่ชัดเจน ตรงไปตรงมา และเข้าใจง่าย
    - ไม่จำเป็นต้องปลอบใจหรือแสดงอารมณ์ร่วม แต่ให้มุ่งเน้นที่การให้ข้อมูลและแนวทางแก้ไขที่เป็นประโยชน์ที่สุด

    **คำตอบของคุณ (ในฐานะเฟิง):**
    """

    try:
        response = gemini_model.generate_content(master_prompt.strip(), generation_config=config)
        return clean_func(response.text)
    except Exception as e:
        error_text = str(e)
        if "429" in error_text and "quota" in error_text:
            return f"ขออภัยครับคุณ{user_name}, ตอนนี้โควต้า API ของผมเต็มแล้ว โปรดลองอีกครั้งในภายหลัง"
        else:
            print(f"❌ [ERROR] Super Advisor failed in Gemini API: {error_text}")
            return None