import os
import uvicorn
from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from service import AgentService
from agents.base_agents import BaseAgent
from agents.parser_agent import TestScenarioAgent
from util import AskRequest

# --- Initialisation du service des agents ---
# agent_service = AgentService()

# --- Création de l'app FastAPI ---
agent = BaseAgent(
    name="TestAgent",
    description="Agent pour test API",
    system_prompt="You are a helpful assistant.",
    tools=[]  # tu peux ajouter des outils si nécessaire
)
parser = TestScenarioAgent()
app = FastAPI(title="LLM Agent API", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:8081")],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# --- Endpoints ---
@app.get("/")
def root():
    return {"message": "API LLM is up"}


@app.post("/askagent")
def ask_agent(request: AskRequest):
    try:
        response = agent.query(request.question)
        return {"answer": response}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/parse")
def parse_scenario(request: AskRequest):
    try:
        response = parser.analyze_scenario(request.question)
        return {"answer":response}
    except Exception as e:
        print(e)
        raise HTTPException(status_code = 500, detail= str(e))


# --- Lancement via Uvicorn ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
    
