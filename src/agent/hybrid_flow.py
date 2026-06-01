import re
import time
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.tools.books_dataset import search_local_db
from src.tools.wikipedia_tool import search_wikipedia
from src.tools.openlibrary_tool import search_book, get_book_subjects, search_books_by_subject
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

class HybridBookAssistant:
    """
    Hệ thống trợ lý Hybrid:
    - Tầng 1: Kiểm tra Local DB trước. Nếu có, trả lời ngay qua Chatbot tốc độ cao.
    - Tầng 2: Nếu không thấy, kích hoạt ReAct Agent gọi Wikipedia và OpenLibrary API.
    """
    def __init__(self, llm: LLMProvider, max_steps: int = 10):
        self.llm = llm
        self.max_steps = max_steps
        self.tools = {
            "search_wikipedia": search_wikipedia,
            "search_book": search_book,
            "get_book_subjects": get_book_subjects,
            "search_books_by_subject": search_books_by_subject
        }

    def get_agent_system_prompt(self) -> str:
        return """You are a STRICT professional literature assistant.
You have access to the following tools:
- search_wikipedia(query): Searches Wikipedia for summaries of books, authors, or literary works.
- search_book(query): Searches OpenLibrary to find the book and return its Work ID.
- get_book_subjects(work_key): Gets priority subjects for a book using its Work ID.
- search_books_by_subject(subject): Finds other books belonging to the same subject.

Khi người dùng hỏi về sách:
1. Suy nghĩ (Thought) MỘT LẦN DUY NHẤT để lập kế hoạch ở bước đầu tiên.
2. Thực hiện tuần tự các công cụ sau (phải đợi Observation trả về trước khi gọi công cụ tiếp theo):
   - search_wikipedia(title)
   - search_book(title)
   - get_book_subjects(work_id)
   - search_books_by_subject(subject đầu tiên)
3. KHÔNG tạo Thought mới sau mỗi tool. Bắt đầu từ tool thứ 2, chỉ in ra Action.
4. Không thử subject khác. Chỉ dùng subject đầu tiên.
5. Sau khi có đủ dữ liệu từ 4 công cụ trên thì trả lời luôn bằng Final Answer.

Ví dụ định dạng BẮT BUỘC:

Thought: Tôi cần lấy thông tin tác phẩm và tìm sách tương tự...
Action: search_wikipedia(Harry Potter)

(Chờ Observation)

Action: search_book(Harry Potter)

(Chờ Observation)

Action: get_book_subjects(OL123W)

(Chờ Observation)

Action: search_books_by_subject(Fantasy)

(Chờ Observation)

Final Answer: [Tổng hợp câu trả lời]

CRITICAL ERROR HANDLING:
- If a tool returns a "Network Timeout", DO NOT retry. Output Final Answer based on what you have.
- If a step completely fails, output Final Answer apologizing.
"""

    def _execute_tool(self, action_str: str, user_input: str = "") -> str:
        """
        Parse và thực thi action dạng: tool_name(query)
        """
        match = re.match(r"(\w+)\((.+)\)", action_str.strip())
        if not match:
            return "Error: Invalid Action format. Must be tool_name(query)."
            
        tool_name = match.group(1)
        query = match.group(2).strip(" '\"")
        
        if tool_name in self.tools:
            logger.log_event("TOOL_CALL", {"tool": tool_name, "query": query})
            start_time = time.time()
            
            # Pass user_input to filter out the original book
            if tool_name == "search_books_by_subject" and user_input:
                result = self.tools[tool_name](query, exclude_title=user_input)
            else:
                result = self.tools[tool_name](query)
                
            duration_ms = int((time.time() - start_time) * 1000)
            logger.log_event("TOOL_RESULT", {"tool": tool_name, "duration_ms": duration_ms})
            return result
        else:
            return f"Error: Tool '{tool_name}' not found."

    def _get_local_db_context(self, user_input: str) -> Optional[str]:
        # Trích xuất các từ khóa đặc trưng trong mock dataset
        local_keywords = ["chí phèo", "lão hạc", "đời thừa", "sống chết mặc bay", "tinh thần thể dục", 
                          "vợ nhặt", "làng", "chiếc lược ngà", "rừng xà nu", "vợ chồng a phủ", 
                          "nam cao", "phạm duy tốn", "nguyễn công hoan", "kim lân", 
                          "nguyễn quang sáng", "nguyễn trung thành", "tô hoài"]
        
        input_lower = user_input.lower()
        has_local_hit = any(keyword in input_lower for keyword in local_keywords)
        
        if not has_local_hit:
            return None
            
        # Tìm kiếm thông tin chi tiết trong Mock DB
        db_results = []
        for kw in local_keywords:
            if kw in input_lower:
                db_results.extend(search_local_db(kw))
        
        # Loại bỏ kết quả trùng lặp
        seen_titles = set()
        unique_results = []
        for b in db_results:
            if b["title"] not in seen_titles:
                seen_titles.add(b["title"])
                unique_results.append(b)
        
        if not unique_results:
            return None
            
        db_context = "\n".join([
            f"- Tác phẩm: {b['title']} | Tác giả: {b['author']} | Năm sáng tác: {b['year']} | Thể loại: {b['genre']} | Khu vực: {b['region']}\n  Tóm tắt: {b['summary']}"
            for b in unique_results
        ])
        return db_context

    def run_chatbot_baseline(self, user_input: str) -> Dict[str, Any]:
        """
        Pipeline 1: Chỉ tìm trong Local DB. Nếu không có thì từ chối trả lời.
        """
        logger.log_event("CHATBOT_START", {"input": user_input})
        start_time = time.time()
        
        db_context = self._get_local_db_context(user_input)
        
        if db_context:
            prompt = f"Dưới đây là thông tin sách từ cơ sở dữ liệu nội bộ:\n{db_context}\n\nHãy trả lời câu hỏi: '{user_input}'. Không bịa đặt ngoài dữ liệu này."
            response = self.llm.generate(prompt, system_prompt="You are a precise Vietnamese Literature Assistant.")
            latency_ms = int((time.time() - start_time) * 1000)
            
            tracker.track_request(
                provider=response.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=response.get("usage", {}),
                latency_ms=latency_ms
            )
            answer = response["content"]
            tokens = response.get("usage", {}).get("total_tokens", 0)
        else:
            latency_ms = int((time.time() - start_time) * 1000)
            answer = "Tôi không có thông tin về câu hỏi này trong cơ sở dữ liệu hệ thống."
            tokens = 0
        
        logger.log_event("CHATBOT_END", {"latency_ms": latency_ms})
        
        return {
            "answer": answer,
            "latency_ms": latency_ms,
            "tokens": tokens,
            "mode": "Local DB Only (Pipeline 1)"
        }

    def run_hybrid_flow(self, user_input: str) -> Dict[str, Any]:
        """
        Chạy luồng Hybrid hoàn chỉnh.
        """
        logger.log_event("HYBRID_START", {"input": user_input})
        start_eval_time = time.time()
        
        # --- CHẾ ĐỘ 2: REACT AGENT ONLY ---
        logger.log_event("REACT_AGENT_ACTIVATED", {"reason": "User selected Mode 2"})
        
        current_history = []
        steps = 0
        total_tokens = 0
        
        # Khởi đầu prompt cho Agent
        agent_prompt = f"User Question: {user_input}\n"
        
        while steps < self.max_steps:
            # Chuẩn bị toàn bộ ngữ cảnh truyền vào LLM bao gồm cả lịch sử suy nghĩ
            prompt_context = agent_prompt + "\n".join(current_history)
            if current_history:
                prompt_context += "\n"
                
            start_time = time.time()
            response = self.llm.generate(prompt_context, system_prompt=self.get_agent_system_prompt())
            latency_ms = int((time.time() - start_time) * 1000)
            
            usage = response.get("usage", {})
            total_tokens += usage.get("total_tokens", 0)
            
            tracker.track_request(
                provider=response.get("provider", "unknown"),
                model=self.llm.model_name,
                usage=usage,
                latency_ms=latency_ms
            )
            
            content = response["content"].strip()
            
            # CHỐNG HALLUCINATION: Ép dừng nếu LLM cố tự sinh ra Observation
            if "Observation:" in content:
                content = content.split("Observation:")[0].strip()
                
            logger.log_event("AGENT_THOUGHT_ACTION", {"step": steps + 1, "content": content})
            
            # IN BƯỚC SUY NGHĨ (THOUGHT & ACTION)
            print(f"\n[Bước {steps + 1}] 🤔 Agent đang lập luận và chọn hành động:")
            print(">>> " + content.replace("\n", "\n>>> "))
            
            # Thêm suy nghĩ của Agent vào lịch sử
            current_history.append(content)
            
            # Trích xuất Action
            action_match = re.search(r"Action:\s*(.+)", content)
            
            if action_match:
                action_str = action_match.group(1).strip()
                # Thực thi tool
                observation = self._execute_tool(action_str, user_input)
                logger.log_event("AGENT_OBSERVATION", {"step": steps + 1, "observation": observation})
                
                # IN KẾT QUẢ QUAN SÁT (OBSERVATION)
                print(f"\n[Bước {steps + 1}] 👁️ Kết quả quan sát nhận lại từ API mạng:")
                print(">>> " + observation.replace("\n", "\n>>> "))
                print("-" * 50)
                
                # Thêm kết quả quan sát
                current_history.append(f"Observation: {observation}")
            
            # Kiểm tra nếu có câu trả lời cuối cùng
            final_match = re.search(r"Final Answer:\s*(.+)", content, re.DOTALL)
            if final_match:
                final_answer = final_match.group(1).strip()
                total_duration = int((time.time() - start_eval_time) * 1000)
                logger.log_event("HYBRID_END", {"mode": "ReAct Agent Only", "latency_ms": total_duration})
                
                return {
                    "answer": final_answer,
                    "latency_ms": total_duration,
                    "tokens": total_tokens,
                    "mode": "ReAct Agent Only"
                }
                
            steps += 1
            
        # Nếu đạt max steps mà chưa có Final Answer -> Trả về kết quả thô
        total_duration = int((time.time() - start_eval_time) * 1000)
        logger.log_event("HYBRID_TIMEOUT", {"steps": steps})
        return {
            "answer": "Không thể hoàn thành câu trả lời trong giới hạn bước cho phép.",
            "latency_ms": total_duration,
            "tokens": total_tokens,
            "mode": "ReAct Agent Only (Timeout)"
        }
