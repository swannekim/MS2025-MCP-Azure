"""
FastMCP quickstart example.
ref. https://github.com/modelcontextprotocol/python-sdk/blob/main/examples/snippets/servers/fastmcp_quickstart.py
"""

from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo-Server")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


# ========== OPTIONAL ==========
# Add a tool that uses a literal type for style
from typing import Literal

@mcp.tool()
def generate_greeting(
    name: str,
    style: Literal["friendly", "formal", "casual"] = "friendly"
) -> str:
    """Return a ready-made greeting sentence in the given style."""
    styles = {
        "friendly": f"Hi, {name}! It's great to meet you 🙂",
        "formal":   f"Hello {name}. I hope you're doing well. Please let me know if you need any assistance.",
        "casual":   f"Hey {name}! Good to see you 😄",
    }
    return styles.get(style, styles["friendly"])