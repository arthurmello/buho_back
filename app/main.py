from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import (
    qa_tracker as qa_tracker_router,
    files as files_router,
    chat as chat_router,
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


# Include routers
app.include_router(qa_tracker_router.router, prefix="/qa_tracker", tags=["qa tracker"])
app.include_router(files_router.router, prefix="/files", tags=["files"])
app.include_router(chat_router.router, prefix="/chat", tags=["chat"])

if __name__ == "__main__":
    uvicorn.run(
        app, host="0.0.0.0", port=8080, timeout_keep_alive=600, forwarded_allow_ips="*"
    )
