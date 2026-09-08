from app.core.firebase import db
from datetime import datetime, timezone

COLLECTION = "conversations"

def create_conversation(title: str, messages: list) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    payload = {
        "title": title,
        "messages": messages,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_ref.set(payload)
    return {"id": doc_ref.id, **payload}

def list_conversations() -> list:
    docs = db.collection(COLLECTION).order_by("created_at", direction="DESCENDING").stream()
    result = []
    for d in docs:
        data = d.to_dict()
        result.append({
            "id": d.id,
            "title": data.get("title"),
            "created_at": data.get("created_at"),
            "message_count": len(data.get("messages", [])),
        })
    return result

def get_conversation(doc_id: str) -> dict:
    doc_ref = db.collection(COLLECTION).document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise ValueError("대화를 찾을 수 없습니다.")
    return {"id": doc.id, **doc.to_dict()}

def add_message(doc_id: str, message: dict) -> dict:
    doc_ref = db.collection(COLLECTION).document(doc_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise ValueError("대화를 찾을 수 없습니다.")
    messages = doc.to_dict().get("messages", [])
    messages.append(message)
    doc_ref.update({"messages": messages})
    return {"id": doc_id, **doc_ref.get().to_dict()}

def delete_conversation(doc_id: str) -> None:
    doc_ref = db.collection(COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        raise ValueError("대화를 찾을 수 없습니다.")
    doc_ref.delete()