# Antigravity: Local AI Engineering Assistant

This is an offline, portable AI assistant optimized for your hardware. It specializes in Electronics Engineering, Signals, and Physics.

## 🚀 Getting Started

### Windows:
1. **Environment Setup**:
   Run the `install_windows.bat` file.
2. **Download the Model**:
   ```bash
   venv\Scripts\python download_model.py
   ```
3. **Launch the Assistant**:
   Run the `run.bat` file.

### Linux (Arch):
1. **Environment Setup**:
   ```bash
   chmod +x install_linux.sh
   ./install_linux.sh
   ```
2. **Download the Model**:
   ```bash
   venv/bin/python download_model.py
   ```
3. **Launch the Assistant**:
   ```bash
   ./run.sh
   ```

### All Systems:
**Access the Web Interface**:
Open your browser at `http://localhost:8000`.

## 📚 Key Features

- **Engineering Assistant**: Expert in Electronics, Signals, and Physics.
- **RAG (Knowledge Context)**: Place your PDFs and Markdown files in the `data/uploads` folder. The assistant will read these files to provide context-aware answers.
- **Multi-Chat**: Save and manage multiple conversations locally (SQLite).
- **Circuit Diagrams**: Request diagrams and it will generate **Circuitikz** (LaTeX) or **SPICE** code.
- **Multilingual**: Supports English (Native) and European Portuguese.

## 🛠️ Performance Notes (CPU-Only)

- The **Qwen2.5 3B** model is optimized for CPU inference.
- Text generation speed is approximately 5-10 tokens per second.
- RAG helps maintain accuracy without exhausting your RAM.

## 📂 Project Structure

- `/backend`: FastAPI logic, LLM, and RAG implementation.
- `/frontend`: Web Interface (HTML/JS/CSS).
- `/models`: Storage for GGUF model files.
- `/data/uploads`: Folder for your study materials.
