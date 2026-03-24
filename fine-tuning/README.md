# Fine-tuning Data

Place your fine-tuning datasets and scripts here.

## Recommended structure

```
fine-tuning/
├── datasets/        # Training data (JSONL format preferred)
│   └── example.jsonl
├── scripts/         # Fine-tuning scripts (e.g., using llama.cpp or unsloth)
└── output/          # Fine-tuned model outputs / adapters (LoRA)
```

## Dataset format (JSONL)
Each line should be a JSON object in instruction-following format:
```json
{"instruction": "What is...", "input": "", "output": "..."}
```

## Notes
- For CPU-only fine-tuning, consider **LoRA** adapters via `llama.cpp` or `unsloth`.
- The base model is `models/qwen2.5-3b-instruct-q4_k_m.gguf`.
