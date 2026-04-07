from fastmcp import FastMCP

from MCP.research.youtube_tools import youtube_search, youtube_transcript
from MCP.research.search_docs import search_docs


mcp = FastMCP("research_mcp")

mcp.tool()(youtube_search)
mcp.tool()(youtube_transcript)
mcp.tool()(search_docs)


if __name__ == "__main__":
    mcp.run()