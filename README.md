# ACIsstant: Local AI Engineering Assistant

ACIsstant is a specialized, fully offline AI engineering assistant optimized for Windows and Linux systems. It provides high-performance local inference tailored for Electronics Engineering, Signals and Systems, Physics, and Mathematics, ensuring all data remains on your machine.

---

## Key Features

### Hardware Optimization
The application automatically detects system resources—including RAM and CPU cores—upon startup. It adjusts the context window (up to 32k tokens) and optimizes thread counts to ensure efficient performance on your specific hardware.

### Scientific Notation and Formulas
ACIsstant includes comprehensive support for LaTeX equations. Mathematical formulas are rendered via KaTeX, providing clear and professional visualization of complex expressions directly within the chat interface.

### Advanced UI Features & Debugging
ACIsstant now features a robust, self-healing frontend with multiple Quality-of-Life upgrades:
*   **Math Protection Engine:** A built-in regex-based shielding parser (`mathPlaceholders`) ensures that KaTeX LaTeX delimiters never collide with `marked.js` markdown parsers, solving the classic underscore-italic corruption bug in equations.
*   **Graceful Prompt Cancellation:** Generative inference can be immediately aborted mid-stream by the user via an `AbortController` injection, instantly halting computational overhead.
*   **Inline Debug UI:** Network and asynchronous JS errors during generation are caught and explicitly printed with full stack traces natively inside the affected chat bubbles for painless maintenance.
*   **Cache Bypassing:** The FastAPI backend serves `index.html` with explicit strict `Cache-Control: no-cache` parameters to prevent stale frontend caching.

### Circuit Diagram Generation
The assistant can generate and render circuit diagrams. Utilizing Circuitikz and TikzJax, requested diagrams are produced as high-quality SVG images within the browser environment.

### Retrieval-Augmented Generation (RAG)
Users can upload documents in PDF, Markdown, or TXT formats. ACIsstant indexes these materials locally using FAISS and Sentence-Transformers, enabling accurate, context-aware responses based on private study materials.

### Local Conversation Management
All chat history is stored in a local SQLite database. This allows for secure management, renaming, and retrieval of past conversations without an internet connection.

---

## Technical Specifications

*   **Model:** Qwen2.5 3B Instruct (GGUF Q4_K_M)
*   **Inference Engine:** llama-cpp-python
*   **Backend:** FastAPI / Uvicorn (With Auto Cache-Control headers)
*   **Frontend:** Vanilla HTML/JS/CSS with KaTeX, Highlight.js and Marked.js
*   **Vector Database:** FAISS
*   **Privacy:** 100% Offline; no telemetry or external data transmission.

---

## Installation and Setup

### Windows
**Prerequisite:** Python 3.10 or higher (must be added to the system PATH).

1.  **Install Dependencies:** Run `install_windows.bat`.
2.  **Download Model:** Execute `venv\Scripts\python download_model.py`.
3.  **Start Application:** Run `run.bat` (Use `Ctrl+R` to trigger Hot-Restart inside the terminal at any time).

### Linux (Arch and other distributions)
**Prerequisite:** Python and virtual environment (venv) support.

1.  **Install Dependencies:**
    ```bash
    chmod +x install_arch.sh
    ./install_arch.sh
    ```
2.  **Download Model:** Execute `venv/bin/python download_model.py`.
3.  **Start Application:**
    ```bash
    chmod +x run.sh
    ./run.sh
    ```

---

## Project Structure

| Directory/File | Description |
| :--- | :--- |
| `backend/` | Application logic, LLM engine, and RAG implementation. |
| `frontend/` | Web-based user interface components, math protection, streaming parsers. |
| `data/uploads/` | Storage for documents used in RAG indexing. |
| `models/` | Storage for model GGUF files. |
| `install_windows.bat` | Automated installation script for Windows. |
| `run.bat` | Startup script for Windows systems. |

---

## Performance Notes

*   **Latency:** Approximately 5-15 tokens per second on modern CPUs using AVX2 or AVX512 instruction sets.
*   **Language Support:** Optimized for English with support for European Portuguese.

---
*Created for Engineering Students and Professionals.*
