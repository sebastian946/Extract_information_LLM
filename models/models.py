from pydantic import BaseModel, Field


class FormatOutput(BaseModel):
    """Structured information extracted from a document."""

    title: str = Field(description="Title or main subject of the document.")
    description: str = Field(description="Two or three sentence summary of the document content.")
    list_names: list[str] = Field(
        default_factory=list,
        description="Names of people or organizations mentioned in the document.",
    )
    date: str = Field(
        default="",
        description="Main date of the document in ISO format (YYYY-MM-DD). Empty string if not found.",
    )
    num_pages: int = Field(
        default=0,
        description="Number of pages. This is filled in by the extractor, not by the model.",
    )
    general_info: dict[str, str] = Field(
        default_factory=dict,
        description="Other relevant key/value facts found in the document (e.g. 'author': 'Jane Doe').",
    )
