from app.core.firebase import db
from datetime import datetime, timezone
import statistics

COLLECTION = "data"

def create_data(item: dict) -> dict:
    doc_ref = db.collection(COLLECTION).document()
    payload = {
        "date": item["date"],
        "value": item["value"],
        "memo": item["memo"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    doc_ref.set(payload)
    return {"id": doc_ref.id, **payload}

def list_data() -> list:
    docs = db.collection(COLLECTION).order_by("date").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def update_data(doc_id: str, item: dict) -> dict:
    doc_ref = db.collection(COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        raise ValueError("문서를 찾을 수 없습니다.")
    update_payload = {"date": item["date"], "value": item["value"], "memo": item["memo"]}
    doc_ref.update(update_payload)
    return {"id": doc_id, **doc_ref.get().to_dict()}

def delete_data(doc_id: str) -> None:
    doc_ref = db.collection(COLLECTION).document(doc_id)
    if not doc_ref.get().exists:
        raise ValueError("문서를 찾을 수 없습니다.")
    doc_ref.delete()

def get_summary() -> dict:
    docs = list(db.collection(COLLECTION).order_by("date").stream())
    if not docs:
        return {"period": None, "count": 0, "metrics_by_indicator": {}, "trend": "데이터 없음"}

    records = [d.to_dict() for d in docs]
    dates = [r["date"] for r in records]

    by_memo = {}
    for r in records:
        by_memo.setdefault(r["memo"], []).append(r["value"])

    metrics_by_indicator = {}
    for memo, values in by_memo.items():
        # 변동성(표준편차): 데이터가 2개 이상일 때만 의미가 있음 (보너스 - 추가 지표)
        volatility = statistics.pstdev(values) if len(values) >= 2 else 0

        metrics_by_indicator[memo] = {
            "count": len(values),
            "latest": values[-1],
            "average": sum(values) / len(values),
            "max": max(values),
            "min": min(values),
            "volatility": volatility,
        }

    revenue_values = by_memo.get("매출액", [])
    if len(revenue_values) >= 2:
        trend = "상승" if revenue_values[-1] > revenue_values[-2] else "하락"
    else:
        trend = "판단 불가(데이터 부족)"

    return {
        "period": f"{min(dates)} ~ {max(dates)}",
        "count": len(records),
        "metrics_by_indicator": metrics_by_indicator,
        "trend": trend,
    }
