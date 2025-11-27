import os
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langgraph.graph import StateGraph, END
from agents.state.AgentState import AgentState
from util.Encoder import Encoder


class BaseAgent:
    """
    Base Agent class for multi-agent system with LangGraph workflow.
    Supports tool calling and inter-agent communication.
    """
    
    def __init__(self, name: str, description: str, system_prompt: str, tools: list = None):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.llama_base_url = os.getenv("LLAMA_BASE_URL")
        self.llm_model = os.getenv("LLM_MODEL")
        self.tools = tools if tools is not None else []
        self.tools_dict = {}
        self.llm = None
        self.graph = None
        
        self._setup_models()
        self._setup_tools()
        self._build_graph()
    
    def run_interactive(self):
        """Run the agent in interactive mode."""
        print(f"\n=== {self.name.upper()} AGENT ===")
        print(f"Description: {self.description}")
        print("Type 'exit' or 'quit' to stop.\n")
        
        while True:
            user_input = input("\n🤖 Your question: ")
            if user_input.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            try:
                clean_input = Encoder.clean_text(user_input)
                
                start_time = time.time()
                response = self.query(clean_input)
                end_time = time.time()
                
                elapsed = end_time - start_time
                
                print("\n=== ANSWER ===")
                print(response)
                print(f"\033[92m⏱ Time taken: {elapsed:.2f}s\033[0m")
            except Exception as e:
                print(f"\033[91mError: {e}\033[0m")

    def query(self, question: str) -> str:
        """Query the agent with a question and return the response."""
        messages = [HumanMessage(content=question)]
        result = self.graph.invoke({"messages": messages})
        print(result['messages'][-1].content)
        return result['messages'][-1].content
    
    def add_tool(self, tool):
        """
        Add a new tool to the agent dynamically.
        Useful for adding inter-agent communication tools after initialization.
        """
        if tool not in self.tools:
            self.tools.append(tool)
            self._setup_tools()
            print(f"✓ Tool '{tool.name}' added to {self.name}")
        
    def _build_graph(self):
        """Build the LangGraph workflow."""
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("llm", self._call_llm)
        graph.add_node("tools", self._take_action)
        
        # Add edges
        graph.add_conditional_edges(
            "llm",
            self._should_continue,
            {True: "tools", False: END}
        )
        graph.add_edge("tools", "llm")
        
        # Set entry point
        graph.set_entry_point("llm")
        
        self.graph = graph.compile()

    def _should_continue(self, state: AgentState) -> bool:
        """Check if the last message contains tool calls."""
        last_message = state['messages'][-1]
        return hasattr(last_message, 'tool_calls') and len(last_message.tool_calls) > 0
    
    def _call_llm(self, state: AgentState) -> AgentState:
        """Call the LLM with the current state."""
        messages = [SystemMessage(content=self.system_prompt)] + list(state['messages'])
        
        # Invoke LLM
        print("----------")
        print(messages)
        response = self.llm.invoke(messages)
        
        # Log response
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"\033[94m[{self.name}]\033[0m Requesting tools: {[t['name'] for t in response.tool_calls]}")
        else:
            print(f"\033[94m[{self.name}]\033[0m Response: {response.content[:100]}...")
        
        return {'messages': state['messages'] + [response]}
    
    def _take_action(self, state: AgentState) -> AgentState:
        """Execute tool calls from the LLM's response."""
        tool_calls = state['messages'][-1].tool_calls
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            
            print(f"\033[93m[Tool]\033[0m Executing: {tool_name}({tool_args})")
            
            if tool_name not in self.tools_dict:
                result = f"Error: Tool '{tool_name}' not found. Available tools: {list(self.tools_dict.keys())}"
                print(f"\033[91m{result}\033[0m")
            else:
                try:
                    result = self.tools_dict[tool_name].invoke(tool_args)
                    print(f"\033[92m[Tool]\033[0m Result: {str(result)[:200]}...")
                except Exception as e:
                    result = f"Error executing {tool_name}: {str(e)}"
                    print(f"\033[91m{result}\033[0m")
            
            results.append(
                ToolMessage(
                    tool_call_id=tool_call['id'],
                    name=tool_name,
                    content=str(result)
                )
            )
        
        return {'messages': state['messages'] + results}
    
    def _setup_tools(self):
        """Setup tools dictionary and bind to LLM."""
        self.tools_dict = {tool.name: tool for tool in self.tools}
        
        if self.tools:
            self.llm = self.llm.bind_tools(self.tools)
            print(f"✓ {len(self.tools)} tool(s) bound to {self.name}")
        
    def _setup_models(self):
        """Initialize LLM model."""
        self.llm = ChatOpenAI(
            base_url=self.llama_base_url,
            api_key="not-needed",  # llama.cpp doesn't need API key
            model=self.llm_model,
            temperature=0.1,
            streaming=False  # Explicitly disable streaming
        )
        print(f"LLM initialized: {self.llm_model} at {self.llama_base_url}")
    
    def get_info(self) -> dict:
        """Return agent information for inter-agent communication."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": [tool.name for tool in self.tools]
        }