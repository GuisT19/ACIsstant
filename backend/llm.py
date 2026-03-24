import os
from pathlib import Path
from llama_cpp import Llama
from typing import List, Dict, Optional, Generator

class LLMManager:
    def __init__(self, model_name: str = "qwen2.5-3b-instruct-q4_k_m.gguf"):
        # Model path setup
        self.models_dir = Path(__file__).parent.parent / "models"
        self.model_path = self.models_dir / model_name
        
        # Check if model exists
        if not self.model_path.exists():
            print(f"[LLM] Model not found at {self.model_path}. Please download it.")
            self.llm = None
        else:
            print(f"[LLM] Loading model: {self.model_path}")
            # Hardware-optimized settings for ThinkPad T480s (CPU-only)
            # - n_threads: 4-6 (it has 4 cores / 8 threads, but too many makes it slow)
            # - n_ctx: 4096 (good balance for CPU RAM)
            self.llm = Llama(
                model_path=str(self.model_path),
                n_threads=6,
                n_ctx=4096,
                n_batch=512,
                verbose=False
            )

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
        
        stream = self.llm.create_completion(
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

    def get_system_prompt(self, language: str = "pt-PT") -> str:
        if language == "pt-PT":
            return (
                "És um Assistente de Engenharia de IA Local (Antigravity). "
                "Respondes em Português Europeu de forma técnica e precisa. "
                "És especialista em Engenharia Eletrónica, Sinais, Física e Matemática. "
                "Sempre que gerar circuitos, usa Circuitikz (LaTeX) ou SPICE netlists. "
                "Se o utilizador falar em Inglês, responde em Inglês, mas para questões de engenharia complexas em Português, usa a terminologia portuguesa correta com os termos ingleses entre parênteses se necessário."
            )
        else:
            return (
                "You are a Local AI Engineering Assistant (Antigravity). "
                "Respond accurately and technically. "
                "You are an expert in Electronics, Signals, Physics, and Mathematics. "
                "When generating circuits, use Circuitikz (LaTeX) or SPICE netlists."
            )
