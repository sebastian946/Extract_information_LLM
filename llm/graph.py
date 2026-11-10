from typing import Literal, TypedDict

from langgraph.graph import StateGraph, START, END
from PIL import Image
from models.models import FormatOutput
from langchain_anthropic import ChatAnthropic
from config.settings import settings

import pdfplumber
import pytesseract


# Ruta al ejecutable de Tesseract (necesario en Windows)
if settings.URL_TESSERACT:
    pytesseract.pytesseract.tesseract_cmd = settings.URL_TESSERACT


class FlowStateGraph(TypedDict, total=False):
    """Estado compartido entre los nodos del grafo.

    `total=False` indica que no todas las claves existen desde el inicio:
    al invocar el grafo solo se pasan `type_file` y `file_url`, y los demás
    campos los van llenando los nodos.
    """
    type_file: str
    file_url: str
    extracted_text: str
    num_pages: int
    formatted_output: FormatOutput


llm = ChatAnthropic(
    model_name="claude-sonnet-5-5",
    api_key=settings.ANTHROPIC_API_KEY,
    timeout=120,
    stop=None,
)

structure_llm = llm.with_structured_output(FormatOutput, method="json_schema")

SYSTEM_PROMPT = """You are an information extraction assistant.
You receive raw text extracted from a document (PDF, image via OCR, or plain text).
Fill in every field of the output schema using only information present in the text.
If a value is not present, use an empty string, an empty list, or an empty object as appropriate.
Never invent data."""


def extract_PDF_agent(state: FlowStateGraph):
    print(f"Extracting text from PDF: {state['file_url']}")
    with pdfplumber.open(state["file_url"]) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
        num_pages = len(pdf.pages)
    return {"extracted_text": text, "num_pages": num_pages}


def extract_PNG_agent(state: FlowStateGraph):
    print(f"Extracting text from PNG: {state['file_url']}")
    image = Image.open(state["file_url"])
    text = pytesseract.image_to_string(image)
    return {"extracted_text": text, "num_pages": 1}


def extract_TXT_agent(state: FlowStateGraph):
    print(f"Extracting text from TXT: {state['file_url']}")
    with open(state["file_url"], "r", encoding="utf-8") as file:
        text = file.read()
    return {"extracted_text": text, "num_pages": 1}


def format_extracted_text(state: FlowStateGraph):
    extracted_text = state["extracted_text"]

    result = structure_llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("user", f"Document text:\n\n{extracted_text}"),
        ]
    )

    # num_pages lo conocemos con certeza desde el extractor; no se lo pedimos al modelo.
    result.num_pages = state.get("num_pages", 0)
    return {"formatted_output": result}


def root_type_file(state: FlowStateGraph) -> Literal["extract_PDF", "extract_PNG", "extract_TXT"]:
    selection = state.get("type_file", "").lower()

    if selection == "pdf":
        return "extract_PDF"
    elif selection == "png":
        return "extract_PNG"
    elif selection == "txt":
        return "extract_TXT"
    else:
        raise ValueError(f"Unsupported file type: {state.get('type_file')}")


workflow = StateGraph(FlowStateGraph)

# 1. Registrar los nodos
workflow.add_node("node_pdf_extract", extract_PDF_agent)
workflow.add_node("node_png_extract", extract_PNG_agent)
workflow.add_node("node_txt_extract", extract_TXT_agent)
workflow.add_node("node_format_text", format_extracted_text)

# 2. Enrutamiento inicial según el tipo de archivo
workflow.add_conditional_edges(
    START,
    root_type_file,
    {
        "extract_PDF": "node_pdf_extract",
        "extract_PNG": "node_png_extract",
        "extract_TXT": "node_txt_extract",
    },
)

# 3. Cada extractor pasa al nodo de formato
workflow.add_edge("node_pdf_extract", "node_format_text")
workflow.add_edge("node_png_extract", "node_format_text")
workflow.add_edge("node_txt_extract", "node_format_text")

# 4. El formato es el último paso
workflow.add_edge("node_format_text", END)

graph = workflow.compile()
