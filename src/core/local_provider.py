import time
import os
import requests
from typing import Dict, Any, Optional, Generator
from src.core.llm_provider import LLMProvider

try:
    # pyrefly: ignore [missing-import]
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LocalProvider(LLMProvider):
    """
    LLM Provider for local models.
    Supports native llama-cpp-python and auto-fallback to Local LLM Servers (Ollama / LM Studio / Llamafile).
    """
    def __init__(self, model_path: str, n_ctx: int = 4096, n_threads: Optional[int] = 4):
        super().__init__(model_name=os.path.basename(model_path))
        
        self.use_fallback_server = False
        num_threads = n_threads if n_threads is not None else 4
        
        # Thử khởi động llama-cpp-python truyền thống
        try:
            if Llama is None:
                raise ImportError("Thư viện llama-cpp-python chưa được cài đặt.")
                
            abs_path = os.path.abspath(model_path)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Không tìm thấy model tại {abs_path}")
                
            print(f"⚡ Đang thử nạp native llama-cpp-python (Threads: {num_threads})...")
            self.llm = Llama(
                model_path=abs_path,
                n_ctx=n_ctx,
                n_threads=num_threads,
                verbose=False
            )
            print("✅ Đã nạp thành công mô hình offline bằng native llama-cpp!")
            
        except Exception as e:
            # FALLBACK PATH: Nếu bị crash hoặc lỗi nhị phân C++ (Segfault/Access Violation)
            print(f"\n⚠️ Cảnh báo: Lỗi nạp native llama-cpp-python ({e}).")
            print("🔄 Tự động chuyển hướng sang chế độ kết nối Local LLM Server (Ollama / LM Studio / Llamafile)...")
            self.use_fallback_server = True

    def _generate_fallback(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Gọi API kết nối tới các Local LLM Server đang chạy trên máy"""
        start_time = time.time()
        
        # Danh sách các cổng mặc định của Ollama (11434), LM Studio (1234), Llamafile (8080)
        local_servers = [
            "http://localhost:11434/v1/chat/completions",  # Ollama
            "http://localhost:1234/v1/chat/completions",   # LM Studio
            "http://localhost:8080/v1/chat/completions"    # Llamafile / Llama.cpp Server
        ]
        
        headers = {"Content-Type": "application/json"}
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "phi3",  # Model mặc định cho Ollama hoặc LM Studio
            "messages": messages,
            "temperature": 0.3
        }
        
        response = None
        used_url = ""
        for url in local_servers:
            try:
                response = requests.post(url, json=payload, headers=headers, timeout=5)
                if response.status_code == 200:
                    used_url = url
                    break
            except Exception:
                continue
                
        if not response or response.status_code != 200:
            raise RuntimeError(
                "\n❌ Lỗi: Không thể kết nối tới bất kỳ Local LLM Server nào!\n"
                "👉 Hướng dẫn khắc phục:\n"
                "1. Bạn hãy tải và cài đặt Ollama miễn phí từ: https://ollama.com\n"
                "2. Chạy lệnh sau trên terminal của bạn để kích hoạt mô hình: 'ollama run phi3'\n"
                "3. Hệ thống sẽ tự động liên kết thành công 100%!"
            )
            
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {
            "prompt_tokens": len(prompt) // 4,
            "completion_tokens": len(content) // 4,
            "total_tokens": (len(prompt) + len(content)) // 4
        })
        
        latency_ms = int((time.time() - start_time) * 1000)
        logger_name = "Ollama" if "11434" in used_url else "LM Studio" if "1234" in used_url else "Llamafile"
        print(f"\n📡 [Kết nối thành công tới Local Server: {logger_name}]")
        
        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": f"local-{logger_name.lower()}"
        }

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        if self.use_fallback_server:
            return self._generate_fallback(prompt, system_prompt)
            
        start_time = time.time()
        
        # Lập định dạng prompt Phi-3
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{prompt}<|end|>\n<|assistant|>"
        else:
            full_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>"
            
        response = self.llm(
            full_prompt,
            max_tokens=1024,
            stop=["<|end|>", "Observation:"],
            echo=False
        )
        
        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)
        
        content = response["choices"][0]["text"].strip()
        usage = {
            "prompt_tokens": response["usage"]["prompt_tokens"],
            "completion_tokens": response["usage"]["completion_tokens"],
            "total_tokens": response["usage"]["total_tokens"]
        }
        
        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "local"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        if self.use_fallback_server:
            # Fallback stream gọi gián tiếp generate
            result = self._generate_fallback(prompt, system_prompt)
            yield result["content"]
            return
            
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{prompt}<|end|>\n<|assistant|>"
        else:
            full_prompt = f"<|user|>\n{prompt}<|end|>\n<|assistant|>"
            
        stream = self.llm(
            full_prompt,
            max_tokens=1024,
            stop=["<|end|>", "Observation:"],
            stream=True
        )
        
        for chunk in stream:
            token = chunk["choices"][0]["text"]
            if token:
                yield token
