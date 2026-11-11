import logging
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from llm.graph import graph
from models.models import DataInput, FormatOutput

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Information Extraction"],
)

UPLOAD_DIR = Path("files")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOW_EXTENSIONS = {"pdf", "png", "txt"}


def _get_extension(filename: str) -> str:
    extension = Path(filename).suffix.lstrip(".").lower()
    if extension not in ALLOW_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: '{extension}'. Supported types are: {', '.join(sorted(ALLOW_EXTENSIONS))}",
        )
    return extension


async def _run_graph(file_path: Path, extension: str) -> FormatOutput:
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {file_path}",
        )

    try:
        # ainvoke no bloquea el servidor mientras el modelo responde
        result = await graph.ainvoke({"type_file": extension, "file_url": str(file_path)})
    except Exception:
        logger.exception("Extraction failed for %s", file_path)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Error occurred while extracting information. Check server logs.",
        )

    return result["formatted_output"]


@router.post("/extract", response_model=FormatOutput)
async def extract_from_upload(file: UploadFile = File(...)) -> FormatOutput:
    """Sube un archivo (pdf, png o txt) y devuelve la información extraída."""
    extension = _get_extension(file.filename or "")

    # Nombre único para evitar colisiones y rutas manipuladas por el cliente
    destination = UPLOAD_DIR / f"{uuid4().hex}.{extension}"
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        return await _run_graph(destination, extension)
    finally:
        destination.unlink(missing_ok=True)


@router.post("/extract-from-path", response_model=FormatOutput)
async def extract_from_path(data: DataInput) -> FormatOutput:
    """Procesa un archivo que ya existe en el disco del servidor."""
    extension = _get_extension(data.file_url)
    return await _run_graph(Path(data.file_url), extension)
