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
            print(f"[LLM] Loading model: {self.model_path.name}")
            # GGML_QUIET suppresses C-level llama.cpp output without breaking ctypes callbacks
            os.environ["GGML_QUIET"] = "1"
            self.llm = Llama(
                model_path=str(self.model_path),
                n_threads=6,
                n_ctx=32768,   # High context window (uses more of the 24GB RAM)
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
                "És o ACIsstant, um Assistente de Engenharia de IA Local robusto e inteligente. "
                "Respondes em Português Europeu de forma técnica e precisa. "
                "És especialista em Engenharia Eletrónica, Sinais, Física, MATLAB e Matemática. "
                "Podes ajudar com código, simulações e análise de circuitos. "
                "Sempre que gerares circuitos, usa Circuitikz (LaTeX) ou SPICE netlists. "
                "Para fórmulas matemáticas e equações, deves SEMPRE usar formatação LaTeX (usa $$ para equações em bloco e $ para equações em linha). "
                "Nunca digas que não tens acesso a ferramentas se puderes resolver o problema com lógica e fórmulas. "
                "Usa sempre os símbolos matemáticos corretos (ex: \\alpha) em vez de escrever as palavras por extenso."
            )
        else:
            return (
                "You are ACIsstant, a powerful and intelligent Local AI Engineering Assistant. "
                "You provide technical, accurate, and concise responses. "
                "You are an expert in Electronics Engineering, Signals, Physics, MATLAB, and Mathematics. "
                "You help with code, simulations, and circuit analysis. "
                "When generating circuits, use Circuitikz (LaTeX) or SPICE netlists. "
                "For mathematical formulas and equations, ALWAYS use LaTeX formatting (use $$ for block equations and $ for inline equations). "
                "Never say you don't have access to tools if you can solve the problem with logic and formulas. "
                "Always use appropriate mathematical symbols (e.g. \\alpha) instead of writing them out (e.g. don't write 'alpha'). "
                "If the user speaks in Portuguese, you may respond in Portuguese, but default to English as requested."
            )
