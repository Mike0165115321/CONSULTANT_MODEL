# File: modules/system_tools.py (Refactored with a Central Handler)

import pyperclip
import os
import subprocess
import platform
import webbrowser
import re
from typing import Optional

current_os = platform.system().lower()
if current_os == 'windows':
    try:
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        print("[System Tools] pycaw loaded successfully for Windows volume control.")
    except ImportError:
        print("[System Tools] WARNING: pycaw or comtypes not found. Volume control on Windows will be disabled.")
        AudioUtilities = None
else:
    AudioUtilities = None
    print(f"[System Tools] Running on {current_os}. Windows-specific features (pycaw) are disabled.")

def _read_clipboard():
    try:
        content = pyperclip.paste()
        return f"ข้อความในคลิปบอร์ดคือ:\n---\n{content}\n---" if content else "ในคลิปบอร์ดไม่มีข้อความอยู่ครับ"
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการอ่านคลิปบอร์ด: {e}")
        return "ขออภัยครับ เกิดข้อผิดพลาดบางอย่างในการเข้าถึงคลิปบอร์ด"

def _write_to_clipboard(text: str):
    if not isinstance(text, str): return "ข้อมูลที่ส่งมาไม่ใช่ข้อความครับ"
    try:
        pyperclip.copy(text)
        return "เรียบร้อยครับ! ข้อความถูกคัดลอกไปยังคลิปบอร์ดแล้ว"
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเขียนลงคลิปบอร์ด: {e}")
        return "ขออภัยครับ เกิดข้อผิดพลาดบางอย่างในการเขียนลงคลิปบอร์ด"

def _open_application(app_name: str) -> str:
    app_name_lower = app_name.lower().strip()
    command = ""
    thai_to_eng_app = {
        'เครื่องคิดเลข': 'calculator',
        'โน้ตแพด': 'notepad',
        'โครม': 'chrome',
        'เบราว์เซอร์': 'browser',
        'เวิร์ด': 'word',
        'เอ็กเซล': 'excel',
        'พาวเวอร์พอยท์': 'powerpoint',
        'สปอติฟาย': 'spotify',
        'วีเอสโค้ด': 'vscode',
    }
    app_map = {
        'notepad': {'windows': 'notepad.exe', 'darwin': 'open -a TextEdit', 'linux': 'gedit'},
        'calculator': {'windows': 'calc.exe', 'darwin': 'open -a Calculator', 'linux': 'gnome-calculator'},
        'browser': {'windows': r'start chrome', 'darwin': 'open -a "Google Chrome"', 'linux': 'google-chrome-stable'},
        'chrome': {'windows': r'start chrome', 'darwin': 'open -a "Google Chrome"', 'linux': 'google-chrome-stable'},
        'vscode': {'windows': 'code', 'darwin': 'code', 'linux': 'code'},
        'spotify': {'windows': 'spotify', 'darwin': 'open -a Spotify', 'linux': 'spotify'},
        'word': {'windows': 'winword'},
        'excel': {'windows': 'excel'},
        'powerpoint': {'windows': 'powerpnt', 'darwin': 'open -a "Microsoft PowerPoint"'},
    }
    app_key = thai_to_eng_app.get(app_name_lower, app_name_lower)
    if app_key in app_map:
        command = app_map[app_key].get(current_os)
    if not command:
        return f"ขออภัยครับ ผมไม่รู้จักวิธีเปิด '{app_name}' บนระบบปฏิบัติการของคุณ ({current_os})"
    try:
        print(f"[System Tools] Executing command: {command}")
        subprocess.Popen(command, shell=True)
        return f"กำลังเปิด {app_name} ให้ครับ..."
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเปิดแอปพลิเคชัน: {e}")
        return f"ขออภัยครับ เกิดข้อผิดพลาดบางอย่างขณะพยายามเปิด {app_name}"

def _open_website(site_name: str) -> str:
    site_map = {
        'youtube': 'https://www.youtube.com', 'facebook': 'https://www.facebook.com',
        'google': 'https://www.google.com', 'gmail': 'https://mail.google.com',
        'github': 'https://www.github.com'
    }
    url = site_map.get(site_name.lower().strip())
    if not url:
        return f"ขออภัยครับ ผมไม่รู้จักเว็บไซต์ '{site_name}'"
    try:
        print(f"[System Tools] Opening website: {url}")
        webbrowser.open_new_tab(url)
        return f"กำลังเปิด {site_name.capitalize()} ให้ในเบราว์เซอร์ครับ"
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเปิดเว็บไซต์: {e}")
        return f"ขออภัยครับ เกิดข้อผิดพลาดขณะพยายามเปิด {site_name}"

