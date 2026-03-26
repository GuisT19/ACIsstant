# Antigravity: Local AI Engineering Assistant

A fully offline, portable AI assistant running on CPU. Specialised in Electronics, Signals, Physics and Mathematics.

---

## Getting Started

### Windows 11

**Prerequisite:** [Python 3.10 or higher](https://www.python.org/downloads/) must be installed.
During installation, make sure to check the **"Add Python to PATH"** option.

**Step 1 — Install dependencies**

Double-click `install_windows.bat` or run it from a terminal:

```bat
install_windows.bat
```

This script will:
- Create an isolated virtual environment (`venv`) in the project folder
- Install all Python dependencies inside that `venv` (nothing is installed globally)
- Create the required directories (`models/`, `data/uploads/`, `data/vectordb/`)

**Step 2 — Download the AI model**

```bat
venv\Scripts\python download_model.py
```

This downloads the Qwen2.5 3B GGUF model (~2.3 GB) into the `models/` folder.

**Step 3 — Start the assistant**

Double-click `run.bat` or run it from a terminal:

```bat
run.bat
```

**Step 4 — Open the interface**

Open your browser and go to `http://localhost:8000`.

---

### Arch Linux

**Step 1 — Install and configure the environment**

```bash
chmod +x install_arch.sh
./install_arch.sh
```

**Step 2 — Download the AI model**

```bash
venv/bin/python download_model.py
```

**Step 3 — Start the assistant**

```bash
./run.sh
```

**Step 4 — Open the interface**

Open your browser and go to `http://localhost:8000`.

---

## Features

- **Engineering Assistant**: Expert in Electronics, Signals, Physics and Mathematics.
- **RAG (Knowledge Context)**: Place your PDFs and Markdown files in `data/uploads/`. The assistant will use them to answer your questions with relevant context.
- **Multi-Chat**: Create and manage multiple conversations stored locally in SQLite.
- **Circuit Diagrams**: Ask for circuit diagrams and it will generate Circuitikz (LaTeX) or SPICE netlists.
- **Multilingual**: Supports European Portuguese and English.

---

## Performance Notes (CPU-Only)

- The **Qwen2.5 3B** model is the recommended choice for CPU-only machines.
- Expect approximately 5-10 tokens per second on a mid-range CPU (e.g. Intel Core i5/i7 4-core).
- RAG keeps responses contextually accurate without overloading RAM.

---

## Project Structure

| Path | Description |
|---|---|
| `backend/` | FastAPI server, LLM engine and RAG logic |
| `frontend/` | Web interface (HTML/JS/CSS) |
| `models/` | GGUF model files are stored here |
| `data/uploads/` | Place your study materials here (PDF, Markdown, TXT) |
| `data/vectordb/` | Auto-generated FAISS vector index |
| `install_windows.bat` | Installer script for Windows 11 |
| `install_arch.sh` | Installer script for Arch Linux |
| `run.bat` | Launch script for Windows |
| `run.sh` | Launch script for Arch Linux |
| `download_model.py` | Script to download the AI model |
