from pydantic import BaseModel
from typing import List, Optional

class DataItem(BaseModel):
    date: str
    value: float
    memo: str

class DataItemResponse(DataItem):
    id: str
    created_at: Optional[str] = None

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ConversationCreate(BaseModel):
    title: str
    messages: List[Message]

class ConversationResponse(ConversationCreate):
    id: str
    created_at: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None