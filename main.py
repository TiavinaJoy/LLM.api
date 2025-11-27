import os
import uvicorn
from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from service import AgentService
# from util import AskRequest

# --- Initialisation du service des agents ---
# agent_service = AgentService()

# --- Création de l'app FastAPI ---
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


# @app.post("/ask")
# def ask_agent(request: AskRequest):
#     try:
#         response = agent_service.query_agent(request.agent_name, request.question)
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# --- Lancement via Uvicorn ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
