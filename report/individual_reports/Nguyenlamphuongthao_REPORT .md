# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Nguyen Lam Phuong Thao
- **Student ID**: 2A202600873
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/tools/openlibrary_tool.py`, `src/tools/wikipedia_tool.py`, `src/agent/hybrid_flow.py`, `tests/run_eval.py`
- **Code Highlights**:
  - Tôi tham gia thiết kế lại luồng OpenLibrary từ kiểu "God Tool" sang bộ tool modular trong `src/tools/openlibrary_tool.py`. Ở version cũ, toàn bộ logic bị dồn vào một hàm `recommend_openlibrary(query)`. Ở version mới, tool được tách thành `search_book(query)`, `get_book_subjects(work_key)`, và `search_books_by_subject(subject, exclude_title="")`. Cách tách này giúp agent có thể thực hiện đúng chuỗi ReAct: tìm sách -> lấy Work ID -> lấy subject -> gợi ý sách tương tự.
  - Tôi bổ sung guardrail cho OpenLibrary ở `src/tools/openlibrary_tool.py`: retry 3 lần cho các request timeout (`for attempt in range(3)`) và chuẩn hóa `work_key` trong `get_book_subjects()` để tránh lỗi URL khi LLM chỉ trả về `OL...W` mà quên tiền tố `/works/`.
  - Tôi bổ sung cơ chế fallback đa ngôn ngữ trong `src/tools/wikipedia_tool.py`. Luồng hiện tại thử Wikipedia tiếng Việt trước, nếu không lấy được summary thì chuyển sang Wikipedia tiếng Anh. Nhờ đó các tác phẩm nước ngoài như *War and Peace* vẫn có cơ hội được agent xử lý thay vì dừng ở `PageError` hoặc lỗi không tìm thấy trang tiếng Việt.
  - Tôi tham gia tối ưu prompt điều khiển agent trong `src/agent/hybrid_flow.py`, đặc biệt là `get_agent_system_prompt()`. Prompt được ép theo dạng "1 Thought duy nhất ở bước đầu, các bước sau chỉ được Action", đồng thời khóa luôn thứ tự tool và quy tắc dừng khi đã đủ dữ liệu.
  - Tôi thêm guardrail chống ảo giác trong `src/agent/hybrid_flow.py` bằng đoạn cắt chuỗi khi LLM tự sinh ra `Observation:`. Mục tiêu là buộc agent phải chờ tool thực thi thật thay vì tự bịa observation trong cùng một lượt sinh.
  - Tôi sử dụng bộ `test prompts` trong `tests/run_eval.py` để kiểm tra hành vi của `Chatbot Baseline` và `Hybrid Flow`, đồng thời tổng hợp thêm benchmark trọng tâm với truy vấn `"The Hobbit – summary and similar books"` để so sánh rõ sự khác biệt giữa baseline, Gemini, GPT-4o, và local Phi-3.
- **Code References**: `src/tools/openlibrary_tool.py` (comment `# VERSION 1` và toàn bộ V2 tool chain), `src/tools/wikipedia_tool.py` (fallback vi -> en), `src/agent/hybrid_flow.py` (`get_agent_system_prompt()`, anti-hallucination `if "Observation:" in content`), `tests/run_eval.py` (5 test cases dùng cho comparison).
- **Documentation**: Phần tôi làm tác động trực tiếp vào vòng lặp ReAct theo cách sau: LLM trong `HybridBookAssistant.run_hybrid_flow()` sinh `Thought/Action`, Python parse `Action`, gọi tool tương ứng, nhận `Observation`, rồi đưa observation ngược lại vào context cho bước kế tiếp. Việc modular hóa tool và thêm guardrail làm cho quan sát môi trường sạch hơn, ít lỗi hơn, và giúp agent có khả năng lập luận từng bước thay vì trả lời một phát như chatbot.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Một failure điển hình xuất hiện khi chạy local model qua Ollama ở chế độ Hybrid. Agent bị lặp lại cùng một hướng suy nghĩ và gọi lại cùng một tool thay vì tiến sang bước tiếp theo, sau đó kết thúc bằng `HYBRID_TIMEOUT`.
- **Log Source**: File `logs/2026-06-01.log`. Ví dụ ở phần xử lý truy vấn `"Tôi muốn tìm thông tin tác phẩm 'Tắt đèn'..."`, log ghi:
  - `AGENT_THOUGHT_ACTION` step 1 -> `Action: search_wikipedia(Ngô Tất Tố)`
  - `AGENT_OBSERVATION` step 1 -> nhận summary từ Wikipedia
  - `AGENT_THOUGHT_ACTION` step 2 -> tiếp tục `Action: search_wikipedia(Ngô Tất Tố)`
  - `HYBRID_TIMEOUT` -> `{"steps": 2}`
  Một pattern tương tự cũng xuất hiện với truy vấn `"Hành trình bay vào không gian của chú Cuội năm 2099"` khi step 1 và step 2 đều quay lại `search_wikipedia(Chú Cuội)`.
