from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.documents import router as documents_router
from routes.chat import router as chat_router
from routes.comparison import router as comparison_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://contract-ai-phi.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    documents_router,
    prefix="/api/documents"
)

app.include_router(
    chat_router,
    prefix="/api/chat"
)

app.include_router(
    comparison_router,
    prefix="/api/comparison"
)


@app.get("/")
def root():
    return {
        "message": "Contract AI backend is running"
    }