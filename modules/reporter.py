# File: modules/reporter.py (Revised for specific time)

from datetime import datetime

def handle_reporter_query(query_lower: str, daily_context: dict, user_name: str) -> str:
    """
    สร้างคำตอบเกี่ยวกับข้อมูลวัน-เวลาปัจจุบัน โดยแยกตามคำถาม
    """
    if "กี่โมง" in query_lower or "เวลาอะไร" in query_lower:
        current_time = daily_context.get('current_time', 'ไม่สามารถตรวจสอบได้')
        return f"ตอนนี้เวลา {current_time} น. ครับคุณ{user_name}"

    day_of_week = daily_context.get('day_of_week_thai', 'ไม่ทราบวัน')
    full_date_str = daily_context.get('full_date', '')
    special_event = daily_context.get('special_event')

    response_parts = [f"ครับคุณ{user_name}, วันนี้คือ{day_of_week}"]

    if full_date_str:
        try:
            date_obj = datetime.strptime(full_date_str, "%Y-%m-%d")
            thai_months = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]
            formatted_date = f"วันที่ {date_obj.day} {thai_months[date_obj.month - 1]} พ.ศ. {date_obj.year + 543}"
            response_parts.append(f"ตรงกับ{formatted_date}")
        except ValueError:
            response_parts.append(f"ตรงกับวันที่ {full_date_str}")
    
    if special_event:
        response_parts.append(f"และยังเป็น{special_event}ด้วยครับ")

    return " ".join(response_parts)