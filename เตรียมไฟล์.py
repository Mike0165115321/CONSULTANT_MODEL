import os
import json
import faiss
import numpy as np
import sys
from sentence_transformers import SentenceTransformer

def load_data(data_folder):
    texts = []
    mapping = {}
    idx = 0

    if not os.path.exists(data_folder):
        print(f"❌ โฟลเดอร์ '{data_folder}' ไม่พบ")
        return texts, mapping

    for filename in sorted(os.listdir(data_folder)):
        if not filename.endswith(".jsonl"): continue

        path = os.path.join(data_folder, filename)
        print(f"🔄 กำลังประมวลผลไฟล์: {filename}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip(): continue
                    
                    try:
                        item = json.loads(line)
                        content = item.get("content", "").strip()

                        if content:
                            book = item.get("book_title", "ไม่ระบุ").strip()
                            category = item.get("category", "ไม่ระบุหมวดหมู่").strip()
                            chapter = item.get("chapter_title", "").strip()
                            title = item.get("title", "").strip()
                            
                            context_parts = [f"จากหนังสือ '{book}'", f"หมวดหมู่ '{category}'"]
                            if chapter: context_parts.append(f"บทที่ว่าด้วย '{chapter}'")
                            if title: context_parts.append(f"หัวข้อ '{title}'")
                            
                            embedding_text = ", ".join(context_parts) + f": {content}"
                            
                            texts.append(embedding_text)
                            
                            mapped_item = item.copy()
                            mapped_item['embedding_text'] = embedding_text
                            mapping[str(idx)] = mapped_item
                            idx += 1
                        else:
                            print(f"  ❗ ไฟล์ '{filename}' บรรทัดที่ {line_num}: ไม่พบ 'content' ที่จะใช้ได้")

                    except json.JSONDecodeError as e:
                        print(f"  ❌ ไฟล์ '{filename}' บรรทัดที่ {line_num} อ่าน JSON ไม่ได้: {e}")
        except Exception as e:
            print(f"❌ ไม่สามารถเปิดหรืออ่านไฟล์ '{filename}' ได้: {e}")

    return texts, mapping

def create_faiss_index(texts, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
    model = SentenceTransformer(model_name)
    print("\n⏳ กำลังสร้าง Embeddings จากข้อความทั้งหมด (อาจใช้เวลาสักครู่)...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True).astype("float32")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def save_index_and_mapping(index, mapping, index_folder="./index"):
    os.makedirs(index_folder, exist_ok=True)
    faiss_path = os.path.join(index_folder, "faiss.index")
    mapping_path = os.path.join(index_folder, "mapping.json")
    print(f"\n💾 กำลังบันทึก Index ไปที่ '{faiss_path}'...")
    faiss.write_index(index, faiss_path)
    print(f"💾 กำลังบันทึก Mapping ไปที่ '{mapping_path}'...")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    data_folder = "data"
    index_output_folder = "./index"
    
    if not os.path.exists(data_folder):
        print(f"❌ โฟลเดอร์ '{data_folder}' ไม่พบ")
        sys.exit(1)

    if not os.path.exists(index_output_folder):
        os.makedirs(index_output_folder)
        print(f"📁 สร้างโฟลเดอร์ '{index_output_folder}' แล้ว")

    print("\n--- เริ่มกระบวนการสร้าง Index ---")
    texts, mapping = load_data(data_folder)

    if not texts:
        print("❌ ไม่มีข้อความที่ถูกต้องให้สร้าง Index ได้, จบการทำงาน")
        sys.exit(1)

    print(f"\n📦 พบข้อความสำหรับสร้าง Index ทั้งหมด: {len(texts)} รายการ")
    index = create_faiss_index(texts)
    save_index_and_mapping(index, mapping)
    print(f"\n✅ สร้าง faiss.index และ mapping.json ใหม่เรียบร้อยแล้ว!")