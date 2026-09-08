import csv
from app.core.firebase import db

COLLECTION = "data"

def upload():
    with open("../data/naver_financials.csv", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    batch = db.batch()
    count = 0
    for row in rows:
        doc_ref = db.collection(COLLECTION).document()
        batch.set(doc_ref, {
            "date": row["date"],
            "value": float(row["value"]),
            "memo": row["memo"],
        })
        count += 1
        if count % 400 == 0:
            batch.commit()
            batch = db.batch()

    batch.commit()
    print(f"업로드 완료: 총 {count}건")

if __name__ == "__main__":
    upload()