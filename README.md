# ACIsstant: Local AI Engineering Assistant

A powerful, fully offline, and portable AI assistant optimized for Windows 11. Specialized in **Electronics Engineering, Signals & Systems, Physics, and Mathematics**.

---

## ⚡ Quick Start (Windows 11)

**Prerequisite:** [Python 3.10 or higher](https://www.python.org/downloads/) must be installed. (Make sure to check **"Add Python to PATH"** during installation).

**1. Install Environment**
Double-click `install_windows.bat`. This creates a local virtual environment and installs all dependencies (FastAPI, Llama-cpp, LangChain, etc.).

**2. Download AI Model**
Run the following in a terminal to download the Qwen2.5 3B model (~2.3 GB):
```bat
venv\Scripts\python download_model.py
```

**3. Run ACIsstant**
Double-click `run.bat`. The assistant will start on `http://localhost:8000`.

---

## 🚀 Key Features

### 🛠️ Hardware Auto-Optimization
ACIsstant automatically detects your machine's **RAM** and **CPU Cores** on startup. It scales the context window (up to **32k tokens**) and thread count to ensure the best performance for your specific hardware (e.g., optimized for 24GB RAM machines like the T480s).

### 📐 Scientific Math & Formulas
Full support for **LaTeX** equations. Using **KaTeX**, ACIsstant renders complex mathematical formulas beautifully in the chat interface. Use `$$` for blocks and `$` for inline math.

### 🔌 Circuit Diagrams (SVG)
The assistant can generate real circuit diagrams! When you ask for a circuit (e.g., *"Draw an inverted Op-Amp circuit"*), it generates **Circuitikz** code which is instantly rendered as a high-quality **SVG diagram** in the browser using **TikzJax**.

### 📚 RAG (Knowledge Context)
Upload your PDFs, Markdown, or TXT study materials via the UI. ACIsstant indexes them locally using **FAISS** and **Sentence-Transformers** to provide accurate answers based on your own documents.

### 💬 Local History & Multi-Chat
All conversations are stored in a local **SQLite** database. You can create, rename, and delete chats anytime.

---

## 🛠️ Performance & Support

- **Model:** Qwen2.5 3B Instruct (GGUF Q4_K_M).
- **Latency:** ~5-15 tokens/sec on modern CPUs (using AVX2/AVX512).
- **Offline:** 100% private. No data leaves your machine.
- **Language:** Default is **English**, with full support for **European Portuguese**.

---

## 📂 Project Structure

| Path | Description |
|---|---|
| `backend/` | FastAPI server, LLM engine & RAG logic |
| `frontend/` | Web UI (HTML/JS/CSS) |
| `data/uploads/` | Place your study PDFs here |
| `models/` | AI Model storage |
| `run.bat` | The main launcher |

---
*Created for Engineering Students & Professionals.*
