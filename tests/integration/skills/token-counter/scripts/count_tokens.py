# /// script
# dependencies = [
#   "tiktoken>=0.7,<1",
# ]
# requires-python = ">=3.9"
# ///

"""
Count tokens in text or files for LLM context planning.

Outputs structured JSON to stdout; diagnostics go to stderr.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import tiktoken

    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False

MODEL_ENCODINGS: dict[str, str] = {
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-4": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "claude-sonnet-4": "cl100k_base",
    "claude-opus-4": "cl100k_base",
    "claude-haiku-4": "cl100k_base",
    "gemini-2.0-flash": "cl100k_base",
    "gemini-2.5-pro": "cl100k_base",
}

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".ts",
    ".js",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".html",
    ".css",
    ".sh",
    ".rs",
    ".go",
    ".java",
    ".cpp",
    ".c",
}


def _approx_tokens(text: str) -> int:
    """Approximation: ~3.5 chars per token (covers prose and code)."""
    return max(1, round(len(text) / 3.5))


def count_tokens(text: str, encoding_name: str) -> tuple[int, bool]:
    """Returns (token_count, is_exact).
    Falls back to char approximation if tiktoken BPE files can't be fetched.
    """
    if _TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.get_encoding(encoding_name)
            return len(enc.encode(text)), True
        except Exception as e:
            print(
                f"Warning: tiktoken failed ({e}), using approximation.", file=sys.stderr
            )
    return _approx_tokens(text), False


def process_path(path: Path, encoding_name: str) -> tuple[list[dict], bool]:
    """Returns (results, is_exact)."""
    results = []
    exact = True
    if path.is_file():
        content = path.read_text(errors="replace")
        tokens, e = count_tokens(content, encoding_name)
        exact = exact and e
        results.append({"source": str(path), "tokens": tokens, "chars": len(content)})
    elif path.is_dir():
        for f in sorted(path.rglob("*")):
            if f.is_file() and f.suffix in TEXT_EXTENSIONS:
                content = f.read_text(errors="replace")
                tokens, e = count_tokens(content, encoding_name)
                exact = exact and e
                results.append(
                    {"source": str(f), "tokens": tokens, "chars": len(content)}
                )
        if not results:
            print(f"Warning: no recognized text files found in {path}", file=sys.stderr)
    else:
        raise FileNotFoundError(f"path not found: {path}")
    return results, exact


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Count tokens in text or files for LLM context planning.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Models and encodings:
  {chr(10).join(f'  {m:<30} {e}' for m, e in MODEL_ENCODINGS.items())}
  (any other model name falls back to cl100k_base)

Examples:
  uv run scripts/count_tokens.py --text "Hello, world!"
  uv run scripts/count_tokens.py --input README.md --model claude-sonnet-4
  uv run scripts/count_tokens.py --input ./src --format table
  echo "some text" | uv run scripts/count_tokens.py

Exit codes:
  0  Success
  1  Input not found or unreadable
  2  Invalid arguments
""",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="File or directory to analyze",
    )
    parser.add_argument(
        "--text",
        "-t",
        help="Inline text to count tokens for",
    )
    parser.add_argument(
        "--model",
        "-m",
        default="gpt-4o",
        help="Model name to select tokenizer encoding (default: gpt-4o)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "table"],
        default="json",
        help="Output format: json (default) or table",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.input and args.text:
        print("Error: --input and --text are mutually exclusive.", file=sys.stderr)
        print(
            "Usage: provide either --input <path> or --text <string>, not both.",
            file=sys.stderr,
        )
        sys.exit(2)

    encoding_name = MODEL_ENCODINGS.get(args.model, "cl100k_base")
    if args.model not in MODEL_ENCODINGS:
        print(
            f"Warning: unknown model '{args.model}', falling back to cl100k_base encoding.",
            file=sys.stderr,
        )

    # collect results
    is_exact = True
    if args.text:
        tokens, is_exact = count_tokens(args.text, encoding_name)
        results = [{"source": "<inline>", "tokens": tokens, "chars": len(args.text)}]
    elif args.input:
        try:
            results, is_exact = process_path(args.input, encoding_name)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        content = sys.stdin.read()
        tokens, is_exact = count_tokens(content, encoding_name)
        results = [{"source": "<stdin>", "tokens": tokens, "chars": len(content)}]

    total_tokens = sum(r["tokens"] for r in results)
    total_chars = sum(r["chars"] for r in results)
    method = "tiktoken" if is_exact else "approximation (~3.5 chars/token)"

    if args.format == "json":
        output = {
            "model": args.model,
            "encoding": encoding_name,
            "method": method,
            "files": results,
            "total_tokens": total_tokens,
            "total_chars": total_chars,
        }
        print(json.dumps(output, indent=2))
    else:
        col = 52
        print(f"{'Source':<{col}} {'Tokens':>10} {'Chars':>10}")
        print("-" * (col + 22))
        for r in results:
            source = r["source"]
            if len(source) > col - 1:
                source = "..." + source[-(col - 4) :]
            print(f"{source:<{col}} {r['tokens']:>10,} {r['chars']:>10,}")
        print("-" * (col + 22))
        print(f"{'TOTAL':<{col}} {total_tokens:>10,} {total_chars:>10,}")
        print(
            f"\nModel: {args.model}  |  Encoding: {encoding_name}  |  Method: {method}"
        )


if __name__ == "__main__":
    main()
