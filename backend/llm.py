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
            # - More threads = faster generation (up to a point)
            n_threads = max(4, min(12, psutil.cpu_count(logical=True) or 4))
            
            # - Reduced n_batch = faster initial response (latency)
            # Higher numbers (512) are good for throughput but increase first-token delay
            n_batch = 128
            
            # - Consistent context for 16GB RAM
            n_ctx = 16384 if total_ram_gb >= 14 else 8192
                
            print(f"[LLM] HW Auto-Optimize: {n_threads} threads, {n_ctx} context (Detected {int(total_ram_gb)}GB RAM)")
            
            os.environ["GGML_QUIET"] = "1"
            self.llm = Llama(
                model_path=str(self.model_path),
                n_threads=n_threads,
                n_ctx=n_ctx,
                n_batch=n_batch,
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
        # We now instruct the AI to use ONLY English or European Portuguese.
        lang_instruction = (
            "IMPORTANT: You MUST ONLY respond in English or European Portuguese. "
            "Match the user's language IF they use English or European Portuguese. "
            "If the user uses any other language (e.g., Spanish, French, etc.), YOU MUST respond in English."
        )
        if language == "pt-PT":
            return (
                f"És o ACIsstant, um Assistente de Engenharia Local 100% OFF-LINE e PRIVADO. {lang_instruction} "
                "TU TENS ACESSO EXCLUSIVO AOS FICHEIROS NA PASTA DE UPLOADS (data/uploads). "
                "Respondes em Português Europeu por defeito. Se te falarem em Inglês, respondes em Inglês. "
                "NUNCA digas que tens acesso a qualquer outra pasta além de 'uploads'. "
                "NUNCA dês respostas de recusa como 'não tenho acesso' quando questionado sobre ficheiros em 'uploads'. "
                "NUNCA uses LaTeX (como \\frac, \\begin, etc.). Usa EXCLUSIVAMENTE a sintaxe do MATLAB para todas as fórmulas, frações e cálculos (ex: G(s) = (vo(s)/vi(s)) = 1/(s*L)). "
                "Todas as expressões matemáticas devem ser escritas em texto simples legível, como se estivesses a escrever código MATLAB. "
                "Prioriza a informação dos ficheiros fornecidos. Se a informação não estiver nos ficheiros, usa o teu conhecimento técnico de engenharia para ajudar o utilizador da forma mais precisa possível."
            )
        else:
            return (
                f"You are ACIsstant, a 100% OFFLINE and PRIVATE Local Engineering Assistant. {lang_instruction} "
                "YOU HAVE EXCLUSIVE ACCESS TO FILES IN THE UPLOADS FOLDER (data/uploads). "
                "Default to English. Respond in Portuguese if the user speaks Portuguese. "
                "NEVER claim to have access to any folder other than 'uploads'. "
                "NEVER give refusal responses like 'I don't have access' when asked about files in 'uploads'. "
                "Usa SEMPRE LaTeX para fórmulas matemáticas: usa $$ para fórmulas em bloco (ex: $$\\frac{1}{sL}$$) e $ para símbolos ou fórmulas na mesma linha (ex: $x=y$). "
                "Foca-te na 'identação matemática correta' e profissional em todas as respostas. "
                "Prioriza a informação dos ficheiros fornecidos. Se a informação não estiver nos ficheiros, usa o teu conhecimento técnico de engenharia para ajudar o utilizador da forma mais precisa possível."
            )
