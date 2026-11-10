import argparse
from pathlib import Path

from llm.graph import graph


def main():
    parser = argparse.ArgumentParser(description="Extract structured information from a file.")
    parser.add_argument("file", help="Path to the file (.pdf, .png or .txt)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    result = graph.invoke(
        {
            "type_file": path.suffix.lstrip(".").lower(),
            "file_url": str(path),
        }
    )

    print("\n--- Extracted text (first 300 chars) ---")
    print(result["extracted_text"][:300])
    print("\n--- Structured output ---")
    print(result["formatted_output"].model_dump_json(indent=2))


if __name__ == "__main__":
    main()
