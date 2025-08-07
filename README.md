# 🧠 Personal AI Consultant Model

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**โมเดลที่ปรึกษาส่วนบุคคล (Personal Consultant Model)** คือ AI Assistant ที่ทำหน้าที่เป็น "สมองกลหลัก" เน้นการให้คำปรึกษาเชิงลึกจากฐานความรู้ (หนังสือ) และสามารถทำงานตามคำสั่งเสริมต่างๆ ผ่านหน้าเว็บอินเตอร์เฟสที่รองรับการสั่งงานด้วยเสียง

---

## ✨ คุณสมบัติหลัก (Key Features)

- **ที่ปรึกษาอัจฉริยะ (Super Advisor):** ใช้เทคนิค RAG (Retrieval-Augmented Generation) ร่วมกับโมเดล Gemini เพื่อค้นหาข้อมูลจากฐานความรู้หนังสือและนำมาสังเคราะห์เป็นคำตอบที่ลึกซึ้ง
- **ระบบความจำระยะสั้น:** จดจำบทสนทนาล่าสุดเพื่อให้การพูดคุยต่อเนื่องและเป็นธรรมชาติ โดยใช้ฐานข้อมูล SQLite
- **ชุดเครื่องมือเสริม (Tool-Based Functions):**
  - **Reporter:** รายงานวัน/เวลาปัจจุบัน
  - **System Tools:** ควบคุม OS พื้นฐาน (เช่น เปิดโปรแกรม, จัดการ Clipboard)
  - **Image Search:** ค้นหารูปภาพจากอินเทอร์เน็ตผ่าน Unsplash API
- **ตอบกลับด่วน (Quick Responses):** มีคลังคำตอบสำเร็จรูปสำหรับคำถามง่ายๆ เพื่อการตอบสนองที่รวดเร็ว
- **Web Interface:** หน้าเว็บสำหรับโต้ตอบกับ AI รองรับ:
  - การพิมพ์ข้อความ
  - การสั่งงานด้วยเสียง (Speech-to-Text)
  - การอ่านออกเสียงคำตอบ (Text-to-Speech)

---

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)

- **Backend:** FastAPI, Uvicorn
- **AI & Machine Learning:** Google Gemini, FAISS (Vector Search), Sentence-Transformers
- **Frontend:** HTML, CSS, JavaScript (Web Speech API)
- **Database:** SQLite
- **Development:** Python 3.10+, Visual Studio Code, WSL (Ubuntu)

---

## 🚀 การติดตั้งและใช้งาน (Installation & Usage)

ทำตามขั้นตอนต่อไปนี้เพื่อรันโปรเจกต์บนเครื่องของคุณ

**1. Clone Repository:**
```bash
git clone https://github.com/Mike0165115321/CONSULTANT_MODEL.git
cd CONSULTANT_MODEL

2. สร้างและเปิดใช้งาน Virtual Environment:

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
# สร้าง venv
python3 -m venv venv

# เปิดใช้งาน (สำหรับ Linux/WSL)
source venv/bin/activate

3. ติดตั้ง Dependencies:

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
pip install -r requirements.txt

4. ตั้งค่า Environment Variables:

สร้างไฟล์ชื่อ .env ในโฟลเดอร์หลักของโปรเจกต์

เพิ่ม API Keys ของคุณลงในไฟล์ .env ดังนี้:

code
Env
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
UNSPLASH_ACCESS_KEY="YOUR_UNSPLASH_ACCESS_KEY_HERE"

5. เตรียมฐานข้อมูลความรู้:

รันสคริปต์เพื่อสร้าง Vector Index จากข้อมูลหนังสือในโฟลเดอร์ data/

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
python เตรียมไฟล์.py

6. รันแอปพลิเคชัน:

code
Bash
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
uvicorn main:app --reload

เปิดเว็บเบราว์เซอร์แล้วไปที่ http://127.0.0.1:8000

🏛️ สถาปัตยกรรมและโฟลว์การทำงาน (Architecture & Flow)

ระบบถูกออกแบบให้มีการประมวลผลเป็นลำดับชั้น (Flow) เพื่อประสิทธิภาพสูงสุด:

Flow 0-0.5 (Quick Response): ตรวจจับคำถามง่ายๆ และตอบกลับทันที

Flow 1-4 (Tool Use): หากเป็นคำสั่งเฉพาะทาง (เช็คเวลา, ค้นหารูป, ควบคุม OS) ระบบจะเรียกใช้โมดูลที่เกี่ยวข้อง

Flow 5 (Super Advisor): หากไม่ใช่คำสั่งข้างต้น คำถามจะถูกส่งต่อไปยัง "สมองกลหลัก" เพื่อทำการค้นหาข้อมูลเชิงลึก (RAG) และสังเคราะห์เป็นคำตอบ

code
Code
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
User Query -> [main.py] -> Quick Response? -> Tool? -> [super_advisor.py] -> Gemini -> Response

📂 โครงสร้างโปรเจกต์ (Project Structure)
code
Code
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
CONSULTANT_MODEL/
├── data/             # ข้อมูลดิบ, โปรไฟล์ผู้ใช้/AI
├── index/            # ฐานข้อมูล FAISS ที่สร้างขึ้น (ถูก ignore โดย .gitignore)
├── modules/          # เครื่องมือเสริมของ AI (reporter, image_search, etc.)
├── web/              # Frontend (HTML, CSS, JS)
├── 🛠️/               # (โฟลเดอร์สมมติ) สคริปต์สำหรับจัดการข้อมูล
│
├── .env              # ไฟล์เก็บ API Keys (ต้องสร้างเอง)
├── .gitignore        # ไฟล์ที่ Git ต้องเมิน
├── ai_bot.py         # ห้องเครื่อง: โหลดโมเดลและจัดการทรัพยากร
├── main.py           # FastAPI app และตัวควบคุม Flow หลัก
├── quick_responses.py# คลังคำตอบสำเร็จรูป
└── requirements.txt  # รายการแพ็คเกจที่ต้องใช้
📄 License

โปรเจกต์นี้อยู่ภายใต้ลิขสิทธิ์ของ MIT License - ดูรายละเอียดเพิ่มเติมได้ที่ไฟล์ LICENSE.

IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END

#### **ขั้นตอนที่ 3: บันทึกและอัปโหลดขึ้น GitHub**

หลังจากวางเนื้อหาและ **Save** ไฟล์ `README.md` เรียบร้อยแล้ว ให้กลับไปที่ **Terminal** แล้วรัน 3 คำสั่งสุดท้ายนี้:

```bash
# 1. เตรียมไฟล์ README.md ที่เพิ่มเข้ามาใหม่
git add README.md

# 2. บันทึกการเปลี่ยนแปลง
git commit -m "docs: Create comprehensive project README from blueprint"

# 3. อัปเดตขึ้น GitHub
git push

