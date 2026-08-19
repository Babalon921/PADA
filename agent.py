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



def respond(message: str) -> str:


    
    return message