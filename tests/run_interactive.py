import os
import sys
import time
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.run_eval import initialize_provider
from src.agent.hybrid_flow import HybridBookAssistant

def main():
    print("=======================================================")
    print("📚 TRÌNH DEMO TƯƠNG TÁC: TRỢ LÝ SÁCH VĂN HỌC HYBRID")
    print("=======================================================")
    
    # 1. Khởi tạo LLM Provider từ .env
    try:
        llm = initialize_provider()
    except Exception as e:
        print(f"❌ Lỗi khởi tạo: {e}")
        print("Mẹo: Hãy kiểm tra xem bạn đã lưu file .env và điền API keys chưa nhé!")
        return

    assistant = HybridBookAssistant(llm=llm, max_steps=10)
    
    print("\n✅ Hệ thống sẵn sàng! Gõ 'exit' hoặc 'quit' để thoát.")
    print("=======================================================\n")

    while True:
        try:
            # Nhận câu hỏi từ người dùng
            user_query = input("👤 Bạn: ").strip()
            if not user_query:
                continue
                
            if user_query.lower() in ["exit", "quit"]:
                print("\n👋 Cảm ơn bạn đã sử dụng trợ lý văn học. Tạm biệt!")
                break
            
            # Chọn chế độ chạy
            print("\nChọn chế độ chạy thử nghiệm:")
            print("  [1] Local DB Only (Chỉ trả lời nếu có trong sách giáo khoa/book_dataset, không có thì từ chối)")
            print("  [2] ReAct Agent Only (Tìm kiếm trực tiếp trên Wikipedia & OpenLibrary bằng AI)")
            choice = input("👉 Lựa chọn của bạn (mặc định là 2): ").strip()
            
            mode = "hybrid"
            if choice == "1":
                mode = "chatbot"
                
            print("\n🤖 Trợ lý đang xử lý...")
            print("-" * 50)
            
            start_time = time.time()
            
            if mode == "chatbot":
                result = assistant.run_chatbot_baseline(user_query)
                print(f"\n💬 [Chatbot Baseline]:")
                print(result["answer"])
                print("-" * 50)
                print(f"⏱️ Độ trễ: {result['latency_ms']} ms | 📊 Tokens tiêu thụ: {result['tokens']}")
            else:
                result = assistant.run_hybrid_flow(user_query)
                print(f"\n💬 [Hybrid Flow] - Cơ chế: {result['mode']}:")
                print(result["answer"])
                print("-" * 50)
                print(f"⏱️ Độ trễ: {result['latency_ms']} ms | 📊 Tokens tiêu thụ: {result['tokens']}")
                
            print("=======================================================\n")
            
        except KeyboardInterrupt:
            print("\n👋 Đã ngắt chương trình. Tạm biệt!")
            break
        except Exception as e:
            print(f"\n❌ Có lỗi xảy ra trong quá trình xử lý: {e}\n")

if __name__ == "__main__":
    main()
