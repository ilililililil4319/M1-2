from app.core.firebase import db

docs = db.collection("data").stream()
for d in docs:
    data = d.to_dict()
    if data.get("date") == "string" or data.get("memo") == "string":
        print("발견:", d.id, data)