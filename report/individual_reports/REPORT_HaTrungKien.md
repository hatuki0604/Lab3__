# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Hà Trung Kiên
- **Student ID**: 2A202600709
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

### Modules Implemented

Tôi chịu trách nhiệm thiết kế và triển khai toàn bộ **thư mục `src/tools/`** — hệ thống công cụ (tools) cho ReAct Agent. Hệ thống gồm 3 module chính theo kiến trúc **3-tầng tìm kiếm**:

| # | Module | Vai trò |
|---|--------|---------|
| 1 | `src/tools/books_dataset.py` | **Tầng 1 — Local Database**: Mock dataset văn học Việt Nam + hàm tìm kiếm nội bộ |
| 2 | `src/tools/openlibrary_tool.py` | **Tầng 2 — OpenLibrary API**: Tìm kiếm sách quốc tế, lấy chủ đề, và gợi ý sách cùng thể loại |
| 3 | `src/tools/wikipedia_tool.py` | **Tầng 3 — Wikipedia API**: Lấy tóm tắt bách khoa cho tác phẩm/tác giả (hỗ trợ cả tiếng Việt và tiếng Anh) |

### Code Highlights

#### 1. `books_dataset.py` — Mock Dataset & Local Search

```python
# Dataset gồm 10 tác phẩm văn học Việt Nam kinh điển
BOOKS_DATASET = [
    {"title": "Chí Phèo", "author": "Nam Cao", "year": 1941, "genre": "truyện ngắn", ...},
    {"title": "Lão Hạc", "author": "Nam Cao", "year": 1943, ...},
    # ... 10 tác phẩm
]

def search_local_db(query: str) -> list:
    """Tìm kiếm không phân biệt hoa thường theo tên tác phẩm hoặc tác giả."""
    query_lower = query.lower().strip()
    results = []
    for book in BOOKS_DATASET:
        if query_lower in book["title"].lower() or query_lower in book["author"].lower():
            results.append(book)
    return results
```

**Điểm nổi bật**: Dataset bao phủ nhiều tác giả (Nam Cao, Kim Lân, Tô Hoài, Nguyễn Quang Sáng...) và chứa đầy đủ metadata (title, author, year, genre, region, summary) để agent có thể trả lời đa dạng câu hỏi mà không cần gọi API.

#### 2. `openlibrary_tool.py` — Thiết kế theo ReAct Pattern (Decomposed Tools)

File này có **2 phiên bản** được giữ lại để so sánh:

- **Version 1 (God Tool)**: Một hàm `recommend_openlibrary()` làm tất cả — tìm + gợi ý. Đã bị comment lại.
- **Version 2 (ReAct Pattern)**: Tách thành 3 hàm nhỏ, mỗi hàm làm đúng 1 việc:

```python
# Tool 1: Tìm sách → lấy Work ID
def search_book(query: str) -> str:
    """Tìm kiếm sách trên OpenLibrary để lấy Work ID."""

# Tool 2: Lấy chủ đề từ Work ID
def get_book_subjects(work_key: str) -> str:
    """Lấy danh sách các chủ đề (subjects) dựa vào Work ID."""

# Tool 3: Tìm sách cùng chủ đề (có filter sách gốc)
def search_books_by_subject(subject: str, exclude_title: str = "") -> str:
    """Tìm danh sách sách cùng chủ đề, có lọc tên sách gốc."""
```

**Điểm nổi bật**:
- **Retry mechanism**: Mỗi hàm đều có vòng lặp retry 3 lần khi gặp Timeout, tăng độ ổn định.
- **Priority Subjects**: `get_book_subjects()` có danh sách chủ đề ưu tiên (Fantasy, Magic, Adventure...) để chọn subject hữu ích nhất thay vì lấy ngẫu nhiên.
- **Programmatic filter**: `search_books_by_subject()` có tham số `exclude_title` để loại sách gốc khỏi kết quả gợi ý — tránh agent gợi ý lại chính cuốn sách người dùng đang hỏi.

#### 3. `wikipedia_tool.py` — Bilingual Wikipedia Search

```python
def search_wikipedia(query: str) -> str:
    """Tìm kiếm tóm tắt trên Wikipedia Việt Nam, fallback sang tiếng Anh."""
    # Bước 1: Thử Wikipedia tiếng Việt (vi.wikipedia.org)
    # Bước 2: Nếu thất bại → fallback sang Wikipedia tiếng Anh (en.wikipedia.org)
```

**Điểm nổi bật**:
- **Bilingual fallback**: Thử tiếng Việt trước (phù hợp với dataset văn học Việt Nam), nếu không tìm được thì tự động chuyển sang tiếng Anh.
- **Custom User-Agent header**: Tuân thủ best practice của Wikipedia API.
- **2-step search**: Dùng OpenSearch API để tìm title chính xác → sau đó dùng REST Summary API để lấy tóm tắt.

