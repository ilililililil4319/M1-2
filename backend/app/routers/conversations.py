from fastapi import APIRouter, HTTPException
from app.models.schemas import ConversationCreate, Message
from app.services import conversation_service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.post("")
def create(conv: ConversationCreate):
    return conversation_service.create_conversation(
        conv.title, [m.model_dump() for m in conv.messages]
    )

@router.get("")
def list_all():
    return conversation_service.list_conversations()

@router.get("/{doc_id}")
def get_one(doc_id: str):
    try:
        return conversation_service.get_conversation(doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{doc_id}/messages")
def add_message(doc_id: str, message: Message):
    try:
        return conversation_service.add_message(doc_id, message.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{doc_id}")
def delete(doc_id: str):
    try:
        conversation_service.delete_conversation(doc_id)
        return {"deleted": doc_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))