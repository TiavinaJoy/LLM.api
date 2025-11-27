from pydantic import BaseModel

class AskRequest(BaseModel):
    agent_name: str
    question: str