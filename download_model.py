import os
from huggingface_hub import hf_hub_download
from pathlib import Path

def download_qwen():
    model_repo = "Qwen/Qwen2.5-3B-Instruct-GGUF" # 4B is actually the 3B model in some namings, we'll use the 3B-Instruct GGUF
    model_file = "qwen2.5-3b-instruct-q4_k_m.gguf" # This is ~2.3GB, fits well in 8-16GB RAM
    
    # Alternatively, the 7B might be too slow on T480s, so 3B/4B is the sweet spot.
    # Qwen 2.5 7B is ~5GB, might work but slow.
    
    print(f"--- Downloading {model_file} from {model_repo} ---")
    dest_path = Path(__file__).parent / "models"
    dest_path.mkdir(exist_ok=True)
    
    target = dest_path / model_file
    if target.exists():
        print(f"Model already exists at {target}")
        return

    hf_hub_download(
        repo_id=model_repo,
        filename=model_file,
        local_dir=str(dest_path),
        local_dir_use_symlinks=False
    )
    print(f"Successfully downloaded to {target}")

if __name__ == "__main__":
    download_qwen()
