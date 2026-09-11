import re
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

# 제어 문자(널바이트 등) 제거용 정규식
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _sanitize_text(value: str) -> str:
    """서버 측 기본 정제: 제어 문자 제거 + 앞뒤 공백 제거.
    프론트엔드는 textContent로만 렌더링해 XSS를 막고 있지만,
    서버 측에서도 방어적으로 한 번 더 정제한다(AI 사전평가 항목 #17 보완).
    """
    value = _CONTROL_CHARS_RE.sub("", value)
    return value.strip()


class DataItem(BaseModel):
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD 형식")
    value: float
    memo: str = Field(..., min_length=1, max_length=100)

    @field_validator("memo")
    @classmethod
    def sanitize_memo(cls, v: str) -> str:
        v = _sanitize_text(v)
        if not v:
            raise ValueError("memo는 공백만으로 구성될 수 없습니다.")
        return v


class DataItemResponse(DataItem):
    id: str
    created_at: Optional[str] = None


class Message(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=5000)
    timestamp: Optional[str] = None

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        v = _sanitize_text(v)
        if not v:
            raise ValueError("content는 공백만으로 구성될 수 없습니다.")
        return v


class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    messages: List[Message]

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        return _sanitize_text(v)


class ConversationResponse(ConversationCreate):
    id: str
    created_at: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(default=None, max_length=200)

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        v = _sanitize_text(v)
        if not v:
            raise ValueError("message는 공백만으로 구성될 수 없습니다.")
        return v
