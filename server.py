"""
Stub entry point to maintain backwards compatibility for local execution.
(e.g., 'python server.py')
"""
from mcp_server import mcp
import logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting Google Workspace MCP Server locally (via stub)...")
    mcp.run()
