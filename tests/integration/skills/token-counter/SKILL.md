---
name: token-counter
description: Count tokens in text, files, or directories for LLM context planning. Use when estimating token usage, checking if content fits in a context window, comparing token costs across models, or planning LLM API calls.
compatibility: Requires Python 3.9+ and uv (for script execution)
metadata:
  author: test
  version: "1.0"
---

## Token Counter Skill

Use this skill to analyze token counts before making LLM API calls.

### Workflow

1. Read `references/model-limits.md` to find the context limit for the target model.
2. Run the counting script against the input:
   ```bash
   uv run scripts/count_tokens.py --input <file_or_directory> --model <model_name>
   ```
   Or for inline text:
   ```bash
   uv run scripts/count_tokens.py --text "your text here" --model <model_name>
   ```
3. Compare `total_tokens` in the output against the model's context limit.
4. Report findings using the template in `assets/token-report-template.md`.

### Available scripts

- **`scripts/count_tokens.py`** — Counts tokens using tiktoken. Supports files, directories, piped stdin, and inline text. Outputs JSON by default.

### Notes

- Use `--format table` for human-readable output
- Default model is `gpt-4o`; use `--model claude-sonnet-4` etc. to select encoding
- For unknown models, the script falls back to `cl100k_base` with a warning on stderr
- Run `uv run scripts/count_tokens.py --help` to see all options
