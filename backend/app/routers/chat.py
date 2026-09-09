from fastapi import APIRouter, HTTPException
from openai import OpenAI
import httpx
import os

from app.models.schemas import ChatRequest
from app.services import data_service, conversation_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

# trust_env=False: httpx가 Windows 시스템 환경변수를 자동으로 읽지 않도록 차단
# (한글 Windows 환경에서 encoding 오류 방지)
client = OpenAI(
    api_key=os.getenv("CODYSSEY_API_KEY"),
    base_url="https://copa.codyssey.kr/v1",
    http_client=httpx.Client(trust_env=False),
)

MODEL = "gpt-5-mini"
MAX_RETRIES = 2           # 기획서 Ⅶ: 최대 2회 재시도
TIMEOUT_SECONDS = 15       # 기획서 Ⅶ: 15초 이상 지연 시 타임아웃 처리
MAX_TOKENS = 2000          # gpt-5-mini는 추론(reasoning) 과정도 토큰을 소모하므로
                           # 800으로는 답변 전에 토큰이 소진되어 빈 응답이 나옴 (실측 확인됨)

SYSTEM_PROMPT_TEMPLATE = """당신은 온라인 셀러가 네이버 스마트스토어 입점을 결정하기 전에
플랫폼(네이버)의 재무 건전성을 판단하도록 돕는 분석 비서입니다.

조건:
1) 제공된 재무 데이터에 근거한 사실만 서술하고, 입점을 권하거나 말리는 확정적 조언은 하지 않는다.
2) 핵심 변동을 1~2문장으로 요약한다.
3) 부채비율·유동비율 같은 전문 용어는 짧게 풀어서 설명한다.

[네이버 재무 데이터 요약]
- 기간: {period}
- 데이터 개수: {count}개
- 최근 매출 추세: {trend}
- 지표별 통계(최신값/평균/최대/최소): {metrics}
"""


def _build_system_prompt() -> str:
    """/api/data/summary 로직을 재사용해 시스템 프롬프트에 데이터 요약을 주입한다."""
    summary = data_service.get_summary()
    return SYSTEM_PROMPT_TEMPLATE.format(
        period=summary.get("period") or "데이터 없음",
        count=summary.get("count", 0),
        trend=summary.get("trend", "판단 불가"),
        metrics=summary.get("metrics_by_indicator", {}),
    )


def _call_codyssey(system_prompt: str, user_message: str) -> str:
    """코디세이 API 호출. 실패 시 최대 MAX_RETRIES회 재시도 후 예외를 던진다."""
    last_error = None
    for _ in range(MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                timeout=TIMEOUT_SECONDS,
                max_tokens=MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:  # noqa: BLE001 - 인증오류/rate limit/타임아웃 등 모두 재시도 대상
            last_error = e
            continue
    raise RuntimeError(f"AI 응답 생성에 실패했습니다: {last_error}")


@router.post("")
def chat(req: ChatRequest):
    """
    워크플로우 (기획서 Ⅴ-2):
    질문 입력 → /api/data/summary 조회 → 시스템 프롬프트 주입
    → 코디세이 API 호출 → conversations에 자동 저장 → 응답 반환
    """
    system_prompt = _build_system_prompt()

    try:
        answer = _call_codyssey(system_prompt, req.message)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    user_msg = {"role": "user", "content": req.message}
    assistant_msg = {"role": "assistant", "content": answer}

    try:
        if req.conversation_id:
            # 기존 대화에 이어서 저장
            conversation_service.add_message(req.conversation_id, user_msg)
            conversation = conversation_service.add_message(req.conversation_id, assistant_msg)
        else:
            # 새 대화 생성 (제목은 첫 질문 앞부분으로 자동 생성)
            title = req.message[:30] + ("..." if len(req.message) > 30 else "")
            conversation = conversation_service.create_conversation(
                title=title,
                messages=[user_msg, assistant_msg],
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "conversation_id": conversation["id"],
        "answer": answer,
    }