### Documentation — Cách tools tương tác với ReAct Loop

Luồng hoạt động của agent khi sử dụng các tools:

```
User Query: "Gợi ý sách tương tự Harry Potter"
   │
   ▼
[Thought 1] Tìm trong database nội bộ trước
[Action 1]  search_local_db("Harry Potter")
[Observation 1] Không tìm thấy → Cần tìm trên OpenLibrary
   │
   ▼
[Thought 2] Tìm trên OpenLibrary để lấy Work ID
[Action 2]  search_book("Harry Potter")
[Observation 2] Work ID: /works/OL82563W
   │
   ▼
[Thought 3] Lấy chủ đề của sách này
[Action 3]  get_book_subjects("/works/OL82563W")
[Observation 3] Chủ đề: Fantasy, Magic, Wizards
   │
   ▼
[Thought 4] Tìm sách cùng chủ đề Fantasy, loại trừ Harry Potter
[Action 4]  search_books_by_subject("Fantasy", "Harry Potter")
[Observation 4] Sách cùng chủ đề: The Hobbit, A Wizard of Earthsea, ...
   │
   ▼
[Final Answer] Dựa trên chủ đề Fantasy và Magic, tôi gợi ý...
```

Việc **decompose từ God Tool thành nhiều tool nhỏ** cho phép agent thực hiện multi-step reasoning rõ ràng — mỗi bước Thought-Action-Observation đều có ý nghĩa logic, thay vì chỉ gọi 1 hàm và chờ kết quả.

---

## II. Debugging Case Study (10 Points)

### Problem Description

**Vấn đề**: Khi agent gọi `get_book_subjects()` với Work ID trả về từ `search_book()`, hàm thường xuyên trả về lỗi **404 Not Found** do format của `work_key` không nhất quán.

Cụ thể, `search_book()` trả về chuỗi dạng:
```
Tìm thấy sách: 'Harry Potter'. Work ID: /works/OL82563W
```

Nhưng khi agent parse ra `work_key`, nó có thể truyền vào dưới nhiều dạng khác nhau:
- `"/works/OL82563W"` (đúng)
- `"OL82563W"` (thiếu prefix)
- `"works/OL82563W"` (thiếu `/` đầu)

### Log Source

```json
{"event": "TOOL_CALL", "tool": "get_book_subjects", "args": "OL82563W",
 "timestamp": "2026-06-01T10:15:22"}
{"event": "TOOL_ERROR", "error": "404 Client Error: Not Found for url:
 https://openlibrary.org/OL82563W.json", "timestamp": "2026-06-01T10:15:23"}
```

### Diagnosis

Nguyên nhân gốc rễ là do **LLM parsing không nhất quán**. Khi LLM đọc observation `"Work ID: /works/OL82563W"`, nó có thể:
1. Lấy đúng `/works/OL82563W`
2. Chỉ lấy phần ID `OL82563W` (bỏ prefix)
3. Lấy `works/OL82563W` (bỏ `/` đầu)

Đây **không phải lỗi của prompt hay model**, mà là lỗi của **tool spec** — hàm `get_book_subjects()` ban đầu không xử lý các format đầu vào khác nhau.

### Solution

Thêm logic **normalize work_key** vào đầu hàm `get_book_subjects()`:

```python
def get_book_subjects(work_key: str) -> str:
    work_key = work_key.strip()
    if not work_key.startswith("/"):
        if work_key.startswith("OL"):
            work_key = f"/works/{work_key}"   # OL82563W → /works/OL82563W
        else:
            work_key = f"/{work_key}"          # works/OL82563W → /works/OL82563W
    # ... phần còn lại
```

**Bài học**: Khi thiết kế tool cho ReAct agent, phải luôn **defensive coding** — không tin tưởng hoàn toàn vào output mà LLM parse được. Tool nên tự xử lý và chuẩn hóa input thay vì yêu cầu LLM truyền đúng format 100%.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning — Vai trò của block `Thought`

Block `Thought` tạo ra sự khác biệt **bản chất** giữa Chatbot thường và ReAct Agent:

- **Chatbot thường**: Khi hỏi "Gợi ý sách tương tự Chí Phèo", chatbot sẽ trả lời ngay dựa trên kiến thức huấn luyện — thường là hallucinate ra các tác phẩm không tồn tại hoặc gợi ý không liên quan.
- **ReAct Agent**: Block `Thought` buộc LLM phải **suy nghĩ trước khi hành động**: "Tôi cần tìm Chí Phèo trong database trước → nếu có thì lấy thể loại → tìm sách cùng thể loại". Mỗi bước suy luận đều được ghi nhận, giúp agent tránh hallucination vì mọi câu trả lời đều dựa trên **dữ liệu thực** từ tool.

