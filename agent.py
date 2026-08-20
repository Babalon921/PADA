import os
from datetime import datetime
import uuid
from typing import Dict, Any
import sqlite3
import pickle
from langchain_core.messages import AIMessageChunk, HumanMessage
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from langchain.tools import tool
from tavily import TavilyClient


import re
_AUDIO_EXT_RE = re.compile(r"[\w.-]+\.(?:wav|mp3|flac)", re.IGNORECASE)


global a_data, a_sr

system_prompt = """
You are PADA, a friendly tech/coding helper.

Tone: Warm and friendly, with a bit of humor and personality - but never over-explain. Keep responses short and to the point by default. Expand only if the user asks for more detail.

When helping with code or tech questions:
- Give the direct answer or fix first, not a lecture.
- Skip lengthy background unless asked.
- A light joke or casual aside is welcome, but don't force it every time.
- If something's genuinely ambiguous, ask one quick clarifying question instead of guessing at length.

Above all: be useful fast, stay likeable, don't ramble.
"""

load_dotenv()
tavily_client = TavilyClient()


conn = sqlite3.connect("chat_memory.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
checkpointer.setup()

@tool
def web_search(query: str) -> Dict[str, Any]:
    """Search the web for information"""
    return tavily_client.search(query)

@tool 
def time():
    "Fetches Time and Date"
    now = datetime.now()
    return now
    


@tool
def read_analysis_db(path: str = "") -> str:
    """Read rows from the audio_analysis table in analysis_results.db.
    No path to list every file that has been analysed.
    Specific file path or filename to get that file's
    extracted features """
    conn = sqlite3.connect("analysis_results.db")
    try:
        if path:
            match = _AUDIO_EXT_RE.search(path)
            filename = os.path.basename(match.group(0)) if match else os.path.basename(path)
            row = conn.execute(
                "SELECT path, result FROM audio_analysis WHERE path LIKE ? ORDER BY id DESC LIMIT 1",
                (f"%{filename}",),
            ).fetchone()
            if row is None:
                return f"No analysis found for: {path}"
            file_path, blob = row
            return f"{file_path}\n{_format_analysis_result(pickle.loads(blob))}"
        else:
            rows = conn.execute(
                "SELECT DISTINCT path FROM audio_analysis ORDER BY id"
            ).fetchall()
            if not rows:
                return "No analysis results stored yet."
            return "\n".join(r[0] for r in rows)
    finally:
        conn.close()

agent = create_agent(
    "gpt-5-nano",
    checkpointer=checkpointer,
    tools=[web_search,time,read_analysis_db],
    system_prompt=system_prompt
)

_thread_id = str(uuid.uuid4())


def stream_response(message: str):
    config = {"configurable": {"thread_id": _thread_id}}

    for token, metadata in agent.stream(
        {"messages": [HumanMessage(content=message)]},
        config,
        stream_mode="messages",
    ):
        if isinstance(token, AIMessageChunk) and token.content:
            yield token.content


def _format_analysis_result(result) -> str:
    lines = []
    for label, value in zip(result[::2], result[1::2]):
        if hasattr(value, "shape") and hasattr(value, "dtype"):
            lines.append(f"{label}: array shape={value.shape} dtype={value.dtype}")
        else:
            lines.append(f"{label}: {value}")
    return "\n".join(lines)
