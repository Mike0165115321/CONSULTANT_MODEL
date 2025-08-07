import json
import os

entries = [

]

# เขียนไฟล์ .jsonl
filename = "data/Steve Jobs.jsonl"
with open(filename, "w", encoding="utf-8") as f:
    for entry in entries:
        json_line = json.dumps(entry, ensure_ascii=False)
        f.write(json_line + "\n")

print(f"✅ สร้างไฟล์ .jsonl สำเร็จ: {filename}")