def _set_system_volume(level: int) -> str:
    if not 0 <= level <= 100:
        return "โปรดระบุระดับเสียงระหว่าง 0 ถึง 100 ครับ"
    print(f"[System Tools] Setting volume to {level}% on {current_os}")
    try:
        if current_os == 'windows':
            if not AudioUtilities: raise NotImplementedError("Volume control disabled (pycaw missing).")
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        elif current_os == 'darwin':
            subprocess.run(['osascript', '-e', f'set volume output volume {level}'])
        elif current_os == 'linux':
            subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{level}%'])
        return f"ปรับระดับเสียงเป็น {level}% แล้วครับ"
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการปรับระดับเสียง: {e}")
        return f"ขออภัยครับ เกิดข้อผิดพลาดขณะพยายามปรับระดับเสียงบน {current_os}"

def _get_current_volume() -> Optional[int]:
    try:
        if current_os == 'windows':
            if not AudioUtilities: return None
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = interface.QueryInterface(IAudioEndpointVolume)
            return round(volume.GetMasterVolumeLevelScalar() * 100)
        elif current_os == 'darwin':
            result = subprocess.run(['osascript', '-e', 'output volume of (get volume settings)'], capture_output=True, text=True)
            return int(result.stdout.strip())
        elif current_os == 'linux':
            result = subprocess.run(['amixer', '-D', 'pulse', 'sget', 'Master'], capture_output=True, text=True)
            match = re.search(r"\[(\d{1,3})%\]", result.stdout)
            if match: return int(match.group(1))
        return None
    except Exception as e:
        print(f"❌ [System Tools] Error getting current volume: {e}")
        return None

def _change_volume(direction: str, amount: int = 10) -> str:
    current_level = _get_current_volume()
    if current_level is None:
        return "ขออภัยครับ ผมไม่สามารถตรวจสอบระดับเสียงปัจจุบันได้"
        
    if direction == "increase":
        new_level = min(current_level + amount, 100)
        print(f"🔊 Increasing volume from {current_level}% to {new_level}%")
        return _set_system_volume(new_level)
    elif direction == "decrease":
        new_level = max(current_level - amount, 0)
        print(f"🔉 Decreasing volume from {current_level}% to {new_level}%")
        return _set_system_volume(new_level)
    else:
        return "ขออภัยครับ ไม่รู้จักทิศทางการปรับเสียงนั้น"

# ==============================================================================
# Public Handler Function (ฟังก์ชันหลักสำหรับเรียกจาก main.py)
# ==============================================================================

def handle_system_tool_query(query: str) -> Optional[str]:
    """
    ตรวจสอบ query และเรียกใช้ฟังก์ชันเครื่องมือที่เหมาะสม
    คืนค่าเป็น string คำตอบถ้าตรงกับเครื่องมือ, คืนค่า None ถ้าไม่ตรง
    """
    q_lower = query.lower()

    # --- Volume Control ---
    set_volume_match = re.search(r"(ปรับ|ตั้งค่า)\s*เสียง\s*(?:เป็น|ไปที่)?\s*(\d{1,3})", q_lower)
    if set_volume_match:
        return _set_system_volume(int(set_volume_match.group(2)))
    
    if "เพิ่มเสียง" in q_lower:
        return _change_volume("increase")
    
    if "ลดเสียง" in q_lower:
        return _change_volume("decrease")

    # --- Application & Website Control ---
    # รองรับชื่อแอปภาษาไทยและอังกฤษ
    open_app_match = re.search(r"เปิด(โปรแกรม|แอป)?\s+([\wก-๙_.-]+)", q_lower)
    if open_app_match:
        entity_name = open_app_match.group(2)
        if entity_name in ['youtube', 'facebook', 'google', 'gmail', 'github']:
            return _open_website(entity_name)
        else:
            return _open_application(entity_name)
    
    open_site_match = re.search(r"เปิดเว็บ\s+(.+)", q_lower)
    if open_site_match:
        return _open_website(open_site_match.group(1))

    # --- Clipboard Control ---
    write_clip_match = re.search(r"(คัดลอก|copy)\s*(ข้อความ)?\s*['\"](.+)['\"]", query, re.IGNORECASE)
    if write_clip_match:
        return _write_to_clipboard(write_clip_match.group(3))
        
    if "อ่านคลิปบอร์ด" in q_lower or "ในคลิปบอร์ดมีอะไร" in q_lower:
        return _read_clipboard()

    # ถ้าไม่มีคำสั่งใดตรงกับเงื่อนไข
    return None