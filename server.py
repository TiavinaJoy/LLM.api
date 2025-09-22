from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import Agent
import json
import re

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
        raw_response = agent.ask(request.prompt)
        # Nettoyage : enlever ```json ... ``` si présent
        cleaned = re.sub(r"```json\s*|```", "", raw_response, flags=re.IGNORECASE).strip()
        # Essayer de parser en JSON
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # si impossible, renvoyer juste texte
            parsed = {"response": cleaned}
        return parsed
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    