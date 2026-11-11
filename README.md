# Extract Information LLM

A FastAPI service that extracts structured information from documents (PDF, PNG, TXT) using a [LangGraph](https://langchain-ai.github.io/langgraph/) workflow and Claude (Anthropic) for structured output.

## How it works

The service receives a file, routes it to the right extractor based on its type, and then sends the extracted text to Claude, which returns a validated Pydantic object.

```
START ──► root_type_file ──┬──► node_pdf_extract (pdfplumber) ──┐
                           ├──► node_png_extract (Tesseract OCR) ├──► node_format_text (Claude) ──► END
                           └──► node_txt_extract (plain read) ───┘
```

| Node | Responsibility |
|---|---|
| `root_type_file` | Conditional router. Reads `type_file` from the state and picks the extractor. |
| `node_pdf_extract` | Extracts text page by page with `pdfplumber` and records the page count. |
| `node_png_extract` | Runs OCR with `pytesseract`. |
| `node_txt_extract` | Reads the file as UTF-8 text. |
| `node_format_text` | Calls Claude with `with_structured_output(FormatOutput, method="json_schema")` and returns the structured result. |

The graph state is a plain `TypedDict` (not `MessagesState`), since this is a data pipeline rather than a conversation: each node writes its own keys and the next one reads them.

### Output schema

```json
{
  "title": "string",
  "description": "string",
  "list_names": ["string"],
  "date": "YYYY-MM-DD",
  "num_pages": 0,
  "general_info": { "key": "value" }
}
```

`num_pages` is filled in by the extractor, not by the model, so it is always exact.

## Project structure

```
.
├── main.py                 # FastAPI app, /health endpoint, uvicorn entry point
├── config/settings.py      # Environment settings (pydantic-settings)
├── llm/graph.py            # LangGraph workflow and Claude configuration
├── models/models.py        # FormatOutput (LLM schema) and DataInput (API input)
├── routes/routes.py        # /api/extract and /api/extract-from-path
├── scripts/make_test_files.py  # Generates sample PDF, PNG and TXT files
├── files/                  # Sample files and temporary uploads
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml          # Managed with uv
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (only for PNG extraction when running locally; the Docker image already includes it)
- An Anthropic API key

## Configuration

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-api03-...
URL_TESSERACT=C:\Program Files\Tesseract-OCR\tesseract.exe
PORT=8000
```

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key. Required. |
| `URL_TESSERACT` | Path to the Tesseract executable. Needed on Windows. Inside Docker it is set automatically to `/usr/bin/tesseract`. |
| `PORT` | Port used by `python main.py`. Defaults to `8000`. |

## Running locally

```bash
uv sync
uv run python scripts/make_test_files.py   # optional: creates files/sample.{pdf,png,txt}
uv run python main.py
```

The API is available at `http://localhost:8000` and the interactive docs at `http://localhost:8000/docs`.

## Running with Docker

```bash
docker compose build
docker compose up
```

The container listens on port `8002`. Source folders are mounted as volumes and uvicorn runs with `--reload`, so code changes are picked up without rebuilding. The `.env` file is loaded by compose; `URL_TESSERACT` is overridden with the Linux path.

## API

### `GET /health`

Returns `{"status": "ok"}`. Does not call the model.

### `POST /api/extract`

Upload a file (`multipart/form-data`, field `file`) and get the structured result.

```bash
curl --location 'http://localhost:8000/api/extract' \
  --form 'file=@"files/sample.pdf"'
```

### `POST /api/extract-from-path`

Process a file that already exists on the server's disk. Useful for local development.

```bash
curl --location 'http://localhost:8000/api/extract-from-path' \
  --header 'Content-Type: application/json' \
  --data '{"file_url": "files/sample.txt"}'
```

### Error responses

| Status | Meaning |
|---|---|
| `400` | Unsupported file type. Allowed: `pdf`, `png`, `txt`. |
| `404` | File not found (only for `/api/extract-from-path`). |
| `502` | The extraction or the model call failed. Details are written to the server log. |

## Testing the pipeline without calling the model

The extractor nodes can be run directly, which is useful to debug extraction without spending tokens:

```bash
uv run python -c "from llm.graph import extract_PDF_agent; print(extract_PDF_agent({'file_url': 'files/sample.pdf'}))"
```

## Implementation notes

- **Model**: `claude-sonnet-5-5` through `langchain-anthropic`. Structured output uses `method="json_schema"` because forced tool calling is not supported on this model.
- **`timeout` / `stop`** on `ChatAnthropic` are optional. `timeout` is the HTTP timeout in seconds (default 10 minutes); `stop` is a list of stop sequences and is not needed with structured output.
- **Async**: the route awaits `graph.ainvoke`, so the server keeps serving requests while the model responds.
- **Uploads** are saved under `files/` with a random name and deleted after processing.
- **Dependencies**: `python-multipart` is required by FastAPI for file uploads; `uvicorn` serves the app.
