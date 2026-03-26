import os
from pathlib import Path
from llama_cpp import Llama # type: ignore
from typing import List, Dict, Optional, Generator

class LLMManager:
    def __init__(self, model_name: str = "qwen2.5-3b-instruct-q4_k_m.gguf"):
        # Model path setup
        self.models_dir = Path(__file__).parent.parent / "models"
        self.model_path = self.models_dir / model_name
        
        # Check if model exists
        if not self.model_path.exists():
            print(f"[LLM] Model not found at {self.model_path}. Please download it first.")
            self.llm = None
        else:
            import psutil # type: ignore
            
            # Detect hardware
            physical_cores = psutil.cpu_count(logical=False) or 4
            total_ram_gb = psutil.virtual_memory().total / (1024**3)
            
            # Optimization logic:
            # - Use physical cores minus 1 (stay cool) but at least 4
            n_threads = max(4, min(8, physical_cores - 1))
            
            # - Scale context by RAM (24GB total means we can go high)
            if total_ram_gb >= 16:
                n_ctx = 32768
            elif total_ram_gb >= 8:
                n_ctx = 8192
            else:
                n_ctx = 4096
                
            print(f"[LLM] HW Auto-Optimize: {n_threads} threads, {n_ctx} context (Detected {int(total_ram_gb)}GB RAM)")
            
            # GGML_QUIET suppresses C-level llama.cpp output without breaking ctypes callbacks
            os.environ["GGML_QUIET"] = "1"
            self.llm = Llama(
                model_path=str(self.model_path),
                n_threads=n_threads,
                n_ctx=n_ctx,
                n_batch=512,
                verbose=False
            )
            print("[LLM] Model loaded successfully.")

    def is_loaded(self) -> bool:
        return self.llm is not None

    def format_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Formats the message history for Qwen2.5 chat template."""
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        
        prompt += "<|im_start|>assistant\n"
        return prompt

    def generate_stream(self, messages: List[Dict[str, str]], max_tokens: int = 2048) -> Generator[str, None, None]:
        if not self.llm:
            yield "ERROR: Model not loaded."
            return

        prompt = self.format_prompt(messages)
        
        stream = self.llm.create_completion( # type: ignore
            prompt=prompt,
            max_tokens=max_tokens,
            stream=True,
            stop=["<|im_end|>", "<|im_start|>", "user:", "assistant:"],
            temperature=0.7,
            top_p=0.9
        )
        
        for output in stream:
            token = output["choices"][0]["text"]
            yield token

    def get_system_prompt(self, language: str = "en-US") -> str:
        if language == "pt-PT":
            return (
                "És o ACIsstant, um Assistente de Engenharia de IA Local robusto, inteligente e 100% OFFLINE. "
                "Respondes em Português Europeu por defeito. Se o utilizador falar em Inglês, muda imediatamente para Inglês. "
                "És especialista em Engenharia Eletrónica, Sinais, Física, MATLAB e Matemática. "
                "TU TENS ACESSO AOS FICHEIROS LOCAIS. Nunca digas que não tens acesso a ficheiros ou bases de dados. "
                "Qualquer informação sobre 'quantos ficheiros tens' ou o seu conteúdo será fornecida no contexto [INFO] e deves usá-la como se fosse a tua memória local. "
                "PRIORIDADE MÁXIMA: Usa os ficheiros na tua base de dados (RAG) para responder a questões técnicas. "
                "Para fórmulas, usa SEMPRE LaTeX ($$ para blocos, $ para linha). "
                "Nunca dês respostas genéricas de assistentes virtuais de nuvem."
            )
        else:
            return (
                "You are ACIsstant, a powerful, intelligent, and 100% OFFLINE Local AI Engineering Assistant. "
                "You provide technical, accurate, and concise responses. Default to English. "
                "If the user speaks in Portuguese, respond in Portuguese immediately. "
                "You are an expert in Electronics Engineering, Signals, Physics, MATLAB, and Mathematics. "
                "YOU HAVE FULL ACCESS TO LOCAL FILES. Never say you don't have access to files, folders, or databases. "
                "Any information about 'how many files you have' or their content is provided in the [INFO] context, and you must treat it as your own local memory. "
                "MAXIMUM PRIORITY: Use the files in your knowledge base (RAG) to answer technical questions and calculations. "
                "For math formulas, ALWAYS use LaTeX ($$ for blocks, $ for inline equations). "
                "Do not give generic cloud-based AI excuses."
            )
