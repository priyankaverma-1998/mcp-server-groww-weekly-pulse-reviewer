from fastapi import FastAPI
from contextlib import asynccontextmanager
import sys
import os

# Add root directory to sys.path so we can import mcp_server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_server import mcp

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield

app = FastAPI(lifespan=lifespan)
app.mount("/mcp", mcp.streamable_http_app())

@app.get("/")
def health():
    return {"status": "ok", "server": "google-workspace-mcp"}
