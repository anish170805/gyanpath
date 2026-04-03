# search_docs.py

import os
from dotenv import load_dotenv
from typing import List, Dict
from config import config   
from fastmcp import FastMCP
from langchain_exa import ExaSearchRetriever

# ---------------------------------------------------
# Load environment variables
# ---------------------------------------------------

load_dotenv()


if not config.EXA_API_KEY:
    raise ValueError("EXA_API_KEY not found in environment variables")


# ---------------------------------------------------
# Initialize MCP server
# ---------------------------------------------------

mcp = FastMCP("research_mcp")


# ---------------------------------------------------
# Initialize Exa retriever
# ---------------------------------------------------

retriever = ExaSearchRetriever(
    api_key=config.EXA_API_KEY,
    k=5,               # number of results
    highlights=True    # include highlighted snippets
)


# ---------------------------------------------------
# Helper function to format Exa results
# ---------------------------------------------------

def format_results(documents) -> List[Dict]:

    results = []

    for doc in documents:

        metadata = doc.metadata or {}

        results.append({
            "title": metadata.get("title"),
            "url": metadata.get("url"),
            "highlights": metadata.get("highlights"),
            "score": metadata.get("score")
        })

    return results


# ---------------------------------------------------
# MCP Tool: Search Docs
# ---------------------------------------------------

@mcp.tool()
async def search_docs(query: str) -> List[Dict]:
    """
    Search official documentation and high-quality learning resources
    using Exa semantic search.

    Args:
        query: topic or question to search

    Returns:
        list of resources containing title, url, highlights and score
    """

    try:

        # Improve query for learning resources
        refined_query = f"{query} documentation tutorial guide"

        docs = retriever.invoke(refined_query)

        return format_results(docs)

    except Exception as e:

        return [{
            "error": str(e)
        }]


# ---------------------------------------------------
# Run MCP Server
# ---------------------------------------------------

if __name__ == "__main__":
    mcp.run()