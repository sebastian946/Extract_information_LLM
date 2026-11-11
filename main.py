import logging

import uvicorn
from fastapi import FastAPI

from config.settings import settings
from routes.routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Information Extraction API",
    description="API for extracting structured information from documents.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
