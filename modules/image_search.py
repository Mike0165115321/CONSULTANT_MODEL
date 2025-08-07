# File: modules/image_search.py

import os
import requests
from typing import Optional, Dict

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
UNSPLASH_API_URL = "https://api.unsplash.com/search/photos"

def search_for_image(query: str) -> Optional[Dict]:
    """
    ค้นหารูปภาพที่เกี่ยวข้องจาก Unsplash API

    Args:
        query (str): คำค้นหาสำหรับรูปภาพ (เช่น 'cat', 'stoicism philosophy')

    Returns:
        Optional[Dict]: Dictionary ที่มีข้อมูลรูปภาพที่เจอ หรือ None หากไม่เจอ/เกิดข้อผิดพลาด
                         ตัวอย่างผลลัพธ์: 
                         {
                             "url": "https://images.unsplash.com/...",
                             "description": "A cat sitting on a table.",
                             "photographer": "John Doe",
                             "profile_url": "https://unsplash.com/@johndoe"
                         }
    """
    if not UNSPLASH_ACCESS_KEY:
        print("❌ [Image Search] Error: UNSPLASH_ACCESS_KEY is not set in the .env file.")
        return None

    params = {
        'query': query,
        'per_page': 1,
        'orientation': 'landscape',
        'lang': 'en'
    }
    
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }

    try:
        print(f"🖼️  [Image Search] Searching for '{query}' on Unsplash...")
        response = requests.get(UNSPLASH_API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        results = data.get('results', [])

        if results:
            first_image = results[0]
            image_info = {
                "url": first_image['urls']['regular'],
                "description": first_image.get('alt_description', 'No description available.'),
                "photographer": first_image['user']['name'],
                "profile_url": first_image['user']['links']['html']
            }
            print(f"✅ [Image Search] Found image by {image_info['photographer']}")
            return image_info
        else:
            print(f"🟡 [Image Search] No results found for '{query}'.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ [Image Search] Error connecting to Unsplash API: {e}")
        return None
    except Exception as e:
        print(f"❌ [Image Search] An unexpected error occurred: {e}")
        return None