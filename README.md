# Antigravity: Local AI Engineering Assistant

Este é um assistente de IA offline e portátil, otimizado para o teu ThinkPad T480s.

## 🚀 Como Iniciar

### No Windows:
1. **Espera pela conclusão da instalação** (o ambiente `venv` está a ser configurado).
2. **Faz o download do modelo**:
   ```bash
   venv\Scripts\python download_model.py
   ```
3. **Inicia o Assistente**:
   Executa o ficheiro `run.bat`.

### No Arch Linux:
1. **Instala e Configura o ambiente**:
   ```bash
   chmod +x install_arch.sh
   ./install_arch.sh
   ```
2. **Faz o download do modelo**:
   ```bash
   venv/bin/python download_model.py
   ```
3. **Inicia o Assistente**:
   Executa o ficheiro `run.sh`:
   ```bash
   ./run.sh
   ```

### Todos os Sistemas:
**Acede à Interface**:
Abre o teu browser em `http://localhost:8000`.

## 📚 Funcionalidades Principais

- **Engineering Assistant**: Especialista em Eletrónica, Sinais e Física.
- **RAG (Knowledge Context)**: Coloca os teus PDFs e ficheiros Markdown na pasta `data/uploads`. O assistente irá ler estes ficheiros para responder às tuas perguntas.
- **Multi-Chat**: Guarda e gere múltiplas conversas guardadas localmente (SQLite).
- **Circuitos**: Pede diagramas e ele irá gerar código **Circuitikz** ou **SPICE**.
- **Multilingue**: Suporta Português Europeu e Inglês.

## 🛠️ Notas de Performance (CPU-Only)

- O modelo **Qwen2.5 3B/4B** é o ideal para o teu CPU.
- A geração de texto será de aproximadamente 5-10 tokens por segundo.
- O RAG ajuda a manter o contexto sem sobrecarregar a memória RAM.

## 📂 Estrutura de Pastas

- `/backend`: Lógica FastAPI, LLM e RAG.
- `/frontend`: Interface Web (HTML/JS/CSS).
- `/models`: Onde o modelo GGUF é guardado.
- `/data/uploads`: Onde deves colocar os teus materiais de estudo.
