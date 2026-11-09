from pydantic import BaseModel, Field


class FormatOutput(BaseModel):
    """
    A Pydantic model to define the expected output format for the LLM.
    """
    title: str
    description: str
    list_names: list[str]
    date: str
    num_pages: int = Field(default=0)
    general_info: dict = Field(default_factory=dict)
    