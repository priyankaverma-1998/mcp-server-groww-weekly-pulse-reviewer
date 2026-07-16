from fastapi import FastAPI
from contextlib import asynccontextmanager
import sys
import os

# Import the shared MCP server instance
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import mcp

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield

app = FastAPI(lifespan=lifespan)
app.mount("/mcp", mcp.streamable_http_app())

@app.get("/")
def health():
    return {"status": "ok", "server": "google-workspace-mcp"}
