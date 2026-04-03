import re
import yt_dlp
from fastmcp import FastMCP
from youtubesearchpython import VideosSearch
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi



mcp = FastMCP("youtube_tools")


# -----------------------------------------------------
# YouTube Search Tool
# -----------------------------------------------------

@mcp.tool()
async def youtube_search(topic: str):
    """
    Search YouTube for learning videos on a topic.
    Returns top tutorial videos.
    """

    query = f"ytsearch5:{topic} tutorial"

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "extract_flat": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(query, download=False)

    videos = []

    for entry in results["entries"]:
        videos.append({
            "title": entry["title"],
            "url": f"https://www.youtube.com/watch?v={entry['id']}",
            "channel": entry.get("uploader", "Unknown"),
        })

    return videos


# -----------------------------------------------------
# YouTube Transcript Tool
# -----------------------------------------------------

@mcp.tool()
async def youtube_transcript(url: str):
    """
    Get transcript of a YouTube video.
    """

    video_id = re.search(r"(?:v=|youtu\.be/)([^&]+)", url).group(1)

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)

        text = " ".join([t.text for t in transcript])

        return {
            "video_url": url,
            "transcript": text[:5000]
        }

    except (TranscriptsDisabled, NoTranscriptFound):
        return None