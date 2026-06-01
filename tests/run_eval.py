import os
import sys
import time
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.core.local_provider import LocalProvider
from src.agent.hybrid_flow import HybridBookAssistant

def initialize_provider():
    """Khởi tạo LLM Provider dựa trên file .env"""
    load_dotenv()
    provider_type = os.getenv("DEFAULT_PROVIDER", "openai").lower()
    
    if provider_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        model_name = os.getenv("DEFAULT_MODEL", "gpt-4o")
        if not api_key or "your_" in api_key:
            raise ValueError("Vui lòng thiết lập OPENAI_API_KEY hợp lệ trong file .env")
        print(f"🔹 Đang kết nối tới OpenAI Provider (Model: {model_name})...")
        return OpenAIProvider(model_name=model_name, api_key=api_key)
        
    elif provider_type == "google":
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")
        if not api_key or "your_" in api_key:
            raise ValueError("Vui lòng thiết lập GEMINI_API_KEY hợp lệ trong file .env")
        print(f"🔹 Đang kết nối tới Gemini Provider (Model: {model_name})...")
        return GeminiProvider(model_name=model_name, api_key=api_key)
        
    elif provider_type == "local":
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy model local tại {model_path}. Vui lòng kiểm tra lại hướng dẫn trong README.md")
        print(f"🔹 Đang tải Local LLM Provider (Model: {os.path.basename(model_path)})...")
        return LocalProvider(model_path=model_path)
        
    else:
        raise ValueError(f"Provider '{provider_type}' không được hỗ trợ. Sử dụng: openai | google | local")

