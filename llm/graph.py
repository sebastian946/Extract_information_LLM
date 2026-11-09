from typing import Literal

from langgraph.graph import StateGraph, MessagesState, START, END
from PIL import Image
from models.models import FormatOutput
from langchain_anthropic import ChatAnthropic

import pdfplumber
import pytesseract


class FlowStateGraph(MessagesState):
    type_file: str
    file_url: str
    extracted_text: str
    formatted_output: FormatOutput

llm = ChatAnthropic(
    model_name="claude-sonnet-4-5-20250929",
    timeout=120,
    stop=None,
)

structure_llm = llm.with_structured_output(FormatOutput)


def extract_PDF_agent(state: FlowStateGraph):
    print(f"Extracting text from PDF: {state['file_url']}")
    with pdfplumber.open(state["file_url"]) as pdf:
        text = ""
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return {"extracted_text": text}

def extract_PNG_agent(state: FlowStateGraph):
    print(f"Extracting text from PNG: {state['file_url']}")
    image = Image.open(state["file_url"])
    text = pytesseract.image_to_string(image)
    return {"extracted_text": text}

def extract_TXT_agent(state: FlowStateGraph):
    print(f"Extracting text from TXT: {state['file_url']}")
    with open(state["file_url"], "r", encoding="utf-8") as file:
        text = file.read()
    return {"extracted_text": text}

def format_extracted_text(state: FlowStateGraph):
    extracted_text = state["extracted_text"]

    pass

def root_type_file(state: FlowStateGraph) -> Literal["extract_PDF", "extract_PNG", "extract_TXT"]:

    selection = state.get("type_file", "").lower()

    if selection == "pdf":
        return "extract_PDF"
    elif selection == "png":
        return "extract_PNG"
    elif selection == "txt":
        return "extract_TXT"
    else:
        raise ValueError(f"Unsupported file type: {state['type_file']}")


workflow = StateGraph(FlowStateGraph)

workflow.add_node("node_pdf_extract", extract_PDF_agent)
workflow.add_node("node_png_extract", extract_PNG_agent)
workflow.add_node("node_txt_extract", extract_TXT_agent)
workflow.add_node("node_format_text", format_extracted_text)

