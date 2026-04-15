# LLM Context Window Limits

Reference for common models. Limits are in tokens unless noted.

## Anthropic Claude

| Model           | Context window | Notes |
| --------------- | -------------- | ----- |
| claude-opus-4   | 200,000        |       |
| claude-sonnet-4 | 200,000        |       |
| claude-haiku-4  | 200,000        |       |

Output limit is 32,000 tokens (64K with extended thinking enabled).

## OpenAI GPT

| Model         | Context window | Notes |
| ------------- | -------------- | ----- |
| gpt-4o        | 128,000        |       |
| gpt-4o-mini   | 128,000        |       |
| gpt-4-turbo   | 128,000        |       |
| gpt-3.5-turbo | 16,385         |       |

## Google Gemini

| Model            | Context window | Notes     |
| ---------------- | -------------- | --------- |
| gemini-2.5-pro   | 1,048,576      | 1M tokens |
| gemini-2.0-flash | 1,048,576      | 1M tokens |
| gemini-1.5-pro   | 2,097,152      | 2M tokens |

## Meta Llama (self-hosted)

| Model         | Context window | Notes                         |
| ------------- | -------------- | ----------------------------- |
| llama-3.3-70b | 128,000        |                               |
| llama-3.2-3b  | 128,000        |                               |
| qwen3-30b-a3b | 32,768         | MoE, effective context varies |

## Practical thresholds

- **Safe zone**: use ≤ 80% of the context window to leave headroom for the response
- **Warning zone**: 80–95% — risk of truncation depending on output length
- **Danger zone**: > 95% — likely to hit limits; split input or summarize

## Cost estimation notes

Token costs vary by model and provider. As a rough guide:

- Input tokens are typically cheaper than output tokens
- Cached/prompt-caching tokens (Anthropic, OpenAI) can reduce cost 50-90%
- Always check the provider's current pricing page for exact figures
