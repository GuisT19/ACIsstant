
import os
import logging
from pathlib import Path
from llama_cpp import Llama # type: ignore
from typing import List, Dict, Optional, Generator

logger = logging.getLogger("acisstant.llm")

class LLMManager:
    def __init__(self, model_name: str = "qwen2.5-3b-instruct-q4_k_m.gguf"):
        # Model path setup
        self.models_dir = Path(__file__).parent.parent / "models"
        self.model_path = self.models_dir / model_name
        
        # Check if model exists
        if not self.model_path.exists():
            logger.error(f"[LLM] Model not found at {self.model_path}. Please download it first.")
            self.llm = None
        else:
            try:
                import psutil # type: ignore
                
                # Hardware detection
                physical_cores = psutil.cpu_count(logical=False) or 4
                total_ram_gb = psutil.virtual_memory().total / (1024**3)
                n_threads = max(4, min(12, psutil.cpu_count(logical=True) or 4))
                n_batch = 128
                n_ctx = 16384 if total_ram_gb >= 14 else 8192
                
                logger.info(f"[LLM] HW Auto-Optimize: {n_threads} threads, {n_ctx} context (Detected {int(total_ram_gb)}GB RAM)")
                
                os.environ["GGML_QUIET"] = "1"
                self.llm = Llama(
                    model_path=str(self.model_path),
                    n_threads=n_threads,
                    n_ctx=n_ctx,
                    n_batch=n_batch,
                    verbose=False
                )
                logger.info("[LLM] Model loaded successfully.")
            except Exception as e:
                logger.error(f"[LLM] Failed to load model: {e}")
                self.llm = None

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
            logger.error("[LLM] Tried to generate stream but model is not loaded.")
            yield "ERROR: Model not loaded."
            return
        try:
            prompt = self.format_prompt(messages)
            stream = self.llm.create_completion( # type: ignore
                prompt=prompt,
                max_tokens=max_tokens,
                stream=True,
                stop=["<|im_end|>", "<|im_start|>", "user:", "assistant:"],
                temperature=0.2,
                top_p=0.9
            )
            for output in stream:
                token = output["choices"][0]["text"]
                yield token
        except Exception as e:
            logger.error(f"[LLM] Error during generation: {e}")
            yield f"\nERROR: {str(e)}"

    def get_system_prompt(self, language: str = "en-US") -> str:
        # We now instruct the AI to use ONLY English or European Portuguese.
        lang_instruction = (
            "IMPORTANT: You MUST ONLY respond in English or European Portuguese. "
        )
        if language == "pt-PT":
            return (
                f"És o ACIsstant, um Assistente de Engenharia Local 100% OFF-LINE e PRIVADO. {lang_instruction} "
                "TU TENS ACESSO EXCLUSIVO AOS FICHEIROS NA PASTA DE UPLOADS (data/uploads). "
                "Respondes em Português Europeu por defeito. Se te falarem em Inglês, respondes em Inglês. "
                "NUNCA digas que tens acesso a qualquer outra pasta além de 'uploads'. "
                "REGRAS DE MATEMÁTICA E LATEX (CRÍTICO PARA RENDERIZAÇÃO): "
                "1. Usa SEMPRE LaTeX perfeitamente limpo e fechado. Blocos: $$ ... $$. Linha: $ ... $. "
                "2. NUNCA quebres as fórmulas ao meio com espaçamentos desnecessários nem deixes chaves { } por fechar. "
                "3. Para chavetas nas Transformadas de Laplace usa barras de escape. Exemplo ERRADO: \\mathcal{L}{u(t)}. Exemplo CORRETO (obrigatório): \\mathcal{L}\\{u(t)\\}. "
                "4. Se precisares de colocar texto explicativo ou palavras DENTRO de blocos matemáticos, usa obrigatoriamente \\text{...}. "
                "5. Agrupa tudo de forma limpa. Não mistures caracteres soltos que quebrem os símbolos. "
                "6. DESENHO DE CIRCUITOS ANALÓGICOS: Para desenhar diagramas usa código Markdown 'latex' com 'tikzpicture' básico (componentes como node[draw]). NUNCA uses 'circuitikz'. "
                "7. SISTEMAS DIGITAIS E CRONOGRAMAS: Para desenhar Portas Lógicas ou Sinais de Tempo, usa um bloco 'json' puro formatado para o WaveDrom, usando 'assign' ou 'signal'. "
                "Exemplo Digital: ```json\n{ \"assign\": [ [\"out\", [\"|\", \"a\", [\"&\", \"b\", \"c\"]]] ] }\n```. Pensa passo a passo."
            )
        else:
            return (
                f"You are ACIsstant, a 100% OFFLINE and PRIVATE Local Engineering Assistant. {lang_instruction} "
                "YOU HAVE EXCLUSIVE ACCESS TO FILES IN THE UPLOADS FOLDER (data/uploads). "
                "Default to English. Respond in Portuguese if the user speaks Portuguese. "
                "NEVER claim to have access to any folder other than 'uploads'. "
                "MATH AND LATEX RULES (CRITICAL FOR UI RENDERER): "
                "1. ALWAYS use clean and fully closed LaTeX. Blocks: $$ ... $$. Inline: $ ... $. "
                "2. NEVER break formulas mid-line or leave curly brackets { } unclosed. "
                "3. For Laplace brackets, escape them properly. WRONG: \\mathcal{L}{u(t)}. CORRECT (mandatory): \\mathcal{L}\\{u(t)\\}. "
                "4. If inserting normal text INSIDE math blocks, ALWAYS use \\text{...}. "
                "5. Group everything cleanly. "
                "6. ANALOG CIRCUITS: When drawing diagrams, ALWAYS use a 'latex' Markdown code block with pure 'tikzpicture'. NEVER use 'circuitikz'. Draw components as labeled rectangles (node[draw]). "
                "7. DIGITAL LOGIC & TIMING: To draw logic gates or timing diagrams, use a 'json' code block formatted for WaveDrom (using 'assign' or 'signal'). "
                "Example Digital: ```json\n{ \"assign\": [ [\"out\", [\"|\", \"a\", [\"&\", \"b\", \"c\"]]] ] }\n```. Think step-by-step."
            )