- **Diagnosis**: Đây là lỗi kết hợp giữa prompt adherence yếu của local model và rủi ro thiết kế tool nếu để quá mơ hồ. Model local `phi3` qua Ollama tuân thủ system prompt kém hơn OpenAI nên có xu hướng lặp lại `Thought` và `Action`, dù prompt đã yêu cầu chỉ được suy nghĩ một lần. Nếu tool vẫn theo kiểu God Tool hoặc không ràng buộc rõ thứ tự gọi, agent càng dễ bị lặp, gọi sai tool, hoặc timeout.
- **Solution**: Tôi xử lý ở 3 lớp.
  - Lớp tool: tách OpenLibrary thành 3 tool độc lập để mỗi bước có mục tiêu rõ.
  - Lớp prompt: sửa `get_agent_system_prompt()` theo hướng ép 1 Thought duy nhất, sau đó chỉ được Action tuần tự theo pipeline `search_wikipedia -> search_book -> get_book_subjects -> search_books_by_subject`.
  - Lớp safety: thêm đoạn anti-hallucination cắt `Observation:` do LLM tự bịa trong `src/agent/hybrid_flow.py` để agent bắt buộc chờ dữ liệu thật từ tool.
  Sau khi tối ưu, benchmark `"The Hobbit – summary and similar books"` trong `report/eval_results_openai.txt` và `report/eval_results_gemini.txt` cho thấy hai agent cloud đã hoàn thành đầy đủ truy vấn, trong khi `report/eval_results_local.txt` vẫn thể hiện local Phi-3 chỉ đạt mức incomplete với độ trễ cao. Điều này phản ánh hạn chế của provider local rõ hơn là lỗi cấu trúc tool.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: `Thought` giúp agent phân rã bài toán thành từng bước có kiểm soát. Với chatbot thường, model trả lời trực tiếp từ kiến thức sẵn có nên dễ dừng ở mức từ chối nếu không có dữ liệu trong Local DB. Với ReAct, agent có thể lập kế hoạch theo chuỗi: lấy summary ở Wikipedia, tìm Work ID trên OpenLibrary, lấy subject, rồi mới gợi ý sách tương tự. Benchmark `"The Hobbit – summary and similar books"` cho thấy lợi thế này rất rõ, vì đây là kiểu câu hỏi cần tổng hợp nhiều bước thay vì trả lời một phát.
2.  **Reliability**: Agent không phải lúc nào cũng tốt hơn chatbot. Trong benchmark `"The Hobbit – summary and similar books"`, `Chatbot Baseline` gần như tức thì (`~0 ms`, `0 tokens`) nhưng chỉ có thể từ chối. Ngược lại, `ReAct Agent (GPT-4o)` hoàn thành ở khoảng `~9,600 ms`, `~3,000 tokens`, còn `ReAct Agent (Gemini)` hoàn thành ở khoảng `~7,900 ms`, `~5,700 tokens`. Tuy nhiên, `ReAct Agent (Phi-3-mini - Est.)` mất khoảng `~41,000 ms` và vẫn incomplete. Điều đó cho thấy agent đổi lấy chất lượng bằng độ trễ và token, và chất lượng cuối cùng vẫn phụ thuộc mạnh vào provider.
3.  **Observation**: Observation là phần quyết định agent có đi tiếp đúng hướng hay không. Nếu observation sạch và đúng định dạng, agent có thể dùng nó làm trạng thái trung gian cho bước kế tiếp. Nếu observation lỗi mạng, không tìm thấy dữ liệu, hoặc bị LLM tự bịa, toàn bộ vòng lặp sẽ lệch hướng. Vì vậy tôi đánh giá tool design và observation quality quan trọng không kém bản thân model.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Tách tool calling thành lớp service riêng, có caching cho Wikipedia/OpenLibrary, và dùng async I/O để tránh agent phải chờ nối tiếp từng request mạng.
- **Safety**: Bổ sung validator cho `Action` và `Observation`, đồng thời thêm fallback policy rõ ràng khi API trả `429`, `404`, hoặc timeout thay vì để agent tiếp tục lập luận mù.
- **Performance**: Thêm router chọn provider theo loại câu hỏi. Các câu trong Local DB có thể đi thẳng chatbot baseline; chỉ các câu cần tổng hợp nguồn ngoài mới bật ReAct. Với hệ nhiều tool hơn, nên có retrieval/tool-selection layer hoặc vector index để giảm số lần model phải thử sai.

---
