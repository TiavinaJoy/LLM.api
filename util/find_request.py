from pydantic import BaseModel

class FindRequest(BaseModel):
    action: str
    target: str
    url : str
    htmlcontent : str