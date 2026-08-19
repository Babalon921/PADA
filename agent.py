import os
import uuid
from typing import Dict, Any
import sqlite3
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from langchain.tools import tool
from tavily import TavilyClient

system_prompt = """

Be nice at for the moment, overly nice to the point its annoying.
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
def audio_analyst():
    """Analyse Audio Files with Librosa"""
    return "404"  ## for the moment

@tool
def store_sql():
    """Tool for storing data"""
    return "404"

agent = create_agent(
    "gpt-5-nano",
    checkpointer=checkpointer,
    tools=[web_search, audio_analyst, store_sql],
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
        if token.content:
            yield token.content