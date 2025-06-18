import datetime
import os

from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from prompts import ai_bus_system_prompt


def create_graph():
    llm = ChatOpenAI(
        openai_api_base=os.environ["LLAMACPP_API_ENDPOINT"], 
        openai_api_key="hello.world"
    )

    prompt = SystemMessage(ai_bus_system_prompt)

    tools = load_tools(["serpapi"])

    checkpointer = MemorySaver()
    
    graph = create_react_agent(
        model=llm,
        tools=tools,  
        prompt=prompt,
        checkpointer=checkpointer
    )
    
    return graph
