from fastapi import FastAPI

from backend.app.api.routes import router

app = FastAPI(
    title="DevFlow Copilot API",
    description="API for multimodal software requirement analysis.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "DevFlow Copilot API is running."
    }


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy"
    }