import requests
import urllib.parse
from typing import Dict, Any

HEADERS = {
    "User-Agent": "BookAgent/1.0 (contact@example.com)"
}

def search_wikipedia(query: str) -> str:
    """
    Tìm kiếm và lấy tóm tắt tác phẩm văn học hoặc tác giả trên Wikipedia Việt Nam.
    """
    search_query = urllib.parse.quote(query)
    
    # Thử tiếng Việt trước
    try:
        search_url = f"https://vi.wikipedia.org/w/api.php?action=opensearch&search={search_query}&limit=1&namespace=0&format=json"
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        search_data = response.json()
        
        if len(search_data) > 1 and len(search_data[1]) > 0:
            title = search_data[1][0]
            summary_url = f"https://vi.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
            summary_response = requests.get(summary_url, headers=HEADERS, timeout=10)
            summary_response.raise_for_status()
            summary_data = summary_response.json()
            
            extract = summary_data.get("extract", "")
            if extract:
                return f"Wikipedia Summary for '{title}': {extract}"
    except Exception:
        pass # Nếu tiếng Việt lỗi (404, timeout...), bỏ qua và thử tiếng Anh
        
    # Thử fallback sang Wikipedia tiếng Anh
    try:
        search_url_en = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={search_query}&limit=1&namespace=0&format=json"
        response_en = requests.get(search_url_en, headers=HEADERS, timeout=10)
        response_en.raise_for_status()
        search_data_en = response_en.json()
        
        if len(search_data_en) > 1 and len(search_data_en[1]) > 0:
            title_en = search_data_en[1][0]
            summary_url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title_en)}"
            summary_response_en = requests.get(summary_url_en, headers=HEADERS, timeout=10)
            summary_response_en.raise_for_status()
            summary_data_en = summary_response_en.json()
            
            extract_en = summary_data_en.get("extract", "")
            if extract_en:
                return f"Wikipedia (EN) Summary for '{title_en}': {extract_en}"
                
        return f"Không tìm thấy thông tin cho từ khóa '{query}' trên Wikipedia."
    except Exception as e:
        return f"Lỗi khi kết nối với Wikipedia API: {str(e)}"