def run_suite():
    # 1. Khởi tạo
    try:
        llm = initialize_provider()
    except Exception as e:
        print(f"❌ Lỗi khởi tạo: {e}")
        print("\nMẹo: Vui lòng copy file '.env.example' thành '.env' và điền API keys của bạn vào nhé!")
        return

    assistant = HybridBookAssistant(llm=llm, max_steps=5)

    # 2. Định nghĩa 5 Test Cases
    test_cases = [
        {
            "id": 1,
            "type": "Chatbot-wins (Tán gẫu)",
            "prompt": "Chào bạn! Tôi là một người rất yêu thích đọc sách. Bạn có thể giới thiệu bạn có thể giúp gì cho tôi không?",
            "expected": "Câu trả lời chào hỏi thân thiện, giới thiệu vai trò trợ lý sách nhanh chóng không cần gọi tools."
        },
        {
            "id": 2,
            "type": "Chatbot-wins (Sách có sẵn trong Local DB)",
            "prompt": "Tôi muốn tìm thông tin và năm sáng tác của tác phẩm 'Chí Phèo' của tác giả Nam Cao.",
            "expected": "Tìm thấy Chí Phèo trong Local DB (năm 1941) và trả lời cực nhanh không cần gọi internet."
        },
        {
            "id": 3,
            "type": "Agent-wins (Sách ngoài Local DB - Gọi Wikipedia + OpenLibrary)",
            "prompt": "Tôi muốn tìm thông tin tác phẩm 'Tắt đèn' của nhà văn Ngô Tất Tố. Hãy tóm tắt tác phẩm này và gợi ý một vài sách trên OpenLibrary.",
            "expected": "Không thấy ở Local DB -> Gọi Wikipedia lấy tóm tắt tác phẩm Tắt đèn -> Gọi OpenLibrary lấy sách gợi ý từ Ngô Tất Tố."
        },
        {
            "id": 4,
            "type": "Agent-wins (Suy luận so sánh thời gian phức tạp)",
            "prompt": "Tìm thông tin tác phẩm 'Chiến tranh và hòa bình' (War and Peace) của tác giả Lev Tolstoy. Hãy tóm tắt nó và giới thiệu sách trên OpenLibrary.",
            "expected": "Không thấy ở Local DB -> Gọi Wikipedia tóm tắt Chiến tranh và hòa bình -> Gọi OpenLibrary lấy thông tin gợi ý."
        },
        {
            "id": 5,
            "type": "Edge Case (Sách không tồn tại ở bất kỳ đâu)",
            "prompt": "Hãy tóm tắt giúp tôi cuốn sách 'Hành trình bay vào không gian của chú Cuội năm 2099' và tìm nó trên OpenLibrary.",
            "expected": "Không thấy ở DB và internet -> Kết luận không tìm thấy an toàn, không bị kẹt lặp, không bịa thông tin."
        }
    ]

    results = []

    print("\n=======================================================")
    print("🚀 BẮT ĐẦU CHẠY ĐÁNH GIÁ TỰ ĐỘNG - LAB 3 HYBRID SYSTEM")
    print("=======================================================\n")

    for tc in test_cases:
        print(f"-------------------------------------------------------")
        print(f"📝 TEST CASE {tc['id']}: [{tc['type']}]")
        print(f"👉 Câu hỏi: \"{tc['prompt']}\"")
        print(f"🎯 Kết quả mong đợi: {tc['expected']}")
        print(f"-------------------------------------------------------")

        # Chạy Baseline Chatbot
        print("⚡ [Chế độ: Chatbot Baseline] Đang xử lý...")
        res_chatbot = assistant.run_chatbot_baseline(tc['prompt'])
        print(f"💬 Chatbot trả lời: {res_chatbot['answer'][:120]}...")
        print(f"⏱️ Độ trễ: {res_chatbot['latency_ms']}ms | 📊 Tokens: {res_chatbot['tokens']}\n")

        # Chạy Hybrid Flow
        print("🔋 [Chế độ: Hybrid Flow] Đang xử lý...")
        res_hybrid = assistant.run_hybrid_flow(tc['prompt'])
        print(f"💬 Hybrid trả lời: {res_hybrid['answer'][:120]}...")
        print(f"⏱️ Độ trễ: {res_hybrid['latency_ms']}ms | 📊 Tokens: {res_hybrid['tokens']} | 🛤️ Cơ chế: {res_hybrid['mode']}\n")

        results.append({
            "id": tc['id'],
            "prompt": tc['prompt'],
            "chatbot_ans": res_chatbot['answer'],
            "chatbot_latency": res_chatbot['latency_ms'],
            "chatbot_tokens": res_chatbot['tokens'],
            "hybrid_ans": res_hybrid['answer'],
            "hybrid_latency": res_hybrid['latency_ms'],
            "hybrid_tokens": res_hybrid['tokens'],
            "hybrid_mode": res_hybrid['mode']
        })

    # 3. Tạo thư mục report nếu chưa có và lưu kết quả ra file
    os.makedirs("report", exist_ok=True)
    report_path = "report/eval_results.txt"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=======================================================\n")
        f.write("📊 BÁO CÁO THỬ NGHIỆM ĐÁNH GIÁ: CHATBOT VS HYBRID AGENT\n")
        f.write("=======================================================\n\n")
        
        for r in results:
            f.write(f"📝 TEST CASE {r['id']}: \"{r['prompt']}\"\n")
            f.write(f"-------------------------------------------------------\n")
            f.write(f"[1] CHATBOT BASELINE:\n")
            f.write(f"   - Độ trễ: {r['chatbot_latency']} ms\n")
            f.write(f"   - Số Tokens: {r['chatbot_tokens']}\n")
            f.write(f"   - Câu trả lời: {r['chatbot_ans']}\n\n")
            f.write(f"[2] HYBRID FLOW ({r['hybrid_mode']}):\n")
            f.write(f"   - Độ trễ: {r['hybrid_latency']} ms\n")
            f.write(f"   - Số Tokens: {r['hybrid_tokens']}\n")
            f.write(f"   - Câu trả lời: {r['hybrid_ans']}\n")
            f.write(f"=======================================================\n\n")

    # 4. In bảng so sánh tóm tắt trên console
    print("==========================================================================")
    print("📊 BẢNG SO SÁNH ĐÁNH GIÁ HIỆU NĂNG TỔNG HỢP")
    print("==========================================================================")
    print(f"{'TC':<3} | {'Chế độ Hybrid':<25} | {'Chatbot Latency':<15} | {'Hybrid Latency':<15} | {'Winner (Speed)'}")
    print("-" * 78)
    for r in results:
        winner = "Chatbot" if r['chatbot_latency'] < r['hybrid_latency'] else "Hybrid"
        print(f"#{r['id']:<2} | {r['hybrid_mode']:<25} | {r['chatbot_latency']:>11} ms | {r['hybrid_latency']:>11} ms | {winner}")
    print("==========================================================================")
    print(f"\n🎉 Hoàn thành đánh giá! Báo cáo chi tiết đã được lưu tại: {os.path.abspath(report_path)}")
    print("Hãy copy dữ liệu này điền vào file GROUP_REPORT của nhóm bạn nhé!")

if __name__ == "__main__":
    run_suite()
