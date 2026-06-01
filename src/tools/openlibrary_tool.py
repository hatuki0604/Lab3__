import requests
import urllib.parse
from typing import List, Dict, Any

"""
# VERSION 1 (Bản cũ - God Tool):
# Lưu lại theo yêu cầu của user.

def recommend_openlibrary(query: str) -> str:
    '''
    Tìm kiếm và gợi ý các tác phẩm liên quan từ API OpenLibrary.
    Trả về danh sách tối đa 3 tác phẩm phù hợp.
    '''
    try:
        search_query = urllib.parse.quote(query)
        url = f"https://openlibrary.org/search.json?q={search_query}&limit=3"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        docs = data.get("docs", [])
        if not docs:
            return f"Không tìm thấy gợi ý sách nào trên OpenLibrary cho từ khóa '{query}'."
            
        recommendations = []
        for idx, doc in enumerate(docs):
            title = doc.get("title", "Không rõ tên")
            author_names = doc.get("author_name", ["Không rõ tác giả"])
            publish_year = doc.get("first_publish_year", "Không rõ năm")
            
            recommendations.append(
                f"{idx + 1}. '{title}' - Tác giả: {', '.join(author_names)} (Năm xuất bản lần đầu: {publish_year})"
            )
            
        return "Gợi ý sách tương tự từ OpenLibrary:\n" + "\n".join(recommendations)
        
    except Exception as e:
        return f"Lỗi khi kết nối với OpenLibrary API: {str(e)}"

def search_books_by_subject(subject: str) -> str:
    '''Tìm danh sách sách cùng chủ đề (truyền từng chủ đề riêng lẻ). Bản cũ không có filter.'''
    try:
        subject_safe = urllib.parse.quote(subject.lower())
        url = f"https://openlibrary.org/subjects/{subject_safe}.json?limit=5"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        works = data.get("works", [])
        if not works:
            return f"Không tìm thấy sách nào cho chủ đề '{subject}'."
            
        titles = [w.get("title", "Không rõ tên") for w in works]
        return f"Sách cùng chủ đề '{subject}': {', '.join(titles)}"
    except Exception as e:
        return f"Lỗi API: {str(e)}"
"""

# VERSION 2 (ReAct Pattern)

def search_book(query: str) -> str:
    """Tìm kiếm sách trên OpenLibrary để lấy Work ID."""
    try:
        search_query = urllib.parse.quote(query)
        url = f"https://openlibrary.org/search.json?q={search_query}&limit=1"
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                data = response.json()
                break
            except requests.exceptions.Timeout:
                if attempt == 2:
                    return "Lỗi API: Network Timeout sau 3 lần thử."
                continue
        
        docs = data.get("docs", [])
        if not docs:
            return f"Không tìm thấy sách cho từ khóa '{query}'."
            
        doc = docs[0]
        title = doc.get("title", "Không rõ tên")
        work_key = doc.get("key", "")
        if not work_key:
            return f"Tìm thấy sách '{title}' nhưng không có Work ID."
            
        return f"Tìm thấy sách: '{title}'. Work ID: {work_key}"
    except Exception as e:
        return f"Lỗi API: {str(e)}"

def get_book_subjects(work_key: str) -> str:
    """Lấy danh sách các chủ đề (subjects) của sách dựa vào Work ID."""
    try:
        work_key = work_key.strip()
        if not work_key.startswith("/"):
            if work_key.startswith("OL"):
                work_key = f"/works/{work_key}"
            else:
                work_key = f"/{work_key}"
                
        url = f"https://openlibrary.org{work_key}.json"
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                data = response.json()
                break
            except requests.exceptions.Timeout:
                if attempt == 2:
                    return "Lỗi API: Network Timeout sau 3 lần thử."
                continue
        
        subjects = data.get("subjects", [])
        if not subjects:
            return "Sách này không có chủ đề nào."
            
        PRIORITY_SUBJECTS = [
            "Fantasy", "Magic", "Wizards", "Adventure", "Young adult fiction",
            "Science Fiction", "Romance", "Mystery", "Historical Fiction", "Horror"
        ]
        
        selected = [s for s in subjects if s in PRIORITY_SUBJECTS]
        if not selected:
            selected = subjects[:3]
            
        return f"Các chủ đề chính: {', '.join(selected)}"
    except Exception as e:
        return f"Lỗi API: {str(e)}"

def search_books_by_subject(subject: str, exclude_title: str = "") -> str:
    """Tìm danh sách sách cùng chủ đề, có lọc tên sách gốc (programmatic filter)."""
    try:
        subject_safe = urllib.parse.quote(subject.lower())
        url = f"https://openlibrary.org/subjects/{subject_safe}.json?limit=5"
        for attempt in range(3):
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()
                data = response.json()
                break
            except requests.exceptions.Timeout:
                if attempt == 2:
                    return "Lỗi API: Network Timeout sau 3 lần thử."
                continue
        
        works = data.get("works", [])
        if not works:
            return f"Không tìm thấy sách nào cho chủ đề '{subject}'."
            
        titles = []
        for w in works:
            t = w.get("title", "Không rõ tên")
            if exclude_title and exclude_title.lower() in t.lower():
                continue
            titles.append(t)
            
        if not titles:
            return f"Không tìm thấy sách nào khác cho chủ đề '{subject}' (trừ sách gốc)."
            
        return f"Sách cùng chủ đề '{subject}': {', '.join(titles)}"
    except Exception as e:
        return f"Lỗi API: {str(e)}"

