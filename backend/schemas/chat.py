from pydantic import BaseModel

class ChatRequest(BaseModel):
    node_id: int
    question: str

class ChatResponse(BaseModel):
    node_id: int
    question: str
    answer: str
    model: str
    response_ms: float
