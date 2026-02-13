from fastapi import FastAPI

from crafters_toolkit.api.routers import items, recipes
from crafters_toolkit.core.logging import setup_logging

setup_logging()
app = FastAPI(
    title="Crafters Toolkit",
    version="0.0.1",
)

app.include_router(items.router)
app.include_router(recipes.router)


@app.get("/")
def health_check():
    return {"status": "ok"}