Ví dụ cụ thể: Khi hỏi "Nam Cao viết những tác phẩm nào?", chatbot có thể liệt kê sai, nhưng agent sẽ gọi `search_local_db("Nam Cao")` và trả về chính xác 3 tác phẩm có trong dataset (Chí Phèo, Lão Hạc, Đời thừa).

### 2. Reliability — Khi nào Agent kém hơn Chatbot?

Agent thực tế **kém hơn chatbot** trong các trường hợp:

- **Câu hỏi đơn giản, kiến thức phổ thông**: "Ai viết Truyện Kiều?" — Chatbot trả lời ngay "Nguyễn Du", trong khi agent phải trải qua 2-3 bước tool call (search_local_db → không có → search_wikipedia) rồi mới trả lời, tốn thời gian và tokens.
- **API failure/timeout**: Khi OpenLibrary hoặc Wikipedia bị chậm hoặc down, agent bị "kẹt" ở bước Observation và có thể retry nhiều lần hoặc trả lời lỗi, trong khi chatbot vẫn trả lời được (dù có thể không chính xác 100%).
- **Parsing errors**: LLM đôi khi generate sai format `Action: tool_name(args)`, khiến agent không parse được và lặp vô hạn hoặc trả về "Not implemented".

**Kết luận**: Agent phù hợp cho **câu hỏi cần tra cứu thực tế** (factual queries), nhưng chatbot vẫn tốt hơn cho **câu hỏi mở, sáng tạo, hoặc chit-chat**.

### 3. Observation — Ảnh hưởng của feedback từ môi trường

Observation là yếu tố **quyết định** chất lượng reasoning của agent:

- **Positive feedback**: Khi `search_local_db("Nam Cao")` trả về 3 kết quả, agent biết ngay là đã đủ thông tin và chuyển sang `Final Answer` mà không cần gọi thêm API ngoài → tiết kiệm thời gian và chi phí.
- **Negative feedback**: Khi observation trả về "Không tìm thấy...", agent phải **thay đổi chiến lược** — chuyển từ local search sang OpenLibrary hoặc Wikipedia. Đây chính là sức mạnh của ReAct: khả năng **thích ứng** (adaptive behavior) dựa trên feedback thực tế.
- **Partial feedback**: Khi `get_book_subjects()` trả về "Các chủ đề chính: Fantasy, Magic", agent sử dụng thông tin này để quyết định gọi `search_books_by_subject("Fantasy")` — mỗi observation **thu hẹp không gian tìm kiếm** và dẫn đến câu trả lời chính xác hơn.

---

## IV. Future Improvements (5 Points)

### Scalability

- **Asynchronous tool execution**: Hiện tại các tool call là đồng bộ (synchronous). Khi số lượng tool tăng (ví dụ 20+ tools), nên sử dụng `asyncio` để gọi song song các tool không phụ thuộc nhau, giảm thời gian chờ.
- **Tool Registry pattern**: Thay vì truyền list tools vào agent, sử dụng một `ToolRegistry` class quản lý tập trung, hỗ trợ dynamic loading/unloading tools tại runtime.

### Safety

- **Supervisor LLM**: Triển khai một LLM thứ hai đóng vai trò "giám sát", kiểm tra mỗi Action trước khi thực thi — đặc biệt quan trọng nếu agent có quyền ghi/xóa dữ liệu (write operations).
- **Rate limiting**: Thêm giới hạn số lượng API call mỗi phút cho từng tool, tránh tình trạng agent gọi API vô tội vạ khi bị kẹt trong vòng lặp.
- **Input sanitization**: Validate và sanitize mọi tham số trước khi gọi API bên ngoài, tránh injection attacks.

### Performance

- **Caching layer**: Sử dụng `functools.lru_cache` hoặc Redis để cache kết quả API. Ví dụ, nếu agent đã search "Harry Potter" trên OpenLibrary, lần sau không cần gọi lại API.
- **Vector DB for tool retrieval**: Khi có nhiều tools (50+), thay vì liệt kê tất cả trong system prompt, sử dụng vector database (Chroma, Pinecone) để embed mô tả tool và chỉ retrieve top-k tools liên quan đến query hiện tại — giảm prompt length và tăng accuracy.
- **Streaming response**: Sử dụng streaming API (SSE) để trả kết quả từng phần cho user, cải thiện trải nghiệm chờ đợi.

---

> [!NOTE]
> Báo cáo này được viết bởi Hà Trung Kiên — chịu trách nhiệm triển khai hệ thống tools cho ReAct Agent trong Lab 3.
