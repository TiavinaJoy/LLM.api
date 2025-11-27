from typing import Annotated, Sequence, TypedDict, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """State definition for the agent graph."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    message_sumary : str