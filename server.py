from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import Agent

app = FastAPI(title= "LLM Agent API")

agent = Agent()


class AskRequest(BaseModel):
    prompt: str

@app.get("/health")
async def health_check():
    return {"status": "ok", "llm_agent":agent.is_ready()}

@app.post("/ask")
async def ask_llm(request:AskRequest):
    try:
        response = agent.ask(request.prompt)
        print(f"Response: {response}")
        return {"response":response}
    except Exception as e:
        raise HTTPException(status_code=500, detail = str(e))
    